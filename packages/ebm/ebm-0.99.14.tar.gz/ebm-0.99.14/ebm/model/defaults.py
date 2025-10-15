import pandas as pd

def default_calibrate_heating_rv() -> pd.DataFrame:
    """Creates a default dataframe for heating_rv calibration. The factor is set to 1.0 (no change)

    Returns
    -------
    pd.DataFrame
    """
    df = pd.DataFrame({
        'building_category': ['non_residential', 'residential'],
        'purpose': ['heating_rv', 'heating_rv'],
        'heating_rv_factor': [1.0, 1.0]})
    return df

def default_calibrate_energy_consumption() -> pd.DataFrame:
    """
    Creates an empty dataframe for energy consumption calibration.

    Returns
    -------
    pd.DataFrame
    """
    df = pd.DataFrame({
        'building_category': [],
        'to': [],
        'from': [],
        'factor': []}
    )
    return df