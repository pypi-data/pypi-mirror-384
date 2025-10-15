import pandas as pd

from ebm.s_curve import transform_to_long


def test_transform_to_long():
    df = pd.DataFrame({
        'original_condition':
            {('house', 'TEK49', 2020): 0.5,
             ('house', 'TEK49', 2021): 0.5,
             ('house', 'TEK49', 2022): 0.5,
             ('house', 'TEK49', 2023): 0.4},
        'small_measure': {
            ('house', 'TEK49', 2020): 0.2,
            ('house', 'TEK49', 2021): 0.2,
            ('house', 'TEK49', 2022): 0.2,
            ('house', 'TEK49', 2023): 0.3},
        'renovation': {
            ('house', 'TEK49', 2020): 0.1,
            ('house', 'TEK49', 2021): 0.1,
            ('house', 'TEK49', 2022): 0.1,
            ('house', 'TEK49', 2023): 0.2},
        'renovation_and_small_measure': {
            ('house', 'TEK49', 2020): 0.01,
            ('house', 'TEK49', 2021): 0.02,
            ('house', 'TEK49', 2022): 0.03,
            ('house', 'TEK49', 2023): 0.04},
        'demolition': {
            ('house', 'TEK49', 2020): 0.0,
            ('house', 'TEK49', 2021): 0.0,
            ('house', 'TEK49', 2022): 0.0125,
            ('house', 'TEK49', 2023): 0.025}
    })
    df.index.names = ['building_category', 'building_code', 'year']

    result = transform_to_long(df)

    expected = pd.DataFrame(data={
        's_curve': {
            ('house', 'TEK49', 2020, 'original_condition'): 0.5,
            ('house', 'TEK49', 2020, 'small_measure'): 0.2,
            ('house', 'TEK49', 2020, 'renovation'): 0.1,
            ('house', 'TEK49', 2020, 'renovation_and_small_measure'): 0.01,
            ('house', 'TEK49', 2020, 'demolition'): 0.0,
            ('house', 'TEK49', 2021, 'original_condition'): 0.5,
            ('house', 'TEK49', 2021, 'small_measure'): 0.2,
            ('house', 'TEK49', 2021, 'renovation'): 0.1,
            ('house', 'TEK49', 2021, 'renovation_and_small_measure'): 0.02,
            ('house', 'TEK49', 2021, 'demolition'): 0.0,
            ('house', 'TEK49', 2022, 'original_condition'): 0.5,
            ('house', 'TEK49', 2022, 'small_measure'): 0.2,
            ('house', 'TEK49', 2022, 'renovation'): 0.1,
            ('house', 'TEK49', 2022, 'renovation_and_small_measure'): 0.03,
            ('house', 'TEK49', 2022, 'demolition'): 0.0125,
            ('house', 'TEK49', 2023, 'original_condition'): 0.4,
            ('house', 'TEK49', 2023, 'small_measure'): 0.3,
            ('house', 'TEK49', 2023, 'renovation'): 0.2,
            ('house', 'TEK49', 2023, 'renovation_and_small_measure'): 0.04,
            ('house', 'TEK49', 2023, 'demolition'): 0.025,
        }
    })
    expected.index.names = ['building_category', 'building_code', 'year', 'building_condition']

    pd.testing.assert_frame_equal(result, expected)

