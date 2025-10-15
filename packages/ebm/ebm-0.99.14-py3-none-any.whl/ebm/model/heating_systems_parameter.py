import pandas as pd

from ebm.energy_consumption import EnergyConsumption


def heating_systems_parameter_from_projection(heating_systems_projection: pd.DataFrame) -> pd.DataFrame:
    calculator = EnergyConsumption(heating_systems_projection.copy())

    return calculator.grouped_heating_systems()


def expand_heating_system_parameters(heating_systems_parameter):
    df = heating_systems_parameter
    df = df.assign(**{'heating_system': df['heating_systems'].str.split('-')}).explode('heating_system')
    df['heating_system'] = df['heating_system'].str.strip()
    df['load_share'] = df['base_load_coverage']
    return df
