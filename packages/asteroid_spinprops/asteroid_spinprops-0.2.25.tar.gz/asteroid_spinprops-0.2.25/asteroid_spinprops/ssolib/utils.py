import numpy as np
import pandas as pd
import asteroid_spinprops.ssolib.ssptools as ssptools
import os

import pickle
import requests
import io
import astropy.constants as const


def is_sorted(a):
    return np.all(a[:-1] <= a[1:])


def sigma_condition_func(data):
    """
    Used to wrap the condition to flag points within 3 sigma of a dataset.

    Parameters
    -----------
    data : array-like
        The data to be flagged.

    Returns
    --------
    array-like of bool
        A boolean mask indicating which data points lie **within** mu \pm 3 sigma,
    """
    mean_val = np.mean(data)
    std_val = np.std(data)
    return (data > mean_val - 3 * std_val) & (data < mean_val + 3 * std_val)


def get_atlas_ephem(pdf, name, path_to_cached_ephems=None):
    # TODO: include midtime obs timeshift
    """
    Get the ephemerides for a SSO from the ATLAS catalogue

    Parameters
    -----------------------------
    name: str
        Name of the object
    jd: float or list
        Julian Date(s) of the ephemerides requested
    pdf: pd.DataFrame
        Dataframe containing the name and the JDs of the observations of the object
    path_to_cached_ephems: str
        Path to already computed ephemerids

    Returns
    -----------------------------
    ephem: pd.DataFrame
        Ephemerides for the provided JDs
    """

    namecond = pdf["name"] == name
    jd = pdf[namecond]["cjd"].tolist()[0].tolist()
    if path_to_cached_ephems is not None:
        ephem_file = os.path.join(path_to_cached_ephems, name)
        if os.path.exists(ephem_file):
            eph = pd.read_csv(ephem_file)
        else:
            eph = ssptools.ephemcc(name, jd, tcoor=5, observer="500")
            eph.to_csv(path_to_cached_ephems + "/" + name)
    else:
        eph = ssptools.ephemcc(name, jd, tcoor=5, observer="500")
    return eph


def find_nearest(array, value):
    """
    Find the nearest value of an array to a given value.

    Parameters
    ----------
    array : array-like
        Array from which to find the nearest value.
    value : float
        Value to compare with array

    Returns
    -------
    The value of the array which is nearest to the given value
    """
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def flatten_list(xss):
    """
    Flatten a list.

    Parameters
    ----------
    xss : list
        List of lists (or other iterrable) to flatten in a single array
    Returns
    -------
    Flattened list as a np.array
    """
    flat_list = [x for xs in xss for x in xs]
    return np.array(flat_list)


def c2rd(x, y, z):
    """
    Geocentric cartesian to RA/DEC

    Parameters
    -----------------------------
    x, y, z : float/np.array
        x, y, z coordinates

    Returns
    -----------------------------
    ra, dec : float/np.array
        RA & DEC in degrees from x, y, z
    """

    ra_rad = np.arctan2(y, x)
    ra = np.degrees(ra_rad) % 360

    r = np.sqrt(x**2 + y**2 + z**2)
    dec_rad = np.arcsin(z / r)
    dec = np.degrees(dec_rad)

    return ra, dec


def calculate_reduced_magnitude(magnitude, D_observer, D_sun):
    """
    Calculate reduced magnitude

    Parameters
    -----------------------------
    magnitude : float/np.array
        Mangitude from obervation
    D_oberver : float/np.array
        Object-observer distance
    D_sun : float/np.array
        Object-sun distance

    Returns
    -----------------------------
    float/np.array, reduced magnitude
    """
    return magnitude - 5 * np.log10(D_observer * D_sun)


def find_sso_in_pqdict(sso_name, pqdict):
    """
    Search for a specific SSO name within a dictionary containing names of parquet files as keys
    and lists of sso names as values.

    Parameters
    -----------------------------
    sso_name : str
        The name of the solar system object to search for.
    pqdict : dict
        A dictionary where keys are filenames,
        and values are lists of SSO names contained in each pqfile.

    Returns
    -----------------------------
    pqfile : str or None
        The name of the pqfile that contains the specified SSO
    """

    for pqfile in list(pqdict.keys()):
        if sso_name in pqdict[pqfile]:
            return pqfile


