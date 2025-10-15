from loguru import logger
import pandas as pd

from ebm.model.energy_purpose import EnergyPurpose
from ebm.model.filter_tek import FilterTek

ADJUSTED_REQUIREMENT = 'eq_ts'
# there are 3 time-of-use zones: peak, shoulder and offpeak.
HEATING_RV_BASE_TOTAL = 'RV_GL'
HEATING_RV_PEAK_TOTAL = 'RV_SL'
HEATING_RV_TERTIARY_TOTAL = 'RV_EL'
HEAT_PUMP = 'RV_HP'
COOLING_TOTAL = 'CL_KV'
DHW_TOTAL = 'DHW_TV'
OTHER_TOTAL = 'O_SV'
HEATING_RV = 'heating_rv'
HEATING_DHW = 'heating_dhw'
COOLING = 'cooling'
DHW_EFFICIENCY = 'domestic_hot_water_efficiency'

HEATING_SYSTEMS = 'heating_systems'
HEATING_SYSTEM_SHARE = 'heating_system_share'
GRUNNLAST_ANDEL = 'base_load_coverage'
BASE_LOAD_EFFICIENCY = 'base_load_efficiency'
COOLING_EFFICIENCY = 'cooling_efficiency'
SPESIFIKT_ELFORBRUK = 'Spesifikt elforbruk'
TERTIARY_LOAD_COVERAGE = 'tertiary_load_coverage'
TERTIARY_LOAD_EFFICIENCY = 'tertiary_load_efficiency'
PEAK_LOAD_COVERAGE = 'peak_load_coverage'
PEAK_LOAD_EFFICIENCY = 'peak_load_efficiency'

BASE_LOAD_ENERGY_PRODUCT = 'base_load_energy_product'
PEAK_LOAD_ENERGY_PRODUCT = 'peak_load_energy_product'
TERTIARY_LOAD_ENERGY_PRODUCT = 'tertiary_load_energy_product'
DOMESTIC_HOT_WATER_ENERGY_PRODUCT = 'domestic_hot_water_energy_product'
HP_ENERGY_SOURCE = 'hp_source'


