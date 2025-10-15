import os
import pathlib
from typing import Dict

import pandas as pd
from loguru import logger

from ebm.extractors import extract_area_forecast
from ebm.model.building_category import BuildingCategory

from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.model.energy_requirement import EnergyRequirement
from ebm.energy_consumption import EnergyConsumption
from ebm.heating_system_forecast import HeatingSystemsForecast
from ebm.s_curve import calculate_s_curves


def area_forecast_result_to_dataframe(forecast: pd.DataFrame) -> pd.DataFrame:
    """
    Create a dataframe from a forecast

    Parameters
    ----------
    forecast : Dict[str, list[float]]

    Returns dataframe : pd.Dataframe
        A dataframe of all area values in forecast indexed by building_category, tek and year
    -------

    """
    return forecast


# noinspection PyTypeChecker
def result_to_horizontal_dataframe(result: pd.DataFrame) -> pd.DataFrame:
    """
    Create a dataframe from a forecast with years listed horizontally start to end year

    Parameters
    ----------
    result : pd.DataFrame:

    Returns
    -------
    dataframe : pd.Dataframe
        A dataframe of all area values in forecast indexed by building_category, tek and year


    """
    stacked = result.stack().to_frame().reset_index()

    columns = 'year'
    index = list(filter(lambda x: x != columns and x != 'index' and x not in [0], stacked.columns))
    values = stacked.columns[-1]

    df = stacked.pivot(columns=columns, index=index, values=values)

    df.index.names = df.index.names[:-1] + ['unit']
    return df


def validate_years(start_year: int, end_year: int) -> YearRange:
    """
    Validates the start and end year arguments and returns a YearRange

    Parameters
    ----------
    end_year : int
        The end year to validate.
    start_year : int
        The start year to validate.

    Returns
    -------
    YearRange
        from start_year to end_year

    Raises
    ------
    ValueError
        If `start_year` is greater than or equal to `end_year`.
        If `end_year` is not exactly 40 years after `start_year`.
        If `start_year` is not 2010 or `end_year` is not 2050.
    """
    if start_year >= end_year:
        msg = f'Unexpected input start year ({start_year} is greater than end year ({end_year})'
        raise ValueError(msg)
    if start_year < 2010:
        msg = f'Unexpected start_year={start_year}. The minimum start year is 2010'
        raise ValueError(msg)
    if end_year > 2070:
        msg = f'Unexpected end_year={end_year}. Max end_year year is 2070'
        raise ValueError(msg)
    return YearRange(start_year, end_year)


def calculate_building_category_energy_requirements(building_category: BuildingCategory,
                                                    area_forecast,
                                                    database_manager: DatabaseManager,
                                                    start_year: int,
                                                    end_year: int,
                                                    calibration_year: int = 2019) -> pd.DataFrame:
    """
    Calculate energy need by building_category, TEK, building_condition and purpose.

    The parameter building_category is not used and should be removed.

    Parameters
    ----------
    building_category : BuildingCategory, unused
    area_forecast : pd.DataFrame
    database_manager : DatabaseManager
    start_year : int
    end_year : int
    calibration_year : int, optional

    Returns
    -------
    pd.DataFrame
    """
    energy_requirement = EnergyRequirement.new_instance(
        period=YearRange(start_year, end_year),
        calibration_year=calibration_year if calibration_year > start_year else start_year,
        database_manager=database_manager)
    df = energy_requirement.calculate_for_building_category(database_manager=database_manager)

    df = df.set_index(['building_category', 'building_code', 'purpose', 'building_condition', 'year'])

    q = area_forecast.reset_index()

    q = q.set_index(['building_category', 'building_code', 'building_condition', 'year'])

    merged = q.merge(df, left_index=True, right_index=True)
    merged['energy_requirement'] = merged.kwh_m2 * merged.m2

    return merged


def write_to_disk(constructed_floor_area, building_category: BuildingCategory):
    """Writes constructed_floor_area to disk if the environment variable EBM_WRITE_TO_DISK is True"""
    if os.environ.get('EBM_WRITE_TO_DISK', 'False').upper() == 'TRUE':
        df = result_to_horizontal_dataframe(constructed_floor_area)
        df.insert(0, 'building_category', building_category)
        file_path = pathlib.Path('output/construction.xlsx')
        df.index.name = 'series'

        if building_category == BuildingCategory.HOUSE or not file_path.is_file():
            df.to_excel(file_path, sheet_name='construction')
            logger.debug(f'Wrote {file_path}')
        else:
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                start_row = writer.sheets['construction'].max_row
                df.to_excel(writer, sheet_name='construction', index=True, header=False, startrow=start_row)
            logger.debug(f'Added {building_category} to {file_path}')


def calculate_building_category_area_forecast(database_manager: DatabaseManager,
                                              start_year: int,
                                              end_year: int) -> pd.DataFrame:
    """
    Calculates the area forecast for a given building category from start to end year (including).

    Parameters
    ----------
    database_manager : DatabaseManager
        The database manager used to interact with the database.
    start_year : int
        The starting year of the forecast period.
    end_year : int
        The ending year of the forecast period.

    Returns
    -------
    pd.DataFrame
        A dictionary where keys are strings representing different area categories and values are lists of floats
            representing the forecasted areas for each year in the specified period.

    Notes
    -----
    This function builds the buildings for the specified category, calculates the area forecast, and accounts for
        demolition and construction over the specified period.
    """
    building_code_parameters = database_manager.file_handler.get_building_code()
    years = YearRange(start_year, end_year)
    scurve_params = database_manager.get_scurve_params()
    s_curves_by_condition = calculate_s_curves(scurve_params, building_code_parameters, years)

    area_forecast = extract_area_forecast(years,
                                          building_code_parameters=building_code_parameters,
                                          area_parameters=database_manager.get_area_parameters(),
                                          s_curves_by_condition=s_curves_by_condition,
                                          database_manager=database_manager)

    return area_forecast


def calculate_heating_systems(energy_requirements, database_manager: DatabaseManager) -> pd.DataFrame:
    """
    Calculate heating systems projection, efficiencies and multiplies by energy_requirements for total energy use
    by building_category, TEK, building_condition, purpose and heating_system.

    Parameters
    ----------
    energy_requirements : pd.DataFrame
    database_manager : ebm.model.database_manager.DatabaseManager

    Returns
    -------
    pd.DataFrame

    """
    projection_period = YearRange(2023, 2050)
    hsp = HeatingSystemsForecast.new_instance(projection_period, database_manager)
    hf = hsp.calculate_forecast()
    hf = hsp.pad_projection(hf, YearRange(2020, 2022))
    calculator = EnergyConsumption(hf)
    calculator.heating_systems_parameters = calculator.grouped_heating_systems()
    df = calculator.calculate(energy_requirements)

    return df
