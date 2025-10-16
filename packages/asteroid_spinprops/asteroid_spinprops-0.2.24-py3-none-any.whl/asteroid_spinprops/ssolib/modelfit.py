import numpy as np
import pandas as pd
import asteroid_spinprops.ssolib.ssptools as ssptools

import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import asteroid_spinprops.ssolib.utils as utils

from fink_utils.sso.spins import (
    estimate_sso_params,
    func_sshg1g2,
    func_hg1g2_with_spin,
)
from asteroid_spinprops.ssolib.periodest import get_period_estimate


def get_fit_params(
    data,
    flavor,
    shg1g2_constrained=True,
    blind_scan=True,
    p0=None,
    survey_filter=None,
    alt_spin=False,
    period_in=None,
    terminator=False,
    pole_metadata=False,
):
    if survey_filter is None:
        filter_mask = np.array(data["cfid"].values[0]) >= 0
    if survey_filter == "ZTF":
        filter_mask = (np.array(data["cfid"].values[0]) == 1) | (
            np.array(data["cfid"].values[0]) == 2
        )
    if survey_filter == "ATLAS":
        filter_mask = (np.array(data["cfid"].values[0]) == 3) | (
            np.array(data["cfid"].values[0]) == 4
        )
    if flavor == "SHG1G2":
        if p0 is None:
            Afit = estimate_sso_params(
                magpsf_red=data["cmred"].values[0][filter_mask],
                sigmapsf=data["csigmapsf"].values[0][filter_mask],
                phase=np.radians(data["Phase"].values[0][filter_mask]),
                filters=data["cfid"].values[0][filter_mask],
                ra=np.radians(data["ra"].values[0][filter_mask]),
                dec=np.radians(data["dec"].values[0][filter_mask]),
                model="SHG1G2",
            )

        if p0 is not None:
            Afit = estimate_sso_params(
                magpsf_red=data["cmred"].values[0][filter_mask],
                sigmapsf=data["csigmapsf"].values[0][filter_mask],
                phase=np.radians(data["Phase"].values[0][filter_mask]),
                filters=data["cfid"].values[0][filter_mask],
                ra=np.radians(data["ra"].values[0][filter_mask]),
                dec=np.radians(data["dec"].values[0][filter_mask]),
                model="SHG1G2",
                p0=p0,
            )

        return Afit
    if flavor == "SSHG1G2":
        if shg1g2_constrained is True:
            shg1g2_params = get_fit_params(
                data=data, flavor="SHG1G2", survey_filter=survey_filter
            )
            residuals_dataframe = make_residuals_df(
                data, model_parameters=shg1g2_params
            )
            if period_in is None:
                sg, _, _ = get_period_estimate(residuals_dataframe=residuals_dataframe)
                period_sy = 2 / sg[2][0]
            else:
                period_sy = period_in

            if blind_scan is True:
                rms = []
                model = []

                period_scan = np.linspace(
                    period_sy - 20 / (24 * 60 * 60), period_sy + 20 / (24 * 60 * 60), 50
                )

                ra0, dec0 = shg1g2_params["alpha0"], shg1g2_params["delta0"]
                # ra0alt, dec0alt = utils.flip_spin(
                #     shg1g2_params["alpha0"], shg1g2_params["delta0"]
                # )
                ra_init, dec_init = utils.generate_initial_points(
                    ra0, dec0, dec_shift=45
                )
                if pole_metadata:
                    pole_md = pd.DataFrame()
                    pole_md["ra0"] = [ra0]
                    pole_md["dec0"] = [dec0]
                    pole_md["ra_init"] = [ra_init]
                    pole_md["dec_init"] = [dec_init]

                    ra_fin, dec_fin = [], []
                for ra, dec in zip(ra_init, dec_init):
                    for period_in in period_scan:
                        p_in = [
                            shg1g2_params["H_1"],
                            0.15,
                            0.15,  # G1,2
                            np.radians(ra),
                            np.radians(dec),
                            period_in,  # in days
                            shg1g2_params["a_b"],
                            shg1g2_params["a_c"],
                            0.1,
                        ]  # phi 0

                        sshg1g2 = get_fit_params(
                            data,
                            "SSHG1G2",
                            shg1g2_constrained=False,
                            p0=p_in,
                            terminator=terminator,
                        )
                        try:
                            rms.append(sshg1g2["rms"])
                            model.append(sshg1g2)
                            if pole_metadata:
                                ra_fin.append(sshg1g2["alpha0"])
                                dec_fin.append(sshg1g2["dec0"])
                        except Exception:
                            continue
                rms = np.array(rms)
                sshg1g2_opt = model[rms.argmin()]

                if pole_metadata:
                    ra_fin = np.array(ra_fin)
                    dec_fin = np.array(dec_fin)

                    pole_md["ra_fin"] = [ra_fin]
                    pole_md["dec_fin"] = [dec_fin]

                    return sshg1g2_opt, pole_md
                else:
                    return sshg1g2_opt
            else:
                period_si_t, alt_period_si_t, _ = utils.estimate_sidereal_period(
                    data=data, model_parameters=shg1g2_params, synodic_period=period_sy
                )
                period_si = np.median(period_si_t)
                alt_period_si = np.median(alt_period_si_t)

                if alt_spin is True:
                    period = alt_period_si
                    ra0, de0 = utils.flip_spin(
                        shg1g2_params["alpha0"],
                        shg1g2_params["delta0"],
                    )
                    ra0, de0 = np.radians(ra0), np.radians(de0)
                else:
                    period = period_si
                    ra0, de0 = (
                        np.radians(shg1g2_params["alpha0"]),
                        np.radians(shg1g2_params["delta0"]),
                    )
                #
                H = next(
                    (
                        shg1g2_params.get(f"H_{i}")
                        for i in range(1, 5)
                        if f"H_{i}" in shg1g2_params
                    ),
                    None,
                )
                G1 = next(
                    (
                        shg1g2_params.get(f"G1_{i}")
                        for i in range(1, 5)
                        if f"G1_{i}" in shg1g2_params
                    ),
                    None,
                )
                G2 = next(
                    (
                        shg1g2_params.get(f"G2_{i}")
                        for i in range(1, 5)
                        if f"G2_{i}" in shg1g2_params
                    ),
                    None,
                )

                p0 = [
                    H,
                    G1,
                    G2,
                    ra0,
                    de0,
                    period,
                    shg1g2_params["a_b"],
                    shg1g2_params["a_c"],
                    0.1,
                ]

                # Constrained Fit
                Afit = estimate_sso_params(
                    data["cmred"].values[0][filter_mask],
                    data["csigmapsf"].values[0][filter_mask],
                    np.radians(data["Phase"].values[0][filter_mask]),
                    data["cfid"].values[0][filter_mask],
                    ra=np.radians(data["ra"].values[0][filter_mask]),
                    dec=np.radians(data["dec"].values[0][filter_mask]),
                    jd=data["cjd"].values[0][filter_mask],
                    model="SSHG1G2",
                    p0=p0,
                )
                return Afit

        if shg1g2_constrained is False:
            if p0 is None:
                print("Initialize SSHG1G2 first!")
            if p0 is not None:
                if terminator:
                    Afit = estimate_sso_params(
                        data["cmred"].values[0][filter_mask],
                        data["csigmapsf"].values[0][filter_mask],
                        np.radians(data["Phase"].values[0][filter_mask]),
                        data["cfid"].values[0][filter_mask],
                        ra=np.radians(data["ra"].values[0][filter_mask]),
                        dec=np.radians(data["dec"].values[0][filter_mask]),
                        jd=data["cjd"].values[0][filter_mask],
                        model="SSHG1G2",
                        p0=p0,
                        terminator=terminator,
                        ra_s=np.radians(data["ra_s"].values[0][filter_mask]),
                        dec_s=np.radians(data["dec_s"].values[0][filter_mask]),
                    )
                else:
                    Afit = estimate_sso_params(
                        data["cmred"].values[0][filter_mask],
                        data["csigmapsf"].values[0][filter_mask],
                        np.radians(data["Phase"].values[0][filter_mask]),
                        data["cfid"].values[0][filter_mask],
                        ra=np.radians(data["ra"].values[0][filter_mask]),
                        dec=np.radians(data["dec"].values[0][filter_mask]),
                        jd=data["cjd"].values[0][filter_mask],
                        model="SSHG1G2",
                        p0=p0,
                        terminator=terminator,
                    )
                return Afit
    if flavor not in ["SHG1G2", "SSHG1G2"]:
        print("Model must either be SHG1G2 or SSHG1G2, not {}".format(flavor))


