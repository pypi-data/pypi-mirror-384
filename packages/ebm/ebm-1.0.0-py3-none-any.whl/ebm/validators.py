"""
Pandera validators for ebm input files.
"""
import itertools

import numpy as np
import pandas as pd
import pandera as pa

from ebm.model.building_category import BuildingCategory, RESIDENTIAL, NON_RESIDENTIAL
from ebm.model.building_condition import BuildingCondition
from ebm.model.column_operations import explode_unique_columns, explode_column_alias
from ebm.model.data_classes import YearRange
from ebm.model.energy_purpose import EnergyPurpose
from ebm.model.heating_systems import HeatingSystems


def check_building_category(value: pd.Series) -> pd.Series:
    """
    Makes sure that the series value contains values that are corresponding to a BuildingCategory

    Parameters
    ----------
    value: pd.Series
        A series of str that will be checked against BuildingCategory

    Returns
    -------
    pd.Series of bool values

    """
    return value.isin(iter(BuildingCategory))

def check_default_building_category(value: pd.Series) -> pd.Series:
    """
    Makes sure that the series value contains values that are corresponding to a BuildingCategory or default

    Parameters
    ----------
    value: pd.Series
        A series of str that will be checked against BuildingCategory and 'default' 

    Returns
    -------
    pd.Series of bool values

    """
    return value.isin(list(BuildingCategory) + ['default'])

def check_default_building_category_with_group(value: pd.Series) -> pd.Series:
    """
    Makes sure that the series value contains values that are corresponding to a BuildingCategory, 
    BuildingCategory group (RESIDENTIAL or NON_RESIDENTIAL) or 'default'

    Parameters
    ----------
    value: pd.Series
        A series of str that will be checked against BuildingCategory, RESIDENTIAL, NON_RESIDENTIAL and 'default' 

    Returns
    -------
    pd.Series of bool values
    """
    return value.isin(list(BuildingCategory) + ['default'] + [RESIDENTIAL, NON_RESIDENTIAL])


def check_building_condition(value: pd.Series) -> pd.Series:
    """
    Makes sure that the series value contains values that are corresponding to a BuildingCondition

    Parameters
    ----------
    value: pd.Series
        A series of str that will be checked against BuildingCondition

    Returns
    -------
    pd.Series of bool values

    """
    return value.isin(iter(BuildingCondition))


def check_existing_building_conditions(value: pd.Series) -> pd.Series:
    """
    Makes sure that the series contains values that are corresponding to 'existing' building conditions.

    Existing building conditions are all members (conditions) of BuildingCondition, except of DEMOLITION.

    Parameters
    ----------
    value: pd.Series
        A series of str that will be checked against 'existing' BuildingCondition members

    Returns
    -------
    pd.Series of bool values

    """
    return value.isin(iter(BuildingCondition.existing_conditions()))


def check_all_existing_building_conditions_present(df: pd.DataFrame):
    """
    Ensures that all 'existing' building conditions are present in the 'building_conditions' column for
    each unique combination of 'building_category', 'building_code', and 'purpose'.

    Existing building conditions are all members (conditions) of BuildingCondition, except of DEMOLITION.

    Parameters
    ----------
    df: pd.Dataframe
    """
    grouped = df.groupby(['building_category', 'building_code', 'purpose'])['building_condition']
    existing_conditions = set(BuildingCondition.existing_conditions())
    for _, conditions in grouped:
        if set(conditions) != existing_conditions:
            return False
    return True


def check_energy_purpose(value: pd.Series) -> pd.Series:
    """
    Makes sure that the value contains one of the valid purpose values: 'Cooling', 'Electrical equipment', 'Fans and pumps', 'HeatingDHW', 'HeatingRV', or 'Lighting'

    Args:
        value: Input value to check against the valid purpose values

    Returns:
        pd.Series: Series of bool values indicating if each value matches a valid purpose
    """
    return value.isin(iter(EnergyPurpose))


def check_default_energy_purpose(value: pd.Series) -> pd.Series:
    """
    Makes sure that the value contains one of the default or purpose values: 'Cooling', 'Electrical equipment', 'Fans and pumps', 'HeatingDHW', 'HeatingRV', or 'Lighting'

    Args:
        value: Input value to check against the valid purpose values

    Returns:
        pd.Series: Series of bool values indicating if each value matches a valid purpose
    """
    return value.isin(list(EnergyPurpose) + ['default'])


