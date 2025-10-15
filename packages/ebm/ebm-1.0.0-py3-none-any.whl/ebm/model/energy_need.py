def transform_total_energy_need(energy_need_kwh_m2, area_forecast):
    total_energy_need = area_forecast.reset_index().set_index(
        ['building_category', 'building_code', 'building_condition', 'year']).merge(energy_need_kwh_m2, left_index=True,
                                                                          right_index=True)
    total_energy_need['energy_requirement'] = total_energy_need.kwh_m2 * total_energy_need.m2
    return total_energy_need
