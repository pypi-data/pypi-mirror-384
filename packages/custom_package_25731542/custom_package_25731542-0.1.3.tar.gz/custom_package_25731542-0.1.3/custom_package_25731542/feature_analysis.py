
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_selection import mutual_info_regression

def plot_feature_correlation(df, method='pearson', figsize=(10,8)):
    """Plots correlation heatmap for numeric features."""
    numeric_df = df.select_dtypes(include=[np.number])
    corr = numeric_df.corr(method=method)
    plt.figure(figsize=figsize)
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
    plt.title(f'Feature Correlation Heatmap ({method.title()} Method)', fontsize=14)
    plt.show()

def compute_mutual_information(df, target):
    """Computes mutual information between features and target."""
    X = df.drop(columns=[target])
    y = df[target]
    X_enc = pd.get_dummies(X, drop_first=True)
    mi_scores = mutual_info_regression(X_enc, y, random_state=42)
    mi_series = pd.Series(mi_scores, index=X_enc.columns).sort_values(ascending=False)
    print('Mutual Information Scores:')
    print(mi_series.head(15))
    return mi_series

def remove_outliers_iqr(df, cols):
    """Removes outliers from given columns using IQR method."""
    cleaned_df = df.copy()
    for col in cols:
        if col in cleaned_df.columns:
            Q1 = cleaned_df[col].quantile(0.25)
            Q3 = cleaned_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            before = len(cleaned_df)
            cleaned_df = cleaned_df[(cleaned_df[col] >= lower) & (cleaned_df[col] <= upper)]
            after = len(cleaned_df)
            print(f' {col}: Removed {before - after} outliers (IQR method)')
        else:
            print(f'Column {col} not found in DataFrame.')
    return cleaned_df
