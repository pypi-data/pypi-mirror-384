from typing import cast, Optional

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame, Series
from pandera.typing.common import DataFrameBase

from ebm.model.column_operations import explode_unique_columns, explode_column_alias
from ebm.model.energy_purpose import EnergyPurpose


class EnergyNeedYearlyImprovements(pa.DataFrameModel):
    building_category: Series[str]
    building_code: Series[str]
    purpose: Series[str]
    value: Series[float] = pa.Field(ge=0.0, coerce=True)
    start_year: Optional[Series[int]] = pa.Field(coerce=True, default=2020)
    function: Series[str]
    end_year: Optional[Series[int]] = pa.Field(coerce=True, default=2050)
    _filename = 'energy_need_improvements'

    class Config:
        unique = ['building_category', 'building_code', 'purpose', 'start_year', 'function', 'end_year']


class YearlyReduction(pa.DataFrameModel):
    building_category: Series[str]
    building_code: Series[str]
    purpose: Series[str]
    start_year: Series[int] = pa.Field(coerce=True, default=2020)
    end_year: Series[int] = pa.Field(coerce=True, default=2050)
    yearly_efficiency_improvement: Series[float] = pa.Field(ge=0.0, coerce=True)

    class Config:
        unique = ['building_category', 'building_code', 'purpose', 'start_year', 'function', 'end_year']


    @staticmethod
    def from_energy_need_yearly_improvements(
            en_yearly_improvement: DataFrameBase[EnergyNeedYearlyImprovements]|EnergyNeedYearlyImprovements) -> 'DataFrameBase[YearlyReduction]':
        """
        Transforms a EnergyNeedYearlyImprovement DataFrame into a EnergyNeedYearlyReduction DataFrame.

        Parameters
        ----------
        en_yearly_improvement : DataFrame[EnergyNeedYearlyImprovements]

        Returns
        -------
        DataFrameBase[YearlyReduction]

        Raises
        ------
        pa.errors.SchemaError
            When the resulting dataframe fails to validate
        pa.errors.SchemaErrors
            When the resulting dataframe fails to validate

        """
        unique_columns = ['building_category', 'building_code', 'purpose', 'start_year', 'end_year']

        # Casting en_yearly_improvement to DataFrame so that type checkers complaining about datatype
        df = cast(pd.DataFrame, en_yearly_improvement)
        if 'start_year' not in df.columns:
            df['start_year'] = 2020
        if 'end_year' not in df.columns:
            df['end_year'] = 2050
        df = df.query('function=="yearly_reduction"')
        df = explode_unique_columns(df,
                                                       unique_columns=unique_columns)

        df = explode_column_alias(df,
                                                     column='purpose',
                                                     values=[p for p in EnergyPurpose],
                                                     alias='default',
                                                     de_dup_by=unique_columns)
        df['yearly_efficiency_improvement'] = df['value']
        df = df[['building_category', 'building_code', 'purpose', 'start_year', 'end_year', 'yearly_efficiency_improvement']]
        df = df.reset_index()
        return YearlyReduction.validate(df, lazy=True)


class PolicyImprovement(pa.DataFrameModel):
    building_category: Series[str]
    building_code: Series[str]
    purpose: Series[str]
    start_year: Series[int] = pa.Field(ge=0, coerce=True)
    end_year: Series[int] = pa.Field(ge=0, coerce=True)
    improvement_at_end_year: Series[float] = pa.Field(ge=0.0, lt=2.0, coerce=True)

    class Config:
        unique = ['building_category', 'building_code', 'purpose', 'start_year', 'end_year']

    @pa.dataframe_check
    def start_year_before_end_year(cls, df: pd.DataFrame) -> Series[bool]:
        return df.start_year < df.end_year

    @staticmethod
    def from_energy_need_yearly_improvements(
            energy_need_improvements: DataFrameBase[EnergyNeedYearlyImprovements] | EnergyNeedYearlyImprovements) -> 'DataFrameBase[PolicyImprovement]':

        energy_need_improvements = cast(pd.DataFrame, energy_need_improvements)
        df = energy_need_improvements.query('function=="improvement_at_end_year"')
        if 'start_year' not in df.columns:
            df['start_year'] = 2020
        if 'end_year' not in df.columns:
            df['end_year'] = 2050
        unique_columns = ('building_category', 'building_code', 'purpose', 'start_year', 'function', 'end_year',)
        df = explode_unique_columns(df, unique_columns=unique_columns)
        df = explode_column_alias(df, column='purpose', values=[p for p in EnergyPurpose], alias='default',
                                  de_dup_by=unique_columns)

        df['improvement_at_end_year'] = df['value']

        return PolicyImprovement.validate(df)