def check_building_code(value: str) -> bool:
    """
    A crude check to determine if value is a 'building_code'

    Args:
        value (str): A string to check if it's a building_code

    Returns:
        bool: True when the function thinks that value might be a building_code
    """
    return 'TEK' in value


def check_default_building_code(value: str) -> bool:
    """
    A crude check to determine if value is a 'building_code' or default

    Args:
        value (str): A string to check if it's a TEK or default

    Returns:
        bool: True when the function thinks that value might be a TEK
    """
    return check_building_code(value) or value == 'default'

#TODO: edge cases?
def check_overlapping_building_code_periods(df: pd.DataFrame) -> pd.Series:
    """
    """
    df = df.sort_values(["period_end_year"])
    end_years = df['period_end_year'] + 1
    start_years = df["period_start_year"].shift(-1)

    end_years = end_years.iloc[:-1]
    start_years = start_years.iloc[:-1]
    check = end_years == start_years
    checked_series = pd.Series(check.to_list() +[True])  
    return checked_series


def check_building_category_share(values: pd.DataFrame) -> pd.Series:
    """
    Makes sure that the sum of values in values.new_house_share + values.new_apartment_block_share is 1.0

    Args:
        values (pd.DataFrame): A dataframe with new_house_share and new_apartment_block_share

    Returns:
        pd.Series: A series of bool with the truth value of new_house_share + new_apartment_block_share equals 1.0
    """
    return values.new_house_share + values.new_apartment_block_share == 1.0


def create_residential_area_checks():
    """
    Creates a list of checks used for house and apartment_block categories.
        - Checks that the first two rows are not empty
        - Checks that the next (3) rows are empty
        - Checks that non-empty rows are not negative

    Returns
    -------
    List[pa.Check]
    """
    return [
        pa.Check(lambda s: s.iloc[:2].notnull().all(),
                 element_wise=False,
                 error='Expects number in first two rows for house'),
        pa.Check(lambda s: s.iloc[2:].isnull().all(),
                 element_wise=False,
                 error='Expects empty in the last four years for house'),
        pa.Check.greater_than_or_equal_to(0.0)]


def check_heating_systems(value: pd.Series) -> pd.Series:
    """
    Makes sure that the series contains values that corresponds to a HeatingSystems
    
    Parameters
    ----------
    value: pd.Series
        A series of str that will be checked against HeatingSystems
    
    Returns
    -------
     pd.Series of bool values

    """
    return value.isin(iter(HeatingSystems))


def check_sum_of_heating_system_shares_equal_1(df: pd.DataFrame):
    """
    """
    precision = 4
    df = df.groupby(by=['building_category', 'building_code'])[['heating_system_share']].sum()
    df['heating_system_share'] = round(df['heating_system_share'] * 100, precision)
    return_series = df["heating_system_share"] == 100.0
    return return_series


def make_building_purpose(years: YearRange | None = None) -> pd.DataFrame:
    """
    Returns a dataframe of all combinations building_categories, building_codes, original_condition, purposes
    and optionally years.

    Parameters
    ----------
    years : YearRange, optional

    Returns
    -------
    pd.DataFrame
    """
    data = []
    columns = [list(BuildingCategory),
               ['PRE_TEK49', 'TEK49', 'TEK69', 'TEK87', 'TEK97', 'TEK07', 'TEK10', 'TEK17'],
               EnergyPurpose]

    column_headers = ['building_category', 'building_code', 'building_condition', 'purpose']
    if years:
        columns.append(years)
        column_headers.append('year')

    for bc, building_code, purpose, *year in itertools.product(*columns):
        row = [bc, building_code, 'original_condition', purpose]
        if years:
            row.append(year[0])
        data.append(row)

    return pd.DataFrame(data=data, columns=column_headers)


