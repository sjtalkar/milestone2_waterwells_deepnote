import numpy as np
import pandas as pd
import geopandas as gpd
import functools
import operator

from typing import List, Tuple

from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import davies_bouldin_score, calinski_harabasz_score, silhouette_score


def kmeans_parameters_search(x: pd.DataFrame, random_seed: int, max_k: int = 10) -> pd.DataFrame:
    """This function estimates the Davies-Boudin, Caldinski-Harabasz, Silhouette scores and sum os square distances
    of different k values for the given dataframe.

    :param x: dataframe to calculate the scores for different k values
    :param random_seed: random seed to be used for the clustering
    :param max_k: maximum number of clusters to be tested
    :return: dataframe with the scores for different k values and metrics
    """
    k_range = range(2, max_k+1)
    db_scores = []
    ch_scores = []
    s_scores = []
    i_scores = []
    for k in k_range:
        cls = KMeans(n_clusters=k, init='k-means++', max_iter=100, n_init=1, random_state=random_seed).fit(x)
        cluster_labels = cls.labels_
        db_scores.append(davies_bouldin_score(x, cluster_labels))
        ch_scores.append(calinski_harabasz_score(x, cluster_labels))
        s_scores.append(silhouette_score(x, cluster_labels))
        i_scores.append(cls.inertia_)
    k_estimation_df = pd.DataFrame(data={
        "k": k_range,
        "davies_bouldin_score": db_scores,
        "calinski_harabasz_score": ch_scores,
        "silhouette_score": s_scores,
        "inertia": i_scores
    })
    return k_estimation_df


def dbscan_parameters_search(x: pd.DataFrame, eps_list: List[float], min_samples_list: List[int],
                             max_n_clusters: int = 5, max_noise: int = 100) -> pd.DataFrame:
    """This function estimates the Davies-Boudin, Caldinski-Harabasz and Silhouette scores of different eps and
    min_samples values for the given dataframe.

    :param x: dataframe to calculate the scores for different parameters values
    :param eps_list: list of values to try for the DBSCAN parameter eps
    :param min_samples_list: list of values to try for the DBSCAN parameter min_samples
    :param max_n_clusters: the maximum number of clusters to accept. eps and min_samples values resulting in more
    clusters than this value will be discarded
    :param max_noise: the maximum amount of clustering noise to accept. eps and min_samples values resulting in more
    noise than this value will be discarded
    :return: dataframe with the scores for different eps and min_samples values and metrics
    """
    dbscan_estimation_df = pd.DataFrame(columns=["eps", "min_samples", "davies_bouldin_score",
                                                 "calinski_harabasz_score", "silhouette_score", "n_clusters"])
    for eps in eps_list:
        db_scores = []
        ch_scores = []
        s_scores = []
        n_clusters = []
        relevant_min_samples = []
        noise = []
        labels = []
        for min_samples in min_samples_list:
            cls = DBSCAN(eps=eps, min_samples=min_samples).fit(x)
            cluster_labels = cls.labels_
            n_clusters_ = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            noise_amount = list(cluster_labels).count(-1)
            # Let's not record the result if
            # - the DBSCAN results in only one cluster. This is not interesting.
            # - the number of clusters is above the threshold
            # - the amount of noise is above the threshold
            if 1 < n_clusters_ <= max_n_clusters and noise_amount <= max_noise:
                relevant_min_samples.append(min_samples)
                db_scores.append(davies_bouldin_score(x, cluster_labels))
                ch_scores.append(calinski_harabasz_score(x, cluster_labels))
                s_scores.append(silhouette_score(x, cluster_labels))
                noise.append(noise_amount)
                n_clusters.append(n_clusters_)
                labels.append(cluster_labels)
        min_samples_df = pd.DataFrame(data={
            "eps": eps,
            "min_samples": relevant_min_samples,
            "davies_bouldin_score": db_scores,
            "calinski_harabasz_score": ch_scores,
            "silhouette_score": s_scores,
            "noise": noise,
            "n_clusters": n_clusters,
            "labels": labels
        })
        # If there was clustering results with more than 1 cluster we add the results to the list
        if min_samples_df.shape[0] > 0:
            dbscan_estimation_df = pd.concat([dbscan_estimation_df, min_samples_df], axis=0)
    dbscan_estimation_df.reset_index(inplace=True, drop=True)
    return dbscan_estimation_df