def sort_by_cjd(data):
    """
    Function to sort data containing a `cjd` column by this column.

    Parameters
    -----------
    data : pd.DataFrame
        A single-row DataFrame where each column contains an array of values.

    Returns
    -------
    data: pd.DataFrame
        Sorted dataframe
    """
    cjd_list = data["cjd"].values[0]

    sorted_indices = np.argsort(cjd_list)
    for col in data.columns:
        if col not in ["level_0", "index", "name"]:
            data[col].values[0] = np.array(data[col].values[0])[sorted_indices]
    return data


# sns.set_context('talk')
def sexa_to_deg(ra_list, dec_list):
    """
    Convert 2 lists of RA and DEC angles from sexagesimal format to degrees.

    Parameters
    ----------
    ra_list : list
        List of RA angles.
    dec_list : list
        List of Dec angles

    Returns
    -------
    ra_degrees: np.array
        np.array of RA angles in degrees
    dec_degrees
        np.array of DEC angles in degrees
    """
    ra_array = np.asarray(ra_list, dtype=str)
    dec_array = np.asarray(dec_list, dtype=str)

    ra_signs = np.where(np.char.startswith(ra_array, "-"), -1, 1)
    dec_signs = np.where(np.char.startswith(dec_array, "-"), -1, 1)

    ra_array = np.char.lstrip(ra_array, "+-")
    dec_array = np.char.lstrip(dec_array, "+-")

    ra_h, ra_m, ra_s = np.array([s.split(":") for s in ra_array], dtype=float).T
    dec_d, dec_m, dec_s = np.array([s.split(":") for s in dec_array], dtype=float).T

    ra_degrees = ra_signs * (ra_h * 15 + ra_m * 15 / 60 + ra_s * 15 / 3600)
    dec_degrees = dec_signs * (dec_d + dec_m / 60 + dec_s / 3600)

    return ra_degrees, dec_degrees


def get_obejct_from_fink(name):
    """
    Queries FINK portal for SSO

    Parameters
    -----------
    name: str
        Name of the object

    Returns
    --------
    dframe: pd.DataFrame
        Contains all necessary values for sHG1G2 fit (and previous models)
    """
    r = requests.post(
        "https://api.fink-portal.org/api/v1/sso",
        json={
            "n_or_d": name,
            "withEphem": False,
            "withResiduals": True,
            "output-format": "json",
        },
    )
    dframe = pd.read_json(
        io.BytesIO(r.content),
    )
    return dframe


def get_apparition_indices(dates, threshold=100):
    """
    Identify indices where there is a significant time gap (>threshold days).

    Parameters
    -----------
    dates : np.array
        JDs of observations
    threshold : int
        Assumed threshold between apparitions, default is 100 days

    Returns
    --------
    np.array containing the indices of apparitions in the JD array,
    including 1st and last day (i.e. apparition 1: [0, 97] ...)
    """
    return np.concatenate(([0], np.where(np.diff(dates) > threshold)[0], [len(dates)]))


def pq_folder_to_dictionary(path, save=False):
    sso_in_pq = {}
    for pq_file in os.listdir(path):
        if pq_file.__contains__(".parquet"):
            file_path = os.path.join(path, pq_file)
            sso_names = pd.read_parquet(file_path)["name"]
            sso_in_pq[pq_file] = [n for n in sso_names]
    if save is True:
        with open("ssoname_keys.pkl", "wb") as f:
            pickle.dump(sso_in_pq, f)
    return sso_in_pq


def calc_radec_for_epoch(data, epoch):
    eph = ssptools.ephemcc(
        data["name"].values[0], epoch.tolist(), tcoor=1, observer="500"
    )
    ra, dec = sexa_to_deg(eph["RA"].values, eph["DEC"].values)
    ra, dec = np.radians(ra), np.radians(dec)
    return ra, dec


def flip_spin(ra0, dec0):
    # degree in degree out
    ra0 = np.radians(ra0)
    dec0 = np.radians(dec0)
    ra_alt = (ra0 + np.pi) % (2 * np.pi)
    dec_alt = -dec0
    return np.rad2deg(ra_alt), np.rad2deg(dec_alt)


def calc_atan_parameter(ra, dec, ra0, dec0):
    # degree in
    ra, dec, ra0, dec0 = (
        np.radians(ra),
        np.radians(dec),
        np.radians(ra0),
        np.radians(dec0),
    )
    x = np.cos(dec0) * np.sin(dec) - np.sin(dec0) * np.cos(dec) * np.cos(ra - ra0)
    y = np.cos(dec) * np.sin(ra - ra0)
    return np.arctan2(x, y)