class EnergyConsumption:
    def __init__(self, heating_systems_parameters: pd.DataFrame = None):
        self.heating_systems_parameters = heating_systems_parameters

    def grouped_heating_systems(self) -> pd.DataFrame:
        """
        Groups and sums heating_system_parameters over building_category, TEK, Oppvarmingstyper. All excess values will
            be summed.

        Returns
        -------
        pd.DataFrame
            heating_systems_parameters grouped and summed
        """
        df = self.heating_systems_parameters
        df = df.rename(columns={'heating_system_share': HEATING_SYSTEM_SHARE})

        aggregates = {'base_load_energy_product': 'first', 'peak_load_energy_product': 'first',
                      'tertiary_load_energy_product': 'first', 'domestic_hot_water_energy_product': 'first', HEATING_SYSTEM_SHARE: 'sum',
                      TERTIARY_LOAD_COVERAGE: 'sum', GRUNNLAST_ANDEL: 'sum', PEAK_LOAD_COVERAGE: 'sum',
                      BASE_LOAD_EFFICIENCY: 'sum', PEAK_LOAD_EFFICIENCY: 'sum', TERTIARY_LOAD_EFFICIENCY: 'sum',
                      DHW_EFFICIENCY: 'sum', SPESIFIKT_ELFORBRUK: 'sum', COOLING_EFFICIENCY: 'sum'}
        grouped = df.groupby(by=['building_category', 'building_code', 'year', HEATING_SYSTEMS]).agg(aggregates)
        return grouped.reset_index()

    def calculate(self, energy_requirements: pd.DataFrame) -> pd.DataFrame:
        """
        calculate energy usage by from energy_requirements and heating_systems_parameters

        Parameters
        ----------
        energy_requirements : pd.DataFrame

        Returns
        -------
        pd.DataFrame

        """
        logger.debug('Calculate heating systems')
        if all([col in energy_requirements.columns for col in ['building_category', 'building_code', 'building_condition', 'year', 'purpose']]):
            energy_requirements = energy_requirements.set_index(['building_category', 'building_code', 'building_condition', 'year', 'purpose'])
        energy_requirements = self._remove_building_code_suffix(energy_requirements)
        energy_requirements = self._group_and_sum_same_building_code(energy_requirements)

        # If _RES of _COM is in building_codethis will not work
        # energy_requirements.index[energy_requirements.index.str.endswith('_RES')]
        if energy_requirements.index.get_level_values('building_code').str.endswith(
                '_RES').any() or energy_requirements.index.get_level_values('building_code').str.endswith('_COM').any():
            raise ValueError('Found _RES or _COM in energy_requirements')
        self.heating_systems_parameters = self.heating_systems_parameters.rename(columns={'heating_system_share': HEATING_SYSTEM_SHARE})
        # Merge energy_requirements and heating_systems into df
        df = self._merge_energy_requirement_and_heating_systems(energy_requirements)

        # Make column eq_ts for heating_system_share adjusted energy requirement
        df[ADJUSTED_REQUIREMENT] = (df.energy_requirement * df[HEATING_SYSTEM_SHARE]).astype(float)

        # Zero fill columns before calculating to prevent NaN from messing up sums
        df.loc[:, [HEATING_RV_BASE_TOTAL, HEATING_RV_PEAK_TOTAL, HEATING_RV_TERTIARY_TOTAL, DHW_TOTAL, COOLING_TOTAL, OTHER_TOTAL,
                   HEAT_PUMP]] = 0.0

        # Adjust energy requirements by efficiency
        # heating rv

        df = self.adjust_heat_pump(df)
        df = self.adjust_heating_rv(df)
        df = self.adjust_heating_dhw(df)
        df = self.adjust_cooling(df)
        df = self.adjust_other(df)

        # sum energy use
        df.loc[:, 'kwh'] = df.loc[:,
                           [HEATING_RV_BASE_TOTAL, HEATING_RV_PEAK_TOTAL, HEATING_RV_TERTIARY_TOTAL, DHW_TOTAL, COOLING_TOTAL,
                            OTHER_TOTAL]].sum(axis=1)

        df.loc[:, 'gwh'] = df.loc[:, 'kwh'] / 10 ** 6

        df = df.sort_index(level=['building_category', 'building_code', 'year', 'building_condition', 'purpose', HEATING_SYSTEMS])
        return df[[HEATING_SYSTEM_SHARE, ADJUSTED_REQUIREMENT,
                   HEATING_RV_BASE_TOTAL, BASE_LOAD_ENERGY_PRODUCT, BASE_LOAD_EFFICIENCY,
                   HEATING_RV_PEAK_TOTAL, PEAK_LOAD_ENERGY_PRODUCT, PEAK_LOAD_EFFICIENCY,
                   HEATING_RV_TERTIARY_TOTAL, TERTIARY_LOAD_ENERGY_PRODUCT, TERTIARY_LOAD_EFFICIENCY,
                   DHW_TOTAL, DOMESTIC_HOT_WATER_ENERGY_PRODUCT, COOLING_TOTAL, OTHER_TOTAL, HEAT_PUMP, HP_ENERGY_SOURCE, 'kwh', 'gwh']]

    def adjust_heat_pump(self, df):
        df[HP_ENERGY_SOURCE] = None
        gass = ['HP Central heating - Gas']
        vannbasert = [n for n in df.index.get_level_values('heating_systems').unique() if
                      n.startswith('HP Central heating')]
        elektrisk = [n for n in df.index.get_level_values('heating_systems').unique() if
                     n.startswith('HP') and n not in vannbasert]

        gass_slice = (slice(None), slice(None), slice(None), slice(None), gass)
        vann_slice = (slice(None), slice(None), ['heating_rv', 'heating_dhw'], slice(None), slice(None),
                      vannbasert)  # , 'heating_dhw'
        el_slice = (slice(None), slice(None), ['heating_rv'], slice(None), slice(None), elektrisk)  # 'heating_dhw'

        df.loc[vann_slice, HEAT_PUMP] = df.loc[vann_slice, ADJUSTED_REQUIREMENT] * df.loc[vann_slice, GRUNNLAST_ANDEL]
        df.loc[vann_slice, HP_ENERGY_SOURCE] = 'Heat pump central heating'

        df.loc[el_slice, HEAT_PUMP] = df.loc[el_slice, ADJUSTED_REQUIREMENT] * df.loc[el_slice, GRUNNLAST_ANDEL]
        df.loc[el_slice, HP_ENERGY_SOURCE] = 'Heat pump air-air'
        return df

    def adjust_other(self, df):
        # lighting, electrical equipment, fans and pumps energy use is calculated by dividing with spesific electricity
        # useage
        other_slice = (slice(None), slice(None), EnergyPurpose.other(), slice(None), slice(None))
        df.loc[other_slice, OTHER_TOTAL] = df.loc[other_slice, ADJUSTED_REQUIREMENT] / df.loc[
            other_slice, SPESIFIKT_ELFORBRUK]
        return df

    def adjust_cooling(self, df):
        # cooling energy use is calculated by dividing cooling with 'cooling_efficiency'
        cooling_slice = (slice(None), slice(None), COOLING, slice(None), slice(None))
        df.loc[cooling_slice, COOLING_TOTAL] = df.loc[cooling_slice, ADJUSTED_REQUIREMENT] / df.loc[
            cooling_slice, COOLING_EFFICIENCY]
        return df

    def adjust_heating_dhw(self, df):
        # heating dhw energy use is calculated by dividing heating_dhw with 'domestic_hot_water_efficiency'
        heating_dhw_slice = (slice(None), slice(None), HEATING_DHW, slice(None), slice(None))
        df.loc[heating_dhw_slice, DHW_TOTAL] = df.loc[heating_dhw_slice, ADJUSTED_REQUIREMENT] / df.loc[
            heating_dhw_slice, DHW_EFFICIENCY]
        return df

    def adjust_heating_rv(self, df):
        heating_rv_slice = (slice(None), slice(None), HEATING_RV, slice(None), slice(None))
        df.loc[heating_rv_slice, HEATING_RV_BASE_TOTAL] = (
                df.loc[heating_rv_slice, ADJUSTED_REQUIREMENT] * df.loc[heating_rv_slice, GRUNNLAST_ANDEL] / df.loc[
            heating_rv_slice, BASE_LOAD_EFFICIENCY])
        df.loc[heating_rv_slice, HEATING_RV_PEAK_TOTAL] = (
                df.loc[heating_rv_slice, ADJUSTED_REQUIREMENT] * df.loc[heating_rv_slice, PEAK_LOAD_COVERAGE] / df.loc[
            heating_rv_slice, PEAK_LOAD_EFFICIENCY])
        df.loc[heating_rv_slice, HEATING_RV_TERTIARY_TOTAL] = (
                df.loc[heating_rv_slice, ADJUSTED_REQUIREMENT] * df.loc[heating_rv_slice, TERTIARY_LOAD_COVERAGE] / df.loc[
            heating_rv_slice, TERTIARY_LOAD_EFFICIENCY])
        return df

    def _merge_energy_requirement_and_heating_systems(self, energy_requirements):
        df = energy_requirements.reset_index().merge(self.heating_systems_parameters.reset_index(),
            left_on=['building_category', 'building_code', 'year'], right_on=['building_category', 'building_code', 'year'])[
            ['building_category', 'building_condition', 'purpose', 'building_code', 'year', 'kwh_m2', 'm2', 'energy_requirement',
             HEATING_SYSTEMS, HEATING_SYSTEM_SHARE, GRUNNLAST_ANDEL, BASE_LOAD_EFFICIENCY, BASE_LOAD_ENERGY_PRODUCT,
             PEAK_LOAD_COVERAGE, PEAK_LOAD_EFFICIENCY, PEAK_LOAD_ENERGY_PRODUCT, TERTIARY_LOAD_EFFICIENCY, TERTIARY_LOAD_COVERAGE,
             TERTIARY_LOAD_ENERGY_PRODUCT, DOMESTIC_HOT_WATER_ENERGY_PRODUCT, DHW_EFFICIENCY, SPESIFIKT_ELFORBRUK, COOLING_EFFICIENCY]]
        # Unused columns
        # ,'Innfyrt_energi_kWh','Innfyrt_energi_GWh','Energibehov_samlet_GWh']]
        df = df.set_index(
            ['building_category', 'building_condition', 'purpose', 'building_code', 'year', HEATING_SYSTEMS]).sort_index()
        return df

    @staticmethod
    def _group_and_sum_same_building_code(energy_requirements):
        energy_requirements = FilterTek.merge_building_code(energy_requirements, 'TEK69', ['TEK69_1976', 'TEK69_1986'])
        energy_requirements = FilterTek.merge_building_code(energy_requirements, 'PRE_TEK49',
                                                  ['PRE_TEK49_1940', 'PRE_TEK49_1950'])
        energy_requirements = energy_requirements.sort_index()
        return energy_requirements

    @staticmethod
    def _remove_building_code_suffix(energy_requirements):
        energy_requirements = FilterTek.remove_building_code_suffix(energy_requirements, suffix='_RES')
        energy_requirements = FilterTek.remove_building_code_suffix(energy_requirements, suffix='_COM')
        return energy_requirements


