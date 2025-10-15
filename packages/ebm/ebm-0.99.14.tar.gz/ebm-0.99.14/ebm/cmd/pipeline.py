import os
import pathlib

import pandas as pd

from loguru import logger

from ebm import extractors
from ebm.cmd.helpers import load_environment_from_dotenv, configure_loglevel, configure_json_log
from ebm.cmd.result_handler import transform_model_to_horizontal, transform_to_sorted_heating_systems
from ebm.model import area as a_f, bema
from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.model import energy_need as e_n
from ebm.model import energy_purpose as e_p
from ebm.model import energy_use as e_u
from ebm.model.file_handler import FileHandler
from ebm.model import heating_systems_parameter as h_s_param
from ebm.model import heat_pump as h_p
from ebm.model.heating_systems_share import transform_heating_systems_share_long, transform_heating_systems_share_wide
from ebm.s_curve import calculate_s_curves
from ebm.services.spreadsheet import make_pretty, add_top_row_filter


def main():
    load_environment_from_dotenv()

    configure_loglevel(os.environ.get('LOG_FORMAT', None))
    configure_json_log()
    input_path, output_path, years = load_config()

    output_path.mkdir(exist_ok=True)

    file_handler = FileHandler(directory=input_path)
    database_manager = DatabaseManager(file_handler=file_handler)
    list(export_energy_model_reports(years, database_manager, output_path))


