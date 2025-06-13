# Imports
import pandas as pd


def merge_data(pc_rat_df, other_dfs, dropna=True):
    """Merges rat sightings and other data on postal code. Returns a merged dataframe. 
    NaN values in rat sightings will become 0. Rows with other NaN values will be removed if dropna is set to True.

    Args:
        pc_rat_df: The rat sightings dataframe.
        other_dfs (list): Other dataframes to merge with the rat sightings.
        dropna (bool, True): When True, drop rows with any NaN values in the other dataframes.
    """
    merged_df = pc_rat_df.copy()
    merged_df.index = merged_df.index.astype(int)

    for other_df in other_dfs:    
        other_df.index = other_df.index.astype(int)
        merged_df = merged_df.join(other_df, on='postcode', how='outer')

    # fill non existens rat sightings with 0
    for rat_col in pc_rat_df.columns:
        merged_df[rat_col] = merged_df[rat_col].fillna(0)

    if dropna:
        merged_df = merged_df.dropna()

    # exclude missing postal codes
    merged_df = merged_df.set_index('postcode')
    merged_df = merged_df[(merged_df.index >= 1000) & (merged_df.index <= 9999)]

    return merged_df


def prepare_clf_data(df, target, include_fearues=None, exclude_features=None, clf_treshold = 1):
    """Prepare features (X) and target (y) for a classification model from a dataframe including both.
    
    Args:
        df: The merged dataframe.
        target (str): The name of target column.
        include_features (str list, None): The names of columns to include as features.
        exclude_features (str list, None): The names of columns NOT to include as features. Only used if include_features is None.
        clf_treshold (int, 1): The treshold for assigning the target class.

    Returns:
        result (X, y): Features dataframe and target series.
    """ 
    if include_fearues:
        X = df[include_fearues]
    elif exclude_features:
        X = df.drop(columns=exclude_features)
    else:
        X = df.drop(columns=target)

    # Create binary target (y): 1 if more rat sightings than threshold, 0 otherwise
    y = df["TOTAAL"].apply(lambda x: 1 if pd.notna(x) and x > clf_treshold else 0)

    return X, y


