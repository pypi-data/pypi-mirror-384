import pandas as pd
import requests


# Define a simple ephemerides query
def ephemcc_old(ident, ep, nbd=None, step=None, observer="500", rplane="1", tcoor=5):
    """Gets asteroid ephemerides from IMCCE Miriade for a suite of JD for a single SSO
    Original function by M. Mahlke

    :ident: int, float, str - asteroid identifier
    :ep: float, str, list - Epoch of computation
    :observer: str - IAU Obs code - default to geocenter: https://minorplanetcenter.net//iau/lists/ObsCodesF.html
    :returns: pd.DataFrame - Input dataframe with ephemerides columns appended
              False - If query failed somehow

    """

    # ------
    # Miriade URL
    url = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

    # Query parameters
    # params = {
    #     "-name": f"{ident}",
    #     "-mime": "json",
    #     "-rplane": rplane,
    #     "-tcoor": str(tcoor),
    #     "-output": "--jd",
    #     "-observer": observer,
    #     "-tscale": "UTC",
    # }

    params = {
        "-name": f"{ident}",
        "-mime": "json",
        "-rplane": rplane,
        "-tcoor": str(tcoor),
        "-output": "--jd",
        "-observer": observer,
        "-tscale": "UTC",
        "-ephem_type": "eq",
    }

    # Single epoch of computation
    if type(ep) is not list:
        # Set parameters
        params["-ep"] = ep
        if nbd is not None:
            params["-nbd"] = nbd
        if step is not None:
            params["-step"] = step

        # Execute query
        try:
            r = requests.post(url, params=params, timeout=80)
        except requests.exceptions.ReadTimeout:
            return False

    # Multiple epochs of computation
    else:
        # Epochs of computation
        files = {"epochs": ("epochs", "\n".join(["%.6f" % epoch for epoch in ep]))}

        # Execute query
        try:
            r = requests.post(url, params=params, files=files, timeout=50)
        except requests.exceptions.ReadTimeout:
            return False

    #    # Pass sorted list of epochs to speed up query
    #    files = {'epochs': ('epochs', '\n'.join(['%.6f' % epoch
    #                                             for epoch in jd]))}
    #    # Execute query
    #    try:
    #        r = requests.post(url, params=params, files=files, timeout=2000)
    #    except requests.exceptions.ReadTimeout:
    #        return False

    j = r.json()

    # Read JSON response
    try:
        ephem = pd.DataFrame.from_dict(j["data"])
    except KeyError:
        return False

    return ephem


def ephemcc(ident, ep, nbd=None, step=None, observer="500", rplane="1", tcoor=5):
    """Gets asteroid ephemerides from IMCCE Miriade for a suite of JD for a single SSO

    :ident: int, float, str - asteroid identifier
    :ep: float, str, list - Epoch of computation
    :observer: str - IAU Obs code - default to geocenter
    :returns: pd.DataFrame - DataFrame with ephemerides including RA, DEC, and their rates
              False - If query failed
    """

    # Miriade URL
    url = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

    # Base query parameters using correct output keywords
    params = {
        "-name": f"{ident}",
        "-mime": "json",
        "-rplane": rplane,
        "-tcoor": str(tcoor),
        "-output": "--jd",
        "-observer": observer,
        "-tscale": "UTC",
    }

    # Single epoch of computation
    if not isinstance(ep, list):
        params["-ep"] = ep
        if nbd is not None:
            params["-nbd"] = nbd
        if step is not None:
            params["-step"] = step

        try:
            r = requests.post(url, params=params, timeout=80)
            r.raise_for_status()
        except (requests.exceptions.RequestException, ValueError) as e:
            print("Request error:", e)
            return False

    # Multiple epochs of computation
    else:
        files = {"epochs": ("epochs", "\n".join(["%.6f" % epoch for epoch in ep]))}
        try:
            r = requests.post(url, params=params, files=files, timeout=1000)
            r.raise_for_status()
        except (requests.exceptions.RequestException, ValueError) as e:
            print("Request error:", e)
            return False

    # Parse JSON response
    try:
        j = r.json()
        ephem = pd.DataFrame.from_dict(j["data"])
    except (KeyError, ValueError):
        print("Failed to parse JSON. Response content:")
        print(r.text)
        return False

    return ephem
