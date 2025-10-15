import pathlib
import time

from loguru import logger
import pandas as pd

from ebm.cmd.run_calculation import (calculate_building_category_area_forecast,
                                     calculate_building_category_energy_requirements,
                                     calculate_heating_systems)
from ebm.model import bema
from ebm.model.calibrate_heating_systems import group_heating_systems_by_energy_carrier
from ebm.model.building_category import BuildingCategory
from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.services.spreadsheet import detect_format_from_values, find_max_column_width


def transform_model_to_horizontal(model, value_column = 'm2'):
    hz = model.reset_index().copy()
    if 'energy_requirement' in hz.columns:
        value_column = 'GWh'
        hz['GWh'] = hz['energy_requirement'] / 10**6
    hz = hz.groupby(by=['building_category', 'building_code', 'building_condition', 'year'], as_index=False).sum()[
        ['building_category', 'building_code', 'building_condition', 'year', value_column]]
    hz = hz.pivot(columns=['year'], index=['building_category', 'building_code', 'building_condition'], values=[
        value_column]).reset_index()

    hz = hz.sort_values(by=['building_category', 'building_code', 'building_condition'], key=bema.map_sort_order)
    hz.insert(3, 'U', value_column)
    hz.columns = ['building_category', 'building_code', 'building_condition', 'U'] + [y for y in range(2020, 2051)]

    return hz


def transform_to_sorted_heating_systems(df: pd.DataFrame, holiday_homes: pd.DataFrame,
                                        building_column: str='building_category',
                                        ) -> pd.DataFrame:
    category_order = {'bloig': 100,
                      'Bolig': 100,
                      'Residential': 100,
                      'Fritidsboliger': 200,
                      'fritidsboliger': 200,
                      'Holiday homes': 200,
                      'Non-residential': 300,
                      'yrkesbygg': 300,
                      'Yrkesbygg': 300}
    energy_source = {'Elektrisitet': 10,
                     'Electricity': 10,
                     'Fjernvarme': 11,
                     'DH': 11,
                     'Bio': 12, 'Fossil': 13, 'Solar': 13,
                     'Luft/luft': 24,
                     'Heat pump air-air': 24,
                     'Heat pump central heating': 25}

    rs = pd.concat([df, holiday_homes]).reindex()
    rs = rs.sort_values(by=[building_column, 'energy_source'],
                   key=lambda x: x.map(category_order) if x.name == building_column else x.map(
                       energy_source) if x.name == 'energy_source' else x)

    hz = pd.concat([rs[~rs['energy_source'].isin(['Heat pump air-air', 'Heat pump central heating'])],
                      rs[rs['energy_source'].isin(['Heat pump air-air', 'Heat pump central heating'])]])
    hz.insert(2, 'U', 'GWh')
    return hz


def transform_heating_systems_to_horizontal(model: pd.DataFrame):
    hs2 = model
    energy_carrier_by_building_group = group_heating_systems_by_energy_carrier(hs2)

    r2 = energy_carrier_by_building_group.reset_index()[['building_category', 'energy_source', 'year', 'energy_use']]
    hz = r2.pivot(columns=['year'], index=['building_category', 'energy_source'],
                  values=['energy_use']).reset_index()

    hz.columns = ['building_category', 'energy_source'] + [y for y in range(2020, 2051)]
    return hz


def write_result(output_file, csv_delimiter, output, sheet_name='area forecast'):
    logger.debug(f'Writing to {output_file}')
    write_start = time.time()
    if str(output_file) == '-':
        try:
            print(output.to_markdown())
        except ImportError:
            print(output.to_string())
    elif output_file.suffix == '.csv':
        output.to_csv(output_file, sep=csv_delimiter)
        logger.success('Wrote {filename}', filename=output_file)
    else:
        excel_writer = pd.ExcelWriter(output_file, engine='openpyxl')
        output.to_excel(excel_writer, sheet_name=sheet_name, merge_cells=False, freeze_panes=(1, 3))
        excel_writer.close()
        logger.success('Wrote {filename}', filename=output_file)

    logger.debug(f'  wrote {output_file.stat().st_size/1000:.0} in {time.time() - write_start:.4} seconds')


def append_result(output_file: pathlib.Path, df: pd.DataFrame, sheet_name='Sheet 1'):
    """
    Write df to output_file using sheet_name. If output_file already exists the sheet will be added tp ouput_file rather
    than replacing the entire content.

    Parameters
    ----------
    output_file :
    df :
    sheet_name :

    Returns
    -------

    """
    more_options = {'mode': 'w'}
    if output_file.is_file():
        more_options = {'if_sheet_exists': 'replace', 'mode': 'a'}

    with pd.ExcelWriter(output_file, engine='openpyxl', **more_options) as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        sheet = writer.sheets[sheet_name]

        columns = sheet.iter_cols(min_row=1, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column)

        logger.debug('Formatting cell')
        for col, (col_name, col_values) in zip(columns, df.items()):
            cell_format = detect_format_from_values(col_name, col_values, df)
            if cell_format:
                for row in col[1:]:
                    row.number_format = cell_format

        logger.debug('Adjust columns width')
        for col in sheet.iter_cols(min_col=1):
            adjusted_width = find_max_column_width(col)
            sheet.column_dimensions[col[0].column_letter].width = adjusted_width
        logger.debug(f'Closing {output_file} {sheet_name}')
    logger.debug(f'Wrote {output_file} {sheet_name}')