def export_energy_model_reports(years: YearRange, database_manager: DatabaseManager, output_path: pathlib.Path):
    logger.info('Area to area.xlsx')
    logger.debug('Extract area')

    scurve_parameters = database_manager.get_scurve_params() # 📍

    area_parameters = database_manager.get_area_parameters() # 📍
    area_parameters['year'] = years.start

    building_code_parameters = database_manager.file_handler.get_building_code() # 📍

    s_curves_by_condition = calculate_s_curves(scurve_parameters, building_code_parameters, years) # 📌
    area_forecast = extractors.extract_area_forecast(years, s_curves_by_condition, building_code_parameters, area_parameters, database_manager) # 📍
    energy_need_kwh_m2 = extractors.extract_energy_need(years, database_manager) # 📍
    heating_systems_projection = extractors.extract_heating_systems_forecast(years, database_manager) # 📍
    energy_use_holiday_homes = extractors.extract_energy_use_holiday_homes(database_manager) # 📍

    total_energy_need = e_n.transform_total_energy_need(energy_need_kwh_m2, area_forecast)  # 📌
    heating_systems_parameter = h_s_param.heating_systems_parameter_from_projection(heating_systems_projection) # 📌
    energy_use_kwh = e_u.building_group_energy_use_kwh(heating_systems_parameter, total_energy_need) # 📌

    existing_area = a_f.filter_existing_area(area_forecast)

    logger.debug('Transform fane 1 (wide)')
    merged_building_code_and_condition = a_f.merge_building_code_and_condition(existing_area)
    area_wide = transform_model_to_horizontal(merged_building_code_and_condition)
    area_wide = area_wide.drop(columns=['building_code', 'building_condition']) #🏙️

    logger.debug('Transform fane 2 (long')

    area_by_year_category_building_code = existing_area.groupby(by='year,building_category,building_code'.split(','))[['m2']].sum()
    area_by_year_category_building_code = area_by_year_category_building_code.rename(columns={'m2': 'area'})
    area_by_year_category_building_code.insert(0, 'U', 'm2')
    area_long = area_by_year_category_building_code.reset_index().sort_values(
        by=['building_category', 'building_code', 'year'], key=bema.map_sort_order) #🏙️

    logger.debug('Write file area.xlsx')

    area_output = output_path / 'area.xlsx'

    with pd.ExcelWriter(area_output, engine='xlsxwriter') as writer:
        # Write wide first order matters
        area_wide.to_excel(writer, sheet_name='wide', index=False) # 🏙️️💾
        area_long.to_excel(writer, sheet_name='long', index=False) # 🏙️💾
    logger.debug(f'Adding top row filter to {area_output}')
    make_pretty(area_output)
    add_top_row_filter(workbook_file=area_output, sheet_names=['long'])
    yield area_output

    logger.success(f'Wrote {area_output}')

    logger.info('Energy use to energy_purpose')

    logger.info('Heating_system_share')

    logger.debug('Transform fane 2')
    heating_systems_share = transform_heating_systems_share_long(heating_systems_projection)

    logger.debug('Transform fane 1')
    heating_systems_share_wide = transform_heating_systems_share_wide(heating_systems_share) # ♨️
    heating_systems_share_long = heating_systems_share.rename(columns={ # ♨️
        'heating_system_share': 'Share',
        'heating_systems': 'Heating system'})

    heating_systems_share_wide = heating_systems_share_wide.rename(columns={'heating_systems':'Heating technology'})

    logger.debug('Write file heating_system_share.xlsx')
    heating_system_share_file = output_path / 'heating_system_share.xlsx'
    with pd.ExcelWriter(heating_system_share_file, engine='xlsxwriter') as writer:
        # Write wide first order matters
        heating_systems_share_wide.to_excel(writer, sheet_name='wide', merge_cells=False, index=False) # ♨️💾
        heating_systems_share_long.to_excel(writer, sheet_name='long', merge_cells=False) # ♨️💾
    make_pretty(heating_system_share_file)
    logger.debug(f'Adding top row filter to {heating_system_share_file}')
    add_top_row_filter(workbook_file=heating_system_share_file, sheet_names=['long'])
    logger.success(f'Wrote {heating_system_share_file.name}')
    yield heating_system_share_file

    logger.info('heat_prod_hp')
    logger.debug('Transform heating_system_parameters')

    logger.debug('Transform to hp')
    expanded_heating_systems_parameter = h_s_param.expand_heating_system_parameters(heating_systems_parameter)
    air_air = h_p.air_source_heat_pump(expanded_heating_systems_parameter)
    district_heating = h_p.district_heating_heat_pump(expanded_heating_systems_parameter)

    production = h_p.heat_pump_production(total_energy_need, air_air, district_heating)
    heat_prod_hp_wide = h_p.heat_prod_hp_wide(production) # 🧮

    logger.debug('Write file heat_prod_hp.xlsx')
    heat_prod_hp_file = output_path / 'heat_prod_hp.xlsx'

    with pd.ExcelWriter(heat_prod_hp_file, engine='xlsxwriter') as writer:
        heat_prod_hp_wide.to_excel(writer, sheet_name='wide', index=False) # 🧮💾
    make_pretty(heat_prod_hp_file)
    logger.success(f'Wrote {heat_prod_hp_file.name}')
    yield heat_prod_hp_file

    logger.info('Energy_use')

    logger.debug('Transform energy_use_kwh')

    logger.debug('Transform fane 1')
    energy_use_gwh_by_building_group = e_u.energy_use_gwh_by_building_group(energy_use_kwh)

    logger.debug('Transform fane 2')
    logger.debug('Group by category, year, product')

    column_order = ['year', 'building_category', 'building_code', 'energy_product', 'kwh']
    energy_use_long = energy_use_kwh[column_order].groupby(
        by=['building_category', 'building_code', 'energy_product', 'year']).sum() / 1_000_000
    energy_use_long = energy_use_long.reset_index()[column_order].rename(columns={'kwh': 'energy_use'})
    energy_use_long = energy_use_long.sort_values(
        by=['building_category', 'building_code', 'year'], key=bema.map_sort_order) #🔌

    logger.debug('Transform fane 1')
    logger.debug('Group by group, product year')
    energy_use_wide = transform_to_sorted_heating_systems(energy_use_gwh_by_building_group, energy_use_holiday_homes, #🔌
                                                          building_column='building_group')
    logger.debug('Write file energy_use')
    energy_use_file = output_path / 'energy_use.xlsx'
    with pd.ExcelWriter(energy_use_file, engine='xlsxwriter') as writer:
        # Write wide first order matters
        energy_use_wide.to_excel(writer, sheet_name='wide', index=False) #🔌💾
        energy_use_long.to_excel(writer, sheet_name='long', index=False) #🔌💾
    make_pretty(energy_use_file)
    logger.debug(f'Adding top row filter to {energy_use_file}')
    add_top_row_filter(workbook_file=energy_use_file, sheet_names=['long'])
    logger.success(f'Wrote {energy_use_file.name}')
    yield energy_use_file

    logger.debug('Transform fane 1')
    energy_purpose_wide = e_p.group_energy_use_kwh_by_building_group_purpose_year_wide(energy_use_kwh=energy_use_kwh) # 🚿

    logger.debug('Transform fane 2')
    energy_purpose_long = e_p.group_energy_use_by_year_category_building_code_purpose(energy_use_kwh=energy_use_kwh) # 🚿

    logger.debug('Write file energy_purpose.xlsx')
    energy_purpose_output = output_path / 'energy_purpose.xlsx'
    with pd.ExcelWriter(energy_purpose_output, engine='xlsxwriter') as writer:
        # Write wide first order matters
        energy_purpose_wide.to_excel(writer, sheet_name='wide', index=False) # 🚿 💾
        energy_purpose_long.to_excel(writer, sheet_name='long', index=False) # 🚿💾
    make_pretty(energy_purpose_output)
    logger.debug(f'Adding top row filter to {energy_purpose_output}')
    add_top_row_filter(workbook_file=energy_purpose_output, sheet_names=['long'])
    logger.success(f'Wrote {energy_purpose_output.name}')
    yield energy_purpose_output

    area_change = a_f.transform_area_forecast_to_area_change(area_forecast=area_forecast, building_code_parameters=building_code_parameters)

    logger.info('demolition_construction')
    logger.debug('Transform demolition_construction')
    demolition_construction_long = a_f.transform_demolition_construction(energy_use_kwh, area_change)
    demolition_construction_long = demolition_construction_long.rename(columns={'m2': 'Area [m2]',
                                                                      'gwh': 'Energy use [GWh]'})
    demolition_construction_long = demolition_construction_long.sort_values(
        by=['building_category', 'building_code', 'year', 'demolition_construction'], key=bema.map_sort_order) # 🏗️

    logger.debug('Write file demolition_construction.xlsx')
    demolition_construction_file = output_path / 'demolition_construction.xlsx'
    with pd.ExcelWriter(demolition_construction_file, engine='xlsxwriter') as writer:
        demolition_construction_long.to_excel(writer, sheet_name='long', index=False) # 🏗️💾
    make_pretty(demolition_construction_file)
    logger.debug(f'Adding top row filter to {demolition_construction_file}')
    add_top_row_filter(workbook_file=demolition_construction_file, sheet_names=['long'])
    logger.success(f'Wrote {demolition_construction_file.name}')

    yield demolition_construction_file


def load_config():
    try:
        start_year = int(os.environ.get('EBM_START_YEAR', 2020))
    except ValueError:
        start_year = 2020
    try:
        end_year = int(os.environ.get('EBM_END_YEAR', 2050))
    except ValueError:
        end_year = 2050
    years = YearRange(start_year, end_year)
    input_path = pathlib.Path(os.environ.get('EBM_INPUT_DIRECTORY', 'input'))
    output_path = pathlib.Path(os.environ.get('EBM_OUTPUT_DIRECTORY', 'output'))
    return input_path, output_path, years


if __name__ == '__main__':
    main()

