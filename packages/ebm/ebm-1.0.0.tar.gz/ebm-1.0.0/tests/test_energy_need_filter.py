import io

import pandas as pd
import pytest

from ebm.model.energy_need_filter import de_dupe_dataframe, explode_dataframe


def test_de_dupe_dataframe():
    settings = pd.read_csv(io.StringIO(
"""building_category,building_code,purpose,value,start_year,function,end_year
default,default,cooling,0.0,2020,yearly_reduction,
default,default,electrical_equipment,0.01,2021,yearly_reduction,
default,default,lighting,0.005,2031,yearly_reduction,2050
default,default,lighting,0.5555555555555556,2020,improvement_at_end_year,2030
""".strip()))

    df = de_dupe_dataframe(df=explode_dataframe(settings),
                           unique_columns=['building_category', 'building_code', 'purpose', 'start_year', 'end_year', 'function'])

    others = df.query('purpose not in ["lighting", "electrical_equipment"]')

    assert (others.value == 0.0).all()
    el_eq = df.query('purpose in ["electrical_equipment"]')
    assert len(el_eq) == 143
    assert (el_eq.value == 0.01).all()
    lighting_yearly_reduction = df.query('purpose in ["lighting"] and function=="yearly_reduction"')
    assert len(lighting_yearly_reduction) == 143
    assert (lighting_yearly_reduction.value == 0.005).all()
    lighting_improvement_at_end_year = df.query('function=="improvement_at_end_year"')
    assert len(lighting_improvement_at_end_year) == 143
    assert (lighting_improvement_at_end_year.value == 0.5555555555555556).all()


def test_explode_dataframe():
    """
    If there are more than one match for the given params (building_category, tek and purpose) and
    they have the same priority, then they should be sorted by a pre-defined preferance order. The
    order in which they should be prioritized is as follows: building_category, tek and purpose.
    """
    original_condition = pd.read_csv(io.StringIO("""
    building_category,building_code,purpose,kwh_m2
    default,TEK07,cooling,0.1
    apartment_block,default,cooling,0.2                                                                                   
    apartment_block,TEK07,default,0.3
    default,default,default,0.99                                                                                                                                                                                                                                                                                          
    """.strip()), skipinitialspace=True)

    ex_df = explode_dataframe(
        df=original_condition,
        building_code_list='TEK49 PRE_TEK49 PRE_TEK49_RES_1950 TEK69 TEK87 TEK97 TEK07 TEK10 TEK17 TEK21 TEK01'.split(' '))
    cooling = ex_df.query('building_category=="apartment_block" and building_code=="TEK07" and purpose=="cooling"')

    assert len(cooling) == 4
    assert cooling.iloc[0].kwh_m2 == 0.3


if __name__ == "__main__":
    pytest.main()