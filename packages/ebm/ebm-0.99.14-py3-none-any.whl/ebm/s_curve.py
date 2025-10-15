import numpy as np
import pandas as pd
from pandas import Series

from ebm.model.area import building_condition_accumulated_scurves, building_condition_scurves
from ebm.model.data_classes import YearRange


def original_condition(s_curve_cumulative_demolition, s_curve_renovation,
                       s_curve_renovation_and_small_measure, s_curve_small_measure):
    """
    Calculates buildings remaining as original condition by subtracting every other condition

    Parameters
    ----------
    s_curve_cumulative_demolition : pandas.Series
    s_curve_renovation : pandas.Series
    s_curve_renovation_and_small_measure : pandas.Series
    s_curve_small_measure : pandas.Series

    Returns
    -------
    pandas.Series
        buildings remaining as original condition
    """
    return (1.0 -
            s_curve_cumulative_demolition -
            s_curve_renovation -
            s_curve_renovation_and_small_measure -
            s_curve_small_measure).rename('s_curve_original_condition')


def small_measure(s_curve_renovation_and_small_measure: Series, s_curve_small_measure_total: Series) -> Series:
    """
    Calculates the remaining small measure share by subtracting renovation and small measure values from
    the total small measure curve.

    Parameters
    ----------
    s_curve_renovation_and_small_measure : Series
    s_curve_small_measure_total : Series

    Returns
    -------
    Series
        s_curve_small_measure

    Notes
    -----
    - This function currently does not implement logic to zero out values before the building year.
    - Assumes both input Series are aligned on the index year.
    """

    # ### SharesPerCondition calc_small_measure
    #  - ❌   sett til 0 før byggeår
    # ```python
    #     construction_year = self.building_code_params[tek].building_year
    #     shares.loc[self.period_index <= construction_year] = 0
    # ```

    return (s_curve_small_measure_total - s_curve_renovation_and_small_measure).rename('small_measure')


def renovation_and_small_measure(s_curve_renovation: Series, s_curve_renovation_total: Series) -> Series:
    """
    Calculates the remaining renovation_and_small_measure share by subtracting renovation
    from the total renovation total curve.

    Parameters
    ----------
    s_curve_renovation : pandas.Series
        A time series representing the S-curve of exclusive renovation condition.

    s_curve_renovation_total : pandas.Series
        A time series representing the total S-curve for the total renovation condition.

    Returns
    -------
    pandas.Series
        A time series representing the difference between the total and renovation-only S-curves.
        Values before the building year should be set to 0 (not yet implemented).

    Notes
    -----
    - This function currently does not implement logic to zero out values before the building year.
    - Assumes both input Series are aligned on index year.
    """
    # ### SharesPerCondition calc_renovation_and_small_measure
    #  - ❌ Sett til 0 før byggeår

    return s_curve_renovation_total - s_curve_renovation


def trim_renovation_from_renovation_total(s_curve_renovation: Series,
                                          s_curve_renovation_max: Series,
                                          s_curve_renovation_total: Series,
                                          scurve_total: Series) -> Series:
    """
    Adjust the renovation S-curve by incorporating values from the total renovation curve
    where the total share is less than the maximum renovation share.

    This function identifies time points where the total S-curve (`scurve_total`) is less than
    the maximum renovation S-curve (`s_curve_renovation_max`). For those points, it replaces
    the corresponding values in `s_curve_renovation` with values from `s_curve_renovation_total`.

    Parameters
    ----------
    s_curve_renovation : pandas.Series
        The original renovation S-curve to be adjusted.

    s_curve_renovation_max : pandas.Series
        The maximum allowed values for the renovation S-curve.

    s_curve_renovation_total : pandas.Series
        The total renovation S-curve including all measures.

    scurve_total : pandas.Series
        The actual total S-curve values to compare against the max renovation curve.

    Returns
    -------
    pandas.Series
        The adjusted renovation S-curve with values merged from the total renovation curve
        where the total share is less than the maximum renovation share.

    Notes
    -----
    - Assumes all input Series are aligned on the index year.
    """

    adjusted_values = np.where(scurve_total < s_curve_renovation_max,
                               s_curve_renovation_total,
                               s_curve_renovation)
    trimmed_renovation = pd.Series(adjusted_values, index=s_curve_renovation.index).rename('renovation')
    return trimmed_renovation