def plot_model(
    data, flavor, model_params, x_axis="Date", resolution=400, filterout=False
):
    fink_colors = ["#15284F", "#F5622E", "#0E6B77", "#4A4A4A"]

    jd = np.linspace(
        np.min(data["cjd"].values[0]), np.max(data["cjd"].values[0]), resolution
    ).tolist()
    eph = ssptools.ephemcc(data["name"].values[0], jd, tcoor=1, observer="500")
    ra = eph["RA"].values
    dec = eph["DEC"].values
    ra, dec = utils.sexa_to_deg(ra, dec)

    params = model_params

    if x_axis == "Date":
        xvals_eph = "Date"
        xvals = "cjd"
    else:
        xvals = xvals_eph = "Phase"

    markers = ["<", ">", "^", "v"]

    label_sh = r"$\text{sHG}_1\text{G}_2$"
    label_ssh = r"$\text{ssHG}_1\text{G}_2$"

    if flavor == "SHG1G2":
        label_m = label_sh
    if flavor == "SSHG1G2":
        label_m = label_ssh

    filter_names = ["ZTF g", "ZTF r", "ATLAS orange", "ATLAS cyan"]

    if filterout is True:
        rdata = data.copy()
        ztfcond = (rdata["cfid"].values[0] == 1) | (rdata["cfid"].values[0] == 2)
        for col in rdata.columns:
            values = rdata.at[0, col]
            if isinstance(values, np.ndarray) and len(values) == len(ztfcond):
                rdata.at[0, col] = np.array(values)[ztfcond]

        data = rdata
    nfilts = len(np.unique(data["cfid"].values[0]))

    fig, ax = plt.subplots(
        int(nfilts + nfilts / 2),
        1,
        figsize=(12, 8 * nfilts / 2),
        sharex=True,
        gridspec_kw={
            "top": 0.995,
            "left": 0.075,
            "right": 0.995,
            "bottom": 0.085,
            "hspace": 0.02,
            "height_ratios": [2, 2, 1] if nfilts == 2 else [2, 2, 1, 2, 2, 1],
        },
    )

    if x_axis == "Phase":
        alpha = 0.5
    else:
        alpha = 1

    for i, f in enumerate(np.unique(data["cfid"].values[0])):
        filter_mask = data["cfid"].values[0] == f

        if flavor == "SHG1G2":
            model_params = [
                params["H_{}".format(f)],
                params["G1_{}".format(f)],
                params["G2_{}".format(f)],
                params["R"],
                np.radians(params["alpha0"]),
                np.radians(params["delta0"]),
            ]

            model = func_hg1g2_with_spin(
                [np.radians(eph["Phase"]), np.radians(ra), np.radians(dec)],
                *model_params,
            )

            model_points = func_hg1g2_with_spin(
                [
                    np.radians(data["Phase"].values[0][filter_mask]),
                    np.radians(data["ra"].values[0][filter_mask]),
                    np.radians(data["dec"].values[0][filter_mask]),
                ],
                *model_params,
            )
        if flavor == "SSHG1G2":
            jd_ltc = np.array(jd)
            jd_data_ltc = data["cjd"].values[0][filter_mask]

            model_params = [
                params["H_{}".format(f)],
                params["G1_{}".format(f)],
                params["G2_{}".format(f)],
                np.radians(params["alpha0"]),
                np.radians(params["delta0"]),
                params["period"],
                params["a_b"],
                params["a_c"],
                np.radians(params["phi0"]),
            ]

            model = func_sshg1g2(
                [np.radians(eph["Phase"]), np.radians(ra), np.radians(dec), jd_ltc],
                *model_params,
            )

            model_points = func_sshg1g2(
                [
                    np.radians(data["Phase"].values[0][filter_mask]),
                    np.radians(data["ra"].values[0][filter_mask]),
                    np.radians(data["dec"].values[0][filter_mask]),
                    jd_data_ltc,
                ],
                *model_params,
            )
        residuals = data["cmred"].values[0][filter_mask] - model_points

        if i > 1:
            ax[i + 1].plot(
                eph[xvals_eph].values,
                model,
                c="black",
                linestyle="--",
                linewidth=1.1,
                label=label_m,
                alpha=alpha,
            )
            ax[i + 1].scatter(
                data[xvals].values[0][filter_mask],
                data["cmred"].values[0][filter_mask],
                marker=markers[i],
                c=fink_colors[i],
                label=filter_names[i],
                zorder=1000,
            )

            inset_hist = inset_axes(ax[i + 1], width="30%", height="30%")
            inset_hist.hist(residuals, bins=40, color=fink_colors[i], density=True)

            ax[5].scatter(
                data[xvals].values[0][filter_mask],
                residuals,
                marker=markers[i],
                c=fink_colors[i],
            )
            yabs_max = abs(max(ax[5].get_ylim(), key=abs))
            ax[5].set_ylim(ymin=-yabs_max - 0.2, ymax=yabs_max + 0.2)
            ax[5].axhline(y=0, c="black", linestyle="--", zorder=-1000, alpha=0.5)
            ax[i + 1].legend(loc="lower left")
            if xvals == "Phase":
                ax[i + 1].invert_yaxis()

        else:
            ax[i].plot(
                eph[xvals_eph].values,
                model,
                c="black",
                linestyle="--",
                linewidth=1.1,
                label=label_m,
                alpha=alpha,
            )
            ax[i].scatter(
                data[xvals].values[0][filter_mask],
                data["cmred"].values[0][filter_mask],
                marker=markers[i],
                c=fink_colors[i],
                label=filter_names[i],
                zorder=1000,
            )

            inset_hist = inset_axes(ax[i], width="30%", height="30%")
            inset_hist.hist(residuals, bins=40, color=fink_colors[i], density=True)

            ax[2].scatter(
                data[xvals].values[0][filter_mask],
                residuals,
                marker=markers[i],
                c=fink_colors[i],
            )
            yabs_max = abs(max(ax[2].get_ylim(), key=abs))
            ax[2].set_ylim(ymin=-yabs_max - 0.1, ymax=yabs_max + 0.1)
            ax[2].axhline(y=0, c="black", linestyle="--", zorder=-1000, alpha=0.5)
            ax[i].legend(loc="lower left")
            if x_axis == "Phase":
                ax[i].invert_yaxis()
    if i > 2:
        if xvals == "cjd":
            ax[5].set_xlabel("Time (days)")
        else:
            ax[5].set_xlabel("Phase (degree)")

        ax[5].set_ylabel("Residuals")

        if xvals == "cjd":
            ax[2].set_xlabel("Time (days)")
        else:
            ax[2].set_xlabel("Phase (degree)")

    else:
        if xvals == "cjd":
            ax[2].set_xlabel("Time (days)")
        else:
            ax[2].set_xlabel("Phase (degree)")

    ax[2].set_ylabel("Residuals")

    fig.text(0.01, 0.81, "Reduced magnitude", va="center", rotation="vertical")
    fig.text(0.01, 0.35, "Reduced magnitude", va="center", rotation="vertical")

    plt.tight_layout()

    # if xvals == "Phase":
    #     plt.gca().set_xlim(left=0)