def behaviour_factor_parser(df: pd.DataFrame) -> pd.DataFrame:
    model_years = YearRange(2020, 2050)
    all_combinations = make_building_purpose(years=model_years)

    if 'start_year' not in df.columns:
        df=df.assign(**{'start_year': model_years.start})
    if 'end_year' not in df.columns:
        df=df.assign(**{'end_year': model_years.end})
    if 'function' not in df.columns:
        df=df.assign(function='noop')
    else:
        df['function'] = df.function.fillna('noop')
    if 'parameter' not in df.columns:
        df=df.assign(parameter=0.0)

    df['start_year'] = df.start_year.fillna(model_years.start).astype(int)
    df['end_year'] = df.end_year.fillna(model_years.end).astype(int)

    unique_columns = ['building_category', 'building_code', 'purpose', 'start_year', 'end_year']
    behaviour_factor = explode_unique_columns(df,
                                              unique_columns=unique_columns)

    behaviour_factor = explode_column_alias(behaviour_factor,
                       column='purpose',
                       values=[p for p in EnergyPurpose],
                       alias='default',
                       de_dup_by=unique_columns)

    behaviour_factor['year'] = behaviour_factor.apply(
        lambda row: range(row.start_year, row.end_year+1), axis=1)
    behaviour_factor['interpolation'] = behaviour_factor.apply(
        lambda row: np.linspace(row.behaviour_factor, row.parameter, num=row.end_year+1-row.start_year), axis=1)

    behaviour_factor = behaviour_factor.explode(['year', 'interpolation'])

    behaviour_factor['year'] = behaviour_factor['year'].astype(int)

    interpolation_slice = (behaviour_factor.function == 'improvement_at_end_year') & (~behaviour_factor.interpolation.isna())
    behaviour_factor.loc[interpolation_slice, 'behaviour_factor'] = behaviour_factor.loc[
        interpolation_slice, 'interpolation'].astype(float)

    behaviour_factor.sort_values(['building_category', 'building_code', 'purpose', 'year'])

    behaviour_factor = calculate_yearly_reduction(behaviour_factor)

    behaviour_factor=behaviour_factor.set_index(['building_category', 'building_code', 'purpose', 'year'], drop=True)
    all_combinations=all_combinations.set_index(['building_category', 'building_code', 'purpose', 'year'], drop=True)

    joined = all_combinations.join(behaviour_factor, how='left')
    joined.behaviour_factor = joined.behaviour_factor.fillna(1.0)
    return joined.reset_index()


def calculate_yearly_reduction(df):
    reduction_slice = df[df['function'] == 'yearly_reduction'].index
    df.loc[reduction_slice, 'behaviour_factor'] = df.loc[reduction_slice].behaviour_factor * ((1.0 - df.loc[
        reduction_slice].parameter) ** (df.loc[reduction_slice].year - df.loc[reduction_slice].start_year))
    return df


energy_need_behaviour_factor = pa.DataFrameSchema(
    parsers=pa.Parser(behaviour_factor_parser),
    columns={
        "building_category": pa.Column(str),
        'building_code': pa.Column(str), #
        "purpose": pa.Column(str),
        'year': pa.Column(int, required=False),
        'behaviour_factor': pa.Column(float)
    }
)

area = pa.DataFrameSchema(
    columns={
        "building_category": pa.Column(str, checks=[pa.Check(check_building_category)]),
        'building_code': pa.Column(str, checks=[pa.Check(check_building_code, element_wise=True)]),
        "area": pa.Column(float, checks=[pa.Check.greater_than(0)], coerce=True)},
    name='area_parameters'
)

building_code_parameters = pa.DataFrameSchema(columns={
        'building_code': pa.Column(str, unique=True, checks=[pa.Check(check_building_code, element_wise=True)]),
        'building_year': pa.Column(int, checks=[
            pa.Check.greater_than_or_equal_to(1940),
            pa.Check.less_than_or_equal_to(2070)]),
        'period_start_year': pa.Column(int, checks=[
            pa.Check.greater_than_or_equal_to(0),
            pa.Check.less_than_or_equal_to(2070),
        ]),
        'period_end_year': pa.Column(int, checks=[
            pa.Check.greater_than_or_equal_to(1940),
            pa.Check.less_than_or_equal_to(2070, error='period_end_year should be 2070 or lower'),
            pa.Check.between(1940, 2070, error='period_end_year should be between 1940 and 2070')])},
    checks=[pa.Check(lambda df: df["period_end_year"] > df["period_start_year"],
                     error="period_end_year should be greater than period_start_year"),
            pa.Check(check_overlapping_building_code_periods, 
                     error="building_code periods do not overlap")],
    name='building_code_parameters'
)


