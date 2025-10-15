import logging
import typing

import numpy as np
import pandas as pd

from ebm.model.database_manager import DatabaseManager
from ebm.model.data_classes import YearRange


class HolidayHomeEnergy:
    def __init__(self,
                 population: pd.Series,
                 holiday_homes_by_category: pd.DataFrame,
                 electricity_usage_stats: pd.Series,
                 fuelwood_usage_stats: pd.Series,
                 fossil_fuel_usage_stats: pd.Series):
        self.population = population
        self.fossil_fuel_usage_stats = fossil_fuel_usage_stats
        self.fuelwood_usage_stats = fuelwood_usage_stats
        self.electricity_usage_stats = electricity_usage_stats
        self.holiday_homes_by_category = holiday_homes_by_category

    def calculate_energy_usage(self) -> typing.Iterable[pd.Series]:
        """
        Calculate projected energy usage for holiday homes.

        This method projects future energy usage for electricity, fuelwood, and fossil fuels
        based on historical data and combines these projections with existing statistics.

        Yields
        ------
        Iterable[pd.Series]
            A series of projected energy usage values for electricity, fuelwood, and fossil fuels,
            with NaN values filled from the existing statistics.
        """
        electricity_projection = project_electricity_usage(self.electricity_usage_stats,
                                                           self.holiday_homes_by_category,
                                                           self.population)
        yield electricity_projection.combine_first(self.electricity_usage_stats)

        fuelwood_projection = project_fuelwood_usage(self.fuelwood_usage_stats,
                                                     self.holiday_homes_by_category,
                                                     self.population)
        yield fuelwood_projection.combine_first(self.fuelwood_usage_stats)

        fossil_fuel_projection = project_fossil_fuel_usage(self.fossil_fuel_usage_stats,
                                                           self.holiday_homes_by_category,
                                                           self.population)
        yield fossil_fuel_projection

    @staticmethod
    def new_instance(database_manager: DatabaseManager = None) -> 'HolidayHomeEnergy':
        dm = database_manager or DatabaseManager()
        holiday_homes = dm.get_holiday_home_by_year()

        # 02 Elektrisitet i fritidsboliger statistikk (GWh) (input)
        electricity_usage_stats = dm.get_holiday_home_electricity_consumption()

        # 04 Ved i fritidsboliger statistikk (GWh)
        fuelwood_usage_stats = dm.get_holiday_home_fuelwood_consumption()
        
        # 06 Fossilt brensel i fritidsboliger statistikk (GWh)
        fossil_fuel_usage_stats = dm.get_holiday_home_fossilfuel_consumption()

        # logging.warning('Loading fossil_fuel_usage_stats from hard coded data')
        # fossil_fuel_usage_stats = pd.Series(data=[100], index=YearRange(2006, 2006).to_index(), name='kwh')

        population = dm.file_handler.get_file(dm.file_handler.POPULATION_FORECAST).set_index('year').population

        return HolidayHomeEnergy(population,
                                 holiday_homes,
                                 electricity_usage_stats,
                                 fuelwood_usage_stats,
                                 fossil_fuel_usage_stats)


def project_electricity_usage(electricity_usage_stats: pd.Series,
                              holiday_homes_by_category: pd.DataFrame,
                              population: pd.Series) -> pd.Series:
    """
    Calculate the projected electricity usage for holiday homes.

    This function projects the future electricity usage for holiday homes based on historical
    electricity usage statistics, the number of holiday homes by category, and population data.

    Population is used to work out what years are needed in the projection.

    Parameters
    ----------
    electricity_usage_stats : pd.Series
        A pandas Series containing historical electricity usage statistics.
    holiday_homes_by_category : pd.DataFrame
        A pandas DataFrame containing the number of holiday homes by year. Each column is considered as a category.
    population : pd.Series
        A pandas Series containing population data.

    Returns
    -------
    pd.Series
        A pandas Series with the projected electricity usage in gigawatt-hours (GWh) for future years.

    Raises
    ------
    ValueError
        If the input Series do not meet the expected criteria.
    """
    total_holiday_homes_by_year = sum_holiday_homes(holiday_homes_by_category.iloc[:, 0],
                                                    holiday_homes_by_category.iloc[:, 1])

    people_per_holiday_home = population_over_holiday_homes(population, total_holiday_homes_by_year)
    projected_holiday_homes_by_year = projected_holiday_homes(population, people_per_holiday_home)

    usage_by_homes = energy_usage_by_holiday_homes(electricity_usage_stats, total_holiday_homes_by_year)
    nan_padded_usage_by_homes = usage_by_homes.reindex(population.index, fill_value=np.nan)
    projected_electricity_usage = projected_electricity_usage_holiday_homes(nan_padded_usage_by_homes)

    projected_electricity_usage_kwh = projected_holiday_homes_by_year * projected_electricity_usage
    projected_electricity_usage_gwh = projected_electricity_usage_kwh / 1_000_000
    projected_electricity_usage_gwh.name = 'gwh'

    return projected_electricity_usage_gwh