def get_model_points(data, params):
    model_points_stack = []
    index_points_stack = []
    index = np.array([ind for ind in range(len(data["cfid"].values[0]))])

    for i, f in enumerate(np.unique(data["cfid"].values[0])):
        filter_mask = data["cfid"].values[0] == f

        model_params = [
            params["H_{}".format(f)],
            params["G1_{}".format(f)],
            params["G2_{}".format(f)],
            params["R"],
            np.radians(params["alpha0"]),
            np.radians(params["delta0"]),
        ]

        model_points = func_hg1g2_with_spin(
            [
                np.radians(data["Phase"].values[0][filter_mask]),
                np.radians(data["ra"].values[0][filter_mask]),
                np.radians(data["dec"].values[0][filter_mask]),
            ],
            *model_params,
        )
        index_points_stack.append(index[filter_mask])
        model_points_stack.append(model_points)

    return model_points_stack, index_points_stack


def get_residuals(data, params):
    pstack, istack = get_model_points(data, params)
    fpstack, fistack = utils.flatten_list(pstack), utils.flatten_list(istack)
    df_to_sort = pd.DataFrame({"mpoints": fpstack}, index=fistack)
    df_to_sort = df_to_sort.sort_index()
    df_to_sort["observation"] = data["cmred"].values[0]
    return (df_to_sort["observation"] - df_to_sort["mpoints"]).values


def make_residuals_df(data, model_parameters):
    mpoints, indices = get_model_points(data=data, params=model_parameters)
    flat_mpoints, flat_index = utils.flatten_list(mpoints), utils.flatten_list(indices)

    residual_df = pd.DataFrame({"mpoints": flat_mpoints}, index=flat_index)
    residual_df = residual_df.sort_index()
    residual_df["mred"] = data["cmred"].values[0]
    residual_df["sigma"] = data["csigmapsf"].values[0]
    residual_df["filters"] = data["cfid"].values[0]
    residual_df["jd"] = data["cjd"].values[0]
    residual_df["residuals"] = residual_df["mred"] - residual_df["mpoints"]

    return residual_df