def hierarchical_parameters_search(x: pd.DataFrame, n_clusters_list: List[int], affinity_list: List[str],
                                   linkage_list: List[str]) -> pd.DataFrame:
    """This function estimates the Davies-Boudin, Caldinski-Harabasz and Silhouette scores of different affinity and
    linkage values for the given dataframe.

    :param x: dataframe to calculate the scores for different parameters values
    :param n_clusters_list: the list of number of clusters to compute using hierarchical clustering
    :param affinity_list: list of values to try for the AgglomerativeClustering parameter affinity
    :param linkage_list: list of values to try for the AgglomerativeClustering parameter linkage
    :return: dataframe with the scores for different affinity and linkage values and metrics
    """
    hierarchical_estimation_df = pd.DataFrame(columns=["affinity", "linkage", "n_clusters", "davies_bouldin_score",
                                                       "calinski_harabasz_score", "silhouette_score"])
    for n_clusters in n_clusters_list:
        for affinity in affinity_list:
            db_scores = []
            ch_scores = []
            s_scores = []
            n_clusters_ = []
            linkage_ = []
            labels = []
            for linkage in linkage_list:
                #  If linkage is “ward”, only “euclidean” is accepted.
                if not (linkage == "ward" and affinity != "euclidean"):
                    cls = AgglomerativeClustering(n_clusters=n_clusters, affinity=affinity, linkage=linkage).fit(x)
                    cluster_labels = cls.labels_
                    linkage_.append(linkage)
                    db_scores.append(davies_bouldin_score(x, cluster_labels))
                    ch_scores.append(calinski_harabasz_score(x, cluster_labels))
                    s_scores.append(silhouette_score(x, cluster_labels))
                    n_clusters_.append(n_clusters)
                    labels.append(cluster_labels)
            linkage_df = pd.DataFrame(data={
                "affinity": affinity,
                "linkage": linkage_,
                "n_clusters": n_clusters_,
                "davies_bouldin_score": db_scores,
                "calinski_harabasz_score": ch_scores,
                "silhouette_score": s_scores,
                "labels": labels
            })
            hierarchical_estimation_df = pd.concat([hierarchical_estimation_df, linkage_df], axis=0)
    hierarchical_estimation_df.reset_index(inplace=True, drop=True)
    return hierarchical_estimation_df


def compute_kmeans_clusters_and_top_features(x: pd.DataFrame, k: int, random_state: int, nb_features: int = 10) -> \
        Tuple[pd.DataFrame, List[tuple]]:
    """This function clusters the data and extracts for each cluster the most predominant nb_features features names and
    the cluster center value on that feature. The predominant features are defined as the top nb_features with the
    highest value for each cluster centroid in the feature vector space. The resulting dataframe contains only the
    predominant features.

    :param x: dataframe to be clustered
    :param k: number of clusters
    :param random_state: random state to be used for the clustering
    :param nb_features: number of features to be extracted
    :return: a Tuple containing, the dataframe filtered on the most predominant features and with the cluster labels,
    and a sorted list of the most predominant features of the two clusters
    """
    result_df = x.copy()
    cls = KMeans(n_clusters=k, init='k-means++', max_iter=100, n_init=1, random_state=random_state).fit(x)
    predominant_features = []
    for centroid in cls.cluster_centers_:
        names = list(result_df.columns[np.argsort(centroid)[::-1][:nb_features]])
        centers = np.sort(centroid)[::-1][:nb_features]
        predominant_features.append(list(zip(names, centers)))
    result_df["cluster"] = cls.labels_
    result_df["cluster"] = result_df["cluster"].astype(str)
    all_predominant_features = dict(sorted(functools.reduce(operator.iconcat, predominant_features, []),
                                           key=lambda feature: feature[1]))
    sorted_feature_names = list(all_predominant_features.keys())[::-1]
    result_df = result_df[sorted_feature_names + ["cluster"]]
    return result_df, sorted_feature_names


def get_most_frequent_cluster(x: pd.DataFrame, sjv_township_range_df: pd.DataFrame) -> gpd.GeoDataFrame:
    """This function returns the most frequent cluster for each Township-Range togetheter with the Township-Range
    geospatial information.

    :param x: dataframe with the cluster labels
    :param sjv_township_range_df: dataframe with the Township-Range geospatial information
    :return: dataframe with the Township-Range geospatial information and the most frequent cluster for each
    """
    result_df = x.reset_index()[["TOWNSHIP_RANGE", "cluster"]].groupby("TOWNSHIP_RANGE")["cluster"].agg(
        lambda i: i.value_counts().index[0]).reset_index()
    return pd.merge(sjv_township_range_df, result_df, how="left", on=["TOWNSHIP_RANGE", ])


