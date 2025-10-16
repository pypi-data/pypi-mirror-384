"""Process a dataframe for its ordinal information."""

import warnings

import pandas as pd
from feature_engine.encoding import OrdinalEncoder


def ordinal_process(df: pd.DataFrame, categorical_features: set[str]) -> pd.DataFrame:
    """Process ordinal features."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if not categorical_features:
            return df
        true_categorical_features: list[str] = []
        for categorical_feature in categorical_features:
            if categorical_feature not in df.columns.values:
                continue
            true_categorical_features.append(categorical_feature)
            df[categorical_feature] = df[categorical_feature].astype("category")
        od = OrdinalEncoder(
            missing_values="ignore",
            encoding_method="arbitrary",
            variables=true_categorical_features,  # type: ignore
        )
        df = od.fit_transform(df)
        for categorical_feature in true_categorical_features:
            if categorical_feature not in df.columns.values:
                continue
            try:
                df[categorical_feature] = (
                    df[categorical_feature].fillna(0).astype(int).astype("category")
                )
            except TypeError:
                pass
        return df
