import numpy as np
import pandas as pd
from pandas import DataFrame
from pyod.models.abod import ABOD
from pyod.models.cof import COF
from pyod.models.gmm import GMM
from pyod.models.iforest import IForest
from pyod.models.inne import INNE
from pyod.models.kde import KDE
from pyod.models.knn import KNN
from pyod.models.pca import PCA
from pyod.models.qmcd import QMCD
from pyod.models.sampling import Sampling

from .adapter import Adapter


def moving_average(data, window_size):
    """ Computes moving average using discrete linear convolution of two one dimensional sequences.
        Args:
        -----
                data (pandas.Series): independent variable
                window_size (int): rolling window size

        Returns:
        --------
                ndarray of linear convolution

        References:
        ------------
        [1] Wikipedia, "Convolution", http://en.wikipedia.org/wiki/Convolution.
        [2] API Reference: https://docs.scipy.org/doc/numpy/reference/generated/numpy.convolve.html

        """
    window = np.ones(int(window_size)) / float(window_size)
    return np.convolve(data, window, 'same')
    # left= math.ceil((window_size-1)/2);
    # right = (window_size - 1)-left;

    # return np.convolve( ([data[0]] *left) + data +([data[-1]] * right), window, 'valid')


def moving_average1(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


def low_pass_filter_anomaly(series=None, window_frame: 'int' = 5,
                            sigma: 'float' = 1) -> '[index, y,avg]':
    """
        :param series: (list) list of number to analize
        :param window_frame: (int) rolling window size
        :param sigma:  (float): value for standard deviation
        :rtype: list of anomaly [index, y,avg]
        """

    if series is None:
        series = []
    avg_list = moving_average(series, window_frame).tolist()
    # avg_list = moving_average1(series, window_frame).tolist()
    avg_list = [round(elem, 10) for elem in avg_list]

    # series = series[window_frame-1:]

    residual = np.array(series) - np.array(avg_list)
    # Calculate the variation in the distribution of the residual
    testing_std = pd.Series(residual).rolling(window_frame).std()
    testing_std_as_df = pd.DataFrame(testing_std)
    rolling_std = testing_std_as_df.replace(np.nan,
                                            testing_std_as_df.iloc[window_frame - 1]).round(3).iloc[:, 0].tolist()

    return [(index, y_i, avg_i, rs_i) for index, y_i, avg_i, rs_i in
            zip(list(range(len(series))), series, avg_list, rolling_std)
            if (y_i > avg_i + (sigma * rs_i)) | (
                    y_i < avg_i - (sigma * rs_i))], avg_list, rolling_std


def anomaly_detection(series=None, query: str = None, endpoint: str = None,
                      idSession: str = None, contamination=0.1, max_value=2,
                      min_scores=0.5) :
    if series is None:
        series = []
    if query is not None:
        tidy = Adapter(endpoint, idSession)
        r, sr = tidy.query(query=query)
        m = tidy.to_matrix_number(r, row_name='row', col_name='*')
        series = np.array(m)

    if series.shape[1] == 1:
        series = np.array([[index, v[0]] for index, v in enumerate(series)])
    scores = [
        isolation_forest_anomaly_detection(series=series, contamination=contamination),
        abod_anomaly_detection(series=series, contamination=contamination),
        kde_anomaly_detection(series=series, contamination=contamination),
        cof_anomaly_detection(series=series, contamination=contamination),
        knn_anomaly_detection(series=series, contamination=contamination),
        inne_anomaly_detection(series=series, contamination=contamination),
        qmcd_anomaly_detection(series=series, contamination=contamination),
        sampling_anomaly_detection(series=series, contamination=contamination),
        gmm_anomaly_detection(series=series, contamination=contamination),
        pca_anomaly_detection(series=series, contamination=contamination)]

    num_detector = len(scores)
    result = {}
    for sc in scores:
        for index in sc['index']:
            result[index] = result.get(index, 0) + 1

    result = sorted(result.items(), key=lambda x: x[1], reverse=True)
    result = [r for r in result if r[1] / num_detector >= min_scores]
    return [[r[0], *series[r[0]], r[1] / num_detector] for r in result[:min(len(result), max_value)]]


def isolation_forest_anomaly_detection(series=None, n_estimators=100, max_samples='auto', contamination=0.1,
                                       max_features=1.0, bootstrap=False, n_jobs=1, behaviour='old', random_state=None,
                                       verbose=0) -> 'DataFrame':
    if series is None:
        series = []
    clf = IForest(n_estimators=n_estimators, max_samples=max_samples, contamination=contamination,
                  max_features=max_features, bootstrap=bootstrap, n_jobs=n_jobs,
                  behaviour=behaviour, random_state=random_state, verbose=verbose)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})