def renovation_from_small_measure(s_curve_renovation_max: Series, s_curve_small_measure_total: Series) -> Series:
    """
    Calculate the renovation S-curve by subtracting small measures from the max renovation curve.

    Parameters
    ----------
    s_curve_renovation_max : pandas.Series
        The maximum yearly values for the renovation S-curve.

    s_curve_small_measure_total : pandas.Series
        The yearly total S-curve for small measures.

    Returns
    -------
    pandas.Series
        The resulting renovation S-curve with values clipped at 0
    """
    # ## small_measure and renovation to scurve_small_measure_total, RN
    # ## SharesPerCondition calc_renovation
    #
    #  - ❌ Ser ut som det er edge case for byggeår.
    #  - ❌ Årene før byggeår må settes til 0 for scurve_renovation?
    s_curve_renovation = (s_curve_renovation_max - s_curve_small_measure_total).clip(lower=0.0)
    return s_curve_renovation.rename('s_curve_renovation')


def total(s_curve_renovation_total: Series, s_curve_small_measure_total: Series) -> Series:
    """
    Calculates the yearly sum of renovation and small_measure

    Parameters
    ----------
    s_curve_renovation_total : pandas.Series
    s_curve_small_measure_total : pandas.Series

    Returns
    -------
    pandas.Series
        yearly sum of renovation and small_measure
    """

    return (s_curve_small_measure_total + s_curve_renovation_total).clip(lower=0.0).rename('s_curve_total')


def trim_max_value(s_curve_cumulative_small_measure: Series, s_curve_small_measure_max: Series) ->Series:
    s_curve_cumulative_small_measure_max = s_curve_cumulative_small_measure.combine(s_curve_small_measure_max, min)
    return s_curve_cumulative_small_measure_max.clip(0) # type: ignore


def small_measure_max(s_curve_cumulative_demolition: Series, s_curve_small_measure_never_share: Series):
    """
    Calculates the maximum possible value for small_measure condition

    Parameters
    ----------
    s_curve_cumulative_demolition : pandas.Series
    s_curve_small_measure_never_share : pandas.Series

    Returns
    -------
    pandas.Series
        Yearly maximum possible value for small_measure
    """
    return 1.0 - s_curve_cumulative_demolition - s_curve_small_measure_never_share


def renovation_max(s_curve_cumulative_demolition: Series, s_curve_renovation_never_share: Series):
    """
    Calculates the maximum possible value for renovation condition

    Parameters
    ----------
    s_curve_cumulative_demolition : pandas.Series
    s_curve_renovation_never_share : pandas.Series

    Returns
    -------
    pandas.Series
        Yearly maximum possible value for renovation
    """
    return 1.0 - s_curve_cumulative_demolition - s_curve_renovation_never_share


def cumulative_renovation(s_curves_with_building_code: Series, years: YearRange) -> Series:
    """
    Return the  yearly cumulative sum of renovation condition.


    Parameters
    ----------
    s_curves_with_building_code : pandas.Series
    years : pandas.Series

    Returns
    -------
    pandas.Series
        cumulative sum of renovation

    Notes
    -----
    NaN values are replaced by float 0.0
    """
    return s_curves_with_building_code.renovation_acc.loc[(slice(None), slice(None), list(years.year_range))].fillna(0.0)


def cumulative_small_measure(s_curves_with_building_code: Series, years: YearRange) -> Series:
    """
    Return the  yearly cumulative sum of small_measure condition.


    Parameters
    ----------
    s_curves_with_building_code : pandas.Series
    years : YearRange

    Returns
    -------
    pandas.Series
        cumulative sum of small_measure

    Notes
    -----
    NaN values are replaced by float 0.0
    """
    s_curve_cumulative_small_measure = s_curves_with_building_code.small_measure_acc.loc[(slice(None), slice(None), list(years.year_range))].fillna(0.0)
    return s_curve_cumulative_small_measure


def transform_demolition(demolition: Series, years: YearRange) -> Series:
    """
    Filter yearly demolition for years
    Parameters
    ----------
    demolition : pandas.Series
    years : YearRange

    Returns
    -------
    demolition for years

    """
    return demolition.demolition.loc[(slice(None), slice(None), list(years.year_range))].fillna(0.0)


def transform_to_cumulative_demolition(cumulative_demolition: pd.DataFrame, years:YearRange) -> Series:
    """
    Filter yearly cumulative demolition for years
    Parameters
    ----------
    cumulative_demolition : pandas.DataFrame
    years : YearRange

    Returns
    -------
    pandas.Series
        cumulative demolition for years

    """
    s_curve_cumulative_demolition = cumulative_demolition.demolition_acc.loc[
        (slice(None), slice(None), list(years.year_range))].fillna(0.0)
    return s_curve_cumulative_demolition