def calibrate_heating_systems(df: pd.DataFrame, factor: pd.DataFrame, multiply=False) -> pd.DataFrame:
    # When factor is empty or all factors are 1.0, there is no need to change anything.
    if len(factor) == 0 or (factor.factor == 1.0).all():
        return df
    original = df.copy()
    factor = factor.copy()

    if multiply:
        factor['factor'] = factor['factor'] * 100

    # Add action and value
    df_to = original.merge(factor,
                           left_on=['building_category', 'heating_systems'],
                           right_on=['building_category', 'to'])

    df_from = original.merge(factor,
                             left_on=['building_category', 'heating_systems'],
                             right_on=['building_category', 'from'])

    # Calculate value to add
    df_to_add = df_to.set_index(['building_category', 'building_code', 'year', 'to'])

    if multiply:
        df_to_add['v'] = (df_to_add.heating_system_share * df_to_add.factor)/100 - df_to_add.heating_system_share
    else:
        df_to_add['v'] = df_to_add.heating_system_share * df_to_add.factor - df_to_add.heating_system_share

    # Calculate value to subtract
    df_to_subtract = df_from.set_index(['building_category', 'building_code', 'year', 'from', 'to'])

    df_to_subtract = df_to_subtract.sort_index()
    df_to_subtract.loc[:, 'v'] = -df_to_add.reset_index().groupby(by=['building_category', 'building_code', 'year', 'from', 'to']).agg(
        {'v': 'sum'})

    # Join add and substract rows
    addition_grouped = df_to_add.groupby(by=['building_category', 'building_code', 'year', 'to']).agg(
        {'v': 'sum', 'heating_systems': 'first', 'heating_system_share': 'first', 'factor': 'first', 'from': 'first'})
    subtraction_grouped = df_to_subtract.groupby(by=['building_category', 'building_code', 'year', 'from']).agg(
        {'v': 'sum', 'heating_systems': 'first', 'heating_system_share': 'first', 'factor': 'first'})

    df_to_sum = original.set_index(['building_category', 'building_code', 'year', 'heating_systems'])
    df_to_sum = df_to_sum.sort_index()
    df_to_sum.loc[:, 'add'] = addition_grouped.loc[:, 'v']
    df_to_sum.loc[:, 'sub'] = subtraction_grouped.loc[:, 'v'].fillna(0)
    df_to_sum.loc[:, 'sub'] = df_to_sum.loc[:, 'sub'].fillna(0)

    df_to_sum.heating_system_share = df_to_sum.heating_system_share + df_to_sum['add'].fillna(0) + df_to_sum['sub'].fillna(0)

    calibrated_and_original = pd.concat([df_to_sum.reset_index(), original.reset_index()]).drop_duplicates(
        ['building_category', 'building_code', 'year', 'heating_systems'],
        keep='first').drop(columns='index',
                           errors='ignore')

    columns_to_keep = ['building_category', 'building_code', 'year', 'heating_systems', 'heating_system_share']
    return calibrated_and_original[columns_to_keep].reset_index(drop=True)


