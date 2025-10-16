import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
from asteroid_spinprops.ssolib.modelfit import (
    get_fit_params,
    get_residuals,
)

import asteroid_spinprops.ssolib.utils as utils


def errorbar_filtering(data, mlimit):
    """
    Filter out data points with large photometric uncertainties.

    Parameters
    -----------
    data : pd.DataFrame
        A single-row DataFrame where each column contains an array of values
        for a solar system object.
    mlimit : float
        Threshold value to filter out points with uncertainties greater than mlimit / 2.

    Returns
    -------
    data : pd.DataFrame
        Filtered DataFrame
    rejects : pd.DataFrame
        DataFrame containing the rejected measurements
    """
    errorbar_condition = data["csigmapsf"].values[0] <= mlimit / 2
    rejects = data.copy()

    for c in data.columns:
        if c not in ["index", "kast", "name"]:
            rejects.at[0, c] = data[c].values[0][~errorbar_condition]
            data.at[0, c] = data[c].values[0][errorbar_condition]

    return data, rejects


def projection_filtering(data):
    """
    Filters out photometric outliers in reduced magnitude space per filter using a 3 sigma criterion.

    Parameters
    -----------
    data : pd.DataFrame
        A single-row DataFrame where each column contains an array of values.
    Returns
    --------
    data : pd.DataFrame
        Filtered DataFrame
    rejects : pd.DataFrame
        DataFrame containing the rejected measurements
    """
    rejects = data.copy()
    valid_indices = []

    for f in np.unique(data["cfid"].values[0]):
        filter_mask = np.array(data["cfid"].values[0]) == f

        mean_val = np.mean(data["cmred"].values[0][filter_mask])
        std_val = np.std(data["cmred"].values[0][filter_mask])

        project_condition = (
            filter_mask
            & (data["cmred"].values[0] > mean_val - 3 * std_val)
            & (data["cmred"].values[0] < mean_val + 3 * std_val)
        )

        valid_indices.append(np.where(project_condition)[0])

    valid_indices = np.sort(
        np.concatenate([valid_indices[n] for n in range(len(valid_indices))])
    )

    dummy = np.ones(data["cfid"].values[0].shape, dtype=bool)
    dummy[valid_indices] = False

    for c in data.columns:
        if c not in ["index", "kast", "name"]:
            rejects.at[0, c] = data[c].values[0][dummy]
            data.at[0, c] = data[c].values[0][valid_indices]

    return data, rejects


def iterative_filtering(data, max_iter=10):
    """
    Iteratively removes outliers based on residuals from fitting the SHG1G2 mdoel until convergence.

    Parameters
    -----------
    data : pd.DataFrame
        A single-row DataFrame where each column contains an array of values.

    max_iter : int
        Maximum number of filtering iterations (default is 10).

    Returns
    --------
    data : pd.DataFrame
        Filtered DataFrame

    rejects : pd.DataFrame
        DataFrame containing the rejected measurements
    """
    rejects = data.copy()

    mask = np.ones_like(data["cfid"].values[0], dtype=bool)
    inloop_quants = {}
    reject_quants = {}

    for c in data.columns:
        if c not in ["index", "kast", "name"]:
            inloop_quants[c] = data[c].values[0]
            reject_quants[c] = np.array([])

    for niter in range(max_iter):
        prev_len = len(inloop_quants["cfid"])

        for k in inloop_quants.keys():
            reject_quants[k] = np.append(reject_quants[k], inloop_quants[k][~mask])
            inloop_quants[k] = inloop_quants[k][mask]

        mparams = get_fit_params(pd.DataFrame([inloop_quants]), "SHG1G2")
        try:
            residuals = get_residuals(pd.DataFrame([inloop_quants]), mparams)
        except KeyError:
            break
        mask = np.abs(residuals) < 3 * np.std(residuals)

        if prev_len == len(inloop_quants["Phase"][mask]):
            break

        for c in data.columns:
            if c not in ["index", "kast", "name"]:
                data.at[0, c] = inloop_quants[c]
                rejects.at[0, c] = reject_quants[c]
    return data, rejects


