import itertools
import typing
from typing import Union

import numpy as np
import pandas as pd
from loguru import logger

from ebm.model.building_category import BuildingCategory
from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager


class ConstructionCalculator:
    """
        A class used to calculate various construction metrics for residential and commercial buildings.

        The main method to use is calculate_construction

        Methods
        -------
        calculate_construction(building_category, demolition_floor_area, database_manager)
            Calculate constructed floor area for buildings using provided demolition floor area and input data from
                database manager.
         calculate_construction_as_list(building_category, demolition_floor_area, database_manager=None)
            Calculate constructed floor area for buildings using provided demolition floor area and input data
                from database manager.
        calculate_industrial_construction(building_category, total_floor_area, constructed_floor_area=None, demolition_floor_area=None, population=None)
            Calculate the commercial construction metrics over a given period.
        calculate_residential_construction(population, household_size, building_category_share, build_area_sum, yearly_demolished_floor_area, average_floor_area=175)
            Calculate various residential construction metrics based on population, household size, and building data.

        calculate_yearly_new_building_floor_area_sum(yearly_new_building_floor_area_house)
            Calculate the accumulated constructed floor area over the years.

        calculate_yearly_constructed_floor_area(build_area_sum, yearly_floor_area_change, yearly_demolished_floor_area)
            Calculate the yearly constructed floor area based on changes and demolitions.

        calculate_yearly_floor_area_change(building_change, average_floor_area=175)
            Calculate the yearly floor area change based on building changes and average floor area.

        calculate_population_growth(population)
            Calculate the annual growth in population.

        calculate_building_growth(building_category_share, households_change)
            Calculate the annual growth in building categories based on household changes.

        calculate_household_change(households)
            Calculate the annual change in the number of households.

        calculate_households_by_year(household_size, population)
            Calculate the number of households by year based on household size and population.
        """
    
    def calculate_residential_construction(self, population: pd.Series, household_size: pd.Series,
                                           building_category_share: pd.Series,
                                           build_area_sum: pd.Series,
                                           yearly_demolished_floor_area: pd.Series,
                                           average_floor_area: typing.Union[pd.Series, int] = 175,
                                           period=YearRange(2010, 2050)) -> pd.DataFrame:
        """
        Calculate various residential construction metrics based on population, household size, and building data.

        Parameters
        ----------
        population : pd.Series
            A pandas Series representing the population indexed by year.
        household_size : pd.Series
            A pandas Series representing the average household size over time.
        building_category_share : pd.Series
            A pandas Series representing the share of each building category.
        build_area_sum : pd.Series
            A pandas Series representing the accumulated building area sum.
        yearly_demolished_floor_area : pd.Series
            A pandas Series representing the yearly demolished floor area.
        period : YearRange
            contains start and end year for the model

        Returns
        -------
        pd.DataFrame
            A pandas DataFrame containing various residential construction metrics.

        Notes
        -----
        The function calculates several metrics including population growth, household changes, building growth,
        yearly constructed floor area, and accumulated constructed floor area.
        """
        # A subset of population should be equal to period
        self._check_index(period, population)
        # building_category_share or a subset should be equal to population
        self._check_index(period, building_category_share)
        # yearly_demolished_floor_area to or replace period as the guiding factor
        self._check_index(period, yearly_demolished_floor_area)
        # household_size or a subset should be equal to population
        self._check_index(period, household_size)

        # It might be sensible to calculate total floor area and work from there (like commercial) rather than going
        # through average_floor_area <-> building_growth <-> households_change <-> population_growth
        population = population[yearly_demolished_floor_area.index]
        building_category_share = building_category_share[yearly_demolished_floor_area.index]
        household_size = household_size[yearly_demolished_floor_area.index]
        if isinstance(average_floor_area, pd.Series):
            average_floor_area = average_floor_area[yearly_demolished_floor_area.index]

        households_by_year = self.calculate_households_by_year(household_size, population)

        # Årlig endring i antall boliger (brukt Årlig endring i antall småhus)
        households_change = self.calculate_household_change(households_by_year)
        building_growth = self.calculate_building_growth(building_category_share, households_change)

        # Årlig endring areal småhus (brukt Årlig nybygget areal småhus)
        yearly_floor_area_constructed = self.calculate_yearly_floor_area_change(building_growth, average_floor_area)

        # Årlig revet areal småhus
        floor_area_change = self.calculate_yearly_constructed_floor_area(
            build_area_sum, yearly_floor_area_constructed, yearly_demolished_floor_area)

        # Nybygget småhus akkumulert
        floor_area_change_accumulated = self.calculate_yearly_new_building_floor_area_sum(floor_area_change)

        df = pd.DataFrame(data={
            'population': population,
            'household_size': household_size,
            'households': households_by_year,
            'households_change': households_change,
            'net_constructed_floor_area': yearly_floor_area_constructed,
            'demolished_floor_area': yearly_demolished_floor_area,
            'constructed_floor_area': floor_area_change,
            'accumulated_constructed_floor_area': floor_area_change_accumulated},
            index=floor_area_change_accumulated.index)

        return df

    def _check_index(self, period, values: pd.Series) -> bool:
        name = values.name
        if not all([y in values.index for y in period]):
            logger.debug(
                f'{name}.index({values.index[0]}, {values.index[-1]}) is not equal to period(start={period.start}, {period.end})')
            return False
        return True

    @staticmethod
    def calculate_yearly_new_building_floor_area_sum(yearly_new_building_floor_area_house: pd.Series):
        """
        Calculate the accumulated constructed floor area over the years.

        Parameters
        ----------
        yearly_new_building_floor_area_house : pd.Series
            A pandas Series representing the yearly new building floor area.

        Returns
        -------
        pd.Series
            A pandas Series representing the accumulated constructed floor area, named
                'accumulated_constructed_floor_area'.

        Notes
        -----
        The function calculates the cumulative sum of the yearly new building floor area.
        """
        return pd.Series(yearly_new_building_floor_area_house.cumsum(), name='accumulated_constructed_floor_area')

    @staticmethod
    def calculate_yearly_constructed_floor_area(build_area_sum: pd.Series,
                                                yearly_floor_area_change: pd.Series,
                                                yearly_demolished_floor_area: pd.Series) -> pd.Series:
        """
        Calculate the yearly constructed floor area based on changes and demolitions.

        Parameters
        ----------
        build_area_sum : pd.Series
            A pandas Series representing the accumulated building area sum.
        yearly_floor_area_change : pd.Series
            A pandas Series representing the yearly change in floor area.
        yearly_demolished_floor_area : pd.Series
            A pandas Series representing the yearly demolished floor area.

        Returns
        -------
        pd.Series
            A pandas Series representing the yearly constructed floor area, named 'constructed_floor_area'.

        Notes
        -----
        The function calculates the yearly new building floor area by adding the yearly floor area change
        to the yearly demolished floor area. It then updates the values based on the build_area_sum index.

        """
        bas_missing_year = [str(y) for y in yearly_demolished_floor_area.iloc[0:2].index if
                            y not in build_area_sum.index or
                            np.isnan(build_area_sum.loc[y])]

        if bas_missing_year:
            msg = f'missing constructed floor area for {", ".join(bas_missing_year)}'
            raise ValueError(msg)

        yearly_new_building_floor_area_house = yearly_floor_area_change + yearly_demolished_floor_area
        yearly_new_building_floor_area_house.loc[build_area_sum.index.to_numpy()] = build_area_sum.loc[
            build_area_sum.index.to_numpy()]

        return pd.Series(yearly_new_building_floor_area_house, name='constructed_floor_area')

    @staticmethod
    def calculate_yearly_floor_area_change(building_change: pd.Series,
                                           average_floor_area: typing.Union[pd.Series, int] = 175) -> pd.Series:
        """
        Calculate the yearly floor area change based on building changes and average floor area.

        Parameters
        ----------
        building_change : pd.Series
            A pandas Series representing the change in the number of buildings.
        average_floor_area : typing.Union[pd.Series, int], optional
            The average floor area per building. Can be a pandas Series or an integer. Default is 175.

        Returns
        -------
        pd.Series
            A pandas Series representing the yearly floor area change, named 'house_floor_area_change'.

        Notes
        -----
        The function calculates the yearly floor area change by multiplying the building change by the average floor
            area.
        The floor area change for the first two years set to 0.
        """
        average_floor_area = average_floor_area.loc[building_change.index] if isinstance(average_floor_area, pd.Series) else average_floor_area
        yearly_floor_area_change = average_floor_area * building_change
        yearly_floor_area_change.iloc[0:2] = 0.0
        return pd.Series(yearly_floor_area_change, name='house_floor_area_change')

    @staticmethod
    def calculate_population_growth(population: pd.Series) -> pd.Series:
        """
        Calculate the annual growth in building categories based on household changes.

        Parameters
        ----------
        population : pd.Series
            A pandas Series representing the population indexed by year.
        Returns
        -------
        pd.Series
            A pandas Series representing the annual growth population.

        """
        population_growth = (population / population.shift(1)) - 1
        population_growth.name = 'population_growth'
        return population_growth

    @staticmethod
    def calculate_building_growth(building_category_share: pd.Series, households_change: pd.Series) -> pd.Series:
        """
            Calculate the annual growth in building categories based on household changes.

            Parameters
            ----------
            building_category_share : pd.Series
                A pandas Series representing the share (0 to 1 ) of each building category.
            households_change : pd.Series
                A pandas Series representing the annual change in the number of households.

            Returns
            -------
            pd.Series
                A pandas Series representing the annual growth in building categories, named 'building_growth'.

            """

        house_share = building_category_share
        # Årlig endring i antall småhus (brukt  Årlig endring areal småhus)
        house_change = households_change * house_share
        return pd.Series(house_change, name='building_growth')

    @staticmethod
    def calculate_household_change(households: pd.Series) -> pd.Series:
        """
        Calculate the annual change in the number of households.

        Parameters
        ----------
        households : pd.Series
            A pandas Series representing the number of households over time.

        Returns
        -------
        pd.Series
            A pandas Series representing the annual change in the number of households, named 'household_change'.
        """
        return pd.Series(households - households.shift(1), name='household_change')

    @staticmethod
    def calculate_households_by_year(household_size: pd.Series, population: pd.Series) -> pd.Series:
        """
        Calculate the number of households by year based on household size and population.

        Parameters
        ----------
        household_size : pd.Series
            A pandas Series representing the average household size over time.
        population : pd.Series
            A pandas Series representing the population over time.

        Returns
        -------
        pd.Series
            A pandas Series representing the number of households by year, named 'households'.

        Notes
        -----
        The function calculates the number of households by dividing the population by the average household size.

        """
        households = population / household_size
        households.name = 'households'
        return households

    @staticmethod
    def calculate_industrial_construction(building_category: BuildingCategory,
                                          total_floor_area: typing.Union[pd.Series, int],
                                          constructed_floor_area: pd.Series = None,
                                          demolition_floor_area: pd.Series = None,
                                          population: pd.Series = None,
                                          period=YearRange(2010, 2050)) -> pd.DataFrame:
        """
        Calculate the industrial construction metrics over a given period.

        Parameters
        ----------

        building_category : BuildingCategory, optional
            The category of the building.
        total_floor_area : pd.Series | int
            The total floor area at the start of the period.
        constructed_floor_area : pd.Series, optional
            Series containing the constructed floor area for each year.
        demolition_floor_area : pd.Series, optional
            Series containing the demolished floor area for each year.
        population : pd.DataFrame, optional
            DataFrame containing the population data for each year.
        period : YearRange
            start and end of model in years
        Returns
        -------
        pd.DataFrame
            DataFrame containing the calculated construction metrics:
            - total_floor_area: Total floor area for each year.
            - building_growth: Growth rate of the building floor area.
            - demolished_floor_area: Demolished floor area for each year.
            - constructed_floor_area: Constructed floor area for each year.
            - accumulated_constructed_floor_area: Cumulative constructed floor area.
            - floor_area_over_population_growth: Ratio of floor area growth over population growth.

        Notes
        -----
        - If `building_category` is `BuildingCategory.STORAGE_REPAIRS`, the total floor area remains constant from 2010
            to 2051.
        - The function assumes that the input Series and DataFrame have appropriate indices corresponding to the years.
        """

        logger.debug(f'calculate_industrial_construction {building_category}')

        ConstructionCalculator()._check_index(period, demolition_floor_area)
        ConstructionCalculator()._check_index(period, population)

        # Filter out constructed_floor_area outside period
        constructed_floor_area = constructed_floor_area.loc[[y for y in constructed_floor_area.index if y in period]]

        if not isinstance(total_floor_area, pd.Series):
            total_floor_area = pd.Series(data=[total_floor_area], index=[period.start])

        for year in constructed_floor_area.index:
            if year not in period.subset(1, 4):
                logger.warning(f'Construction floor area for {building_category} {year} is missing from input')
                continue
            total_floor_area.loc[year] = total_floor_area.loc[year - 1] - \
                                         demolition_floor_area.loc[year] + \
                                         constructed_floor_area.loc[year]

        population_growth = ConstructionCalculator.calculate_population_growth(population)
        building_growth = ConstructionCalculator.calculate_floor_area_growth(total_floor_area, period)

        floor_area_over_population_growth = ConstructionCalculator.calculate_floor_area_over_building_growth(
            building_growth=building_growth,
            population_growth=population_growth,
            years=period)

        total_floor_area = ConstructionCalculator.calculate_total_floor_area(
            floor_area_over_population_growth=floor_area_over_population_growth,
            population_growth=population_growth,
            total_floor_area=total_floor_area,
            period=period)

        # STORAGE_REPAIRS has constant floor area
        if building_category == BuildingCategory.STORAGE:
            total_floor_area.loc[period.start:period.end + 1] = total_floor_area.loc[period.start]

        constructed_floor_area = ConstructionCalculator.calculate_constructed_floor_area(
            constructed_floor_area=constructed_floor_area,
            demolition_floor_area=demolition_floor_area,
            total_floor_area=total_floor_area,
            period=period)

        accumulated_constructed_floor_area = constructed_floor_area.cumsum()

        # Make the resulting DataFrame
        construction = pd.DataFrame(data={
            'total_floor_area': total_floor_area,
            'building_growth': building_growth,
            'demolished_floor_area': demolition_floor_area,
            'constructed_floor_area': constructed_floor_area,
            'accumulated_constructed_floor_area': accumulated_constructed_floor_area,
            'floor_area_over_population_growth': floor_area_over_population_growth
        }, index=period.to_index())

        return construction

    @staticmethod
    def calculate_total_floor_area(floor_area_over_population_growth: pd.Series,
                                   population_growth: pd.Series,
                                   total_floor_area: pd.Series,
                                    period: YearRange):
        """
        Calculate the total floor area over a given period based on population growth.

        Parameters
        ----------
        floor_area_over_population_growth : pd.Series
            A pandas Series containing the floor area change over population growth for each year.
        population_growth : pd.Series
            A pandas Series containing the population growth for each year.
        total_floor_area : pd.Series
            A pandas Series containing the total floor area for each year.
        period : YearRange
            A named tuple containing the start and end years of the period.

        Returns
        -------
        pd.Series
            Updated pandas Series with the total floor area for each year in the given period.

        Notes
        -----
        The calculation starts from `period.start + 5` to `period.end`. For each year, the total floor area is updated
        based on the formula:

            total_floor_area[year] = ((change_ratio * pop_growth) + 1) * previous_floor_area
        """
        calculated_total_floor_area = total_floor_area.copy()

        # Dette er grusomt.
        years_to_update = period.subset(offset=list(period).index(max(total_floor_area.index) + 1), length=-1)
        for year in years_to_update:
            change_ratio = floor_area_over_population_growth.loc[year]
            growth = population_growth.loc[year]
            previous_floor_area = calculated_total_floor_area.loc[year - 1]
            calculated_total_floor_area.loc[year] = ((change_ratio * growth) + 1) * previous_floor_area
        calculated_total_floor_area.name = 'total_floor_area'
        return calculated_total_floor_area

    @staticmethod
    def calculate_constructed_floor_area(constructed_floor_area: pd.Series,
                                         demolition_floor_area: pd.Series,
                                         total_floor_area: pd.Series,
                                         period: YearRange) -> pd.Series:
        """
        Calculate the constructed floor area over a specified period.

        Parameters
        ----------
        constructed_floor_area : pd.Series
            A pandas Series to store the constructed floor area for each previous year.
        demolition_floor_area : pd.Series
            A pandas Series containing the demolition floor area for each year.
        total_floor_area : pd.Series
            A pandas Series containing the total floor area for each year.
        period : YearRange
            An object containing the start year, end year, and the range of years.

        Returns
        -------
        pd.Series
            A pandas Series containing the constructed floor area for each year in the period.

        Notes
        -----
        The constructed floor area is calculated from year 6 onwards by subtracting the previous year's
        floor area from the current year's floor area and adding the previous year's demolition floor area.

        Examples
        --------
        >>> construction = pd.Series({2020: 0, 2021: 0, 2022: 0, 2023: 0, 2024: 0, 2025: 0})
        >>> demolition = pd.Series({2020: 50, 2021: 60, 2022: 70, 2023: 80, 2024: 90, 2025: 100})
        >>> total = pd.Series({2020: 1000, 2021: 1100, 2022: 1200, 2023: 1300, 2024: 1400, 2025: 1500})
        >>> years = YearRange(2020, 2025)
        >>> ConstructionCalculator.calculate_constructed_floor_area(construction, demolition, total, years)
        2020      0.0
        2021      0.0
        2022      0.0
        2023      0.0
        2024      0.0
        2025    200.0
        dtype: float64
        """

        # Calculate constructed floor area from year 6 by subtracting last year's floor area with current floor area
        # and adding last year's demolition.
        # Calculate constructed floor area from year 6 by substracting last years floor area with current floor area
        #  and adding last years demolition.
        for year in [y for y in period if y not in constructed_floor_area.index and y > period.start]:
            floor_area = total_floor_area.loc[year]
            previous_year_floor_area = total_floor_area.loc[year - 1]
            demolished = demolition_floor_area.loc[year]
            constructed = floor_area - previous_year_floor_area + demolished
            constructed_floor_area[year] = constructed
        constructed_floor_area.name = 'constructed_floor_area'
        return constructed_floor_area

    @staticmethod
    def calculate_floor_area_growth(total_floor_area: pd.Series, period: YearRange) -> pd.Series:
        """
        Calculate the growth of floor area over a specified period.

        Parameters
        ----------
        total_floor_area : pd.Series
            A pandas Series containing the total floor area for each year.
        period : YearRange
            An object containing the start year, end year, and the range of years.

        Returns
        -------
        pd.Series
            A pandas Series containing the floor area growth for each year in the period.

        Notes
        -----
        The growth for the first year in the period is set to NaN. The growth for the next four years
        is calculated based on the change in total floor area from the previous year.

        Examples
        --------
        >>> total_floor_area = pd.Series({2020: 1000, 2021: 1100, 2022: 1210, 2023: 1331, 2024: 1464})
        >>> period = YearRange(2020, 2024)
        >>> ConstructionCalculator.calculate_floor_area_growth(total_floor_area, period)
        2020       NaN
        2021    0.1000
        2022    0.1000
        2023    0.1000
        2024    0.1000
        dtype: float64
        """
        floor_area_growth = pd.Series(data=itertools.repeat(0.0, len(period.year_range)), index=period.year_range)
        floor_area_growth.loc[period.start] = np.nan
        # The next 4 years of building growth is calculated from change in total_floor_area
        for year in range(period.start + 1, period.start + 5):
            if year in total_floor_area.index:
                floor_area_growth.loc[year] = (total_floor_area.loc[year] / total_floor_area.loc[year - 1]) - 1
        return floor_area_growth

    @staticmethod
    def calculate_floor_area_over_building_growth(building_growth: pd.Series,
                                                  population_growth: pd.Series,
                                                  years: YearRange) -> pd.Series:
        """
            Calculate the floor area over building growth for a given range of years.

            Parameters
            ----------
            building_growth : pd.Series
                A pandas Series representing the building growth over the years.
            population_growth : pd.Series
                A pandas Series representing the population growth over the years.
            years : YearRange
                An object representing the range of years for the calculation.

            Returns
            -------
            pd.Series
                A pandas Series representing the floor area over building growth for each year in the specified range.

            Notes
            -----
            - The first year in the range is initialized with NaN.
            - For the first 4 years, the floor area over building growth is calculated directly from the building and population growth.
            - For the next 5 years, the mean floor area over building growth is used.
            - From the 11th year onwards, the value is set to 1.
            - For the years between the 11th and 21st, the value is interpolated linearly.

            Examples
            --------
            >>> building_growth = pd.Series([1.2, 1.3, 1.4, 1.5, 1.6], index=[2010, 2011, 2012, 2013, 2014])
            >>> pd.Series([1.1, 1.2, 1.3, 1.4, 1.5], index=[2010, 2011, 2012, 2013, 2014])
            >>> years = YearRange(start=2010, end=2050)
            >>> ConstructionCalculator.calculate_floor_area_over_building_growth(building_growth, population_growth, years)
            2010         NaN
            2011    1.083333
            2012    1.076923
            2013    1.071429
            2014    1.066667
            2015    1.074588
            2016    1.074588
            …
            2050    1.000000
            2051    1.000000
            dtype: float64
            """

        floor_area_over_population_growth = pd.Series(
            data=[np.nan] + list(itertools.repeat(1, len(years) - 1)),
            index=years.to_index())

        # Initialize with NaN for the first year
        floor_area_over_population_growth.loc[years.start] = np.nan

        # Calculate for the next 4 years
        for year in building_growth[(building_growth > 0) & (building_growth.index > years.start)].index:
            floor_area_over_population_growth[year] = building_growth.loc[year] / population_growth.loc[year]

        mean_idx = building_growth[building_growth > 0].index

        # If there is no growth, return 0
        if not any(mean_idx):
            return floor_area_over_population_growth

        # Calculate for the next 6 years using the mean
        mean_floor_area_population = floor_area_over_population_growth.loc[mean_idx].mean()
        for year in years.subset(list(years).index(max(mean_idx) + 1), 6):
            floor_area_over_population_growth.loc[year] = mean_floor_area_population

        # Set to 1 from the 11th year onwards
        if len(years) > 11:
            for year in years.subset(11):
                floor_area_over_population_growth.loc[year] = 1

            # Interpolate linearly between the 11th and 21st years
            for year in years.subset(11, 10):
                floor_area_over_population_growth.loc[year] = \
                    (floor_area_over_population_growth.loc[years.start + 10] - (year - (years.start + 10)) * (
                            (floor_area_over_population_growth.loc[
                                 years.start + 10] -
                             floor_area_over_population_growth.loc[
                                 years.start + 20]) / 10))
        return floor_area_over_population_growth

    @staticmethod
    def calculate_construction_as_list(building_category: BuildingCategory,
                                       demolition_floor_area: Union[pd.Series, list],
                                       database_manager: DatabaseManager = None,
                                       period: YearRange = YearRange(2010, 2050)) -> typing.List[float]:
        """
       Calculates constructed floor area for buildings based using provided demolition_floor_area
         and input data from database_manager

       Parameters
       ----------
       building_category: BuildingCategory
       demolition_floor_area: pd.Series expects index=2010..2050
       database_manager: DatabaseManager (optional)
       period : YearRange

       Returns
       -------
       accumulated_constructed_floor_area: List
       """

        yearly_constructed = ConstructionCalculator.calculate_construction(
            building_category=building_category,
            demolition_floor_area=demolition_floor_area,
            database_manager=database_manager if database_manager else DatabaseManager(),
            period=period)

        accumulated_constructed_floor_area = yearly_constructed['accumulated_constructed_floor_area'].to_list()
        return accumulated_constructed_floor_area

    @staticmethod
    def calculate_commercial_construction(building_category: BuildingCategory,
                                          population: pd.Series,
                                          area_by_person: typing.Union[float, pd.Series],
                                          demolition: pd.Series) -> pd.DataFrame:
        """
        Calculate a projection of contructed floor area by building_category. The calculation makes the assumption that
        all demolished floor area will be replaced with construction.

        Parameters
        ----------
        building_category : BuildingCategory
            possibly redundant building_category for the construction projection
        population : pd.Series
            population by year
        area_by_person : pd.Series
            float or pd.Series containing the floor area per person for the building_category
        demolition : pd.Series
            yearly demolition to be added to the floor area.

        Returns
        -------
        pd.Dataframe
            floor area constructed by year
            accumalated contructed floor area 
        """
        if not demolition.index.isin(population.index).all(): 
            raise ValueError('years in demolition series not present in popolutation series')
        
        total_area = area_by_person * population.loc[demolition.index]
        demolition_prev_year = demolition.shift(periods=1, fill_value=0)
        yearly_constructed = total_area.diff().fillna(0) + demolition_prev_year

        accumulated_constructed = yearly_constructed.cumsum()
        commercial_construction = pd.DataFrame({
            'demolished_floor_area': demolition,
            "constructed_floor_area": yearly_constructed,
            "accumulated_constructed_floor_area": accumulated_constructed
        })
        return commercial_construction

    @staticmethod
    def calculate_construction(building_category: BuildingCategory, demolition_floor_area: Union[pd.Series, list],
                               database_manager: DatabaseManager, period: YearRange) -> pd.DataFrame:
        """
        Calculates constructed floor area for buildings based using provided demolition_floor_area
          and input data from database_manager
        Parameters
        ----------

        building_category: BuildingCategory
        demolition_floor_area: pd.Series expects index=2010..2050
        database_manager: DatabaseManager
        period : YearRange

        Returns
        -------
        calculated_construction: pd.DataFrame
                                           dataframe columns include;
                                           (building_growth)
                                           (demolished_floor_area)
                                           (constructed_floor_area)
                                           (accumulated_constructed_floor_area)
                                           (total_floor_area)
                                           (floor_area_over_population_growth)
                                           (households)
                                           (household_size)
                                           (population)
                                           (population_growth)

        -------

        """
        if isinstance(demolition_floor_area, list):
            demolition_floor_area = pd.Series(demolition_floor_area, index=period.range())

        new_buildings_population = database_manager.get_construction_population()[['population', 'household_size']]
        if building_category.is_non_residential():
            return ConstructionCalculator.calculate_commercial_construction(
                building_category=building_category,
                population=new_buildings_population['population'],
                area_by_person=database_manager.get_area_per_person(building_category),
                demolition=demolition_floor_area
            )
        yearly_construction_floor_area = database_manager.get_building_category_floor_area(building_category)
        area_parameters = database_manager.get_area_parameters()
        total_floor_area = area_parameters[area_parameters.building_category == building_category].area.sum()

        if building_category.is_residential():
            household_size = new_buildings_population['household_size']
            population = new_buildings_population['population']

            share_name, floor_area_name = 'new_house_share', 'floor_area_new_house'
            if building_category == BuildingCategory.APARTMENT_BLOCK:
                share_name = 'new_apartment_block_share'
                floor_area_name = 'flood_area_new_apartment_block'
            new_buildings_category_share = database_manager.get_new_buildings_category_share()
            building_category_share = new_buildings_category_share[share_name]
            average_floor_area = new_buildings_category_share[floor_area_name]
            build_area_sum = pd.Series(
                data=yearly_construction_floor_area,
                index=range(period.start, period.start+len(yearly_construction_floor_area)))

            return ConstructionCalculator().calculate_residential_construction(population=population,
                                                                               household_size=household_size,
                                                                               building_category_share=building_category_share,
                                                                               build_area_sum=build_area_sum,
                                                                               yearly_demolished_floor_area=demolition_floor_area,
                                                                               average_floor_area=average_floor_area,
                                                                               period=period)

        return ConstructionCalculator.calculate_industrial_construction(building_category=building_category,
                                                                        total_floor_area=total_floor_area,
                                                                        constructed_floor_area=yearly_construction_floor_area,
                                                                        demolition_floor_area=demolition_floor_area,
                                                                        population=new_buildings_population[
                                                                            'population'],
                                                                        period=period)


    @staticmethod
    def calculate_all_construction(demolition_by_year: Union[pd.Series, list],
                                   database_manager: DatabaseManager, period: YearRange) -> pd.DataFrame:
        """

        Parameters
        ----------
        demolition_by_year : pd.Series, List[float]
        database_manager : DatabaseManager
        period : YearRange

        Returns
        -------
        DataFrame:
            with building_category and area
        """

        construction = []
        for building_category in demolition_by_year.index.get_level_values(level='building_category').unique():
            df = demolition_by_year.to_frame().query(f'building_category=="{building_category}"').reset_index().set_index(['year'])
            c = ConstructionCalculator.calculate_construction(
                BuildingCategory.from_string(building_category),
                df.demolition,
                database_manager,
                period)
            c['building_category'] = building_category
            construction.append(c.reset_index())

        return pd.concat(construction)
