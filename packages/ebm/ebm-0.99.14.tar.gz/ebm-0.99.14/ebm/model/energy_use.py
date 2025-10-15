import numpy as np
import pandas as pd

from ebm import extractors
from ebm.energy_consumption import HEATING_SYSTEM_SHARE, GRUNNLAST_ANDEL, BASE_LOAD_EFFICIENCY, BASE_LOAD_ENERGY_PRODUCT, \
    PEAK_LOAD_ENERGY_PRODUCT, PEAK_LOAD_COVERAGE, PEAK_LOAD_EFFICIENCY, TERTIARY_LOAD_COVERAGE, TERTIARY_LOAD_EFFICIENCY, \
    TERTIARY_LOAD_ENERGY_PRODUCT, COOLING_EFFICIENCY, DHW_EFFICIENCY, DOMESTIC_HOT_WATER_ENERGY_PRODUCT
from ebm.model import energy_need as e_n, heating_systems_parameter as h_s_param
from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.s_curve import calculate_s_curves


def base_load(heating_systems_projection: pd.DataFrame) -> pd.DataFrame:
    heating_systems_projection['heating_system'] = '-'
    df = heating_systems_projection[
        ['building_category', 'building_code', 'year', 'heating_systems', HEATING_SYSTEM_SHARE, GRUNNLAST_ANDEL, BASE_LOAD_EFFICIENCY,
         BASE_LOAD_ENERGY_PRODUCT, 'heating_system']].copy()
    df = df.rename(columns={GRUNNLAST_ANDEL: 'load_share', BASE_LOAD_EFFICIENCY: 'load_efficiency',
                            BASE_LOAD_ENERGY_PRODUCT: 'energy_product'})
    df.loc[:, 'load'] = 'base'
    df.loc[:, 'purpose'] = 'heating_rv'
    df['heating_system'] = df.heating_systems.apply(lambda s: s.split('-')[0])
    df['heating_system'] = df['heating_system'].str.strip()
    return df


def peak_load(heating_systems_projection:pd.DataFrame) -> pd.DataFrame:
    df = heating_systems_projection[
        ['building_category', 'building_code', 'year', 'heating_systems', HEATING_SYSTEM_SHARE, PEAK_LOAD_COVERAGE, PEAK_LOAD_EFFICIENCY,
         PEAK_LOAD_ENERGY_PRODUCT, 'heating_system']].copy()
    df = df.rename(columns={PEAK_LOAD_COVERAGE: 'load_share', PEAK_LOAD_EFFICIENCY: 'load_efficiency',
                            PEAK_LOAD_ENERGY_PRODUCT: 'energy_product'})
    df.loc[:, 'load'] = 'peak'
    df.loc[:, 'purpose'] = 'heating_rv'
    df['heating_system'] = df.heating_systems.apply(lambda s: s.split('-')[1:2]).explode('heating_system')
    df['heating_system'] = df['heating_system'].str.strip()
    return df


def tertiary_load(heating_systems_projection: pd.DataFrame) ->pd.DataFrame:
    df = heating_systems_projection[
        ['building_category', 'building_code', 'year', 'heating_systems', HEATING_SYSTEM_SHARE, TERTIARY_LOAD_COVERAGE, TERTIARY_LOAD_EFFICIENCY,
         TERTIARY_LOAD_ENERGY_PRODUCT, 'heating_system']].copy()
    df = df.rename(columns={TERTIARY_LOAD_COVERAGE: 'load_share', TERTIARY_LOAD_EFFICIENCY: 'load_efficiency',
                            TERTIARY_LOAD_ENERGY_PRODUCT: 'energy_product'})
    df.loc[:, 'load'] = 'tertiary'
    df.loc[:, 'purpose'] = 'heating_rv'
    df['heating_system'] = df.heating_systems.apply(lambda s: s.split('-')[2:3]).explode('heating_system')
    df['heating_system'] = df['heating_system'].str.strip()
    return df


