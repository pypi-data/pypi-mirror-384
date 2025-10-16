import pandas as pd
from tqdm import tqdm
import rocks
import numpy as np

from asteroid_spinprops.ssolib.dataprep import filter_sso_data
from asteroid_spinprops.ssolib.modelfit import get_fit_params, make_residuals_df
from asteroid_spinprops.ssolib.periodest import (
    get_period_estimate,
    perform_residual_resampling,
)
from asteroid_spinprops.ssolib.utils import read_clean_data


def process_single_sso(name: str, path_args: list, filtering=True) -> tuple | None:
    """
    Process a single Solar System Object to extract period estimation metrics.

    Parameters
    ----------
    name : str
        Name of the SSO to be processed.
    path_args : list
        Arguments required to locate and load SSO data,
        paths to parquet files and ephemeris cache.

    Returns
    -------
    tuple or None
        A tuple containing:
            - signal (tuple): Periodogram signal information (power, frequency and the 5 highest peaks).
            - window (tuple): Window function data (power, frequency and the 5 highest peaks).
            - noise (float): Signal noise level.
            - name (str): SSO name.
            - Nbs (int): Bootstrap score.
            - npts (int): Number of data points.
        Returns None if processing fails.
    """
    try:
        if filtering is True:
            data, _ = filter_sso_data(name, *path_args)
        else:
            data = read_clean_data(name, *path_args, return_rejects=False)
        mparams = get_fit_params(data=data, flavor="SHG1G2")
        resid_df = make_residuals_df(data, mparams)
        signal, window, noise = get_period_estimate(resid_df)
        _, Nbs = perform_residual_resampling(resid_df=resid_df)
        npts = len(data["Phase"].values[0])
        return signal, window, noise, name, Nbs, npts
    except Exception:
        return None


def load_light_curve_data(file_path: str) -> pd.DataFrame:
    """
    Load a LCDB CSV file and return a dataframe containing objects periods.

    Parameters
    ----------
    file_path : str
        Path to the CSV file containing light curve details.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing cleaned and filtered light curve data,
        with the 'Period' column converted to float and initial metadata rows skipped.
    """
    lc = pd.read_csv(file_path, skiprows=range(16))
    lc = lc[5:]
    lc["Period"] = lc["Period"].astype(float)
    return lc


def fill_missing_periods_and_powers(periods, powers):
    """
    Replace incomplete period or power arrays with NaN-filled placeholders.

    Parameters
    ----------
    periods : list of array-like
        List of period arrays estimated for each SSO.
    powers : list of array-like
        List of power arrays associated with each estimated period.

    Returns
    -------
    None
        The input lists are modified in place.
    """
    filler = np.full(5, np.nan)
    for i in range(len(periods)):
        if len(periods[i]) < 5:
            periods[i] = filler
        if len(powers[i]) < 5:
            powers[i] = filler


def collect_rocks_periods(names: list[str]) -> list[np.ndarray]:
    """
    Retrieve known periods from the SsODNet service for a list of SSOs.

    Parameters
    ----------
    names : list of str
        List of SSO names to query.

    Returns
    -------
    list of np.ndarray
        Each element is an array of known periods for the corresponding SSO & method.
        If no valid periods are found, returns two arrays with a single NaN.
    """
    periods = []
    methods = []
    for sso in tqdm(names, desc="Querying rocks"):
        r = rocks.Rock(sso, datacloud="spins")
        try:
            values = r.spins["period"].values.astype(np.float64)
            method = r.spins["method"].values

            if (values == [None] * len(values)).all():
                periods.append(np.array([np.nan]))
                methods.append(np.array([np.nan]))
            else:
                periods.append(values[~np.isnan(values)])
                methods.append(method[~np.isnan(values)])
        except Exception:
            periods.append(np.array([np.nan]))
            methods.append(np.array([np.nan]))
    return periods, methods


def match_true_period(Ps, Procks, Pmethods):
    """
    Match the closest known period from SsODNet to each estimated period.

    Parameters
    ----------
    Ps : array-like
        Array of estimated periods
    Procks : list of np.ndarray
        List of known periods from Rocks for each SSO.

    Returns
    -------
    list
        The closest known period from Rocks for each estimate & method.
        Returns NaN if no valid match exists.
    """
    matched = []
    method = []
    for p_est, p_true, m_true in zip(Ps, Procks, Pmethods):
        if isinstance(p_true, float) or len(p_true) == 0 or np.isnan(p_true).all():
            matched.append(np.nan)
            method.append(np.nan)
        else:
            diffs = np.abs(p_est - p_true[:, None]) / p_true[:, None]
            min_idx = np.argmin(diffs, axis=0)
            matched.append(p_true[min_idx[0]])
            method.append(m_true[min_idx[0]])
    return matched, method


def filter_sso_name(name, path_args):
    clean_data, rejects = filter_sso_data(name, *path_args, lc_filtering=False)
    return name, clean_data, rejects