area_new_residential_buildings = pa.DataFrameSchema(
    columns={
        'year': pa.Column(int),
        'house': pa.Column(pa.Float64, nullable=True, checks=create_residential_area_checks()),
        'apartment_block': pa.Column(pa.Float64, nullable=True, checks=create_residential_area_checks())
    },
    name='construction_building_category_yearly'
)


new_buildings_residential = pa.DataFrameSchema(
    columns={
        'year': pa.Column(int, checks=[pa.Check.between(2010, 2070)]),
        'new_house_share': pa.Column(float, checks=[pa.Check.between(0.0, 1.0)]),
        'new_apartment_block_share': pa.Column(float, checks=[pa.Check.between(0.0, 1.0)]),
        'floor_area_new_house': pa.Column(int, checks=[pa.Check.between(1, 1000)]),
        'flood_area_new_apartment_block': pa.Column(int, checks=[pa.Check.between(1, 1000)])
    },
    checks=[pa.Check(check_building_category_share,
                     error='The sum of new_house_share and new_apartment_block_share should be 1.0 (100%)')],
    name='new_buildings_house_share'
)


population_forecast = pa.DataFrameSchema(
    columns={
        'year': pa.Column(int, coerce=True, checks=[pa.Check.between(1900, 2070)]),
        'population': pa.Column(int, coerce=True, checks=[pa.Check.greater_than_or_equal_to(0)]),
        'household_size': pa.Column(float, coerce=True, nullable=True, checks=[pa.Check.greater_than_or_equal_to(0)])},
    name='new_buildings_population')


#TODO: evaluete if restrictions on rush and never share make sense (if the program crashes unless they are there)
s_curve = pa.DataFrameSchema(
    columns={
        'building_category': pa.Column(str, checks=[pa.Check(check_building_category)]),
        'condition': pa.Column(str, checks=[pa.Check(check_building_condition)]),
        'earliest_age_for_measure': pa.Column(int, checks=[pa.Check.greater_than(0)]),
        'average_age_for_measure': pa.Column(int, checks=[pa.Check.greater_than(0)]),
        'rush_period_years': pa.Column(int, checks=[pa.Check.greater_than(0)]),
        'last_age_for_measure': pa.Column(int, checks=[pa.Check.greater_than(0)]),
        'rush_share': pa.Column(float, checks=[pa.Check.between(min_value=0.0, max_value=1.0, include_min=False)]),
        'never_share': pa.Column(float, checks=[pa.Check.between(min_value=0.0, max_value=1.0, include_min=False)])
    },
    name='scurve_parameters')


### TODO: remove strong restrictions on float values and add warnings (should be able to be neg values)
energy_need_original_condition = pa.DataFrameSchema(
    columns={
        'building_category': pa.Column(str, checks=[pa.Check(check_default_building_category)]),
        'building_code': pa.Column(str, checks=[pa.Check(check_default_building_code, element_wise=True)]),
        'purpose': pa.Column(str, checks=[pa.Check(check_default_energy_purpose)]),
        'kwh_m2': pa.Column(float, coerce=True, checks=[pa.Check.greater_than_or_equal_to(0)])
    }, 
    unique=['building_category', 'building_code', 'purpose'],
    report_duplicates='all'
)


improvement_building_upgrade = pa.DataFrameSchema(
    columns={
        'building_category': pa.Column(str, checks=pa.Check(check_default_building_category)),
        'building_code': pa.Column(str, checks=pa.Check(check_default_building_code, element_wise=True)),
        'purpose': pa.Column(str, checks=pa.Check(check_default_energy_purpose)),
        'building_condition': pa.Column(str, checks=[pa.Check(check_existing_building_conditions)]),
        'reduction_share': pa.Column(float, coerce=True, checks=[pa.Check.between(min_value=0.0, include_min=True,
                                                                                  max_value=1.0, include_max=True)])
    },
    unique=['building_category', 'building_code', 'purpose', 'building_condition'],
    report_duplicates='all'
)


energy_need_improvements = pa.DataFrameSchema(
    columns={
        'building_category': pa.Column(str, checks=pa.Check(check_default_building_category)),
        'building_code': pa.Column(str, checks=pa.Check(check_default_building_code, element_wise=True)),
        'purpose':pa.Column(str, checks=pa.Check(check_default_energy_purpose)),
        'value': pa.Column(float, coerce=True,
                                                   checks=[pa.Check.between(min_value=0.0, include_min=True,
                                                                            max_value=1.0, include_max=True)])
    },
    unique=['building_category', 'building_code', 'purpose', 'start_year', 'function', 'end_year'],
    report_duplicates='all'
)