def project_fuelwood_usage(fuelwood_usage_stats: pd.Series,
                           holiday_homes_by_category: pd.DataFrame,
                           population: pd.Series) -> pd.Series:
    total_holiday_homes_by_year = sum_holiday_homes(holiday_homes_by_category.iloc[:, 0],
                                                    holiday_homes_by_category.iloc[:, 1])

    people_per_holiday_home = population_over_holiday_homes(population, total_holiday_homes_by_year)
    projected_holiday_homes_by_year = projected_holiday_homes(population, people_per_holiday_home)

    usage_by_homes = energy_usage_by_holiday_homes(fuelwood_usage_stats, total_holiday_homes_by_year)
    nan_padded_usage_by_homes = usage_by_homes.reindex(population.index, fill_value=np.nan)
    projected_fuelwood_usage = projected_fuelwood_usage_holiday_homes(nan_padded_usage_by_homes)

    projected_fuelwood_usage_kwh = projected_holiday_homes_by_year * projected_fuelwood_usage
    projected_fuelwood_usage_gwh = projected_fuelwood_usage_kwh / 1_000_000
    projected_fuelwood_usage_gwh.name = 'gwh'

    return projected_fuelwood_usage_gwh


def project_fossil_fuel_usage(fossil_fuel_usage_stats: pd.Series,
                              holiday_homes_by_category: pd.DataFrame,
                              population: pd.Series) -> pd.Series:
    projected_fossil_fuel_usage_gwh = fossil_fuel_usage_stats.reindex(population.index, fill_value=np.nan)

    not_na = projected_fossil_fuel_usage_gwh.loc[~projected_fossil_fuel_usage_gwh.isna()].index
    projection_filter = projected_fossil_fuel_usage_gwh.index > max(not_na)
    projected_fossil_fuel_usage_gwh.loc[projection_filter] = projected_fossil_fuel_usage_gwh.loc[not_na].mean()
    projected_fossil_fuel_usage_gwh.name = 'gwh'
    return projected_fossil_fuel_usage_gwh


def sum_holiday_homes(*holiday_homes: pd.Series) -> pd.Series:
    return pd.DataFrame(holiday_homes).sum(axis=0)


def population_over_holiday_homes(population: pd.Series,
                                  holiday_homes: pd.Series) -> pd.Series:
    """
    Average number of holiday homes by population.

    Parameters
    ----------
    population : pd.Series
    holiday_homes : pd.Series

    Returns
    -------
    pd.Series

    """
    return population / holiday_homes


def projected_holiday_homes(population: pd.Series,
                            holiday_homes: pd.Series) -> pd.Series:
    """
    Projects future number of holiday homes based on the population and historical average number of holiday homes

    Parameters
    ----------
    population : pd.Series
        population in every year of the projection
    holiday_homes : pd.Series
        historical number of holiday homes
    Returns
    -------
    pd.Series
        population over average number of holiday homes
    """
    return population / holiday_homes.mean()


def energy_usage_by_holiday_homes(
    energy_usage: pd.Series,
    holiday_homes: pd.Series
) -> pd.Series:
    """

    (08) 14 Elektrisitet pr fritidsbolig staitsikk (kWh) in Energibruk fritidsboliger.xlsx
    (10) 16 Ved pr fritidsbolig statistikk (kWh) 2019 - 2023

    Parameters
    ----------
    energy_usage : pd.Series
        Electricity usage by year from SSB https://www.ssb.no/statbank/sq/10103348 2001 - 2023
    holiday_homes : pd.Series
        Total number of holiday homes of any category from SSB https://www.ssb.no/statbank/sq/10103336
    Returns
    -------

    """
    s = energy_usage * 1_000_000 / holiday_homes
    s.name = 'kwh'
    return s


