import pandas as pd

from ebm.energy_consumption import HP_ENERGY_SOURCE, HEAT_PUMP


def air_source_heat_pump(heating_systems_parameters: pd.DataFrame):
    df = heating_systems_parameters.copy()
    el_slice = df[df['heating_system'] == 'HP'].index
    df.loc[el_slice, 'pump_factor'] = df.loc[el_slice, 'load_share'] * df.loc[el_slice, 'heating_system_share']
    df.loc[el_slice, HP_ENERGY_SOURCE] = 'Heat pump air-air'
    df.loc[el_slice, 'purpose'] = 'heating_rv'

    return  df.query('heating_system=="HP"')


def district_heating_heat_pump(heating_systems_parameters: pd.DataFrame):
    df = heating_systems_parameters.copy()
    vann_slice = df[df['heating_system'] == 'HP Central heating'].index
    df.loc[vann_slice, 'pump_factor'] = df.loc[vann_slice, 'load_share'] * df.loc[vann_slice, 'heating_system_share']
    df.loc[vann_slice, HP_ENERGY_SOURCE] = 'Heat pump central heating'
    df.loc[vann_slice, 'purpose'] = 'heating_rv,heating_dhw'
    df = df.assign(**{'purpose': df['purpose'].str.split(',')}).explode('purpose')

    return df.query('heating_system=="HP Central heating"')


def heat_pump_production(energy_need, air_air, district_heating):
    df_en = energy_need.copy()
    df_hp = pd.concat([air_air, district_heating])

    df = pd.merge(left=df_en,
                  left_on=['building_category', 'building_code', 'purpose', 'year'],
                  right=df_hp,
                  right_on=['building_category', 'building_code', 'purpose', 'year'])


    df[HEAT_PUMP] = df.energy_requirement * df.pump_factor

    return df


def heat_prod_hp(production: pd.DataFrame, group_by:list|None=None) -> pd.DataFrame:
    grouping = ['building_group', 'year'] if not group_by else group_by
    production.loc[production['building_category'].isin(['house', 'apartment_block']), 'building_group'] = 'Residential'
    production.loc[production['building_group'] != 'Residential', 'building_group'] = 'Non-residential'
    return production.groupby(by=grouping+['hp_source']).agg({'RV_HP': 'sum'}) / 1_000_000


def heat_prod_hp_wide(production: pd.DataFrame) -> pd.DataFrame:
    df = heat_prod_hp(production)
    wide = df.reset_index().pivot(columns=['year'], index=['building_group', 'hp_source'], values=['RV_HP']).reset_index()
    wide.columns = ['building_group', 'hp_source'] + [c for c in wide.columns.get_level_values(1)[2:]]

    category_order = {'Residential': 100, 'Holiday homes': 200, 'Non-residential': 300}
    hp_source = {'Heat pump air-air': 24, 'Heat pump central heating': 25}
    wide = wide.sort_values(by=['building_group', 'hp_source'],
                        key=lambda x: x.map(category_order) if x.name == 'building_group' else x.map(
                            hp_source) if x.name == 'hp_source' else x)

    return wide