def get_most_frequent_cluster_for_all_parameters(x: pd.DataFrame, search_result_df: pd.DataFrame,
                                                 parameters: List[str], sjv_township_range_df: pd.DataFrame,
                                                 reverse_cluster: bool = False) -> gpd.GeoDataFrame:
    """This function returns the most frequent cluster for each Township-Range togetheter with the Township-Range
    geospatial information.

    :param x: dataframe with the data which were clustered
    :param search_result_df: dataframe with the parameters values and resulting clusters
    :param parameters: list of parameters used during the clustering
    :param sjv_township_range_df: dataframe with the Township-Range geospatial information
    :param reverse_cluster: if True, the cluster labels are reversed. This is used to show the same cluster labels
    from one algorithm to the other
    :return: a dataframe with, for each of the parameter combination, the Township-Range most frequent cluster and
    their geospatial information
    """
    result_df = gpd.GeoDataFrame()
    for index, cluster in search_result_df.iterrows():
        # Get the most frequent labels for each Township-Range for that specific set of clustering parameters
        parameter_df = x.copy()
        if reverse_cluster:
            parameter_df["cluster"] = ["0" if x == 1 else "1" for x in cluster["labels"]]
        else:
            parameter_df["cluster"] = cluster["labels"]
            parameter_df["cluster"] = parameter_df["cluster"].astype(str)
        parameter_df = get_most_frequent_cluster(parameter_df, sjv_township_range_df)
        paramters_title = ""
        for parameter in parameters:
            paramters_title += f"{parameter}={cluster[parameter]}, "
        parameter_df["parameters"] = paramters_title
        result_df = pd.concat([result_df, parameter_df], axis=0)
    return result_df


def compute_hier_clusters_and_top_features(x: pd.DataFrame, n_clusters: int, affinity: str, linkage: str,
                                           nb_features: int = 10, reverse_cluster: bool = False) \
        -> Tuple[pd.DataFrame, List[tuple]]:
    """This function clusters the data and extracts for each cluster the most predominant nb_features features names and
    the cluster center value on that feature. The predominant features are defined as the top nb_features with the
    highest value for each cluster centroid in the feature vector space. The resulting dataframe contains only the
    predominant features.

    :param x: dataframe to be clustered
    :param n_clusters: the number of clusters to compute using hierarchical clustering
    :param affinity: affinity to be used for the clustering
    :param linkage: linkage to be used for the clustering
    :param nb_features: number of features to be extracted
    :param reverse_cluster: if True, the cluster labels are reversed. This is used to show the same cluster labels
    from one algorithm to the other
    :return: a Tuple containing, the dataframe filtered on the most predominant features and with the cluster labels,
    and a sorted list of the most predominant features of the two clusters
    """
    result_df = x.copy()
    cls = AgglomerativeClustering(n_clusters=n_clusters, affinity=affinity, linkage=linkage,
                                  compute_distances=True).fit(x)
    if reverse_cluster:
        result_df["cluster"] = ["0" if x == 1 else "1" for x in cls.labels_]
    else:
        result_df["cluster"] = cls.labels_
        result_df["cluster"] = result_df["cluster"].astype(str)
    centroids_df = result_df.groupby("cluster").mean().reset_index(drop=True)
    predominant_features = []
    for index, centroid in centroids_df.iterrows():
        centroid_ = list(centroid)
        names = list(centroids_df.columns[np.argsort(centroid_)[::-1][:nb_features]])
        centers = np.sort(centroid_)[::-1][:nb_features]
        predominant_features.append(list(zip(names, centers)))
    all_predominant_features = dict(sorted(functools.reduce(operator.iconcat, predominant_features, []),
                                           key=lambda feature: feature[1]))
    sorted_feature_names = list(all_predominant_features.keys())[::-1]
    result_df = result_df[sorted_feature_names + ["cluster"]]
    return result_df, sorted_feature_names

