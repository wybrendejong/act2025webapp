import pandas as pd
import geopandas as gpd
import numpy as np

from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import train_test_split, GridSearchCV

from imblearn.ensemble import BalancedRandomForestClassifier


features = ['TOTAAL_lag1', 'TOTAAL_lag2', 'rolling_mean', 'rolling_max', 'rolling_std', 'spatial_lag_prev']


def train_classifier(gdf, clf_treshold=0):
    """
    Trains a classifier on a spatio-temporal GeoDataFrame and return the fitted model.

    Splits the GeoDataFrame into training and testing data to train and evaluate the model.
    After evaluation it retrains the model on all data for increased performance
    
    Args:
        gdf (GeoDataFrame): Spatio-temporal GeoDataFrame to be used for training and testing.
        clf_treshold (int default 0): Treshold to use for splitting data in binary classes.
        
    Returns:
        BalancedRandomForestClassifier: Fitted balanced random forest model.
    """
    # Create binary target (y): 1 if more rat sightings than threshold, 0 otherwise
    y = gdf['TOTAAL'].apply(lambda x: 1 if pd.notna(x) and x > clf_treshold else 0)
    X = gdf[features]

    # Split into train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=16)

    # Train Balanced Random Forest
    brf = BalancedRandomForestClassifier(random_state=42, n_estimators=180, max_depth=4, min_samples_split=4, n_jobs=-1)
    brf.fit(X_train, y_train)

    # Predict and evaluate
    y_pred = (brf.predict_proba(X_test)[:, 1] > 0.8).astype(int)

    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    # After evaluation retrain the model on all data, for better performance
    brf.fit(X, y)

    return brf


def predict_probabilities(gdf, clf):
    """
    Predicts probabilities for the upcoming month for all postcodes using a trained classifier.
    
    Args:
        gdf (GeoDataFrame): Spatio-temporal GeoDataFrame with all features up to the latest month.
        clf: Trained classifier with predict_proba method.
        
    Returns:
        GeoDataFrame: DataFrame for the next month with predicted probabilities.
    """
    # Determine the next month
    last_month = gdf['month'].max()
    next_month = (last_month + pd.offsets.MonthBegin(1))
    
    # Create a DataFrame for all postcodes for the next month
    postcodes = gdf['postcode'].unique()
    next_month_df = pd.DataFrame({'postcode': postcodes})
    next_month_df['month'] = next_month

    # For each postcode, copy the latest available feature values
    latest_features = (
        gdf.sort_values(['postcode', 'month'])
        .groupby('postcode')
        .tail(1)
        .set_index('postcode')
    )

    # Merge features into next_month_df
    for col in features:
        next_month_df[col] = latest_features.loc[next_month_df['postcode'], col].values

    # Add geometry   
    next_month_df['geometry'] = latest_features.loc[next_month_df['postcode'], 'geometry'].values

    # Predict probabilities
    X_pred = next_month_df[features]
    next_month_df['prob_positive'] = clf.predict_proba(X_pred)[:, 1]

    # GeoDataFrame
    next_month_gdf = gpd.GeoDataFrame(next_month_df, geometry='geometry')
    return next_month_gdf