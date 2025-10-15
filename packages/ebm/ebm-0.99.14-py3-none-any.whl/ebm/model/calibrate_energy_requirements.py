import pathlib
import typing

from loguru import logger
import pandas as pd

from ebm.model.file_handler import FileHandler


class EnergyRequirementCalibrationWriter:

    def __init__(self):
        pass

    def load(self, df: pd.DataFrame, to_file: typing.Union[str, pathlib.Path] = None):
        logger.debug(f'Save {to_file}')
        if to_file is None:
            to_file = pathlib.Path('input') / FileHandler.CALIBRATE_ENERGY_REQUIREMENT
        file_path: pathlib.Path = to_file if isinstance(to_file, pathlib.Path) else pathlib.Path(to_file)
        df = df[df['group'].isin(['energy_requirements', 'energy_requirement'])]
        df = df.rename(columns={'variable': 'purpose'})
        df = df[['building_category', 'purpose', 'heating_rv_factor']].reset_index(drop=True)
        if file_path.suffix == '.csv':
            df.to_csv(file_path, index=False)
        elif file_path.suffix == '.xlsx':
            df.to_excel(file_path, index=False)
        logger.info(f'Wrote {to_file}')


class EnergyConsumptionCalibrationWriter:
    df: pd.DataFrame

    def __init__(self):
        pass

    def transform(self, df):
        df = df[df['group'] == 'energy_consumption']
        df = df[['building_category', 'variable', 'extra', 'heating_rv_factor']].reset_index(drop=True)
        df = df.rename(columns={'variable': 'to',
                                'extra': 'from',
                                'heating_rv_factor': 'factor'}, errors='ignore')

        self.df = df
        return df

    def load(self, df: pd.DataFrame, to_file: typing.Union[str, pathlib.Path] = None):
        logger.debug(f'Save {to_file}')
        if to_file is None:
            to_file = pathlib.Path('input/calibrate_energy_consumption.xlsx')
        file_path: pathlib.Path = to_file if isinstance(to_file, pathlib.Path) else pathlib.Path(to_file)

        if file_path.suffix == '.csv':
            df.to_csv(file_path, index=False)
        elif file_path.suffix == '.xlsx':
            df.to_excel(file_path, index=False)
        logger.info(f'Wrote {to_file}')


def transform(heating_rv: pd.Series, heating_rv_factor=None) -> pd.Series:
    if heating_rv_factor is None:
        return heating_rv
    calibrated = heating_rv * heating_rv_factor
    calibrated.name = heating_rv.name
    return calibrated


class EbmCalibration:
    energy_requirement_original_condition: pd.Series
    pass


class CalibrationReader:
    def extract(self) -> pd.Series:
        pass

    def transform(self) -> pd.Series:
        pass

    def load(self) -> None:
        pass


class CalibrationWriter:
    pass