def projected_fuelwood_usage_holiday_homes(historical_fuelwood_usage: pd.Series) -> pd.Series:
    """
    Projects future fuelwood usage for holiday homes based on historical data. The projection
        is calculated as the mean of the last 5 years of historical_fuelwood_usage.

    Parameters
    ----------
    historical_fuelwood_usage : pd.Series

    Returns
    -------
    pd.Series
        A pandas Series with with NaN values in fuelwood usage replaced by projected use. Years present
            in historical_fuelwood_usage is returned as NaN
    """
    projected_fuelwood_usage = pd.Series(data=[np.nan] * len(historical_fuelwood_usage),
                                         index=historical_fuelwood_usage.index)

    not_na = historical_fuelwood_usage.loc[~historical_fuelwood_usage.isna()].index
    average = historical_fuelwood_usage.loc[not_na].iloc[-5:].mean()
    projection_filter = projected_fuelwood_usage.index > max(not_na)
    projected_fuelwood_usage.loc[projection_filter] = average
    return projected_fuelwood_usage


def projected_electricity_usage_holiday_homes(electricity_usage: pd.Series):
    """
    Project future electricity usage for holiday homes based on historical data.

    This function projects future electricity usage by creating three ranges of projections
    and padding the series with NaN values and the last projection value as needed.

    15 (09) Elektrisitet pr fritidsbolig framskrevet (kWh) in Energibruk fritidsboliger.xlsx

    Parameters
    ----------
    electricity_usage : pd.Series
        A pandas Series containing historical electricity usage data. The index should include the year 2019,
        and the Series should contain at least 40 years of data with some NaN values for projection.

    Returns
    -------
    pd.Series
        A pandas Series with with NaN values in electricity usage replaced by projected energy use. Years with
            values in energy_usage has a projected usage of NaN

    Raises
    ------
    ValueError
        If the year 2019 is not in the index of the provided Series.
        If there are no NaN values in the provided Series.
        If the length of the Series is less than or equal to 40.
    """
    if 2019 not in electricity_usage.index:
        msg = 'The required year 2019 is not in the index of electricity_usage for the electricity projection'
        raise ValueError(msg)
    if not any(electricity_usage.isna()):
        raise ValueError('Expected empty energy_usage for projection')
    if len(electricity_usage.index) <= 40:
        raise ValueError('At least 41 years of electricity_usage is required to predict future electricity use')
    left_pad_len = len(electricity_usage) - electricity_usage.isna().sum()

    initial_e_u = electricity_usage[2019]
    first_range = [initial_e_u + (i * 75) for i in range(1, 6)]

    second_range = [first_range[-1] + (i * 50) for i in range(1, 5)]

    third_range = [second_range[-1] + (i * 25) for i in range(1, 9)]

    right_pad_len = len(electricity_usage) - left_pad_len - len(first_range) - len(second_range) - len(third_range)
    right_padding = [third_range[-1]] * right_pad_len

    return pd.Series(([np.nan] * left_pad_len) +
                     first_range +
                     second_range +
                     third_range +
                     right_padding,
                     name='projected_electricity_usage_kwh',
                     index=electricity_usage.index)


if __name__ == '__main__':
    holiday_home_energy = HolidayHomeEnergy.new_instance()
    for energy_usage, h in zip(holiday_home_energy.calculate_energy_usage(), ['electricity', 'fuelwood', 'fossil fuel']):
        print('====', h, '====')
        print(energy_usage)


def calculate_energy_use(database_manager: DatabaseManager) -> pd.DataFrame:
    """
    Calculates holiday home energy use by from HolidayHomeEnergy.calculate_energy_usage()

    Parameters
    ----------
    database_manager : DatabaseManager

    Returns
    -------
    pd.DataFrame
    """
    holiday_home_energy = HolidayHomeEnergy.new_instance(database_manager=database_manager)
    el, wood, fossil = [e_u for e_u in holiday_home_energy.calculate_energy_usage()]
    df = pd.DataFrame(data=[el, wood, fossil])
    df.insert(0, 'building_category', 'holiday_home')
    df.insert(1, 'energy_type', 'n/a')
    df['building_category'] = 'holiday_home'
    df['energy_type'] = ('electricity', 'fuelwood', 'fossil')
    output = df.reset_index().rename(columns={'index': 'unit'})
    output = output.set_index(['building_category', 'energy_type', 'unit'])
    return output


def transform_holiday_homes_to_horizontal(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reset_index()
    df = df.rename(columns={'energy_type': 'energy_source'})
    columns_to_keep = [y for y in YearRange(2020, 2050)] + ['building_category', 'energy_source']
    df = df.drop(columns=[c for c in df.columns if c not in columns_to_keep])
    df['energy_source'] = df['energy_source'].apply(lambda x: 'Elektrisitet' if x == 'electricity' else 'Bio' if x == 'fuelwood' else x)
    df['building_category'] = 'Holiday homes'
    return df