def lightcurve_filtering(data, window=10, maglim=0.6):
    """
    Filters out lightcurve points that deviate from the median by more than given mag limitation within time bins.

    Parameters
    ----------
    data : pd.DataFrame
        Single-row DataFrame
    window : float
        Time bin size (default is 10 days).
    maglim : float
        Magnitude deviation threshold from the median (default is 0.4 mag).

    Returns
    -------
    data : pd.DataFrame
        Filtered data
    rejects : pd.DataFrame
        DataFrame containing the rejected measurements
    """
    dummym, dummyt, dummyf, dummyi = [], [], [], []

    dates = data["cjd"].values[0]
    magnitudes = data["cmred"].values[0]
    filters = data["cfid"].values[0]
    indices = np.array([ind for ind in range(len(data["cfid"].values[0]))])

    ufilters = np.unique(filters)

    mag_pfilt = {}

    date0 = dates.min()
    date0_plus_step = date0 + window
    # TODO: Use np.digitize instead of this
    while date0 < dates.max():
        prev_ind = np.where(dates == utils.find_nearest(dates, date0))[0][0]
        plus_ten_index = np.where(dates == utils.find_nearest(dates, date0_plus_step))[
            0
        ][0]

        dummym.append(magnitudes[prev_ind:plus_ten_index])
        dummyt.append(dates[prev_ind:plus_ten_index])
        dummyf.append(filters[prev_ind:plus_ten_index])
        dummyi.append(indices[prev_ind:plus_ten_index])

        date0 = dates[plus_ten_index]
        date0_plus_step = date0_plus_step + window

    dummym.append(magnitudes[plus_ten_index:])
    dummyt.append(dates[plus_ten_index:])
    dummyf.append(filters[plus_ten_index:])
    dummyi.append(indices[plus_ten_index:])

    mag_binned, _, filt_binned, ind_binned = (
        np.asarray(dummym, dtype=object),
        np.asarray(dummyt, dtype=object),
        np.asarray(dummyf, dtype=object),
        np.asarray(dummyi, dtype=object),
    )

    for f in ufilters:
        dummymain, dummym, dummyt, dummydiff, dummyi = [], [], [], [], []
        for n in range(len(mag_binned)):
            fcond = filt_binned[n] == f
            dummymain.append(mag_binned[n][fcond])
            dummym.append(np.median(mag_binned[n][fcond]))
            dummydiff.append(
                np.max(mag_binned[n][fcond], initial=0)
                - np.min(mag_binned[n][fcond], initial=1e3)
            )
            dummyi.append(ind_binned[n][fcond])

        dummydiff = np.array(dummydiff)
        dummydiff[dummydiff == np.float64(-1000.0)] = 0

        mag_pfilt["medimag_{}".format(f)] = dummym
        mag_pfilt["mxmnmag_{}".format(f)] = dummydiff
        mag_pfilt["mag_{}".format(f)] = dummymain
        mag_pfilt["ind_{}".format(f)] = dummyi

    valid_indices = []
    reject_indices = []

    rejects = data.copy()

    for f in ufilters:
        for n in range(len(mag_binned)):
            bin_cond = (
                mag_pfilt["mag_{}".format(f)][n]
                > mag_pfilt["medimag_{}".format(f)][n] + maglim
            ) | (
                mag_pfilt["mag_{}".format(f)][n]
                < mag_pfilt["medimag_{}".format(f)][n] - maglim
            )
            valid_indices.append(mag_pfilt["ind_{}".format(f)][n][~bin_cond])
            reject_indices.append(mag_pfilt["ind_{}".format(f)][n][bin_cond])

    valid_indices = np.array(utils.flatten_list(valid_indices), dtype=int)
    reject_indices = np.array(utils.flatten_list(reject_indices), dtype=int)

    for c in data.columns:
        if c not in ["index", "kast", "name"]:
            rejects.at[0, c] = data[c].values[0][reject_indices]
            data.at[0, c] = data[c].values[0][valid_indices]

    data = utils.sort_by_cjd(data)

    return data, rejects