def heating_rv(heating_systems_projection: pd.DataFrame) -> pd.DataFrame:
    df = heating_systems_projection.copy()

    base = base_load(df)
    peak = peak_load(df)
    tertiary = tertiary_load(df)

    return pd.concat([base, peak, tertiary])


def heating_dhw(heating_systems_projection: pd.DataFrame) ->pd.DataFrame:
    df = heating_systems_projection[
        ['building_category', 'building_code', 'year', 'heating_systems', HEATING_SYSTEM_SHARE, GRUNNLAST_ANDEL, DHW_EFFICIENCY,
         DOMESTIC_HOT_WATER_ENERGY_PRODUCT]].copy()
    df.loc[:, GRUNNLAST_ANDEL] = 1.0
    df = df.rename(columns={GRUNNLAST_ANDEL: 'load_share', DHW_EFFICIENCY: 'load_efficiency',
                            DOMESTIC_HOT_WATER_ENERGY_PRODUCT: 'energy_product'})

    df.loc[:, 'load'] = 'dhw'
    df['purpose'] = 'heating_dhw'
    return df


def cooling(heating_systems_projection: pd.DataFrame) -> pd.DataFrame:
    df = heating_systems_projection[
        ['building_category', 'building_code', 'year', 'heating_systems', HEATING_SYSTEM_SHARE, GRUNNLAST_ANDEL, COOLING_EFFICIENCY,
         BASE_LOAD_ENERGY_PRODUCT]].copy()
    df.loc[:, GRUNNLAST_ANDEL] = 1.0
    df.loc[:, BASE_LOAD_ENERGY_PRODUCT] = 'Electricity'
    df = df.rename(columns={GRUNNLAST_ANDEL: 'load_share', COOLING_EFFICIENCY: 'load_efficiency',
                            BASE_LOAD_ENERGY_PRODUCT: 'energy_product'})

    df.loc[:, 'load'] = 'base'
    df.loc[:, 'purpose'] = 'cooling'
    return df


def other(heating_systems_projection: pd.DataFrame) -> pd.DataFrame:
    df = heating_systems_projection[
        ['building_category', 'building_code', 'year', 'heating_systems', HEATING_SYSTEM_SHARE, GRUNNLAST_ANDEL, BASE_LOAD_EFFICIENCY,
         BASE_LOAD_ENERGY_PRODUCT]].copy()
    df.loc[:, GRUNNLAST_ANDEL] = 1.0
    df.loc[:, BASE_LOAD_EFFICIENCY] = 1.0
    df.loc[:, BASE_LOAD_ENERGY_PRODUCT] = 'Electricity'
    df = df.rename(columns={GRUNNLAST_ANDEL: 'load_share', BASE_LOAD_EFFICIENCY: 'load_efficiency',
                            BASE_LOAD_ENERGY_PRODUCT: 'energy_product'})
    df.loc[:, 'load'] = 'base'
    df.loc[:, '_purposes'] = 'electrical_equipment,fans_and_pumps,lighting'
    df = df.assign(**{'purpose': df['_purposes'].str.split(',')}).explode('purpose')
    df = df.drop(columns=['_purposes'], errors='ignore')

    return df.reset_index().drop(columns=['index'], errors='ignore')


