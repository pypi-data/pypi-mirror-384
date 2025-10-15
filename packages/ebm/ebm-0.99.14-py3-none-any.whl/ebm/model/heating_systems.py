from enum import unique, StrEnum

@unique
class HeatingSystems(StrEnum):
    ELECTRICITY = 'Electricity'
    ELECTRICITY_BIO = 'Electricity - Bio'
    ELECTRIC_BOILER = 'Electric boiler'
    ELECTRIC_BOILER_SOLAR = 'Electric boiler - Solar'
    GAS = 'Gas'
    DISTRICT_HEATING = 'DH'
    DISTRICT_HEATING_BIO = 'DH - Bio'
    HP_BIO = 'HP - Bio - Electricity'
    HP_ELECTRICITY = 'HP - Electricity'
    HP_CENTRAL_HEATING = 'HP Central heating - Electric boiler'
    HP_CENTRAL_HEATING_GAS = 'HP Central heating - Gas'
    HP_CENTRAL_HEATING_BIO = 'HP Central heating - Bio'


    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'