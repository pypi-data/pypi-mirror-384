from types import MappingProxyType

from ebm.model.building_category import BuildingCategory, RESIDENTIAL, NON_RESIDENTIAL
from ebm.model.building_condition import BuildingCondition

_building_category_order = {
    BuildingCategory.HOUSE: 101, BuildingCategory.APARTMENT_BLOCK: 102, RESIDENTIAL: 199,
    'holiday_home': 299,
    BuildingCategory.RETAIL: 301, BuildingCategory.OFFICE: 302, BuildingCategory.KINDERGARTEN: 303, BuildingCategory.SCHOOL: 304,
    BuildingCategory.UNIVERSITY: 305, BuildingCategory.HOSPITAL: 306, BuildingCategory.NURSING_HOME: 307,
    BuildingCategory.HOTEL: 308, BuildingCategory.SPORTS: 309, BuildingCategory.CULTURE: 310,
    BuildingCategory.STORAGE: 312, 'storage': 311, NON_RESIDENTIAL: 399}

BUILDING_CATEGORY_ORDER = MappingProxyType(_building_category_order)
"""An immutable dict of BeMa sorting order for building_category"""

_building_group_order = {'residential': 199, 'holiday_home': 299, 'non_residential': 399}

BUILDING_GROUP_ORDER = MappingProxyType(_building_group_order)
"""An immutable dict of BeMa sorting order for building_group"""


_building_mix_order = _building_group_order| _building_category_order


_building_code_order = {'PRE_TEK49': 1814, 'TEK49': 1949, 'TEK69': 1969, 'TEK87': 1987, 'TEK97': 1997,
              'TEK07': 2007, 'TEK10': 2010, 'TEK17': 2017,
              'TEK21': 2021, 'default': 9998, 'all': 9999}

TEK_ORDER = MappingProxyType(_building_code_order)
"""A dict of BeMa sorting order for TEK"""

_purpose_order = {'heating_rv': 1, 'heating_dhw': 2, 'fans_and_pumps': 3, 'lighting': 4,
                    'electrical_equipment': 5, 'cooling': 6}

PURPOSE_ORDER = MappingProxyType(_purpose_order)
"""A dict of BeMa sorting order for purpose"""

_building_condition_order = {BuildingCondition.ORIGINAL_CONDITION: 1, BuildingCondition.SMALL_MEASURE: 2,
    BuildingCondition.RENOVATION: 3, BuildingCondition.RENOVATION_AND_SMALL_MEASURE: 4, BuildingCondition.DEMOLITION: 5}

BUILDING_CONDITION_ORDER = MappingProxyType(_building_condition_order)
"""A dict of BeMa sorting order for building_condition"""

_start_row_building_category_construction = {BuildingCategory.HOUSE: 11, BuildingCategory.APARTMENT_BLOCK: 23,
    BuildingCategory.KINDERGARTEN: 41, BuildingCategory.SCHOOL: 55, BuildingCategory.UNIVERSITY: 69,
    BuildingCategory.OFFICE: 83, BuildingCategory.RETAIL: 97, BuildingCategory.HOTEL: 111,
    BuildingCategory.HOSPITAL: 125, BuildingCategory.NURSING_HOME: 139, BuildingCategory.CULTURE: 153,
    BuildingCategory.SPORTS: 167, BuildingCategory.STORAGE: 182}

START_ROWS_CONSTRUCTION_BUILDING_CATEGORY = MappingProxyType(_start_row_building_category_construction)
"""A dict of BeMa sorting order for start row of each building category in the sheet `nybygging`"""


def get_building_category_sheet(building_category: BuildingCategory, area_sheet: bool = True) -> str:
    """
    Returns the appropriate sheet name based on the building category and area sheet type.

    Parameters
    ----------
    - building_category: An instance of BuildingCategory.
    - area_sheet (bool): Determines whether to return the area sheet ('A') or rates sheet ('R') name. Defaults to True for the area sheet.

    Returns
    -------
    - sheet (str): The sheet name corresponding to the building category and sheet type.
    """
    building_category_sheets = {BuildingCategory.HOUSE: ['A hus', 'R hus'],
        BuildingCategory.APARTMENT_BLOCK: ['A leil', 'R leil'], BuildingCategory.KINDERGARTEN: ['A bhg', 'R bhg'],
        BuildingCategory.SCHOOL: ['A skole', 'R skole'], BuildingCategory.UNIVERSITY: ['A uni', 'R uni'],
        BuildingCategory.OFFICE: ['A kont', 'R kont'], BuildingCategory.RETAIL: ['A forr', 'R forr'],
        BuildingCategory.HOTEL: ['A hotell', 'R hotell'], BuildingCategory.HOSPITAL: ['A shus', 'R shus'],
        BuildingCategory.NURSING_HOME: ['A shjem', 'R shjem'], BuildingCategory.CULTURE: ['A kult', 'R kult'],
        BuildingCategory.SPORTS: ['A idr', 'R idr'], BuildingCategory.STORAGE: ['A ind', 'R ind']}

    if area_sheet:
        sheet = building_category_sheets[building_category][0]
    else:
        sheet = building_category_sheets[building_category][1]

    return sheet


# noinspection PyTypeChecker
def map_sort_order(column):
    """
    Map the sort order from bema to a DataFrame. The function is meant to be used as the key parameter for
    a pandas DataFrame methods sort_values and sort_index.

    Example below.

    Parameters
    ----------
    column : pandas.Series
        A pandas Series whose `name` attribute determines which predefined
        mapping to apply to its values.

    Returns
    -------
    pandas.Series
        A Series with values mapped to integers according to the corresponding
        sort order. If the column name does not match any predefined mapping,
        the original Series is returned unchanged.

    Notes
    -----
    The function supports the following mappings:

    - 'building_category': uses `_building_mix_order`
    - 'building_group': uses `BUILDING_GROUP_ORDER`
    - 'building_condition': uses `BUILDING_CONDITION_ORDER`
    - 'purpose': uses `PURPOSE_ORDER`
    - 'building_code': uses `TEK_ORDER`

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame(
    >>>    data=[('culture', 'PRE_TEK49', 'heating_rv', 2022, 'LAST'),
    >>>          ('house', 'TEK07', 'heating_dhw', 2021, 'FIRST')],
    >>>    columns=['building_category', 'building_code', 'purpose', 'year', 'value'])
    >>> df.sort_values(by=['building_category', 'building_code', 'purpose', 'year'], key=map_sort_order)
        building_category        building_code     purpose  year  value
     1  house      TEK07  heating_dhw  2020  FIRST
     0  culture  PRE_TEK49   heating_rv  2021   LAST
    …
    >>> from ebm.model.bema import map_sort_order
    >>> import pandas as pd
    >>> df = pd.DataFrame(data=['3', '2', 'last', 'first'],
    >>>                  index=pd.Index(['non_residential', 'holiday_home', 'all', 'residential'],
    >>>                                 name='building_group'))
    >>> df.sort_index(key=map_sort_order)
      building_group
      residential      first
      holiday_home         2
      non_residential      3
      all               last
    """
    if column.name=='building_category':
        return column.map(_building_mix_order)
    if column.name=='building_group':
        return column.map(BUILDING_GROUP_ORDER)
    if column.name=='building_condition':
        return column.map(BUILDING_CONDITION_ORDER)
    if column.name=='purpose':
        return column.map(PURPOSE_ORDER)
    if column.name=='building_code':
        return column.map(TEK_ORDER)
    return column