def calibrate_heating_systems_adder(df: pd.DataFrame, factor: pd.DataFrame) -> pd.DataFrame:
    # When factor is empty or all factors are 1.0, there is no need to change anything.
    if len(factor) == 0 or (factor.factor == 0.0).all():
        return df
    original = df.copy()
    factor = factor.copy()

    # Add action and value
    df_to = original.merge(factor,
                           left_on=['building_category', 'heating_systems'],
                           right_on=['building_category', 'to'])

    df_from = original.merge(factor,
                             left_on=['building_category', 'heating_systems'],
                             right_on=['building_category', 'from'])

    # Calculate value to add
    df_to_add = df_to.set_index(['building_category', 'building_code', 'year', 'to'])

    df_to_add['v'] = df_to_add.factor

    # Calculate value to subtract
    df_to_subtract = df_from.set_index(['building_category', 'building_code', 'year', 'from', 'to'])
    df_to_subtract.loc[:, 'v'] = -df_to_add.reset_index().groupby(by=['building_category', 'building_code', 'year', 'from', 'to']).agg(
        {'v': 'sum'})

    # Join add and substract rows
    addition_grouped = df_to_add.groupby(by=['building_category', 'building_code', 'year', 'to']).agg(
        {'v': 'sum', 'heating_systems': 'first', 'heating_system_share': 'first', 'factor': 'first', 'from': 'first'})
    subtraction_grouped = df_to_subtract.groupby(by=['building_category', 'building_code', 'year', 'from']).agg(
        {'v': 'sum', 'heating_systems': 'first', 'heating_system_share': 'first', 'factor': 'first'})

    df_to_sum = original.set_index(['building_category', 'building_code', 'year', 'heating_systems'])
    df_to_sum.loc[:, 'add'] = addition_grouped.loc[:, 'v']
    df_to_sum.loc[:, 'sub'] = subtraction_grouped.loc[:, 'v'].fillna(0)
    df_to_sum.loc[:, 'sub'] = df_to_sum.loc[:, 'sub'].fillna(0)

    df_to_sum.heating_system_share = df_to_sum.heating_system_share + df_to_sum['add'].fillna(0) + df_to_sum['sub'].fillna(0)

    calibrated_and_original = pd.concat([df_to_sum.reset_index(), original.reset_index()]).drop_duplicates(
        ['building_category', 'building_code', 'year', 'heating_systems'],
        keep='first').drop(columns='index',
                           errors='ignore')

    columns_to_keep = ['building_category', 'building_code', 'year', 'heating_systems', 'heating_system_share']
    return calibrated_and_original[columns_to_keep].reset_index(drop=True)