def get_tr_with_highest_values(df: pd.DataFrame, sjv_township_range_df: gpd.GeoDataFrame, top: int, feature: str,
                               agg: str) -> gpd.GeoDataFrame:
    """This function returns all the Township-Ranges together with the center points for the top Township-Ranges having
    the highest value for the feature

    :param df: dataframe with the data which were clustered
    :param sjv_township_range_df: dataframe with the Township-Range geospatial information
    :param top: number of top Township-Ranges to be returned
    :param feature: feature for which to get the top Township-Ranges
    :param agg: aggregation function to be used to get the top Township-Ranges
    """
    df = df[[feature]]
    df.reset_index(inplace=True)
    # Get the toop Township-Ranges with the highest value for the feature
    df = df.groupby("TOWNSHIP_RANGE")[feature].agg(agg)
    df.sort_values(ascending=False, inplace=True)
    df = df.iloc[0:top]
    # Get these Township-Ranges geospatial information by doing a left merge with the geospatial information
    # of all Township-Ranges
    df = gpd.GeoDataFrame(pd.merge(df.reset_index(), sjv_township_range_df, how="left", on=["TOWNSHIP_RANGE", ]))
    # Get the centroids for these Township-Ranges with the top values
    # Switch temporarily to a coordinate systems based on linear units (meters) to compute the centroids
    df.to_crs(epsg=3347, inplace=True)
    df["points"] = df.centroid
    # Revert back to WGS84, or simple lat/lon cartesian projection for display
    df.to_crs(epsg=4326, inplace=True)
    df["points"] = df["points"].to_crs(epsg=4326)
    df = df[["TOWNSHIP_RANGE", "points"]]
    # Add the points of the top Township-Ranges with the highest value for the feature to all the TOwnship-Ranges
    # geospatial DataFrame
    df = pd.merge(sjv_township_range_df, df, how="left", on=["TOWNSHIP_RANGE"])
    return df

def get_tr_with_most_wells(df: pd.DataFrame, sjv_township_range_df: gpd.GeoDataFrame, top: int = 30) -> gpd.GeoDataFrame:
    """This function returns the Township-Ranges with the biggest total amount of wells being over the entire period.

    :param df: dataframme with the Township-Range wells information
    :param sjv_township_range_df: dataframe with the Township-Range geospatial information
    :param top: number of Township-Ranges to be returned
    """
    tr_with_most_wells_df = df.copy()
    tr_with_most_wells_df["WELL_TOTAL"] = tr_with_most_wells_df["WELL_COUNT_AGRICULTURE"] + \
                                          tr_with_most_wells_df["WELL_COUNT_DOMESTIC"] + \
                                          tr_with_most_wells_df["WELL_COUNT_INDUSTRIAL"] +\
                                          tr_with_most_wells_df["WELL_COUNT_PUBLIC"]
    return get_tr_with_highest_values(tr_with_most_wells_df, sjv_township_range_df, top, "WELL_TOTAL", "sum")

def get_tr_with_deepest_wells(df: pd.DataFrame, sjv_township_range_df: gpd.GeoDataFrame, top: int = 30) -> gpd.GeoDataFrame:
    """This function returns the Township-Ranges with the deepest average GSE_GWE well depth over the entire period.

    :param df: dataframme with the Township-Range wells information
    :param sjv_township_range_df: dataframe with the Township-Range geospatial information
    :param top: number of Township-Ranges to be returned
    """
    tr_with_deepest_wells = df.copy()
    return get_tr_with_highest_values(tr_with_deepest_wells[["GSE_GWE"]], sjv_township_range_df, top, "GSE_GWE", "mean")

def get_tr_with_most_wells(df: pd.DataFrame, sjv_township_range_df: gpd.GeoDataFrame, top: int = 30) -> gpd.GeoDataFrame:
    """This function returns the Township-Ranges with the biggest total amount of wells being drilled over the entire
    period.

    :param df: dataframme with the Township-Range wells information
    :param sjv_township_range_df: dataframe with the Township-Range geospatial information
    :param top: number of Township-Ranges to be returned
    """
    tr_with_most_wells_df = df.copy()
    tr_with_most_wells_df["WELL_TOTAL"] = tr_with_most_wells_df["WELL_COUNT_AGRICULTURE"] + \
                                          tr_with_most_wells_df["WELL_COUNT_DOMESTIC"] + \
                                          tr_with_most_wells_df["WELL_COUNT_INDUSTRIAL"] + \
                                          tr_with_most_wells_df["WELL_COUNT_PUBLIC"]
    return get_tr_with_highest_values(tr_with_most_wells_df, sjv_township_range_df, top, "WELL_TOTAL", "sum")

def get_tr_with_most_shortages(df: pd.DataFrame, sjv_township_range_df: gpd.GeoDataFrame, top: int = 30) -> gpd.GeoDataFrame:
    """This function returns the Township-Ranges with the biggest total amount of wel shortages reported over the
    entire period.

    :param df: dataframme with the Township-Range wells information
    :param sjv_township_range_df: dataframe with the Township-Range geospatial information
    :param top: number of Township-Ranges to be returned
    """
    tr_with_most_shortages_df = df.copy()
    return get_tr_with_highest_values(tr_with_most_shortages_df[["SHORTAGE_COUNT"]], sjv_township_range_df, top,
                                      "SHORTAGE_COUNT", "sum")
