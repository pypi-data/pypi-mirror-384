import pathlib

from loguru import logger
import pandas as pd

from dotenv import load_dotenv

from ebm.model.bema import map_sort_order

from ebm.model.calibrate_heating_systems import extract_area_forecast, extract_energy_requirements, \
    extract_heating_systems
from ebm.model.data_classes import YearRange
from ebm.services.files import make_unique_path

CALIBRATION_YEAR = 2023

model_period = YearRange(2020, 2050)
start_year = model_period.start
end_year = model_period.end


def run_calibration(database_manager,
                    calibration_year,
                    area_forecast: pd.DataFrame = None,
                    write_to_output = False):
    """

    Parameters
    ----------
    database_manager : ebm.model.database_manager.DatabaseManager

    Returns
    -------
    pandas.core.frame.DataFrame
    """
    load_dotenv(pathlib.Path('.env'))

    input_directory = database_manager.file_handler.input_directory

    logger.info(f'Using input directory "{input_directory}"')
    logger.info('Extract area forecast')
    area_forecast = extract_area_forecast(database_manager) if area_forecast is None else area_forecast
    if write_to_output:
        write_dataframe(area_forecast[area_forecast.year == calibration_year], 'area_forecast')

    logger.info('Extract energy requirements')
    energy_requirements = extract_energy_requirements(area_forecast, database_manager)
    if write_to_output:
        en_req = energy_requirements.xs(2023, level='year').reset_index().sort_values(
            by='building_category', key=lambda x: x.map(map_sort_order))
        write_dataframe(en_req, 'energy_requirements')
        grouped = en_req[['building_category', 'm2', 'kwh_m2', 'energy_requirement']].groupby(
            by=['building_category'], as_index=False).agg({'m2': 'first', 'kwh_m2': 'first', 'energy_requirement': 'sum'})
        grouped = grouped.sort_values(by='building_category', key=lambda x: x.map(map_sort_order))
        write_dataframe(grouped, 'energy_requirements_sum', sheet_name='sum')

    logger.info('Extract heating systems')
    heating_systems = extract_heating_systems(energy_requirements, database_manager)
    if write_to_output:
        write_dataframe(heating_systems.xs(2023, level='year'), 'heating_systems')


    return heating_systems


def write_dataframe(df, name='dataframe', sheet_name='Sheet1'):
    output_directory = pathlib.Path('output')
    if output_directory.is_dir():
        logger.debug(f'Writing {name} to file')
        output_file = output_directory / f'{name}.xlsx'
        output_file = make_unique_path(output_file)
        df.to_excel(output_file, merge_cells=False, sheet_name=sheet_name)
        logger.info(f'Wrote {name} to {output_file} ! {sheet_name if sheet_name!="Sheet1" else ""}')
    else:
        logger.warning(f'Cannot write to {output_directory}. Directory does not exists')


def main():
    raise NotImplementedError('Running calibrate as a script is not supported')


if __name__ == '__main__':
    main()