def plot_filtering(
    clean_data, rejects, lc_filtering=False, iter_filtering=True, xaxis="Phase"
):
    if xaxis == "Date":
        coll = "cjd"
    if xaxis == "Phase":
        coll = "Phase"
    errorbar_rejects, projection_rejects, iterative_rejects, lightcurve_rejects = (
        rejects[0],
        rejects[1],
        rejects[2],
        rejects[3],
    )

    fig, ax = plt.subplots(2, 2, figsize=(12, 6))

    filter_names = ["ZTF g", "ZTF r", "ATLAS orange", "ATLAS cyan"]

    for i, f in enumerate(np.unique(clean_data["cfid"].values[0])):
        if f in [1, 2]:
            row = 0
        if f in [3, 4]:
            row = 1

        if i % 2 != 0:
            col = 1
        else:
            col = 0

        filter_mask = np.array(clean_data["cfid"].values[0]) == f
        filter_mask_r1 = np.array(errorbar_rejects["cfid"].values[0]) == f
        filter_mask_r2 = np.array(projection_rejects["cfid"].values[0]) == f

        if iter_filtering is True:
            filter_mask_r3 = np.array(iterative_rejects["cfid"].values[0]) == f
        else:
            filter_mask_r3 = None

        if lc_filtering is True:
            filter_mask_r4 = np.array(lightcurve_rejects["cfid"].values[0]) == f
        else:
            filter_mask_r4 = None

        ax[row, col].errorbar(
            x=clean_data[coll].values[0][filter_mask],
            y=clean_data["cmred"].values[0][filter_mask],
            yerr=clean_data["csigmapsf"].values[0][filter_mask],
            fmt=".",
            capsize=2,
            ms=5,
            elinewidth=1,
            label="Valid points",
        )

        ax[row, col].errorbar(
            x=errorbar_rejects[coll].values[0][filter_mask_r1],
            y=errorbar_rejects["cmred"].values[0][filter_mask_r1],
            yerr=errorbar_rejects["csigmapsf"].values[0][filter_mask_r1],
            fmt="x",
            capsize=2,
            ms=15,
            elinewidth=1,
            c="tab:red",
            label=r"$\delta m > 3\sigma_{LCDB}$",
        )

        ax[row, col].errorbar(
            x=projection_rejects[coll].values[0][filter_mask_r2],
            y=projection_rejects["cmred"].values[0][filter_mask_r2],
            yerr=projection_rejects["csigmapsf"].values[0][filter_mask_r2],
            fmt="+",
            capsize=2,
            ms=15,
            elinewidth=1,
            c="tab:green",
            label=r"$\substack{m > \bar{m} + 3\sigma_m \\ m < \bar{m} - 3\sigma_m}$",
        )
        if iter_filtering is True:
            ax[row, col].errorbar(
                x=iterative_rejects[coll].values[0][filter_mask_r3],
                y=iterative_rejects["cmred"].values[0][filter_mask_r3],
                yerr=iterative_rejects["csigmapsf"].values[0][filter_mask_r3],
                fmt=">",
                capsize=2,
                ms=7,
                elinewidth=1,
                label=r"sHG$_1$G$_2$ filtering",
            )
        if lc_filtering is True:
            ax[row, col].errorbar(
                x=lightcurve_rejects[coll].values[0][filter_mask_r4],
                y=lightcurve_rejects["cmred"].values[0][filter_mask_r4],
                yerr=lightcurve_rejects["csigmapsf"].values[0][filter_mask_r4],
                fmt="P",
                capsize=2,
                ms=7,
                elinewidth=1,
                c="black",
                label="Lightcurve",
            )

        ax[row, col].invert_yaxis()
        ax[row, col].text(
            0.05,
            0.05,
            filter_names[i],
            transform=ax[row, col].transAxes,
            va="bottom",
            ha="left",
            bbox=dict(
                facecolor="white",
                edgecolor="black",
                boxstyle="round,pad=0.3",
                alpha=0.8,
            ),
        )
    if xaxis == "Phase":
        ax[1, 0].set_xlabel("Phase / deg")
        ax[1, 1].set_xlabel("Phase / deg")
    if xaxis == "Date":
        ax[1, 0].set_xlabel("JD")
        ax[1, 1].set_xlabel("JD")
    ax[0, 0].set_ylabel("Reduced magnitude")
    ax[1, 0].set_ylabel("Reduced magnitude")

    ax[0, 1].legend(loc="upper right")