def all_purposes(heating_systems_projection: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([heating_rv(heating_systems_projection), heating_dhw(heating_systems_projection),
               cooling(heating_systems_projection), other(heating_systems_projection)])


def efficiency_factor(heating_systems: pd.DataFrame) -> pd.DataFrame:
    df = heating_systems
    df.loc[:, 'efficiency_factor'] = df.loc[:, 'heating_system_share'] * df.loc[:, 'load_share'] / df.loc[:, 'load_efficiency']

    return df


def energy_use_kwh(energy_need: pd.DataFrame, efficiency_factor: pd.DataFrame) -> pd.DataFrame:
    nrj = energy_need.copy()

    df = nrj.reset_index().merge(efficiency_factor,
                                 left_on=['building_category', 'building_code', 'purpose', 'year'],
                                 right_on=['building_category', 'building_code', 'purpose', 'year'])

    df['kwh'] = df['energy_requirement'] * df['heating_system_share'] * df['load_share'] / df['load_efficiency']
    if 'kwh_m2' in df.columns:
        df['kwh_m2'] = df['kwh_m2'] * df['efficiency_factor']
    else:
        df['kwh_m2'] = np.nan
    return df


def building_group_energy_use_kwh(heating_systems_parameter: pd.DataFrame, energy_need: pd.DataFrame) -> pd.DataFrame:
    df = all_purposes(heating_systems_parameter)
    df.loc[:, 'building_group'] = 'Non-residential'
    df.loc[df.building_category.isin(['house', 'apartment_block']), 'building_group'] = 'Residential'

    efficiency_factor_df = efficiency_factor(df)
    df = energy_use_kwh(energy_need=energy_need, efficiency_factor=efficiency_factor_df)

    return df


def energy_use_gwh_by_building_group(energy_use_kwh: pd.DataFrame) -> pd.DataFrame:
    energy_use_by_building_group = energy_use_kwh[['building_group', 'year', 'energy_product', 'kwh']].groupby(
        by=['building_group', 'energy_product', 'year']).sum() / 1_000_000
    energy_use_wide = energy_use_by_building_group.reset_index().pivot(columns=['year'],
                                                                       index=['building_group', 'energy_product'],
                                                                       values=['kwh'])
    energy_use_wide = energy_use_wide.reset_index()
    energy_use_wide.columns = ['building_group', 'energy_source'] + [c for c in energy_use_wide.columns.get_level_values(1)[2:]]
    return energy_use_wide


def calculate_energy_use(database_manager: 'DatabaseManager',
                         years: YearRange|None=YearRange(2020, 2050),
                         area_parameters:pd.DataFrame|None=None,
                         scurve_parameters: pd.DataFrame|None=None,
                         building_code_parameters:pd.DataFrame|None=None) -> pd.DataFrame:
    """
    calculates energy use in KWh by building_category, TEK, building_condition, year, purpose.

    The dataframe is index by row index. (subject to change)

    extra columns
    m2, original_kwh_m2, reduction_yearly, reduction_policy, reduction_condition, reduced_kwh_m2,
       behaviour_factor, kwh_m2, energy_requirement, heating_systems,
       heating_system_share, load_share, load_efficiency, energy_product,
       heating_system, load, building_group, efficiency_factor

    Parameters
    ----------
    database_manager : pd.DataFrame
    years : YearRange, optional
    area_parameters : pd.DataFrame, optional
    scurve_parameters : pd.DataFrame, optional
    building_code_parameters : pd.DataFrame, optional

    Returns
    -------
    pd.DataFrame
        energy use in KWh by building_category, TEK, building_condition, year, purpose
        ,
    """
    scurve_parameters = database_manager.get_scurve_params() if scurve_parameters is None else scurve_parameters
    area_parameters = database_manager.get_area_parameters() if area_parameters is None else area_parameters
    area_parameters['year'] = years.start
    building_code_parameters = database_manager.file_handler.get_building_code() if building_code_parameters is None else building_code_parameters

    s_curves_by_condition = calculate_s_curves(scurve_parameters, building_code_parameters, years)  # 📌
    area_forecast = extractors.extract_area_forecast(years, s_curves_by_condition, building_code_parameters, area_parameters, database_manager)  # 📍

    energy_need_kwh_m2 = extractors.extract_energy_need(years, database_manager)  # 📍
    total_energy_need = e_n.transform_total_energy_need(energy_need_kwh_m2, area_forecast)  # 📌

    heating_systems_projection = extractors.extract_heating_systems_forecast(years, database_manager)  # 📍
    heating_systems_parameter = h_s_param.heating_systems_parameter_from_projection(heating_systems_projection)  # 📌
    energy_use_kwh_with_building_group = building_group_energy_use_kwh(heating_systems_parameter, total_energy_need)

    return energy_use_kwh_with_building_group
