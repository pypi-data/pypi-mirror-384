# noinspection SpellCheckingInspection
import pandas as pd
from loguru import logger

from ebm.model.building_category import NON_RESIDENTIAL, RESIDENTIAL, BuildingCategory
from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.model.heating_systems import HeatingSystems

BUILDING_CATEGORY = 'building_category'
BUILDING_CODE = 'building_code'
HEATING_SYSTEMS = 'heating_systems'
NEW_HEATING_SYSTEMS = 'new_heating_systems'
YEAR = 'year'
TEK_SHARES = 'heating_system_share'


class HeatingSystemsForecast: # noqa: D101

    def __init__(self, shares_start_year: pd.DataFrame, efficiencies: pd.DataFrame, forecast: pd.DataFrame, building_code_list: list[str], period: YearRange):
        """Init HeatingSystemsForecast."""
        self.shares_start_year = shares_start_year
        self.efficiencies = efficiencies
        self.forecast = forecast
        self.building_code_list = building_code_list
        self.period = period

        self._validate_years()
        check_sum_of_shares(shares_start_year)

    def _validate_years(self) -> None:
        """
        Ensure that the years in the dataframes provided during initialization align with the specified period.

        This method performs the following validations:
         1. Confirms that `shares_start_year` has exactly one unique start year.
         2. Checks that the minimum year in `projection` for each combination of `BUILDING_CATEGORY` and `TEK` matches the expected start year + 1.
         3. Verifies that all years in the given `period` are present in the `projection` dataframe for unique combinations of `BUILDING_CATEGORY` and `TEK`.

        Raises
        ------
        ValueError
            If any of the above validations fail.

        """
        start_year = self.shares_start_year[YEAR].unique()
        if len(start_year) != 1:
            raise ValueError("More than one start year in dataframe.")
        start_year = start_year[0]

        if start_year != self.period.start:
            raise ValueError("Start year in dataframe doesn't match start year for given period.")

        projection = self.forecast.melt(id_vars = [BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, NEW_HEATING_SYSTEMS],
                                        var_name = YEAR, value_name = "Andel_utskiftning")
        projection[YEAR] = projection[YEAR].astype(int)
        min_df = projection.groupby([BUILDING_CATEGORY, BUILDING_CODE]).agg(min_year=(YEAR, 'min')).reset_index()
        min_mismatch = min_df[min_df['min_year'] != (start_year + 1)]

        if not min_mismatch.empty:
            raise ValueError("Years don't match between dataframes.")

        projection_period = self.period.subset(1).range()

        def check_years(group: pd.Series): # noqa: ANN202
            return set(projection_period).issubset(group[YEAR])

        period_match = projection.groupby(by=[BUILDING_CATEGORY, BUILDING_CODE]).apply(check_years).reset_index()
        if not period_match[period_match[0] == False].empty: # noqa: E712
            raise ValueError("Years in dataframe not present in given period.")

    def calculate_forecast(self) -> pd.DataFrame:
        """
        Project heating system shares across model years.

        Returns
        -------
        pd.Dataframe
            TEK shares for heating systems per year, along with different load shares and efficiencies.

        Raises
        ------
        ValueError
            If sum of shares for a building_code is not equal to 1.

        """
        shares_all_heating_systems = add_missing_heating_systems(self.shares_start_year,
                                                                 HeatingSystems,
                                                                 self.period.start)
        projected_shares = expand_building_category_building_code(self.forecast, self.building_code_list)
        new_shares = project_heating_systems(shares_all_heating_systems, projected_shares, self.period)
        heating_systems_projection = add_existing_heating_system_shares_to_projection(new_shares,
                                                                           self.shares_start_year,
                                                                           self.period)
        check_sum_of_shares(heating_systems_projection)
        heating_systems_projection = add_load_shares_and_efficiencies(heating_systems_projection, self.efficiencies)
        return heating_systems_projection

    @staticmethod
    def new_instance(period: YearRange,
                     database_manager: DatabaseManager = None) -> 'HeatingSystemsForecast':
        """
        Create a new instance of the HeatingSystemsProjection class, using the specified YearRange Period and an optional database manager.

        If a database manager is not provided, a new DatabaseManager instance will be created.

        Parameters
        ----------
        period: YearRange
            period of forecast
        database_manager: DatabaseManager
            a database manager for heating system forecast

        Returns
        -------
        HeatingSystemsForecast
            A new instance of HeatingSystemsProjection initialized with data from the specified database manager.

        """
        dm = database_manager if isinstance(database_manager, DatabaseManager) else DatabaseManager()
        shares_start_year = dm.get_heating_systems_shares_start_year()
        efficiencies = dm.get_heating_system_efficiencies()
        projection = dm.get_heating_system_forecast()
        building_code_list = dm.get_building_code_list()
        return HeatingSystemsForecast(shares_start_year=shares_start_year,
                                      efficiencies=efficiencies,
                                      forecast=projection,
                                      building_code_list=building_code_list,
                                      period=period)

    @staticmethod
    def pad_projection(hf: pd.DataFrame, years_to_pad: YearRange) -> pd.DataFrame:
        """
        Left pad dataframe hf with years in years_to_pad. The padding will be equal to existing first year of hf.

        Parameters
        ----------
        hf : pd.DataFrame
            heating systems to pad
        years_to_pad : YearRange
            range of years to pad unto hf

        Returns
        -------
        pd.DataFrame
            hf with left padding

        """
        padding_value = hf[hf.year == years_to_pad.end + 1].copy()
        left_padding = []
        for year in years_to_pad:
            year_values = padding_value.copy()
            year_values['year'] = year
            left_padding.append(year_values)

        return pd.concat(left_padding + [hf]) # noqa: RUF005