def scurve_parameters_to_never_share(s_curves: pd.DataFrame, scurve_parameters: pd.DataFrame) -> pd.DataFrame:
    """
    Transform scurve_parameters with s_curve to never_share.
    Parameters
    ----------
    s_curves : pandas.DataFrame
    scurve_parameters : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame

    Notes
    -----
    Age is padded from -max age to 0

    """
    max_age = s_curves.index.get_level_values(level='age').max()
    df_never_share = pd.DataFrame(
        # noinspection PyTypeChecker
        [(row.building_category, idx, row.condition + '_never_share', row.never_share) for idx in range(-max_age, max_age + 1)
         for row in
         scurve_parameters.itertuples()],
        columns=['building_category', 'age', 'building_condition', 'scurve']).sort_values(
        ['building_category', 'building_condition', 'age']).set_index(
        ['building_category', 'age', 'building_condition'])
    return df_never_share


def scurve_parameters_to_scurve(scurve_parameters: pd.DataFrame) -> Series:
    """
    Create scurve new dataframe from scurve_parameters using ebm.model.area.building_condition_scurves and
        ebm.model.area.building_condition_accumulated_scurves

    Each row represent a building_category and building_condition at a certain age.

    Parameters
    ----------
    scurve_parameters : pandas.DataFrame

    Returns
    -------
    pandas.Series
    """
    scurve_by_year = building_condition_scurves(scurve_parameters)
    scurve_accumulated = building_condition_accumulated_scurves(scurve_parameters)
    s_curves = pd.concat([scurve_by_year, scurve_accumulated])

    return s_curves


def accumulate_demolition(s_curves_long: pd.DataFrame, years: YearRange) -> pd.DataFrame:
    """
    Sets demolition in year 0 (2020) to 0.0 and sums up the yearly demolition using years

    Parameters
    ----------
    s_curves_long : pandas.DataFrame
    years : YearRange

    Returns
    -------
    pandas.DataFrame
    """
    demolition_acc = s_curves_long
    demolition_acc.loc[demolition_acc.query(f'year<={years.start}').index, 'demolition'] = 0.0
    demolition_acc['demolition_acc'] = demolition_acc.groupby(by=['building_category', 'building_code'])[['demolition']].cumsum()[
        ['demolition']]

    return demolition_acc

# noinspection PyTypeChecker
def merge_s_curves_and_building_code(s_curves: pd.DataFrame, df_never_share: pd.DataFrame, building_code_parameters: pd.DataFrame) -> pd.DataFrame:
    """
    Cross merge s_curves and df_never_share with all building_code in building_code_parameters

    Parameters
    ----------
    s_curves : pandas.DataFrame
    df_never_share : pandas.DataFrame
    building_code_parameters : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """
    s_curves = pd.concat([s_curves, df_never_share])

    s_curves_by_building_code = s_curves.reset_index().join(building_code_parameters, how='cross')
    s_curves_by_building_code['year'] = s_curves_by_building_code['building_year'] + s_curves_by_building_code['age']
    s_curves_long = s_curves_by_building_code.pivot(index=['building_category', 'building_code', 'year'],
                                          columns=['building_condition'],
                                          values='scurve').reset_index()
    s_curves_long = (s_curves_long
        .reset_index(drop=True)
        .set_index(['building_category', 'building_code', 'year'], drop=True)
        .rename_axis(None, axis=1))
    return s_curves_long


def transform_to_dataframe(s_curve_cumulative_demolition: Series, s_curve_original_condition: Series, s_curve_renovation: Series,
                           s_curve_renovation_and_small_measure: Series, s_curve_small_measure: Series, s_curve_demolition: Series) -> pd.DataFrame:
    """
    Creates a pandas DataFrame from the parameters

    Parameters
    ----------
    s_curve_cumulative_demolition : pandas.Series
    s_curve_original_condition : pandas.Series
    s_curve_renovation : pandas.Series
    s_curve_renovation_and_small_measure : pandas.Series
    s_curve_small_measure : pandas.Series
    s_curve_demolition : pandas.Series

    Returns
    -------
    pandas.DataFrame
    """
    s_curves_by_condition = pd.DataFrame({
        'original_condition': s_curve_original_condition,
        'demolition': s_curve_cumulative_demolition,
        'small_measure': s_curve_small_measure,
        'renovation': s_curve_renovation,
        'renovation_and_small_measure': s_curve_renovation_and_small_measure,
        's_curve_demolition': s_curve_demolition
    })
    return s_curves_by_condition


def transform_to_long(s_curves_by_condition: pd.DataFrame) -> pd.DataFrame:
    """
    
    Parameters
    ----------
    s_curves_by_condition : pandas.DataFrame 

    Returns
    -------
    pandas.DataFrame
        transformed to long, on condition for each row
    """
    df_long = s_curves_by_condition.stack().to_frame(name='s_curve')

    df_long.index.names = ['building_category', 'building_code', 'year', 'building_condition']
    return df_long


