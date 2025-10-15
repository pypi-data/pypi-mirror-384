import os
from typing import Optional

import pandas as pd

from ebm import extractors
from ebm.cmd.result_handler import transform_to_sorted_heating_systems
from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.model import heating_systems_parameter as h_s_param
from ebm.model import energy_need as e_n
from ebm.model import energy_use as e_u

from ebm.model.file_handler import FileHandler
from ebm.s_curve import calculate_s_curves


def calculate_energy_use_wide(ebm_input):
    fh = FileHandler(directory=ebm_input)
    database_manager = DatabaseManager(file_handler=fh)
    years = YearRange(2020, 2050)

    heating_systems_projection = extractors.extract_heating_systems_forecast(years, database_manager)  # 📍
    heating_systems_parameter = h_s_param.heating_systems_parameter_from_projection(heating_systems_projection)  # 📌

    building_code_parameters = database_manager.file_handler.get_building_code()  # 📍
    scurve_parameters = database_manager.get_scurve_params()  # 📍

    s_curves_by_condition = calculate_s_curves(scurve_parameters, building_code_parameters, years)  # 📌
    area_parameters = database_manager.get_area_parameters()  # 📍
    area_forecast = extractors.extract_area_forecast(years, s_curves_by_condition, building_code_parameters,
                                                     area_parameters, database_manager)  # 📍
    energy_need_kwh_m2 = extractors.extract_energy_need(years, database_manager)  # 📍
    total_energy_need = e_n.transform_total_energy_need(energy_need_kwh_m2, area_forecast)  # 📌

    energy_use_kwh = e_u.building_group_energy_use_kwh(heating_systems_parameter, total_energy_need)  # 📌
    energy_use_gwh_by_building_group = e_u.energy_use_gwh_by_building_group(energy_use_kwh)
    energy_use_holiday_homes = extractors.extract_energy_use_holiday_homes(database_manager)  # 📍
    energy_use_wide = transform_to_sorted_heating_systems(energy_use_gwh_by_building_group, energy_use_holiday_homes,
                                                          building_column='building_group')

    return energy_use_wide


def calculate_area_forecast(input_directory: Optional[str] = None, file_handler: Optional[FileHandler] = None,
                            database_manager: Optional[DatabaseManager] = None,
                            years: Optional[YearRange] = None,
                            scurve_parameters: Optional[pd.DataFrame] = None,
                            area_parameters: Optional[pd.DataFrame] = None,
                            building_code_parameters: Optional[pd.DataFrame] = None,
                            s_curves_by_condition: Optional[pd.DataFrame] = None,
                            ) -> pd.DataFrame:
    input_dir = os.environ.get('EBM_INPUT_DIRECTORY', 'input') if input_directory is None else input_directory

    fh = file_handler
    if file_handler is None:
        fh = FileHandler(directory=input_dir)

    dm = database_manager
    if database_manager is None:
        dm = DatabaseManager(file_handler=fh)

    years = years if years is not None else YearRange(
        int(os.environ.get('EBM_START_YEAR', 2020)),
        int(os.environ.get('EBM_END_YEAR', 2050)))

    scurve_parameters = dm.get_scurve_params() if scurve_parameters is None else scurve_parameters
    building_code_parameters = dm.file_handler.get_building_code() if building_code_parameters is None else building_code_parameters
    area_parameters = dm.get_area_parameters() if area_parameters is None else area_parameters

    area_parameters['year'] = years.start

    if not s_curves_by_condition:
        s_curves_by_condition = calculate_s_curves(scurve_parameters, building_code_parameters, years)  # 📌

    df = extractors.extract_area_forecast(years, s_curves_by_condition, building_code_parameters, area_parameters, dm)  # 📍

    return df.set_index(['building_category', 'building_code', 'building_condition', 'year'])


def calculate_energy_need(input_directory: Optional[str] = None, file_handler: Optional[FileHandler] = None,
                          database_manager: Optional[DatabaseManager] = None,
                          years: Optional[YearRange] = None) -> pd.DataFrame:
    dm = database_manager
    input_dir = os.environ.get('EBM_INPUT_DIRECTORY', 'input') if input_directory is None else input_directory

    years = years if years is not None else YearRange(
        int(os.environ.get('EBM_START_YEAR', 2020)),
        int(os.environ.get('EBM_END_YEAR', 2050)))

    fh = file_handler
    if file_handler is None:
        fh = FileHandler(directory=input_dir)

    if database_manager is None:
        dm = DatabaseManager(file_handler=fh)

    energy_need = extractors.extract_energy_need(years, dm)  # 📍
    return energy_need
