import typing

from enum import StrEnum, unique, auto


@unique
class BuildingCondition(StrEnum):
    ORIGINAL_CONDITION = auto()
    SMALL_MEASURE = auto()
    RENOVATION = auto()
    RENOVATION_AND_SMALL_MEASURE = auto()
    DEMOLITION = auto()

    @classmethod
    def _missing_(cls, value: str):
        """
        Attempts to create an enum member from a given value by normalizing the string.

        This method is called when a value is not found in the enumeration. It converts the input value 
        to lowercase, replaces spaces and hyphens with underscores, and then checks if this transformed 
        value matches the value of any existing enum member.

        Parameters:
        - value (str): The input value to convert and check against existing enum members.

        Returns:
        - Enum member: The corresponding enum member if a match is found.

        Raises:
        - ValueError: If no matching enum member is found.
        """
        value = value.lower().replace(' ', '_').replace('-', '_')
        for member in cls:
            if member.value == value:
                return member
        return ValueError(f'No such building condition: {value}')

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    @staticmethod
    def get_scruve_condition_list() -> typing.List[str]:
        """
        Retrieves a list with the building conditions used in S-curve calculations (in lower case). 
        
        Returns:
        - condition_list (list[str]): list of building conditions
        """
        condition_list = [BuildingCondition.SMALL_MEASURE.value, BuildingCondition.RENOVATION.value, BuildingCondition.DEMOLITION.value]
        return condition_list
    
    @staticmethod
    def get_full_condition_list() -> typing.List[str]:
        """
        Retrieves a list with all building conditions (in lower case).
        
        Returns:
        - condition_list (list[str]): list of building conditions 
        """
        condition_list = [condition.value for condition in iter(BuildingCondition)]
        return condition_list

    @staticmethod
    def existing_conditions() -> typing.Iterable['BuildingCondition']:
        """
        Returns all BuildingCondition except demolition

        Returns
        -------
            Iterable of all BuildingCondition except demolition
        """
        yield from (b for b in BuildingCondition if b != BuildingCondition.DEMOLITION)


if __name__ == '__main__':
    for building_condition in BuildingCondition:
        print(building_condition)
        print(repr(building_condition))
