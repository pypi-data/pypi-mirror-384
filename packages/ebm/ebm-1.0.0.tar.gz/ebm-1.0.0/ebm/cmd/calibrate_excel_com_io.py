import os
import pathlib
import time

import pandas as pd
from dotenv import load_dotenv
from loguru import logger

from ebm.cmd.calibrate import run_calibration, write_dataframe
from ebm.cmd.helpers import configure_loglevel
from ebm.model.file_handler import FileHandler
from ebm.model.database_manager import DatabaseManager
from ebm.model.calibrate_energy_requirements import EnergyRequirementCalibrationWriter, \
    EnergyConsumptionCalibrationWriter
from ebm.model.calibrate_heating_systems import DistributionOfHeatingSystems, group_heating_systems_by_energy_carrier
from ebm.services.calibration_writer import ComCalibrationReader, ExcelComCalibrationResultWriter

LOG_FORMAT = """
<green>{time:HH:mm:ss.SSS}</green> | <blue>{elapsed}</blue> | <level>{level: <8}</level> | <cyan>{function: <20}</cyan>:<cyan>{line: <3}</cyan> - <level>{message}</level>
""".strip()


def heatpump_filter(df):
    vannbasert = [n for n in df.index.get_level_values('heating_systems').unique() if
                  n.startswith('HP Central heating')]
    elektrisk = [n for n in df.index.get_level_values('heating_systems').unique() if
                 n.startswith('HP') and n not in vannbasert]
    el_slice = (slice(None), ['original_condition'], ['heating_rv'], ['TEK07'], slice(None), elektrisk + vannbasert)
    df = df.loc[el_slice]  # luftluft
    return df


def main():
    start_time = time.time()
    load_dotenv(pathlib.Path('.env'))
    configure_loglevel(log_format=LOG_FORMAT)

    write_to_disk = os.environ.get('EBM_WRITE_TO_DISK', 'False').upper() == 'TRUE'
    calibration_year = int(os.environ.get('EBM_CALIBRATION_YEAR', 2023))
    calibration_spreadsheet_name = os.environ.get("EBM_CALIBRATION_OUT", "Kalibreringsark.xlsx!Ut")
    calibration_sheet = os.environ.get("EBM_CALIBRATION_SHEET", "Kalibreringsark.xlsx!Kalibreringsfaktorer")
    energy_requirements_calibration_file = os.environ.get('EBM_CALIBRATION_ENERGY_REQUIREMENT',
                                                          f'kalibrering/{FileHandler.CALIBRATE_ENERGY_REQUIREMENT}')
    energy_consumption_calibration_file = os.environ.get('EBM_CALIBRATION_ENERGY_CONSUMPTION',
                                                          f'kalibrering/{FileHandler.CALIBRATE_ENERGY_CONSUMPTION}')

    energy_source_target_cells = os.environ.get('EBM_CALIBRATION_ENERGY_SOURCE_USAGE', 'C64:E68')
    ebm_calibration_energy_heating_pump = os.environ.get('EBM_CALIBRATION_ENERGY_HEATING_PUMP', 'C72:E74')
    hs_distribution_cells = os.environ.get('EBM_CALIBRATION_ENERGY_HEATING_SYSTEMS_DISTRIBUTION', 'C32:F44')

    output_directory = pathlib.Path('output')

    logger.info(f'Loading {calibration_sheet}')
    workbook_name = calibration_sheet.split('!')[0]
    sheet_name = calibration_sheet.split('!')[1] if '!' in calibration_sheet else 'Kalibreringsfaktorer'

    com_calibration_reader = ComCalibrationReader(workbook_name, sheet_name)
    calibration = com_calibration_reader.extract()
    logger.info(f'Make {calibration_sheet} compatible with ebm')
    energy_source_by_building_group = com_calibration_reader.transform(calibration)

    logger.info('Write calibration to ebm')
    eq_calibration_writer = EnergyRequirementCalibrationWriter()
    eq_calibration_writer.load(energy_source_by_building_group, energy_requirements_calibration_file)

    ec_calibration_writer = EnergyConsumptionCalibrationWriter()
    ec_calibration = ec_calibration_writer.transform(energy_source_by_building_group)
    ec_calibration_writer.load(ec_calibration, energy_consumption_calibration_file)

    logger.info('Calculate calibrated energy use')
    area_forecast = None
    area_forecast_file = pathlib.Path('kalibrert/area_forecast.csv')
    if area_forecast_file.is_file():
        logger.info(f'  Using {area_forecast_file}')
        area_forecast = pd.read_csv(area_forecast_file)

    database_manager = DatabaseManager(FileHandler(directory='kalibrert'))

    df = run_calibration(database_manager, calibration_year=2023,
                         area_forecast=area_forecast, write_to_output=write_to_disk)

    # df = heatpump_filter(df)

    logger.info('Transform heating systems')

    energy_source_by_building_group = group_heating_systems_by_energy_carrier(df)
    energy_source_by_building_group = energy_source_by_building_group.xs(2023, level='year')

    if write_to_disk:
        if not output_directory.is_dir():
            output_directory.mkdir()
        write_dataframe(energy_source_by_building_group, 'energy_source_by_building_group')

    energy_source_by_building_group = energy_source_by_building_group.fillna(0)

    logger.info(f'Writing heating systems distribution to {calibration_spreadsheet_name}')
    hs_distribution_writer = ExcelComCalibrationResultWriter(excel_filename=calibration_spreadsheet_name,
                                                             target_cells=hs_distribution_cells)

    distribution_of_heating_systems = DistributionOfHeatingSystems()
    shares_start_year = distribution_of_heating_systems.extract(database_manager)
    heating_systems_distribution = distribution_of_heating_systems.transform(shares_start_year)

    hs_distribution_writer.extract()
    hs_distribution_writer.transform(heating_systems_distribution)
    hs_distribution_writer.load()

    logger.info(f'Writing energy_source using writer to {calibration_spreadsheet_name}')
    energy_source_excel_com_writer = ExcelComCalibrationResultWriter(
        excel_filename=calibration_spreadsheet_name, target_cells=energy_source_target_cells)

    energy_source_excel_com_writer.extract()
    energy_source_excel_com_writer.transform(energy_source_by_building_group)
    energy_source_excel_com_writer.load()

    logger.info(f'Writing calculated energy pump use to {calibration_spreadsheet_name}')
    heatpump_excel_com_writer = ExcelComCalibrationResultWriter(
        excel_filename=calibration_spreadsheet_name, target_cells=ebm_calibration_energy_heating_pump)

    heatpump_excel_com_writer.extract()
    heatpump_excel_com_writer.transform(energy_source_by_building_group)
    heatpump_excel_com_writer.load()

    logger.info(f'Calibrated {calibration_spreadsheet_name} in {round(time.time() - start_time, 2)} seconds')


if __name__ == '__main__':
    main()