def filter_sso_data(
    sso_name,
    path_to_data,
    pqdict,
    compute_ephemerides=False,
    ephem_path=None,
    mlimit=0.7928,
    lc_maglim=0.6,
    lc_filtering=False,
    iter_filtering=True,
):
    """
    Filters data for a given SSO.
    Applies errorbar, projections, iterative sigma-clipping and lightcurve filtering.

    Parameters
    ----------
    sso_name : str
        The name of the solar system object to filter.
    path_to_data : str
        Path to the data files.
    pqdict : dict
        Dictionary linking parquet filename to SSO.
    ephem_path : str | None
        Path to the ephemeris data.
    mlimit : float, optional
        Magnitude limit for errorbar filtering (default is 0.7928).
    lc_filtering : bool, optional
        Whether to apply lightcurve filtering (default is True).
    iter_filtering : bool, optional
        Whether to apply iterative filtering (default is True).

    Returns
    -------
    clean_data : pd.DataFrame
        Cleaned data
    rejects : list
        List of rejected data points from each filtering step.

    Examples
    ---------

    >>> from asteroid_spinprops.ssolib.dataprep import prepare_sso_data, filter_sso_data
    >>> from asteroid_spinprops.ssolib.dataprep import __file__
    >>> import os
    >>> import pickle

    >>> wpath = os.path.dirname(__file__)

    >>> ephem_path = os.path.join(wpath, "testing/ephemeris_testing")
    >>> data_path = os.path.join(wpath, "testing/atlas_x_ztf_testing")
    >>> pq_keys = os.path.join(wpath, "testing/testing_ssoname_keys.pkl")
    >>> available_ssos = os.listdir(ephem_path)

    >>> with open(pq_keys, "rb") as f:
    ...    pqload = pickle.load(f)

    >>> path_args = [data_path, pqload, ephem_path]

    >>> for name in available_ssos:
    ...    origin_data = prepare_sso_data(name, *path_args)
    ...    cdata, rejects = filter_sso_data(name, *path_args)
    ...    clean_p_rejects = cdata["cmred"].values[0].size
    ...    for n in range(4):
    ...        clean_p_rejects += rejects[n]["cmred"].values[0].size

    >>> assert origin_data["cmred"].values[0].size == clean_p_rejects
    """
    if compute_ephemerides is False:
        clean_data = read_sso_data(
            sso_name=sso_name, path_to_data=path_to_data, pqdict=pqdict
        )
    else:
        clean_data = prepare_sso_data(
            sso_name=sso_name,
            path_to_data=path_to_data,
            pqdict=pqdict,
            ephem_path=ephem_path,
        )

    clean_data, errorbar_rejects = errorbar_filtering(data=clean_data, mlimit=mlimit)
    clean_data, projection_rejects = projection_filtering(data=clean_data)
    if iter_filtering is True:
        clean_data, iterative_rejects = iterative_filtering(clean_data)
    else:
        iterative_rejects = None

    if lc_filtering is True:
        clean_data, lightcurve_rejects = lightcurve_filtering(
            clean_data, maglim=lc_maglim
        )
    else:
        lightcurve_rejects = None

    return clean_data, [
        errorbar_rejects,
        projection_rejects,
        iterative_rejects,
        lightcurve_rejects,
    ]