def add_missing_heating_systems(heating_systems_shares: pd.DataFrame,
                                heating_systems: HeatingSystems = None,
                                start_year: int|None = None) -> pd.DataFrame:
    """Add missing HeatingSystems per BuildingCategory and building_codewith a default TEK_share of 0."""
    df_aggregert_0 = heating_systems_shares.copy()
    input_start_year = df_aggregert_0[YEAR].unique()
    if len(input_start_year) != 1:
        raise ValueError("More than one start year in dataframe")

    # TODO: drop start year as input param and only use year in dataframe?
    if not start_year:
        start_year =  input_start_year[0]
    elif start_year != input_start_year:
        raise ValueError("Given start_year doesn't match year in dataframe.")

    if not heating_systems:
        heating_systems = HeatingSystems
    oppvarmingstyper = pd.DataFrame(
        {HEATING_SYSTEMS: [hs for hs in heating_systems]},
    )

    df_aggregert_0_kombinasjoner = df_aggregert_0[[BUILDING_CATEGORY, BUILDING_CODE]].drop_duplicates()
    df_aggregert_0_alle_oppvarmingstyper = df_aggregert_0_kombinasjoner.merge(oppvarmingstyper, how = 'cross')

    df_aggregert_merged = df_aggregert_0_alle_oppvarmingstyper.merge(df_aggregert_0,
                                                                    on = [BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS],
                                                                    how = 'left')
    #TODO: Kan droppe kopi av df og heller ta fillna() for de to kolonnene
    manglende_rader = df_aggregert_merged[df_aggregert_merged[TEK_SHARES].isna()].copy()
    manglende_rader[YEAR] = start_year
    manglende_rader[TEK_SHARES] = 0
    manglende_rader = manglende_rader[[BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, YEAR, TEK_SHARES]]

    df_aggregert_alle_kombinasjoner = pd.concat([df_aggregert_0, manglende_rader])

    return df_aggregert_alle_kombinasjoner


def add_load_shares_and_efficiencies(df: pd.DataFrame,
                                     heating_systems_efficiencies: pd.DataFrame) -> pd.DataFrame:
    """
    Add load share and efficiency data to heating system share records by merging with efficiency reference data.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing heating system shares, including columns for year and heating system type.

    heating_systems_efficiencies : pandas.DataFrame
        DataFrame containing efficiency and load share data for each heating system type.

    Returns
    -------
    pandas.DataFrame
        Merged DataFrame with heating system shares enriched with efficiency and load share information.

    Notes
    -----
    - The merge is performed on the HEATING_SYSTEMS column using a left join.
    - The YEAR column is cast to integer to ensure consistent data types.

    """
    df_hoved_spiss_og_ekstralast = heating_systems_efficiencies.copy()
    df_oppvarmingsteknologier_andeler = df.merge(df_hoved_spiss_og_ekstralast, on = [HEATING_SYSTEMS],
                                                 how ='left')
    df_oppvarmingsteknologier_andeler[YEAR] = df_oppvarmingsteknologier_andeler[YEAR].astype(int)
    return df_oppvarmingsteknologier_andeler


