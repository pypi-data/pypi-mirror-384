import typing

import pandas as pd

from .building_category import BuildingCategory
from .building_condition import BuildingCondition
from .data_classes import ScurveParameters


class FilterScurveParams():
    """
    A utility class for filtering S-curve parameters based on building category and condition.

    This class provides a static method to filter a DataFrame containing S-curve parameters, 
    extracting the relevant data for a specific building category and set of conditions.
    """

    COL_BUILDING_CATEGORY = 'building_category'
    COL_BUILDING_CONDITION = 'condition'
    COL_EARLIEST_AGE = 'earliest_age_for_measure'
    COL_AVERAGE_AGE = 'average_age_for_measure'
    COL_LAST_AGE = 'last_age_for_measure'
    COL_RUSH_YEARS = 'rush_period_years'
    COL_RUSH_SHARE = 'rush_share'
    COL_NEVER_SHARE = 'never_share'

    @staticmethod
    def filter(building_category: BuildingCategory,
               scurve_condition_list: typing.List[str],
               scurve_params: pd.DataFrame) -> typing.Dict[str, ScurveParameters]:
        """
        Filters S-curve parameters by building category and condition.

        This method filters a DataFrame containing S-curve parameters to extract data specific to 
        the provided building category and conditions listed in `scurve_condition_list`. The filtered 
        data is then converted into a dictionary of `ScurveParameters` dataclass instances, each 
        representing the S-curve parameters for a particular condition.

        Parameters:
        - building_category (BuildingCategory): The building category for which the S-curve parameters are being filtered.
        - scurve_condition_list (List[str]): A list of conditions (as strings) for which the S-curve parameters are needed.
        - scurve_params (pd.DataFrame): DataFrame containing the S-curve parameters, with columns for building category, condition, and various age-related metrics.

        Returns:
        - filtered_scurve_params (Dict[str, ScurveParameters]): A dictionary where the keys are conditions (str) and the values 
                                                                are `ScurveParameters` dataclass instances containing the 
                                                                corresponding S-curve parameters for each condition.

        Raises:
        - KeyError: If the provided building category is not found in the S-curve parameters DataFrame.
        """
        filtered_scurve_params = {}

        for condition in scurve_condition_list:
            if not scurve_params.building_category.str.contains(building_category).any():
                msg = 'Unknown building_category "{}" encountered when setting up scurve parameters'.format(building_category)
                raise KeyError(msg)

            # Filter dataframe on building category and condition
            scurve_params_filtered = scurve_params[(scurve_params[FilterScurveParams.COL_BUILDING_CATEGORY] == building_category) &
                                                   (scurve_params[FilterScurveParams.COL_BUILDING_CONDITION] == condition)]

            # Assuming there is only one row in the filtered DataFrame
            scurve_params_row = scurve_params_filtered.iloc[0]

            # Convert the single row to a dictionary
            scurve_params_dict = scurve_params_row.to_dict()
            
            # Map the dictionary values to the dataclass attributes
            scurve_parameters = ScurveParameters(
                building_category=scurve_params_dict[FilterScurveParams.COL_BUILDING_CATEGORY],
                condition=scurve_params_dict[FilterScurveParams.COL_BUILDING_CONDITION],
                earliest_age=scurve_params_dict[FilterScurveParams.COL_EARLIEST_AGE],
                average_age=scurve_params_dict[FilterScurveParams.COL_AVERAGE_AGE], 
                rush_years=scurve_params_dict[FilterScurveParams.COL_RUSH_YEARS], 
                last_age=scurve_params_dict[FilterScurveParams.COL_LAST_AGE],
                rush_share=scurve_params_dict[FilterScurveParams.COL_RUSH_SHARE],
                never_share=scurve_params_dict[FilterScurveParams.COL_NEVER_SHARE],
            )

            filtered_scurve_params[condition] = scurve_parameters

        return filtered_scurve_params 