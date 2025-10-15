import pandas as pd
from loguru import logger

from ebm.model import area
from ebm.holiday_home_energy import calculate_energy_use, transform_holiday_homes_to_horizontal
from ebm.heating_system_forecast import HeatingSystemsForecast
from ebm.model.construction import ConstructionCalculator

from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.model.energy_requirement import EnergyRequirement
from ebm.s_curve import calculate_s_curves


def extract_area_forecast(years: YearRange, s_curves_by_condition: pd.DataFrame, building_code_parameters: pd.DataFrame, area_parameters: pd.DataFrame, database_manager:DatabaseManager):
    logger.debug('Calculating area by condition')

    s_curve_demolition = s_curves_by_condition['s_curve_demolition']
    s_curves_by_condition = s_curves_by_condition[[
        'original_condition',  'small_measure', 'renovation', 'renovation_and_small_measure', 'demolition'
    ]]

    area_parameters = area_parameters.set_index(['building_category', 'building_code'])

    demolition_floor_area_by_year = area.calculate_demolition_floor_area_by_year(area_parameters, s_curve_demolition)

    building_category_demolition_by_year = area.sum_building_category_demolition_by_year(demolition_floor_area_by_year)
    construction_floor_area_by_year = ConstructionCalculator.calculate_all_construction(
        demolition_by_year=building_category_demolition_by_year,
        database_manager=database_manager,
        period=years)

    construction_by_building_category_and_year = area.construction_with_building_code(
        building_category_demolition_by_year=building_category_demolition_by_year,
        construction_floor_area_by_year=construction_floor_area_by_year,
        building_code=building_code_parameters,
        years=years)

    existing_area = area.calculate_existing_area(area_parameters, building_code_parameters, years)

    total_area_floor_by_year = area.merge_total_area_by_year(construction_by_building_category_and_year, existing_area)

    floor_area_forecast = area.multiply_s_curves_with_floor_area(s_curves_by_condition, total_area_floor_by_year)

    return floor_area_forecast


def write_scurve(s_curves_by_condition):
    try:
        output_file = 'output/s_curves.xlsx'
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            s_curves_by_condition.to_excel(writer, sheet_name='s_curves_by_condition', merge_cells=False)  # 💾
            # s_curve_demolition.to_excel(writer, sheet_name='s_curve_demolition', merge_cells=False) # 💾
    except IOError as ex:
        logger.exception(ex)
        logger.info(f'There was an IOError while writing to {output_file}. Moving on!')


def extract_energy_need(years: YearRange, dm: DatabaseManager) -> pd.DataFrame:
    er_calculator = EnergyRequirement.new_instance(period=years, calibration_year=2023,
                                                   database_manager=dm)
    energy_need = er_calculator.calculate_for_building_category(database_manager=dm)

    energy_need = energy_need.set_index(['building_category', 'building_code', 'purpose', 'building_condition', 'year'])

    return energy_need


def extract_heating_systems_forecast(years: YearRange, database_manager: DatabaseManager) -> pd.DataFrame:
    forecast_period = YearRange(2023, 2050)
    hsp = HeatingSystemsForecast.new_instance(forecast_period, database_manager)
    df: pd.DataFrame = hsp.calculate_forecast()
    df = hsp.pad_projection(df, YearRange(2020, 2022))

    heating_system_forecast = df.copy()
    return heating_system_forecast


def extract_energy_use_holiday_homes(database_manager):
    df = transform_holiday_homes_to_horizontal(calculate_energy_use(database_manager)).copy()
    df = df.rename(columns={'building_category': 'building_group'})
    df.loc[df.energy_source=='Elektrisitet', 'energy_source'] = 'Electricity'
    df.loc[df.energy_source=='fossil', 'energy_source'] = 'Fossil'
    return df


def main():
    from ebm.model.file_handler import FileHandler
    fh = FileHandler(directory='input')
    dm = DatabaseManager(fh)
    years = YearRange(2020, 2050)

    building_code_parameters = fh.get_building_code()
    scurve_params = dm.get_scurve_params()
    s_curves_by_condition = calculate_s_curves(scurve_params, building_code_parameters, years)

    area_forecast = extract_area_forecast(years,
                                          building_code_parameters=building_code_parameters,
                                          area_parameters=dm.get_area_parameters(),
                                          s_curves_by_condition=s_curves_by_condition,
                                          database_manager=dm)

    print(area_forecast)

    energy_need_kwh_m2 = extract_energy_need(years, dm)
    print(energy_need_kwh_m2)

    heating_systems_projection = extract_heating_systems_forecast(years, dm)
    print(heating_systems_projection)




if __name__ == '__main__':
    main()
