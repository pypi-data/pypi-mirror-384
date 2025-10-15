import os
import pathlib
import shutil
import typing

import pandas as pd
from loguru import logger
from pandera.errors import SchemaErrors, SchemaError

import ebm.validators as validators
from ebm.model.defaults import default_calibrate_heating_rv, default_calibrate_energy_consumption


class FileHandler:
    """
    Handles file operations.
    """

    # Filenames
    BUILDING_CONDITIONS = 'building_conditions.csv'
    BUILDING_CODE_PARAMS = 'building_code_parameters.csv'
    S_CURVE = 's_curve.csv'
    POPULATION_FORECAST = 'population_forecast.csv'
    NEW_BUILDINGS_RESIDENTIAL = 'new_buildings_residential.csv'
    AREA_NEW_RESIDENTIAL_BUILDINGS = 'area_new_residential_buildings.csv'
    AREA = 'area.csv'
    BEHAVIOUR_FACTOR = 'energy_need_behaviour_factor.csv'
    ENERGY_NEED_ORIGINAL_CONDITION = 'energy_need_original_condition.csv'
    IMPROVEMENT_BUILDING_UPGRADE = 'improvement_building_upgrade.csv'
    ENERGY_NEED_YEARLY_IMPROVEMENTS = 'energy_need_improvements.csv'
    HOLIDAY_HOME_STOCK = 'holiday_home_stock.csv'
    HOLIDAY_HOME_ENERGY_CONSUMPTION = 'holiday_home_energy_consumption.csv'
    AREA_PER_PERSON = 'area_per_person.csv'
    HEATING_SYSTEM_INITIAL_SHARES = 'heating_system_initial_shares.csv'
    HEATING_SYSTEM_EFFICIENCIES = 'heating_system_efficiencies.csv'
    HEATING_SYSTEM_FORECAST = 'heating_system_forecast.csv'
    CALIBRATE_ENERGY_REQUIREMENT = 'calibrate_heating_rv.xlsx'
    CALIBRATE_ENERGY_CONSUMPTION = 'calibrate_energy_consumption.xlsx'

    input_directory: pathlib.Path

    def __init__(self, directory: typing.Union[str, pathlib.Path, None] = None):
        """
        Constructor for FileHandler Object. Sets FileHandler.input_directory.

        Parameters
        ----------
        directory : pathlib.Path | None | (str)
            When directory is None the constructor will attempt to read directory location from
                environment variable EBM_INPUT_DIRECTORY
        """
        if directory is None:
            # Use 'input' as fall back when EBM_INPUT_DIRECTORY is not set in environment.
            directory = os.environ.get('EBM_INPUT_DIRECTORY', 'input')

        self.input_directory = directory if isinstance(directory, pathlib.Path) else pathlib.Path(directory)
        self.files_to_check = [self.BUILDING_CODE_PARAMS, self.S_CURVE, self.POPULATION_FORECAST,
                               self.NEW_BUILDINGS_RESIDENTIAL, self.AREA_NEW_RESIDENTIAL_BUILDINGS,
                               self.AREA, self.BEHAVIOUR_FACTOR, self.ENERGY_NEED_ORIGINAL_CONDITION,
                               self.IMPROVEMENT_BUILDING_UPGRADE, self.ENERGY_NEED_YEARLY_IMPROVEMENTS,
                               self.HOLIDAY_HOME_ENERGY_CONSUMPTION, self.HOLIDAY_HOME_STOCK,
                               self.AREA_PER_PERSON, self.HEATING_SYSTEM_INITIAL_SHARES, self.HEATING_SYSTEM_EFFICIENCIES, self.HEATING_SYSTEM_FORECAST]

    def __repr__(self):
        return f'FileHandler(input_directory="{self.input_directory}")'

    def __str__(self):
        return repr(self)

    @staticmethod
    def default_data_directory() -> pathlib.Path:
        """
        Returns the path for ebm default data. The function is used when content is needed for a new input directory

        Not to be confused with FileHandler.input_directory.

        Returns
        -------
        pathlib.Path

        See Also
        --------
        create_missing_input_files
        """
        data_directory = pathlib.Path(__file__).parent.parent / 'data'
        default_data_directory =  data_directory / 'calibrated'
        if not default_data_directory.is_dir():
            msg = f'Could not find default data directory {default_data_directory}'
            raise FileNotFoundError(msg)
        if not default_data_directory.is_dir():
            msg = f'{default_data_directory} is not a directory'
            raise NotADirectoryError(msg)
        return default_data_directory

    def get_file(self, file_name: str) -> pd.DataFrame:
        """
        Finds and returns a file by searching in the folder defined by self.input_folder

        Parameters:
        - file_name (str): Name of the file to retrieve.

        Returns:
        - file_df (pd.DataFrame): DataFrame containing file data.
        """
        logger.debug(f'get_file {file_name}')
        file_path: pathlib.Path = pathlib.Path(self.input_directory) / file_name
        logger.debug(f'{file_path=}')

        try:
            if file_path.suffix == '.xlsx':
                file_df = pd.read_excel(file_path)
            elif file_path.suffix == '.csv':
                file_df = pd.read_csv(file_path)
            else:
                msg = f'{file_name} is not of type xlsx or csv'
                logger.error(msg)
                raise ValueError(msg)
            return file_df
        except FileNotFoundError as ex:
            logger.exception(ex)
            logger.debug(f'Current directory is {os.getcwd()}')
            logger.error(f'Unable to open {file_path}. File not found.')
            raise
        except PermissionError as ex:
            logger.exception(ex)
            logger.error(f'Unable to open {file_path}. Permission denied.')
            raise
        except IOError as ex:
            logger.exception(ex)
            logger.error(f'Unable to open {file_path}. Unable to read file.')
            raise

    def get_building_code(self) -> pd.DataFrame:
        """
        Get TEK parameters DataFrame.

        Returns:
        - building_code_params (pd.DataFrame): DataFrame containing TEK parameters.
        """
        building_code_params = self.get_file(self.BUILDING_CODE_PARAMS)
        return building_code_params
    
    def get_s_curve(self) -> pd.DataFrame:
        """
        Get S-curve parameters DataFrame.

        Returns:
        - scurve_params (pd.DataFrame): DataFrame containing S-curve parameters.
        """
        scurve_params = self.get_file(self.S_CURVE)
        return scurve_params

    def get_construction_population(self) -> pd.DataFrame:
        """
        Get population and household size DataFrame from a file.

        Returns:
        - construction_population (pd.DataFrame): Dataframe containing population numbers
          year population household_size
        """
        return self.get_file(self.POPULATION_FORECAST)

    def get_population(self) -> pd.DataFrame:
        """
        Loads population data from population.csv as float64

        Should probably be merged with get_construction_population

        Returns population : pd.DataFrame
            dataframe with population
        -------

        """
        file_path = self.input_directory / self.POPULATION_FORECAST
        logger.debug(f'{file_path=}')
        return pd.read_csv(file_path, dtype={"household_size": "float64"})

    def get_construction_building_category_share(self) -> pd.DataFrame:
        """
        Get building category share by year DataFrame from a file.

        The number can be used in conjunction with number of households to calculate total number
        of buildings of category house and apartment block

        Returns:
        - construction_population (pd.DataFrame): Dataframe containing population numbers
          "year", "Andel nye småhus", "Andel nye leiligheter", "Areal nye småhus", "Areal nye leiligheter"
        """
        return self.get_file(self.NEW_BUILDINGS_RESIDENTIAL)

    def get_building_category_area(self) -> pd.DataFrame:
        """
        Get population and household size DataFrame from a file.

        Returns:
        - construction_population (pd.DataFrame): Dataframe containing population numbers
          "area","type of building","2010","2011"
        """
        file_path = self.input_directory / self.AREA_NEW_RESIDENTIAL_BUILDINGS
        logger.debug(f'{file_path=}')
        return pd.read_csv(file_path,
                           index_col=0, header=0)

    def get_area_parameters(self) -> pd.DataFrame:
        """
        Get dataframe with area parameters.

        Returns:
        - area_parameters (pd.DataFrame): Dataframe containing total area (m^2) per
                                          building category and TEK.
        """
        return self.get_file(self.AREA)
    
    def get_energy_req_original_condition(self) -> pd.DataFrame:
        """
        Get dataframe with energy requirement (kWh/m^2) for floor area in original condition.

        Returns
        -------
        pd.DataFrame
            Dataframe containing energy requirement (kWh/m^2) for floor area in original condition,
            per building category and purpose.
        """
        return self.get_file(self.ENERGY_NEED_ORIGINAL_CONDITION)
    
    def get_energy_req_reduction_per_condition(self) -> pd.DataFrame:
        """
        Get dataframe with shares for reducing the energy requirement of the different building conditions.

        Returns
        -------
        pd.DataFrame
            Dataframe containing energy requirement reduction shares for the different building conditions, 
            per building category, TEK and purpose.
        """
        return self.get_file(self.IMPROVEMENT_BUILDING_UPGRADE)
    
    def get_energy_need_yearly_improvements(self) -> pd.DataFrame:
        """
        Get dataframe with yearly efficiency rates for energy requirement improvements.

        Returns
        -------
        pd.DataFrame
            Dataframe containing yearly efficiency rates (%) for energy requirement improvements,
            per building category, tek and purpose.
        """
        return self.get_file(self.ENERGY_NEED_YEARLY_IMPROVEMENTS)

    def get_holiday_home_energy_consumption(self) -> pd.DataFrame:
        return self.get_file(self.HOLIDAY_HOME_ENERGY_CONSUMPTION)

    def get_holiday_home_by_year(self) -> pd.DataFrame:
        return self.get_file(self.HOLIDAY_HOME_STOCK)

    def get_area_per_person(self):
        return self.get_file(self.AREA_PER_PERSON)

    def get_calibrate_heating_rv(self) -> pd.DataFrame:
        """
        Retrieve the calibrated heating requirement values

        This method attempts to load the energy requirement calibration file from the
        input directory. It first checks for a file without extension, then for a `.csv`
        version. If neither is found, it returns a default DataFrame.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the calibrated heating requirement values. If no file
            is found, a default DataFrame is returned.

        """

        calibrate_heating_rv = self.input_directory / self.CALIBRATE_ENERGY_REQUIREMENT
        if calibrate_heating_rv.is_file():
            return self.get_file(calibrate_heating_rv.name)
        if calibrate_heating_rv.with_suffix('.csv').is_file():
            return self.get_file(calibrate_heating_rv.with_suffix('.csv').name)
        return default_calibrate_heating_rv()

    def get_calibrate_heating_systems(self) -> pd.DataFrame:
        """
        Retrieve the calibrated energy consumption values for heating systems

        This method attempts to load the energy consumption calibration file from the
        input directory. It first checks for a file without extension, then for a `.csv`
        version. If neither is found, it returns a default DataFrame.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the calibrated energy consumption values. If no file
            is found, a default DataFrame is returned.

        """

        calibrate_energy_consumption = self.input_directory / self.CALIBRATE_ENERGY_CONSUMPTION
        if calibrate_energy_consumption.is_file():
            return self.get_file(calibrate_energy_consumption.name)
        if calibrate_energy_consumption.with_suffix('.csv').is_file():
            return self.get_file(calibrate_energy_consumption.with_suffix('.csv').name)
        return default_calibrate_energy_consumption()

    def get_heating_systems_shares_start_year(self) -> pd.DataFrame:
        """
        """
        return self.get_file(self.HEATING_SYSTEM_INITIAL_SHARES)
    
    def get_heating_system_efficiencies(self) -> pd.DataFrame:
        """Load heating_system_efficiencies.csv from file into a dataframe
        
        Returns
        -------
        heating_system_efficiencies : pd.DataFrame
            pandas DataFrame with heating system efficiencies
        """

        return self.get_file(self.HEATING_SYSTEM_EFFICIENCIES)

    def get_heating_system_forecast(self) -> pd.DataFrame:
        """
        """
        return self.get_file(self.HEATING_SYSTEM_FORECAST)

    def _check_is_file(self, filename: str) -> bool:
        """
        Check if the filename is a file in self.input_folder

        Parameters
        ----------
        filename : str

        Returns
        -------
        file_exists : bool
        """
        return (pathlib.Path(self.input_directory) / filename).is_file()

    def check_for_missing_files(self) -> typing.List[str]:
        """
        Returns a list of required files that are not present in self.input_folder

        Returns
        -------
        missing_files : List[str]

        Raises
        ------
        FileNotFoundError
            If FileHandler::input_directory not found
        NotADirectoryError
            If FileHandler::input_directory is not a directory
        """
        if not self.input_directory.exists():
            msg=f'{self.input_directory.absolute()} not found'
            logger.error(msg)
            raise FileNotFoundError(f'Input Directory Not Found')
        if not self.input_directory.is_dir():
            raise NotADirectoryError(f'{self.input_directory} is not a directory')

        missing_files = [file for file in self.files_to_check if not self._check_is_file(file)]
        if missing_files:
            plural = 's' if len(missing_files) != 1 else ''
            msg = f'{len(missing_files)} required file{plural} missing from {self.input_directory}'
            logger.error(msg)
            for f in missing_files:
                logger.error(f'Could not find {f}')
        return missing_files


    def create_missing_input_files(self, source_directory: (pathlib.Path | None)=None) -> None:
        """
        Creates any input files missing in self.input_directory. When source is omitted FileHandler

        Parameters
        ----------
        source_directory : pathlib.Path, optional
                           Optional directory for sourcing files to copy.

        Returns
        -------
        None

        See Also
        --------
        default_data_directory : default source for data files
        """
        source = FileHandler.default_data_directory() if not source_directory else source_directory

        if not source.is_dir():
            raise NotADirectoryError(f'{self.input_directory} is not a directory')
        if not self.input_directory.is_dir():
            logger.info(f'Creating directory {self.input_directory}')
            self.input_directory.mkdir()
        for file in self.files_to_check:
            logger.debug(f'Create input file {file}')
            self.create_input_file(file, source_directory=source)

    def create_input_file(self, file, source_directory=None):
        source_directory = FileHandler.default_data_directory() if not source_directory else source_directory

        source_file = source_directory / file
        target_file = self.input_directory / file
        if target_file.is_file():
            logger.debug(f'Skipping existing file {target_file}')
        elif not source_file.is_file():
            logger.error(f'Source file {source_file} does not exist!')
        else:
            shutil.copy(source_file, target_file)
            logger.info( f'Creating missing file  {target_file}')

    def validate_input_files(self):
        """
        Validates the input files for correct formatting and content using the validators module

        Raises
        ------
        pa.errors.SchemaErrors
            If any invalid data for formatting is found when validating files. The validation is lazy, meaning
            multiple errors may be listed in the exception.
        """
        for file_to_validate in self.files_to_check:
            df = self.get_file(file_to_validate)
            validator = getattr(validators, file_to_validate[:-4].lower())

            try:
                validator.validate(df, lazy=True)
            except (SchemaErrors, SchemaError):
                logger.error(f'Got error while validating {file_to_validate}')
                raise

    def is_calibrated(self) -> bool:
        """
        Check if calibration files exist in the input directory.

        This method verifies the presence of both energy consumption and energy
        requirement files in either `.xlsx` or `.csv` format within the specified
        input directory.

        Returns
        -------
        bool
            `True` if both required files exist with the same extension (`.xlsx` or `.csv`),
            otherwise `False`.
        """

        energy_consumption = (self.input_directory / self.CALIBRATE_ENERGY_CONSUMPTION)
        energy_requirement = (self.input_directory / self.CALIBRATE_ENERGY_REQUIREMENT)

        if energy_consumption.with_suffix('.xlsx').is_file() and energy_requirement.with_suffix('.xlsx').is_file():
            return True
        if energy_consumption.with_suffix('.csv').is_file() and energy_requirement.with_suffix('.csv').is_file():
            return True
        return False