def calculate_s_curves(scurve_parameters, building_code_parameters, years, **kwargs):
    # Transform s_curve_parameters into long form with each row representing a building_condition at a certain age
    s_curves = scurve_parameters_to_scurve(scurve_parameters)
    df_never_share = scurve_parameters_to_never_share(s_curves, scurve_parameters)

    s_curves_with_building_code = merge_s_curves_and_building_code(s_curves, df_never_share, building_code_parameters)
    s_curves_with_building_code = s_curves_with_building_code.loc[(slice(None), slice(None), [y for y in years])]

    s_curves_with_demolition_acc = accumulate_demolition(s_curves_with_building_code, years)
    s_curve_demolition = s_curves_with_building_code.demolition

    s_curve_cumulative_demolition = transform_to_cumulative_demolition(s_curves_with_demolition_acc, years)
    s_curve_renovation_never_share = s_curves_with_building_code.renovation_never_share
    s_curve_small_measure_never_share = kwargs.get('small_measure_never_share', s_curves_with_building_code.small_measure_never_share)
    s_curve_cumulative_small_measure = kwargs.get('cumulative_small_measure', cumulative_small_measure(s_curves_with_building_code, years))
    s_curve_cumulative_renovation = cumulative_renovation(s_curves_with_building_code, years)

    s_curve_renovation_max = renovation_max(s_curve_cumulative_demolition, s_curve_renovation_never_share)
    s_curve_small_measure_max = kwargs.get('s_curve_small_measure_max', small_measure_max(s_curve_cumulative_demolition, s_curve_small_measure_never_share))


    s_curve_small_measure_total = trim_max_value(s_curve_cumulative_small_measure, s_curve_small_measure_max)
    s_curve_renovation_total = trim_max_value(s_curve_cumulative_renovation, s_curve_renovation_max)
    scurve_total = total(s_curve_renovation_total, s_curve_small_measure_total)

    s_curve_renovation_from_small_measure = renovation_from_small_measure(s_curve_renovation_max, s_curve_small_measure_total)
    s_curve_renovation = trim_renovation_from_renovation_total(s_curve_renovation=s_curve_renovation_from_small_measure,
                                                               s_curve_renovation_max=s_curve_renovation_max,
                                                               s_curve_renovation_total=s_curve_renovation_total,
                                                               scurve_total=scurve_total)

    s_curve_renovation_and_small_measure = renovation_and_small_measure(s_curve_renovation, s_curve_renovation_total)

    s_curve_small_measure = small_measure(s_curve_renovation_and_small_measure, s_curve_small_measure_total)

    s_curve_original_condition = original_condition(s_curve_cumulative_demolition, s_curve_renovation,
                                                            s_curve_renovation_and_small_measure,
                                                            s_curve_small_measure)

    s_curves_by_condition = transform_to_dataframe(s_curve_cumulative_demolition,
                                                           s_curve_original_condition,
                                                           s_curve_renovation,
                                                           s_curve_renovation_and_small_measure,
                                                           s_curve_small_measure,
                                                           s_curve_demolition)

    s_curves_by_condition['original_condition'] = s_curve_original_condition
    s_curves_by_condition['demolition'] =  s_curve_cumulative_demolition
    s_curves_by_condition['small_measure'] =  s_curve_small_measure
    s_curves_by_condition['renovation'] =  s_curve_renovation
    s_curves_by_condition['renovation_and_small_measure'] =  s_curve_renovation_and_small_measure

    s_curves_by_condition['s_curve_sum'] =  s_curve_original_condition + s_curve_cumulative_demolition + s_curve_small_measure + s_curve_renovation + s_curve_renovation_and_small_measure

    s_curves_by_condition['s_curve_demolition'] =  s_curve_demolition
    s_curves_by_condition['s_curve_cumulative_demolition'] = s_curve_cumulative_demolition
    s_curves_by_condition['s_curve_small_measure_total'] =  s_curve_small_measure_total
    s_curves_by_condition['s_curve_small_measure_max'] = s_curve_small_measure_max
    s_curves_by_condition['s_curve_cumulative_small_measure'] = s_curve_cumulative_small_measure
    s_curves_by_condition['s_curve_small_measure_never_share'] = s_curve_small_measure_never_share
    s_curves_by_condition['scurve_total'] = scurve_total
    s_curves_by_condition['s_curve_renovation_max'] = s_curve_renovation_max
    s_curves_by_condition['s_curve_cumulative_renovation'] = s_curve_cumulative_renovation
    s_curves_by_condition['s_curve_renovation_total'] =  s_curve_renovation_total
    s_curves_by_condition['renovation_never_share'] = s_curve_renovation_never_share


    return s_curves_by_condition
