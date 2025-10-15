import pandas as pd
from loguru import logger


class SCurve:
    """
    Calculates S-curve per building condition.

    Raises
    ------
    ValueError
        When any of the arguments are less than zero
        
    Notes
    -----
    To make calculations return better rounded more and accurate results, _rush_share and _never_share area
    multiplied by 100 internally.  _calc_pre_rush_rate() _calc_rush_rate() _calc_post_rush_rate() will
    still return percent as a value between 0 and 1.
    """ 

    # TODO:
    # - add check to control that defined periods match building lifetime index in get_rates_per_year

    earliest_age: int = 0
    average_age: int
    last_age: int
    rush_years: int
    rush_share: float
    never_share: float
    building_lifetime: int = 130

    def __init__(self, 
                 earliest_age: int,
                 average_age: int,
                 last_age: int,
                 rush_years: int,
                 rush_share: float,
                 never_share: float,
                 building_lifetime: int = 130):
        errors = []
        if earliest_age < 0:
            logger.warning(f'Expected value above zero for {earliest_age=}')
            errors.append('earliest_age')
        if average_age < 0:
            logger.warning(f'Expected value above zero for {average_age=}')
            errors.append('average_age')
        if last_age < 0:
            logger.warning(f'Expected value above zero for {last_age=}')
            errors.append('last_age')
        if rush_share < 0:
            logger.warning(f'Expected value above zero for {rush_share=}')
            errors.append('rush_share')
        if never_share < 0:
            logger.warning(f'Expected value above zero for {never_share=}')
            errors.append('never_share')
        if errors:
            msg = f'Illegal value for {" ".join(errors)}'
            raise ValueError(msg)

        self._building_lifetime = building_lifetime
        self._earliest_age = earliest_age
        self._average_age = average_age
        self._last_age = last_age
        self._rush_years = rush_years
        self._rush_share = rush_share * 100
        self._never_share = never_share * 100

        # Calculate yearly rates
        self._pre_rush_rate = self._calc_pre_rush_rate() 
        self._rush_rate = self._calc_rush_rate()
        self._post_rush_rate = self._calc_post_rush_rate()
        
        # Calculate S-curves
        self.scurve = self.calc_scurve() 

    def _calc_pre_rush_rate(self) -> float:
        """
        Calculate the yearly measure rate for the pre-rush period.

        The pre-rush rate represents the percentage share of building area that has 
        undergone a measure per year during the period before the rush period begins.

        Returns
        -------
        float
            Yearly measure rate in the pre-rush period.

        Notes
        -----
        To make calculations return better rounded more and accurate results, _rush_share and _never_share area
        multiplied by 100 internally.  _calc_pre_rush_rate() _calc_rush_rate() _calc_post_rush_rate() will
        still return percent as a value between 0 and 1.
        """
        remaining_share = (100 - self._rush_share - self._never_share)
        age_range = (50 / (self._average_age - self._earliest_age - (self._rush_years / 2)))
        pre_rush_rate = remaining_share * age_range / 100
        return round(pre_rush_rate / 100, 13)
    
    def _calc_rush_rate(self) -> float:
        """
        Calculate the yearly measure rate for the rush period.

        The rush rate represents the percentage share of building area that has 
        undergone a measure per year during the rush period.

        Returns
        -------
        float
            Yearly rate in the rush period.

        Notes
        -----
        To make calculations return better rounded more and accurate results, _rush_share and _never_share area
        multiplied by 100 internally.  _calc_pre_rush_rate() _calc_rush_rate() _calc_post_rush_rate() will
        still return percent as a value between 0 and 1.
        """
        rush_rate = self._rush_share / self._rush_years
        return round(rush_rate / 100, 13)
    
    def _calc_post_rush_rate(self) -> float:
        """
        Calculate the yearly measure rate for the post-rush period.

        The post-rush rate represents the percentage share of building area that has 
        undergone a measure per year during the period after the rush period ends.

        Returns
        -------
        float
            Yearly rate in the post-rush period.

        Notes
        -----
        To make calculations return better rounded more and accurate results, _rush_share and _never_share area
        multiplied by 100 internally.  _calc_pre_rush_rate() _calc_rush_rate() _calc_post_rush_rate() will
        still return percent as a value between 0 and 1.
        """
        remaining_share = (100 - self._rush_share - self._never_share)
        age_range = (50 / (self._last_age - self._average_age - (self._rush_years / 2)))
        post_rush_rate = remaining_share * age_range / 100
        return round(post_rush_rate / 100, 13)

    def get_rates_per_year_over_building_lifetime(self) -> pd.Series:
        """
        Create a series that holds the yearly measure rates over the building lifetime.

        This method defines the periods in the S-curve, adds the yearly measure rates to
        the corresponding periods, and stores them in a pandas Series.

        Returns
        -------
        pd.Series
            A Series containing the yearly measure rates over the building lifetime
            with an index representing the age from 1 to the building lifetime.

        """

        # Define the length of the different periods in the S-curve
        earliest_years = self._earliest_age - 1
        pre_rush_years = int(self._average_age - self._earliest_age - (self._rush_years/2))
        rush_years = self._rush_years
        post_rush_years = int(self._last_age - self._average_age - (self._rush_years/2))
        last_years = self._building_lifetime - earliest_years - pre_rush_years - rush_years - post_rush_years
        
        # Redefine periods for Demolition, as the post_rush_year calculation isn't the same as for Small measures and
        # rehabilitation
        if last_years < 0:
            last_years = 0 
            post_rush_years = self._building_lifetime - earliest_years - pre_rush_years - rush_years

        # Create list where the yearly rates are placed according to their corresponding period in the buildings
        # lifetime

        rates_per_year = (
            [0] * earliest_years + 
            [self._pre_rush_rate] * pre_rush_years +
            [self._rush_rate] * rush_years +
            [self._post_rush_rate] * post_rush_years +
            [0] * last_years
        )  
        
        # Create a pd.Series with an index from 1 to building_lifetime 
        index = range(1, self._building_lifetime + 1)
        rates_per_year = pd.Series(rates_per_year, index=index, name='scurve')
        rates_per_year.index.name = 'age'

        return rates_per_year

    def calc_scurve(self) -> pd.Series:
        """
        Calculates the S-curve by accumulating the yearly measure rates over the building's lifetime.

        This method returns a pandas Series representing the S-curve, where each value corresponds 
        to the accumulated rate up to that age.

        Returns
        -------
        pd.Series
            A Series containing the accumulated rates of the S-curve with an index representing the age from 1 to the
                building lifetime.
        """
        # Get rates_per_year and accumulate them over the building lifetime
        rates_per_year = self.get_rates_per_year_over_building_lifetime() 
        scurve = rates_per_year.cumsum()
        return scurve


def main():
    import pathlib
    logger.info('Calculate all scurves from data/s_curve.csv')
    area_parameters_path = pathlib.Path(__file__).parent.parent / 'data/s_curve.csv'
    df = pd.read_csv(area_parameters_path)
    for r, v in df.iterrows():
        scurve = SCurve(earliest_age=v.earliest_age_for_measure,
                        average_age=v.average_age_for_measure,
                        last_age=v.last_age_for_measure,
                        rush_years=v.rush_period_years,
                        never_share=v.never_share,
                        rush_share=v.rush_share)
        print(scurve.calc_scurve())
    logger.info('done')

if __name__ == '__main__':
    main()
