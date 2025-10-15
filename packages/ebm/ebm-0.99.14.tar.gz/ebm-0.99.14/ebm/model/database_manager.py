import itertools
import typing

import pandas as pd
from loguru import logger

from ebm import validators
from ebm.energy_consumption import calibrate_heating_systems
from ebm.model.column_operations import explode_building_category_column, explode_building_code_column, explode_unique_columns
from ebm.model.dataframemodels import EnergyNeedYearlyImprovements, YearlyReduction, PolicyImprovement
from ebm.model.energy_purpose import EnergyPurpose
from ebm.model.file_handler import FileHandler
from ebm.model.building_category import BuildingCategory, expand_building_categories
from ebm.model.data_classes import TEKParameters, YearRange


# TODO:
# - add method to change all strings to lower case and underscore instead of space
# - change column strings used in methods to constants


class DatabaseManager:
    """
    Manages database operations.
    """

    # Column names
    COL_TEK = 'building_code'
    COL_TEK_BUILDING_YEAR = 'building_year'
    COL_TEK_START_YEAR = 'period_start_year'
    COL_TEK_END_YEAR = 'period_end_year'
    COL_BUILDING_CATEGORY = 'building_category'
    COL_BUILDING_CONDITION = 'building_condition'
    COL_AREA = 'area'
    COL_ENERGY_REQUIREMENT_PURPOSE = 'purpose'
    COL_ENERGY_REQUIREMENT_VALUE = 'kwh_m2'
    COL_HEATING_REDUCTION = 'reduction_share'

    DEFAULT_VALUE = 'default'

    def __init__(self, file_handler: FileHandler = None):
        # Create default FileHandler if file_handler is None

        self.file_handler = file_handler if file_handler is not None else FileHandler()
    
    def get_building_code_list(self):
        """
        Get a list of building_code.

        Returns:
        - building_code_list (list): List of building_code.
        """
        building_code_id = self.file_handler.get_building_code()
        building_code_list = building_code_id[self.COL_TEK].unique()
        return building_code_list

    def make_building_purpose(self, years: YearRange | None = None) -> pd.DataFrame:
        """
        Returns a dataframe of all combinations building_categories, teks, original_condition, purposes
        and optionally years.

        Parameters
        ----------
        years : YearRange, optional

        Returns
        -------
        pd.DataFrame
        """
        data = []
        columns = [list(BuildingCategory), self.get_building_code_list().tolist(), EnergyPurpose]
        column_headers = ['building_category', 'building_code', 'building_condition', 'purpose']
        if years:
            columns.append(years)
            column_headers.append('year')

        for bc, tek, purpose, *year in itertools.product(*columns):
            row = [bc, tek, 'original_condition', purpose]
            if years:
                row.append(year[0])
            data.append(row)

        return pd.DataFrame(data=data, columns=column_headers)

    def get_building_codes(self) -> pd.DataFrame:
        """
        Retrieve building_code_parameters

        Returns
        -------
        pd.DataFrame
            Pandas Dataframe containing building_code with parameters
        """
        building_code_params_df = self.file_handler.get_building_code()
        return building_code_params_df


    def get_building_code_params(self, building_code_list: typing.List[str]=None):
        """
        Retrieve building_codeparameters for a list of building_code.

        This method fetches building_codeparameters for each building_codeID in the provided list,
        converts the relevant data to a dictionary, and maps these values to the 
        corresponding attributes of the TEKParameters dataclass. The resulting 
        dataclass instances are stored in a dictionary with building_code as keys.

        Parameters:
        - building_code_list (list of str): List of building_code.

        Returns:
        - building_code_params (dict): Dictionary where each key is a building_codeID and each value
                            is a TEKParameters dataclass instance containing the 
                            parameters for that building_codeID.
        """
        building_code_params = {}
        building_code_params_df = self.file_handler.get_building_code()
        if not building_code_list:
            return building_code_params_df
        for tek in building_code_list:
            # Filter on building_code
            building_code_params_filtered = building_code_params_df[building_code_params_df[self.COL_TEK] == tek]

            # Assuming there is only one row in the filtered DataFrame
            building_code_params_row = building_code_params_filtered.iloc[0]

            # Convert the single row to a dictionary
            building_code_params_dict = building_code_params_row.to_dict()

            # Map the dictionary values to the dataclass attributes
            building_code_params_per_id = TEKParameters(
                tek = building_code_params_dict[self.COL_TEK],
                building_year = building_code_params_dict[self.COL_TEK_BUILDING_YEAR],
                start_year = building_code_params_dict[self.COL_TEK_START_YEAR],
                end_year = building_code_params_dict[self.COL_TEK_END_YEAR],
                )

            building_code_params[tek] = building_code_params_per_id    

        return building_code_params

    def get_scurve_params(self):
        """
        Get input dataframe with S-curve parameters/assumptions.

        Returns:
        - scurve_params (pd.DataFrame): DataFrame with S-curve parameters.
        """
        scurve_params = self.file_handler.get_s_curve()
        return scurve_params

    def get_construction_population(self) -> pd.DataFrame:
        """
        Get construction population DataFrame.

        Returns:
        - construction_population (pd.DataFrame): Dataframe containing population numbers
          year population household_size
        """
        new_buildings_population = self.file_handler.get_construction_population()
        new_buildings_population["household_size"] = new_buildings_population['household_size'].astype('float64')
        new_buildings_population = new_buildings_population.set_index('year')
        return new_buildings_population

    def get_new_buildings_category_share(self) -> pd.DataFrame:
        """
        Get building category share by year as a DataFrame.

        The number can be used in conjunction with number of households to calculate total number
        of buildings of category house and apartment block

        Returns:
        - new_buildings_category_share (pd.DataFrame): Dataframe containing population numbers
          "year", "Andel nye småhus", "Andel nye leiligheter", "Areal nye småhus", "Areal nye leiligheter"
        """
        df = self.file_handler.get_construction_building_category_share()
        df['year'] = df['year'].astype(int)
        df = df.set_index('year')
        return df

    def get_building_category_floor_area(self, building_category: BuildingCategory) -> pd.Series:
        """
        Get population and household size DataFrame from a file.

        Returns:
        - construction_population (pd.DataFrame): Dataframe containing population numbers
          "area","type of building","2010","2011"
        """
        df = self.file_handler.get_building_category_area()

        building_category_floor_area = df[building_category].dropna()

        return building_category_floor_area

    #TODO: remove after refactoring
    def get_area_parameters(self) -> pd.DataFrame:
        """
        Get total area (m^2) per building category and TEK.

        Parameters:
        - building_category (str): Optional parameter that filter the returned dataframe by building_category

        Returns:
        - area_parameters (pd.DataFrame): Dataframe containing total area (m^2) per
                                          building category and TEK.
        """
        area_params = self.file_handler.get_area_parameters()
        return area_params
    
    def get_area_start_year(self) -> typing.Dict[BuildingCategory, pd.Series]:
        """
        Retrieve total floor area in the model start year for each TEK within a building category.

        Returns
        -------
        dict
            A dictionary where:
            - keys are `BuildingCategory` objects derived from the building category string.
            - values are `pandas.Series` with the 'tek' column as the index and the corresponding
              'area' column as the values.
        """
        area_data = self.file_handler.get_area_parameters()
        
        area_dict = {}
        for building_category in area_data[self.COL_BUILDING_CATEGORY].unique():
            area_building_category = area_data[area_data[self.COL_BUILDING_CATEGORY] == building_category]
            area_series = area_building_category.set_index(self.COL_TEK)[self.COL_AREA]
            area_series.index.name = "tek"
            area_series.rename(f"{BuildingCategory.from_string(building_category)}_area", inplace=True)
            
            area_dict[BuildingCategory.from_string(building_category)] = area_series

        return area_dict

    def get_behaviour_factor(self) -> pd.DataFrame:
        f = self.file_handler.get_file(self.file_handler.BEHAVIOUR_FACTOR)
        behaviour_factor = validators.energy_need_behaviour_factor.validate(f)
        return behaviour_factor


    def get_energy_req_original_condition(self) -> pd.DataFrame:
        """
        Get dataframe with energy requirement (kWh/m^2) for floor area in original condition. The result will be
            calibrated using the dataframe from DatabaseManger.get_calibrate_heating_rv

        Returns
        -------
        pd.DataFrame
            Dataframe containing energy requirement (kWh/m^2) for floor area in original condition,
            per building category and purpose.
        """
        logger.debug('Using default year 2020 -> 2050')
        building_purpose = self.make_building_purpose(years=YearRange(2020, 2050)).set_index(
            ['building_category', 'purpose', 'building_code', 'year'], drop=True
        )
        building_purpose = building_purpose.drop(columns=['building_condition'])
        ff = self.file_handler.get_energy_req_original_condition()[['building_category', 'building_code', 'purpose', 'kwh_m2']]
        df = self.explode_unique_columns(ff, ['building_category', 'building_code', 'purpose'])
        if len(df[df.building_code=='TEK21']) > 0:
            logger.warning('Detected TEK21 in {filename}', filename=self.file_handler.ENERGY_NEED_ORIGINAL_CONDITION)
        df = df.set_index(['building_category', 'purpose', 'building_code']).sort_index()

        df = building_purpose.join(df, how='left')

        behaviour_factor = self.get_behaviour_factor().set_index(['building_category', 'building_code', 'purpose', 'year'])

        df = df.join(behaviour_factor, how='left')

        heating_rv_factor = self.get_calibrate_heating_rv().set_index(['building_category', 'purpose']).heating_rv_factor

        df['heating_rv_factor'] = heating_rv_factor
        df['heating_rv_factor'] = df['heating_rv_factor'].astype(float).fillna(1.0)
        df['uncalibrated_kwh_m2'] = df['kwh_m2']
        df['calibrated_kwh_m2'] = df.heating_rv_factor * df.kwh_m2
        df.loc[df.calibrated_kwh_m2.isna(), 'calibrated_kwh_m2'] = df.loc[df.calibrated_kwh_m2.isna(), 'kwh_m2']
        df['kwh_m2'] = df['calibrated_kwh_m2']
        return df.reset_index()


    def get_energy_req_reduction_per_condition(self) -> pd.DataFrame:
        """
        Get dataframe with shares for reducing the energy requirement of the different building conditions. This
        function calls explode_unique_columns to expand building_category and TEK as necessary.

        Returns
        -------
        pd.DataFrame
            Dataframe containing energy requirement reduction shares for the different building conditions, 
            per building category, TEK and purpose.        
        """
        reduction_per_condition = self.file_handler.get_energy_req_reduction_per_condition()
        if len(reduction_per_condition[reduction_per_condition.building_code=='TEK21']) > 0:
            logger.warning('Detected TEK21 in {filename}', filename=self.file_handler.IMPROVEMENT_BUILDING_UPGRADE)

        return self.explode_unique_columns(reduction_per_condition,
                                           ['building_category', 'building_code', 'purpose', 'building_condition'])
    
    def get_energy_need_yearly_improvements(self) -> pd.DataFrame:
        """
        Get dataframe with yearly efficiency rates for energy need improvements. This
        function calls explode_unique_columns to expand building_category and TEK as necessary.

        The column yearly_efficiency_improvement is expected to contain the yearly reduction as
        a float between 0.1 and 1.0.

        Returns
        -------
        pd.DataFrame
            Dataframe containing yearly efficiency rates (%) for energy need improvements,
            per building category, tek and purpose.        
        """
        yearly_improvements = self.file_handler.get_energy_need_yearly_improvements()
        improvements = EnergyNeedYearlyImprovements.validate(yearly_improvements)
        eny = YearlyReduction.from_energy_need_yearly_improvements(improvements)
        return eny
    
    def get_energy_need_policy_improvement(self) -> pd.DataFrame:
        """
        Get dataframe with total energy need improvement in a period related to a policy. This
        function calls explode_unique_columns to expand building_category and TEK as necessary.

        Returns
        -------
        pd.DataFrame
            Dataframe containing total energy need improvement (%) in a policy period,
            per building category, tek and purpose.        
        """
        en_improvements = self.file_handler.get_energy_need_yearly_improvements()
        improvements = EnergyNeedYearlyImprovements.validate(en_improvements)
        enp = PolicyImprovement.from_energy_need_yearly_improvements(improvements)
        return enp

    def get_holiday_home_fuelwood_consumption(self) -> pd.Series:
        df = self.file_handler.get_holiday_home_energy_consumption().set_index('year')["fuelwood"]
        return df
    
    def get_holiday_home_fossilfuel_consumption(self) -> pd.Series:
        df = self.file_handler.get_holiday_home_energy_consumption().set_index('year')["fossilfuel"]
        return df

    def get_holiday_home_electricity_consumption(self) -> pd.Series:
        df = self.file_handler.get_holiday_home_energy_consumption().set_index('year')["electricity"]
        return df

    def get_holiday_home_by_year(self) -> pd.DataFrame:
        return self.file_handler.get_holiday_home_by_year().set_index('year')

    def get_calibrate_heating_rv(self) -> pd.Series:
        df = self.file_handler.get_calibrate_heating_rv()
        df = expand_building_categories(df, unique_columns=['building_category', 'purpose'])
        return df[['building_category', 'purpose', 'heating_rv_factor']]

    def get_calibrate_heating_systems(self) -> pd.DataFrame:
        df = self.file_handler.get_calibrate_heating_systems()
        df = expand_building_categories(df, unique_columns=['building_category', 'to', 'from'])
        return df

    def get_area_per_person(self,
                            building_category: BuildingCategory = None) -> pd.Series:
        """
        Return area_per_person as a pd.Series

        Parameters
        ----------
        building_category: BuildingCategory, optional
            filter for building category
        Returns
        -------
        pd.Series
            float values indexed by building_category, (year)
        """
        df = self.file_handler.get_area_per_person()
        df = df.set_index('building_category')

        if building_category:
            return df.area_per_person.loc[building_category]
        return df.area_per_person

    def validate_database(self):
        missing_files = self.file_handler.check_for_missing_files()
        return True

    def get_heating_systems_shares_start_year(self):
        df = self.file_handler.get_heating_systems_shares_start_year()
        heating_systems_factor = self.get_calibrate_heating_systems()
        calibrated = calibrate_heating_systems(df, heating_systems_factor)

        return calibrated

    def get_heating_system_efficiencies(self):
        return self.file_handler.get_heating_system_efficiencies()

    def get_heating_system_forecast(self):
        return self.file_handler.get_heating_system_forecast()

    def explode_unique_columns(self, df, unique_columns):
        return explode_unique_columns(df, unique_columns, default_building_code=self.get_building_code_list())

    def explode_building_category_column(self, df, unique_columns):
        return explode_building_category_column(df, unique_columns)

    def explode_building_code_column(self, ff, unique_columns):
        return explode_building_code_column(ff, unique_columns, default_building_code=self.get_building_code_list())


if __name__ == '__main__':
    db = DatabaseManager()
    building_category = BuildingCategory.HOUSE

    a = db.get_energy_need_policy_improvement()
    print(a)
