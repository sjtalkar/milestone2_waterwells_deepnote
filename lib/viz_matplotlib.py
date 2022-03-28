import matplotlib.pyplot as plt
import numpy as np

# Function to plot several maps in one figure of the Townships feature per year
def plot_townships_feature_per_year(df, feature_name: str, cmap: str = None, columns: int = 3):
    """
    Function to plot several maps in one figure of the Townships feature per year
    :param df: The GeoPandas DataFrame to plot
    :param feature_name: The feature to plot
    :param cmap: The color map to use
    :param columns: The number of columns to use
    """
    rows = int(np.ceil(len(df["YEAR"].unique()) / columns))
    fig, axs = plt.subplots(rows, columns, figsize=(30,30))
    fig.suptitle(f"San Joaquin Valley Townships {feature_name} per year", fontsize=20)
    for i, year in enumerate(sorted(df["YEAR"].unique())):
        ax = axs[int(i / columns), i % columns]
        df_year = df[df["YEAR"] == year]
        df_year.plot(ax=ax, column=feature_name, edgecolor="black", linewidth=1, cmap=cmap, legend=True)
        ax.set_title(f"{year}", fontsize=20)
    plt.show()

# Function to plot several maps in one figure of the Townships features for a specific year
def plot_townships_features(df, feature_name: str, year: str, cmap: str = None, columns: int = 3):
    """
    Function to plot several maps in one figure of the Townships features for a specific year
    :param df: The GeoPandas DataFrame to plot
    :param feature_name: The feature name to display in the title
    :param year: The year to plot
    :param cmap: The color map to use
    :param columns: The number of columns to use
    """
    rows = int(np.ceil(len(df["YEAR"].unique()) / columns))
    fig, axs = plt.subplots(rows, columns, figsize=(30, 30))
    fig.suptitle(f"San Joaquin Valley Townships {feature_name} in {year}", fontsize=20)
    df_year = df[df["YEAR"] == year]
    features = df_year.columns.columns.tolist() - ["YEAR", "TOWNSHIP", "geometry"]
    for i, feature in enumerate(features):
        ax = axs[int(i / columns), i % columns]

        df_year.plot(ax=ax, column=feature, edgecolor="black", linewidth=1, cmap=cmap, legend=True)
        ax.set_title(f"{feature}", fontsize=20)
    plt.show()