class EbmDefaultHandler:
    def extract_model(self,
                      year_range: YearRange,
                      building_categories: list[BuildingCategory] | None,
                      database_manager: DatabaseManager,
                      step_choice: str='energy-use') -> pd.DataFrame:
        """
        Extract dataframe for a certain step in the ebm model.

        Possible steps are energy_use (default), heating-systems, energy-use, area-forecast

        Parameters
        ----------
        year_range : ebm.model.dataclasses.YearRange
        building_categories : list[BuildingCategory]
        database_manager : ebm.model.database_manager.DatabaseManager
        step_choice : str, optional

        Returns
        -------
        pd.DataFrame
        """
        b_c = building_categories if building_categories else [e for e in BuildingCategory]
        area_forecast = self.extract_area_forecast(b_c,
                                                   database_manager,
                                                   period=year_range)
        area_forecast = area_forecast.set_index(['building_category', 'building_code', 'building_condition', 'year'])
        df = area_forecast

        if 'energy-requirements' in step_choice or 'heating-systems' in step_choice or 'energy-use' in step_choice:
            logger.debug('Extracting area energy requirements')
            energy_requirements_result = self.extract_energy_requirements(b_c,
                                                                          database_manager,
                                                                          area_forecast,
                                                                          period=year_range)
            df = energy_requirements_result

            if 'heating-systems' in step_choice or 'energy-use' in step_choice:
                logger.debug('Extracting heating systems')
                df = calculate_heating_systems(energy_requirements=energy_requirements_result,
                                               database_manager=database_manager)
        return df

    # noinspection PyTypeChecker
    @staticmethod
    def extract_energy_requirements(building_categories,
                                    database_manager: DatabaseManager,
                                    area_forecast: pd.DataFrame,
                                    period: YearRange) -> pd.DataFrame:
        """
        Extracts energy needs for building_categories and period

        Parameters
        ----------
        building_categories : list[BuildingCategory]
        database_manager : ebm.model.database_manager.DatabaseManager
        area_forecast : pd.DataFrame
        period :ebm.model.dataclasses.YearRange

        Returns
        -------
        pd.DataFrame

        """
        energy_requirements_result = calculate_building_category_energy_requirements(
            building_category=building_categories,
            area_forecast=area_forecast,
            database_manager=database_manager,
            start_year=period.start,
            end_year=period.end)
        return energy_requirements_result


    @staticmethod
    def extract_area_forecast(building_categories,
                              database_manager: DatabaseManager,
                              period: YearRange) -> pd.DataFrame:

        area_forecast = calculate_building_category_area_forecast(
                database_manager=database_manager,
                start_year=period.start,
                end_year=period.end)

        return area_forecast

    @staticmethod
    def write_tqdm_result(output_file: pathlib.Path, output: pd.DataFrame, csv_delimiter: str=',', reset_index=True):
        try:
            from tqdm import tqdm
        except ImportError:
            # When tqdm is not installed we use write_result instead
            write_result(output_file, csv_delimiter, output)
            return

        logger.debug(f'Writing to {output_file}')

        if str(output_file) == '-':
            try:
                print(output.to_markdown())
            except ImportError:
                print(output.to_string())
                return

        if reset_index:
            logger.debug('Resetting dataframe index')
            output = output.reset_index()

        chunk_size = 2000
        logger.debug(f'{chunk_size=}')

        closing_file = time.time()
        with tqdm(total=len(output), desc="Writing to spreadsheet") as pbar:
            write_file = time.time()
            if output_file.suffix == '.csv':
                for i in range(0, len(output), chunk_size):  # Adjust the chunk size as needed
                    building_category = output.iloc[i].building_category
                    pbar.update(chunk_size)
                    output.iloc[i:i + chunk_size].to_csv(output_file, mode='a', header=(i == 0), index=False,
                                                         sep=csv_delimiter)
                    pbar.display(f'Writing {building_category}')
                closing_file = time.time()
                pbar.display(f'Wrote {output_file}')
            else:
                with pd.ExcelWriter(output_file, engine='xlsxwriter') as excel_writer:
                    for i in range(0, len(output), chunk_size):  # Adjust the chunk size as needed
                        building_category = output.iloc[i].name[0] if 'building_category' not in output.columns else \
                        output.building_category.iloc[i]
                        pbar.set_description(f'Writing {building_category}')
                        start_row = 0 if i == 0 else i + 1
                        page_start = i
                        page_end = min(i + chunk_size, len(output))
                        logger.trace(f'{start_row=} {page_start=} {page_end=}')
                        output.iloc[page_start:page_end].to_excel(excel_writer, startrow=start_row, header=(i == 0),
                                                                  merge_cells=True, index=not reset_index)
                        pbar.update(chunk_size)
                    pbar.set_description(f'Closing {output_file}')
                    closing_file = time.time()
        logger.success('Wrote {filename}', filename=output_file)
        logger.debug(f'  wrote dataframe in { closing_file - write_file:.4} seconds')
        logger.debug(f'  closed file in {time.time() - closing_file:.4} seconds')
        logger.debug(f'  wrote {int(output_file.stat().st_size/1_000_000):_d} MB in {time.time() - write_file:.4} seconds')