def compute_ltc(jd, d_obs, filt=None):
    """Compute the time with light travel corrected

    Parameters
    ----------
    jd: np.array
        Array of times (JD), in day
    d_obs: np.array
        Array of distance to the observer, in AU
    """
    c_speed = const.c.to("au/day").value
    jd_lt = jd.copy()
    if filt is not None:
        mask_filt = (filt == 1) | (filt == 2)
        jd_lt[mask_filt] -= d_obs[mask_filt] / c_speed
    else:
        jd_lt -= d_obs / c_speed

    return jd_lt


def angle_after_one_synodic_period(angle, synodic_period, rate):
    angle_t1 = (
        angle + synodic_period * (60 * 24) / 3600 * rate
    )  # dRA in arcsec/min, period in days, ra_t0|1 in degrees
    return angle_t1


def estimate_sidereal_period(data, model_parameters, synodic_period):
    ra0 = model_parameters["alpha0"]
    dec0 = model_parameters["delta0"]

    epoch1 = data["cjd"].values[0]

    ra_t0 = data["ra"].values[0]
    dec_t0 = data["dec"].values[0]
    dRA = data["dRA"].values[0]
    dDec = data["dDec"].values[0]

    ra_t1, dec_t1 = (
        angle_after_one_synodic_period(ra_t0, synodic_period, dRA),
        angle_after_one_synodic_period(dec_t0, synodic_period, dDec),
    )

    atan_param_1 = calc_atan_parameter(ra_t0, dec_t0, ra0, dec0)
    atan_param_2 = calc_atan_parameter(ra_t1, dec_t1, ra0, dec0)

    ra_alt, dec_alt = flip_spin(ra0, dec0)

    atan_param_1alt = calc_atan_parameter(ra_t0, dec_t0, ra_alt, dec_alt)
    atan_param_2alt = calc_atan_parameter(ra_t1, dec_t1, ra_alt, dec_alt)

    sidereal_period = (
        2 * np.pi * synodic_period / (atan_param_2 - atan_param_1 + 2 * np.pi)
    )
    sidereal_period_alt = (
        2 * np.pi * synodic_period / (atan_param_2alt - atan_param_1alt + 2 * np.pi)
    )

    return sidereal_period, sidereal_period_alt, epoch1


def read_clean_data(
    sso_name,
    pq_dictionary,
    clean_data_path,
    rejected_data_path=None,
    return_rejects=True,
):
    file_name = find_sso_in_pqdict(sso_name=sso_name, pqdict=pq_dictionary)
    file_path = os.path.join(clean_data_path, file_name)

    pdf = pd.read_parquet(file_path)

    cond_name = pdf["name"] == sso_name
    clean_data = pdf[cond_name].copy().reset_index(drop=True)
    # TODO: is this a good idea? probably not...
    if return_rejects is True:
        rejects = pd.read_pickle(os.path.join(rejected_data_path, sso_name + ".pkl"))

        return clean_data, rejects
    else:
        return clean_data


def oblateness(a_b, a_c):
    return 1 / 2 * a_b / a_c + 1 / 2 * 1 / a_b


def wrap_longitude(long):
    """Wrap RA to [0, 360)."""
    return long % 360


def wrap_latitude(lat):
    """Wrap Dec to [-90, 90] by folding over the poles."""
    m = (lat + 90) % 360  # shift so -90 maps to 0
    if m > 180:
        m = 360 - m
    return m - 90


def generate_initial_points(ra, dec, dec_shift=45):
    """
    Generate 18 initial (RA, Dec) points

    Parameters:
    ra (float): base RA in degrees
    dec (float): base Dec in degrees
    dec_shifts (tuple): the two Dec shifts (in degrees) to try in step 2
    """
    if np.abs(2 * dec - dec_shift) < 10:
        dec_shift += 20

    ra_list = []
    dec_list = []

    base_coords = [(ra, dec), flip_spin(ra, dec)]

    ra_sweep = [0, 120, 240]

    for base_ra, base_dec in base_coords:
        for offset in ra_sweep:
            ra_list.append(wrap_longitude(base_ra + offset))
            dec_list.append(base_dec)

    dec_sweep = [-dec_shift, dec_shift]
    for shift in dec_sweep:
        for base_ra, base_dec in base_coords:
            if (base_dec + shift > 90) | (base_dec - shift < 90):
                flag = 1
            else:
                flag = 0
            shifted_dec = wrap_latitude(base_dec + shift)

            for offset in ra_sweep:
                temp_ra = base_ra + (180 if flag == 1 else 0)
                ra_list.append(wrap_longitude(temp_ra + offset))
                dec_list.append(shifted_dec)
    return ra_list, dec_list