def aggregere_lik_oppvarming_fjern_0(df:pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate heating system shares by summing TEK_share values, excluding entries with zero share.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame containing heating system share data, including TEK_share values.

    Returns
    -------
    pandas.DataFrame
        Aggregated DataFrame grouped by building category, building code, heating system, and year,
        with summed TEK_share values excluding zero-share entries.

    Notes
    -----
    - Rows where TEK_share is zero are removed before aggregation.
    - The resulting DataFrame is grouped by [BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, YEAR].

    """
    df_fjern_null = df.query(f"{TEK_SHARES} != 0").copy()
    df_aggregert = df_fjern_null.groupby([BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, YEAR],
                                         as_index = False)[TEK_SHARES].sum()
    return df_aggregert


def expand_building_category_building_code(projection: pd.DataFrame,
                                 building_code_list: list[str]) -> pd.DataFrame:
    """Add necessary building categories and building_code to the heating_systems_forecast dataframe."""
    score = '_score'
    original_building_category = '_original_bc'
    original_building_code = '_original_building_code'
    projection[original_building_category] = projection['building_category']
    projection[original_building_code] = projection['building_code']

    alle_bygningskategorier = '+'.join(BuildingCategory)
    alle_building_code = '+'.join(tek for tek in building_code_list)
    husholdning = '+'.join(bc for bc in BuildingCategory if bc.is_residential())
    yrkesbygg = '+'.join(bc for bc in BuildingCategory if bc.is_non_residential())

    df = projection.copy()
    df.loc[df[BUILDING_CODE] == "default", BUILDING_CODE] = alle_building_code
    df.loc[df[BUILDING_CATEGORY] == "default", BUILDING_CATEGORY] = alle_bygningskategorier
    df.loc[df[BUILDING_CATEGORY] == RESIDENTIAL, BUILDING_CATEGORY] = husholdning
    df.loc[df[BUILDING_CATEGORY] == NON_RESIDENTIAL, BUILDING_CATEGORY] = yrkesbygg

    df = df.assign(**{BUILDING_CATEGORY: df[BUILDING_CATEGORY].str.split('+')}).explode(BUILDING_CATEGORY)
    df2 = df.assign(**{BUILDING_CODE: df[BUILDING_CODE].str.split('+')}).explode(BUILDING_CODE)
    df2 = df2.reset_index(drop=True)
    df2[score] = (df2[original_building_category] != 'default') * 1 + \
                 (~df2[original_building_category].isin(['default', NON_RESIDENTIAL, RESIDENTIAL])) * 1 + \
                 (df2[original_building_code] != 'default') * 1

    df2 = df2.sort_values(by=[score])
    de_duped = df2.drop_duplicates(subset=[BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, NEW_HEATING_SYSTEMS], keep='last')

    return de_duped.drop(columns=[score, original_building_category, original_building_code])


def project_heating_systems(shares_start_year_all_systems: pd.DataFrame,
                            projected_shares: pd.DataFrame,
                            period: YearRange) -> pd.DataFrame:
    """
    Forecast heating system shares over a given period based on initial shares and projected replacement rates.

    Parameters
    ----------
    shares_start_year_all_systems : pandas.DataFrame
        DataFrame containing TEK_share values for all heating systems at the start year.

    projected_shares : pandas.DataFrame
        DataFrame containing projected replacement shares for heating systems across years.

    period : YearRange
        The projection period, defined by a start and end year.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with projected TEK_share values for both existing and new heating systems
        across the specified period.

    Notes
    -----
    - The function melts the projected shares into long format and filters them to match the projection period.
    - It calculates new shares based on replacement rates and adjusts existing shares accordingly.
    - New and existing heating system shares are merged and aggregated, removing duplicates and zero-share entries.
    - The final output contains TEK_share values per year, building category, building code, and heating system.
    - Internal helper functions like `aggregere_lik_oppvarming_fjern_0` are used to clean and aggregate data.
    - The YEAR column is explicitly cast to integer at the end to ensure consistency.

    """
    df = shares_start_year_all_systems.copy()
    inputfil_oppvarming = projected_shares.copy()

    df_framskrive_oppvarming_long = inputfil_oppvarming.melt(id_vars=[BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS,
                                                                      NEW_HEATING_SYSTEMS],
                                                             var_name=YEAR, value_name="Andel_utskiftning")

    df_framskrive_oppvarming_long[YEAR] = df_framskrive_oppvarming_long[YEAR].astype(int)
    df_framskrive_oppvarming_long = df_framskrive_oppvarming_long[df_framskrive_oppvarming_long[YEAR].isin(period.subset(1).range())]

    liste_eksisterende_oppvarming = list(df_framskrive_oppvarming_long[HEATING_SYSTEMS].unique())
    liste_ny_oppvarming = list(df_framskrive_oppvarming_long[NEW_HEATING_SYSTEMS].unique())

    columns_to_keep = [BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, YEAR, TEK_SHARES]
    oppvarming_og_tek = df.query(f"{HEATING_SYSTEMS} == {liste_eksisterende_oppvarming}")[columns_to_keep].copy()

    columns_to_keep = [BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, TEK_SHARES]
    oppvarming_og_tek_foer_endring = df.query(f"{HEATING_SYSTEMS} == {liste_ny_oppvarming}")[columns_to_keep].copy()

    df_merge = oppvarming_og_tek.merge(df_framskrive_oppvarming_long,
                                       on=[BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS], how='inner')
    df_merge['Ny_andel'] = (df_merge[TEK_SHARES] * df_merge['Andel_utskiftning'])

    df_ny_andel_sum = df_merge.groupby([BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, f'{YEAR}_y'], as_index = False)[['Ny_andel']].sum()
    df_ny_andel_sum = df_ny_andel_sum.rename(columns={"Ny_andel": "Sum_ny_andel"})

    df_merge_sum_ny_andel = df_merge.merge(df_ny_andel_sum, on = [BUILDING_CATEGORY,BUILDING_CODE,HEATING_SYSTEMS, f'{YEAR}_y'])

    df_merge_sum_ny_andel['Eksisterende_andel'] = (df_merge_sum_ny_andel[TEK_SHARES] -
                                                    df_merge_sum_ny_andel['Sum_ny_andel'])

    kolonner_eksisterende = [f'{YEAR}_y', BUILDING_CATEGORY, BUILDING_CODE, 'Eksisterende_andel', HEATING_SYSTEMS]
    navn_eksisterende_kolonner = {"Eksisterende_andel": TEK_SHARES,
                                  NEW_HEATING_SYSTEMS : HEATING_SYSTEMS,
                                  f'{YEAR}_y': YEAR}

    kolonner_nye = [f'{YEAR}_y', BUILDING_CATEGORY, BUILDING_CODE, 'Ny_andel', NEW_HEATING_SYSTEMS]
    navn_nye_kolonner = {"Ny_andel": TEK_SHARES,
                         NEW_HEATING_SYSTEMS: HEATING_SYSTEMS,
                         f'{YEAR}_y': YEAR}

    rekkefolge_kolonner = [YEAR, BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, TEK_SHARES]

    nye_andeler_eksisterende = df_merge_sum_ny_andel[kolonner_eksisterende].rename(columns=navn_eksisterende_kolonner)

    nye_andeler_nye = df_merge_sum_ny_andel[kolonner_nye].rename(columns=navn_nye_kolonner)
    nye_andeler_nye = aggregere_lik_oppvarming_fjern_0(nye_andeler_nye)

    nye_andeler_pluss_eksisterende = nye_andeler_nye.merge(oppvarming_og_tek_foer_endring, on=[BUILDING_CATEGORY,BUILDING_CODE,HEATING_SYSTEMS], how='inner')
    nye_andeler_pluss_eksisterende[TEK_SHARES] = nye_andeler_pluss_eksisterende[f'{TEK_SHARES}_x'] + nye_andeler_pluss_eksisterende[f'{TEK_SHARES}_y']
    nye_andeler_pluss_eksisterende = nye_andeler_pluss_eksisterende.drop(columns=[f'{TEK_SHARES}_x', f'{TEK_SHARES}_y'])

    nye_andeler_samlet = pd.concat([nye_andeler_eksisterende, nye_andeler_pluss_eksisterende])
    nye_andeler_drop_dupe = nye_andeler_samlet.drop_duplicates(
        subset=[YEAR, BUILDING_CATEGORY, BUILDING_CODE, HEATING_SYSTEMS, TEK_SHARES], keep='first')

    nye_andeler_samlet_uten_0 = aggregere_lik_oppvarming_fjern_0(nye_andeler_drop_dupe)
    nye_andeler_samlet_uten_0 = nye_andeler_samlet_uten_0[rekkefolge_kolonner]

    # TODO: check dtype changes in function
    nye_andeler_samlet_uten_0[YEAR] = nye_andeler_samlet_uten_0[YEAR].astype(int)

    return nye_andeler_samlet_uten_0


def check_sum_of_shares(projected_shares: pd.DataFrame, precision: int = 10) -> None:
    """
    Make sure that the sum of heating_system_share equals 1 per TEK, building category and year.

    Parameters
    ----------
    projected_shares: pd.Dataframe
        Dataframe must contain columns: 'building_category', 'building_code', 'year' and 'heating_system_share'
    precision: int
        Precision used for value check (with round)

    Raises
    ------
    ValueError
        If sum of shares for a building_codeis not equal to 1.

    """
    df = projected_shares.copy()
    df = df.groupby(by=[BUILDING_CATEGORY, BUILDING_CODE, YEAR])[[TEK_SHARES]].sum()
    df['check'] = round(df[TEK_SHARES] * 100, precision) == 100.0 # noqa: PLR2004
    invalid_shares = df[df['check'] == False].copy() # noqa: E712
    invalid_shares = invalid_shares.drop(columns=['check'])
    if len(invalid_shares) > 0:
        logger.error('Sum of TEK shares not equal to 1 for:')
        for idx, row in invalid_shares.iterrows():
            logger.error('{idx}: {}', idx=idx, row_dict=row.to_dict())
        logger.warning('Skipping ValueError on sum!=1.0')


def add_existing_heating_system_shares_to_projection(new_shares: pd.DataFrame,
                                          existing_shares: pd.DataFrame,
                                          period: YearRange) -> pd.DataFrame:
    """
    Extend heating system shares in the projection period by preserving TEK_share values for systems with unprojected existing building code shares.

    Parameters
    ----------
    new_shares : pandas.DataFrame
        DataFrame containing projected heating system shares for buildings.

    existing_shares : pandas.DataFrame
        DataFrame containing existing heating system shares for buildings.

    period : YearRange
        The projection period, defined by a start and end year.

    Returns
    -------
    pandas.DataFrame
        Combined DataFrame with projected shares and extended existing shares
        for heating systems not present in the new projections.

    Notes
    -----
    - Heating systems with existing shares but missing from the new projections
      will retain their TEK_share values across the projection period.
    - The function filters out combinations already present in the new projections
      and extends the remaining ones across the projection years.
    - The `Sortering` column is used internally for identifying unique combinations
      of building category, code, and heating system.

    """

    def sortering_oppvarmingstyper(df: pd.DataFrame) -> [pd.DataFrame, list[str]]:
        df_kombinasjoner = df.copy()
        df_kombinasjoner['Sortering'] = df_kombinasjoner[BUILDING_CATEGORY] + df_kombinasjoner[BUILDING_CODE] + \
                                        df_kombinasjoner[HEATING_SYSTEMS]
        kombinasjonsliste = list(df_kombinasjoner['Sortering'].unique())
        return df_kombinasjoner, kombinasjonsliste

    df_nye_andeler_kopi = new_shares.copy()

    new_shares, alle_nye_kombinasjonsliste = sortering_oppvarmingstyper(new_shares)
    existing_shares, _ = sortering_oppvarmingstyper(existing_shares)
    df_eksisterende_filtrert = existing_shares.query(f"Sortering != {alle_nye_kombinasjonsliste}")
    df_eksisterende_filtrert = df_eksisterende_filtrert.drop(columns = ['Sortering'])

    # TODO: set lower limit to period equal to last year (max) present in forecast data?
    projection_period = YearRange(period.start + 1, period.end).year_range
    utvidede_aar_uendret = pd.concat([
        df_eksisterende_filtrert.assign(**{YEAR: year}) for year in projection_period
    ])

    samlede_nye_andeler = pd.concat([utvidede_aar_uendret, df_nye_andeler_kopi,
                                     existing_shares], ignore_index=True)
    samlede_nye_andeler = samlede_nye_andeler.drop(columns=['Sortering'])
    return samlede_nye_andeler