holiday_home_stock = pa.DataFrameSchema(
    columns={
        'year': pa.Column(int),
        'Existing buildings Chalet, summerhouses and other holiday houses': pa.Column(int),
        'Existing buildings Detached houses and farmhouses used as holiday houses': pa.Column(int)
    }
)


holiday_home_energy_consumption = pa.DataFrameSchema(
    columns={
        'year': pa.Column(int),
        'electricity': pa.Column(int),
        'fuelwood': pa.Column(float, nullable=True)
    }
)

area_per_person = pa.DataFrameSchema(
    columns={
        'building_category': pa.Column(str, checks=pa.Check(check_building_category)),
        'area_per_person': pa.Column(float, nullable=True)
    }
)


heating_system_initial_shares = pa.DataFrameSchema(
    columns={
        'building_category': pa.Column(str, checks=pa.Check(check_building_category)),
        'building_code': pa.Column(str, checks=pa.Check(check_default_building_code, element_wise=True)),
        'heating_systems': pa.Column(str, checks=pa.Check(check_heating_systems)),
        'year': pa.Column(int, pa.Check(
            lambda year: len(year.unique()) == 1,
            error="All values in the 'year' column must be identical."
        )),
        'heating_system_share': pa.Column(float, coerce=True,
                                checks=[pa.Check.between(min_value=0.0, include_min=True,
                                                         max_value=1.0, include_max=True)]) 
    },
    #TODO: better warning messages to see where the issues are
    checks=[pa.Check(check_sum_of_heating_system_shares_equal_1, raise_warning=True, 
                     error="Sum of 'heating_system_share' do not equal 1 for one or more combination of 'building_category' and 'building_code'")],
    name='heating_systems_shares_start_year'
)


#TODO: 
# - add check on years. Parse to make long format and check years and values? years must be in order, max limit (2070) etc.
heating_system_forecast = pa.DataFrameSchema(
    columns={
        'building_category': pa.Column(str, checks=pa.Check(check_default_building_category_with_group)),
        'building_code': pa.Column(str, checks=pa.Check(check_default_building_code, element_wise=True)),
        'heating_systems': pa.Column(str, checks=pa.Check(check_heating_systems)),
        'new_heating_systems': pa.Column(str, checks=pa.Check(check_heating_systems)) 
    },
    unique=['building_category', 'building_code', 'heating_systems', 'new_heating_systems'],
    report_duplicates='all'
)


"""
TODO: how to check columns that are heating systems (but not in enum) and 'energivare'. Columns:
        'Grunnlast': pa.Column(str), 
        'Spisslast': pa.Column(str),
        'Ekstralast': pa.Column(str),
        'base_load_energy_product': pa.Column(str),
        'peak_load_energy_product': pa.Column(str),
        'tertiary_load_energy_product': pa.Column(str),  
"""
heating_system_efficiencies = pa.DataFrameSchema(
    columns={
        'heating_systems': pa.Column(str, checks=pa.Check(check_heating_systems)),  
        'base_load_energy_product': pa.Column(str),
        'peak_load_energy_product': pa.Column(str),
        'tertiary_load_energy_product': pa.Column(str),        
        'tertiary_load_coverage': pa.Column(float, coerce=True),
        'base_load_coverage': pa.Column(float, coerce=True),
        'peak_load_coverage': pa.Column(float, coerce=True),
        'base_load_efficiency': pa.Column(float, coerce=True),
        'peak_load_efficiency': pa.Column(float, coerce=True),
        'tertiary_load_efficiency': pa.Column(float, coerce=True),
        'domestic_hot_water_energy_product': pa.Column(str),
        'domestic_hot_water_efficiency': pa.Column(float, coerce=True),
        'Spesifikt elforbruk': pa.Column(float, coerce=True),
        'cooling_efficiency': pa.Column(float, coerce=True)
    }
)


__all__ = [area,
           building_code_parameters,
           area_new_residential_buildings,
           new_buildings_residential,
           population_forecast,
           s_curve,
           new_buildings_residential,
           improvement_building_upgrade]