def abod_anomaly_detection(series=None, contamination=0.1, n_neighbors=5, method='fast') -> 'DataFrame':
    if series is None:
        series = []
    clf = ABOD(contamination=contamination, n_neighbors=n_neighbors, method=method)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})


def kde_anomaly_detection(series=None, contamination=0.1, bandwidth=1.0, algorithm='auto', leaf_size=30,
                          metric='minkowski', metric_params=None) -> 'DataFrame':
    if series is None:
        series = []
    clf = KDE(contamination=contamination, bandwidth=bandwidth, algorithm=algorithm, leaf_size=leaf_size, metric=metric,
              metric_params=metric_params)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})


def cof_anomaly_detection(series=None, contamination=0.1, n_neighbors=20, method='fast') -> 'DataFrame':
    if series is None:
        series = []
    clf = COF(contamination=contamination, n_neighbors=n_neighbors, method=method)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})


def knn_anomaly_detection(series=None, contamination=0.1, n_neighbors=5, method='largest', radius=1.0,
                          algorithm='auto', leaf_size=30, metric='minkowski', p=2, metric_params=None, n_jobs=1,
                          **kwargs) -> 'DataFrame':
    if series is None:
        series = []
    clf = KNN(contamination=contamination, n_neighbors=n_neighbors, method=method, radius=radius, algorithm=algorithm,
              leaf_size=leaf_size, metric=metric, p=p, metric_params=metric_params, n_jobs=n_jobs, **kwargs)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})


def inne_anomaly_detection(series=None, n_estimators=200, max_samples='auto', contamination=0.1,
                           random_state=None) -> 'DataFrame':
    if series is None:
        series = []
    clf = INNE(n_estimators=n_estimators, max_samples=max_samples, contamination=contamination,
               random_state=random_state)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})


def qmcd_anomaly_detection(series=None, contamination=0.1) -> 'DataFrame':
    if series is None:
        series = []
    clf = QMCD(contamination=contamination)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})


def sampling_anomaly_detection(series=None, contamination=0.1, subset_size=20, metric='minkowski',
                               metric_params=None, random_state=None) -> 'DataFrame':
    if series is None:
        series = []
    clf = Sampling(contamination=contamination, subset_size=subset_size, metric=metric, metric_params=metric_params,
                   random_state=random_state)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})


def gmm_anomaly_detection(series=None, n_components=1, covariance_type='full', tol=0.001, reg_covar=1e-06,
                          max_iter=100, n_init=1, init_params='kmeans', weights_init=None, means_init=None,
                          precisions_init=None, random_state=None, warm_start=False,
                          contamination=0.1) -> 'DataFrame':
    if series is None:
        series = []
    clf = GMM(n_components=n_components, covariance_type=covariance_type, tol=tol, reg_covar=reg_covar,
              max_iter=max_iter, n_init=n_init,
              init_params=init_params, weights_init=weights_init, means_init=means_init,
              precisions_init=precisions_init, random_state=random_state,
              warm_start=warm_start, contamination=contamination)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})


def pca_anomaly_detection(series=None, n_components=None, n_selected_components=None, contamination=0.1,
                          copy=True, whiten=False, svd_solver='auto', tol=0.0, iterated_power='auto', random_state=None,
                          weighted=True, standardization=True) -> DataFrame:
    if series is None:
        series = []
    clf = PCA(n_components=n_components, n_selected_components=n_selected_components, contamination=contamination,
              copy=copy, whiten=whiten,
              svd_solver=svd_solver, tol=tol, iterated_power=iterated_power, random_state=random_state,
              weighted=weighted,
              standardization=standardization)
    clf.fit(series)

    scores = clf.decision_function(series)
    anomaly_score = clf.predict(series)
    return pd.DataFrame({'index': [i for i in range(len(anomaly_score)) if anomaly_score[i] == 1],
                         'x': series[anomaly_score == 1][:, 0], 'value': series[anomaly_score == 1][:, 1],
                         'scores': scores[anomaly_score == 1]})