def prepare_sso_data(
    sso_name,
    path_to_data,
    pqdict,
    ephem_path,
):
    """
    Load and prepare observational and ephemeris data for a given solar system object (SSO).

    - Locates the appropriate pqfile containing the SSO & loads its photometric data
    - Retrieves or generates the corresponding ephemeris and appends SSO-Sun & SSO-Obs distances, phase angle, RA/Dec, elongation, reduced magnitude
    - The resulting DataFrame is sorted by Julian date

    Parameters
    -----------------------------
    sso_name : str
        The name of the solar system object to retrieve data for.
    path_to_data : str
        Path to the directory containing pqfiles in Parquet format.
    pqdict : dict
        Dictionary mapping pqfile names to lists of SSOs they contain.
    ephem_path : str | None
        Path to the directory containing cached ephemeris files.

    Returns
    -----------------------------
    data_extra : pd.DataFrame
        A DataFrame containing observational data and appended ephemeris-related quantities:
        - 'Dobs': observer-centric distance [au]
        - 'Dhelio': heliocentric distance [au]
        - 'Phase': phase angle [deg]
        - 'ra', 'dec': right ascension and declination [deg]
        - 'Elongation': solar elongation angle [deg]
        - 'cmred': reduced magnitude
        The data is sorted chronologically by Julian date.
    """
    file_name = utils.find_sso_in_pqdict(sso_name=sso_name, pqdict=pqdict)
    file_path = os.path.join(path_to_data, file_name)

    pdf = pd.read_parquet(file_path)

    cond_name = pdf["name"] == sso_name
    data_extra = pdf[cond_name].copy().reset_index(drop=True)

    ephemeris = utils.get_atlas_ephem(
        pdf=pdf, name=sso_name, path_to_cached_ephems=ephem_path
    )

    Dobs = ephemeris["Dobs"].values

    Dhelio = ephemeris["Dhelio"].values
    Phase = ephemeris["Phase"].values
    Elongation = ephemeris["Elong."].values
    dRA = ephemeris["dRAcosDEC"].values
    dDec = ephemeris["dDEC"].values

    # px, py, pz = ephemeris["px"], ephemeris["py"], ephemeris["pz"]
    ra, dec = ra, dec = utils.sexa_to_deg(
        ephemeris["RA"].values, ephemeris["DEC"].values
    )

    data_extra[
        ["Dobs", "Dhelio", "Phase", "ra", "dec", "Elongation", "dRA", "dDec"]
    ] = pd.DataFrame(
        [[Dobs, Dhelio, Phase, ra, dec, Elongation, dRA, dDec]],
        index=data_extra.index,
    )

    data_extra["cmred"] = [
        utils.calculate_reduced_magnitude(
            magnitude=data_extra["cmagpsf"].values[0],
            D_observer=data_extra["Dobs"].values[0],
            D_sun=data_extra["Dhelio"].values[0],
        )
    ]
    data_extra = utils.sort_by_cjd(data_extra)
    return data_extra


def read_sso_data(
    sso_name,
    path_to_data,
    pqdict,
):
    file_name = utils.find_sso_in_pqdict(sso_name=sso_name, pqdict=pqdict)
    file_path = os.path.join(path_to_data, file_name)

    pdf = pd.read_parquet(file_path)

    cond_name = pdf["name"] == sso_name
    data_extra = pdf[cond_name].copy().reset_index(drop=True)

    data_extra["cmred"] = [
        utils.calculate_reduced_magnitude(
            magnitude=data_extra["cmagpsf"].values[0],
            D_observer=data_extra["Dobs"].values[0],
            D_sun=data_extra["Dhelio"].values[0],
        )
    ]

    data_extra = data_extra.rename(columns={"RA": "ra", "DEC": "dec"})

    data_extra = utils.sort_by_cjd(data_extra)

    return data_extra


if __name__ == "__main__":
    import doctest

    sys.exit(doctest.testmod()[0])
