# Imports
import pandas as pd
import geopandas as gpd
import numpy as np

def load_rm_data(path, year = None, english = False) -> pd.DataFrame:
    """Loads rat monitor export data into a pandas dataframe. 
   
    Takes a file path and keyword arguments, loads data into a dataframa and pre-processes the data.
    Returns a dataframe with all data (for the selected year) from the rat monitor export file.

    Args:
        path (str): The file path to load.
        year (int, None): When None, loads all data.
        english (bool, False): When True, translates dataframe into English.
    """
    # load rat monitor data into dataframe
    rat_df = pd.read_excel(path)

    # clean weird characters
    rat_df.columns = rat_df.columns.str.strip('\n')
    rat_df = rat_df.map(lambda x: x.strip('[').strip(']') if isinstance(x, str) else x)

    # set nan values
    rat_df.replace('[]', np.nan, inplace=True)

    # correct datatypes
    rat_df['Pc4code'] = rat_df['Pc4code'].fillna(0000).astype(float).astype(int)
    rat_df['Datum waarneming'] = pd.to_datetime(rat_df['Datum waarneming'])
    rat_df['Einddatum'] = pd.to_datetime(rat_df['Einddatum'])

    # if a year was selected, return only rat data from that year
    if year:
        rat_df = rat_df[rat_df['Datum waarneming'].dt.year == year]

    # translate to english if requested
    if english:
        rat_df = translate_data(rat_df)

    return rat_df


def group_by_postcode(df):
    """Aggregates rat sightings by PC4Code. 
   
    Takes a dataframe with rat sightings, groups the data by PC4Code and sums rat sightings.
    Returns a dataframe with columns EEN_OF_MEER, MEER_DAN_VIJF, TOTAAL and postcode as index.
    """
    pc_rat_df = df.groupby(['Pc4code', 'Aantal ratten']).size().unstack(fill_value=0)
    pc_rat_df['TOTAAL'] = pc_rat_df.EEN_OF_MEER + pc_rat_df.MEER_DAN_VIJF

    # rename postal code and fix index
    pc_rat_df.reset_index(inplace=True)
    pc_rat_df.rename({'Pc4code': 'postcode'}, axis=1, inplace=True)
    pc_rat_df.set_index('postcode', inplace=True)

    # exclude missing postal codes
    pc_rat_df = pc_rat_df[pc_rat_df.index != 0]

    return pc_rat_df



def group_by_place(df):
    """Aggregates rat sightings by place name. 
   
    Takes a dataframe with rat sightings from a rat monitor export and returns 
    a dataframe with EEN_OF_MEER, MEER_DAN_VIJF, TOTAAL columns and plaatsnaam as index.
    """
    plaats_rat_df = df.groupby(['Plaatsnaam', 'Aantal ratten']).size().unstack(fill_value=0)
    plaats_rat_df['TOTAAL'] = plaats_rat_df.EEN_OF_MEER + plaats_rat_df.MEER_DAN_VIJF

    # rename place name and fix index
    plaats_rat_df.reset_index(inplace=True)
    plaats_rat_df.rename({'Plaatsnaam': 'plaatsnaam'}, axis=1, inplace=True)
    plaats_rat_df.set_index('plaatsnaam', inplace=True)

    # exclude missing place names
    plaats_rat_df = plaats_rat_df[plaats_rat_df.index != 0]

    return plaats_rat_df


def group_by_month(df, fillna=False):
    """Aggregates rat sightings by month. 
   
    Takes a dataframe with rat sightings from rat monitor export and returns 
    a dataframe with year, month, EEN_OF_MEER, MEER_DAN_VIJF, TOTAAL and date columns.

    Args:
        df: The rat sightings dataframe.
        fillna (bool, False): When True, fill missing month 0 rat sightings.
    """
    df['year'] = df['Datum waarneming'].dt.year
    df['month'] = df['Datum waarneming'].dt.month

    month_rat_df = (
        df.groupby(['year', 'month', 'Aantal ratten'])
        .size()
        .unstack(fill_value=0)
    )

    month_rat_df = month_rat_df.reset_index()
    month_rat_df = month_rat_df.rename_axis(None, axis=1)  # Remove column axis name

    month_rat_df['TOTAAL'] = month_rat_df.EEN_OF_MEER + month_rat_df.MEER_DAN_VIJF

    month_rat_df['year'] = month_rat_df['year'].astype(int)
    month_rat_df['month'] = month_rat_df['month'].astype(int)

    # Create a datetime column
    month_rat_df["date"] = pd.to_datetime(month_rat_df["year"].astype(str) + "-" + month_rat_df["month"].astype(str), format="%Y-%m")

    if fillna:
        # Find the date range of sightings in this df
        date_range = pd.date_range(
            start=month_rat_df['date'].min(),
            end=month_rat_df['date'].max(),
            freq='MS'
        )

        # Fill in missing months with 0
        month_rat_df = month_rat_df.set_index('date').reindex(date_range).fillna(0).reset_index()

    # Sort by date
    month_rat_df = month_rat_df.sort_values("date").reset_index(drop=True)

    return month_rat_df

def translate_data(df):
    """Translates a dataframe with rat sightings into English.
    
    Takes a dataframe with rat sightings and returns a dataframe with english column headers, 
    and english values for number_of_rats and measures_taken_ columns.
    
    Note: grouping does not work on a translated dataframe and translating does not work on a grouped dataframe
    """
    rat_df_english = df.rename(columns={
        'Id': 'Id',
        'Registratie ID': 'Registration_ID',
        'Aantal ratten': 'Number_of_rats',
        'Extra informatie': 'Extra_information',
        'Genomen maatregelen bruin': 'Measures_taken_brown',
        'Genomen maatregelen zwart': 'Measures_taken_black',
        'Genomen maatregelen onbekend': 'Measures_taken_unknown',
        'Datum waarneming': 'Observation_date',
        'Doorlooptijd': 'Duration',
        'Einddatum': 'End_date',
        'Type waarneming': 'Observation_type',
        'Mogelijke oorzaak bruin': 'Possible_cause_brown',
        'Mogelijke oorzaak zwart': 'Possible_cause_black',
        'Mogelijke oorzaak onbekend': 'Possible_cause_unknown',
        'Soort rat': 'Rat_species',
        'Gps': 'Gps',
        'Pc4code': 'PC4_code',
        'Plaatsnaam': 'Place_name',
        'Gemeente': 'Municipality',
        'Status': 'Status',
        'Ontvangen op': 'Received_on',
        'Aangepast op': 'Modified_on'
    })

    # Mapping for Number_of_rats
    number_of_rats_map = {
        'EEN_OF_MEER': 'ONE_OR_MORE',
        'MEER_DAN_VIJF': 'MORE_THAN_FIVE'
    }

    # Mapping for Measures_taken columns
    measures_map = {
        'NIET_CHEMISCH': 'NON_CHEMICAL',
        'PREVENTIE': 'PREVENTION',
        'AFSCHOT': 'CULLING'
        # Add more mappings as needed
    }

    # Translate values in 'Number_of_rats' and 'Measures_taken' columns to English
    rat_df_english['Number_of_rats'] = rat_df_english['Number_of_rats'].replace(number_of_rats_map)
    rat_df_english['Measures_taken_brown'] = rat_df_english['Measures_taken_brown'].replace(measures_map)
    rat_df_english['Measures_taken_black'] = rat_df_english['Measures_taken_black'].replace(measures_map)
    rat_df_english['Measures_taken_unknown'] = rat_df_english['Measures_taken_unknown'].replace(measures_map)

    return rat_df_english