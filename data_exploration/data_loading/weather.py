# Imports
import pandas as pd

def load_cnt_data(path, min_date=None, max_date=None):
    """Loads 'centraal nederlands temperatuur' (CNT) data into a pandas dataframe. 
   
    Takes a file path and keyword arguments, loads data into a dataframa and pre-processes the data.
    Returns a dataframe with monthly average temperatures for the Netherlands. 

    Args:
        path (str): The file path to load.
        min_date (int, None): When not None, only load data starting from min_date.
        max_date (int, None): When not None, only load data up until max_date.
    """
    col_names = ["year"] + [i for i in range(1, 13)]
    cnt_df = pd.read_csv(path, delim_whitespace=True, skiprows=8, names=col_names)

    # Melt to long format: each row is a year, month, value
    temp_df = cnt_df.melt(id_vars="year", var_name="month", value_name="mean_temperature")

    # Create a datetime column
    temp_df["date"] = pd.to_datetime(temp_df["year"].astype(str) + "-" + temp_df["month"].astype(str), format="%Y-%m")

    # Sort by date
    temp_df = temp_df.sort_values("date").reset_index(drop=True)

    # If minimum or maximum date specified, filter by date
    if min_date:
        temp_df = temp_df[temp_df["date"] >= min_date]
    if max_date:
        temp_df = temp_df[temp_df["date"] <= max_date]

    return temp_df