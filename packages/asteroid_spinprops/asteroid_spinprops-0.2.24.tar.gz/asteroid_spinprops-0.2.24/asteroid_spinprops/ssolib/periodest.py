import numpy as np
import pandas as pd
import rocks
import matplotlib.pyplot as plt


from astropy.timeseries import LombScargleMultiband, LombScargle
from scipy.signal import find_peaks
import nifty_ls  # noqa: F401
from scipy.stats import f as ftest


def alias_func(x, i, j, p_feat):
    """Return aliases relation

    x: float
        Fink period
    i: int
        Strictly positive integer. Mode.
    j: int
        Alias
    p_feat: float
        Frequency of a feature
    """
    return (i + 1) * p_feat * x / np.abs(p_feat - j * x)


def get_period_estimate(residuals_dataframe, p_min=0.03, p_max=2):
    period_min, period_max = p_min, p_max
    period_range = (period_min, period_max)

    ls = LombScargle(
        residuals_dataframe["jd"].values,
        np.ones(len(residuals_dataframe["jd"])),
        fit_mean=False,
        center_data=False,
    )
    frequencyW, powerW = ls.autopower(
        minimum_frequency=1 / period_range[1],
        maximum_frequency=1 / period_range[0],
        method="fastnifty",
    )
    model = LombScargleMultiband(
        residuals_dataframe["jd"].values,
        residuals_dataframe["residuals"].values,
        residuals_dataframe["filters"].values,
        # residuals_dataframe["sigma"].values,
        normalization="psd",
        fit_mean=True,
        nterms_base=1,
        nterms_band=1,
    )
    frequency, power = model.autopower(
        method="fast",
        sb_method="fastnifty",
        minimum_frequency=1 / period_range[1],
        maximum_frequency=1 / period_range[0],
        samples_per_peak=5,
    )
    pindex, heights = find_peaks(
        power,
        height=0.1,
        threshold=None,
        distance=260,
    )
    pindexW, heightsW = find_peaks(
        powerW,
        height=0.1,
        threshold=None,
        distance=260,
    )
    hindex = np.argsort(heights["peak_heights"])[::-1][:5]
    hindexW = np.argsort(heightsW["peak_heights"])[::-1][:5]

    signal_peaks = frequency[pindex[hindex]]
    signal_power = power[pindex[hindex]]

    window_peaks = frequencyW[pindexW[hindexW]]
    window_power = powerW[pindexW[hindexW]]

    noise_level = np.mean(power) + 3 * np.std(power)

    return (
        [frequency, power, signal_peaks, signal_power],
        [frequencyW, powerW, window_peaks, window_power],
        noise_level,
    )


def get_multiband_period_estimate(
    residuals_dataframe, p_min=0.03, p_max=2, k_free=True, k_val=None
):
    period_min, period_max = p_min, p_max
    period_range = (period_min, period_max)
    results = []
    residuals = np.zeros(len(residuals_dataframe["filters"].values))
    bands = np.unique(residuals_dataframe["filters"].values)
    if k_free:
        for k in range(1, 11):
            model = LombScargleMultiband(
                residuals_dataframe["jd"].values,
                residuals_dataframe["residuals"].values,
                residuals_dataframe["filters"].values,
                residuals_dataframe["sigma"].values,
                normalization="standard",
                fit_mean=True,
                nterms_base=k,
                nterms_band=1,
            )
            frequency, power = model.autopower(
                method="fast",
                sb_method="fastnifty_chi2",
                minimum_frequency=1 / period_range[1],
                maximum_frequency=1 / period_range[0],
                samples_per_peak=5,
            )

            f_best = frequency[np.argmax(power)]
            y_model = model.model(
                residuals_dataframe["jd"].values, f_best, bands_fit=bands
            )

            # y_model.shape is (n_bands, len(time))

            for n, ff in enumerate(bands):
                bindex = np.where(residuals_dataframe["filters"].values == ff)
                residuals[bindex] = (
                    residuals_dataframe["residuals"].values[bindex] - y_model[n][bindex]
                )

            rms = np.sqrt(np.mean(residuals**2))
            n_params = 2 * k + 1 + 3 * len(bands)
            dof = len(residuals) - n_params

            results.append((k, f_best, rms, dof, n_params))

        model_comparison = pd.DataFrame()

        for i in range(len(results) - 1):
            k, f_best, rss, dof, n_params = results[i]
            k_next, f_best_next, rss_next, dof_next, n_params_next = results[i + 1]
            F = ((rss - rss_next) / (dof - dof_next)) / (rss_next / dof_next)

            # Here crit = Fstat value for which model_2 (more complex) is in fact better than model_1 (less complex)
            crit = ftest.ppf(
                q=0.99,
                dfn=n_params_next - n_params,
                dfd=len(residuals) - n_params_next,
            )

            model_comparison.loc[i, "k"] = k
            model_comparison.loc[i, "k_next"] = k_next
            model_comparison.loc[i, "f_best"] = f_best
            model_comparison.loc[i, "Fstat"] = F
            model_comparison.loc[i, "alpha_crit"] = crit
            model_comparison.loc[i, "rms"] = rms

        cond = model_comparison["Fstat"] > model_comparison["alpha_crit"]
        model_comparison = model_comparison[
            ~cond
        ]  # don't go for the more complex model
        f_chosen = model_comparison[
            model_comparison.k == model_comparison.k.min()
        ].f_best[0]  # Simplest model
        k_val = model_comparison[model_comparison.k == model_comparison.k.min()].k[
            0
        ]  # Simplest model
        p_rms = model_comparison[model_comparison.k == model_comparison.k.min()].rms[
            0
        ]  # Simplest model

    if not k_free:
        model = LombScargleMultiband(
            residuals_dataframe["jd"].values,
            residuals_dataframe["residuals"].values,
            residuals_dataframe["filters"].values,
            residuals_dataframe["sigma"].values,
            normalization="standard",
            fit_mean=True,
            nterms_base=k_val,
            nterms_band=1,
        )
        frequency, power = model.autopower(
            method="fast",
            sb_method="fastnifty_chi2",
            minimum_frequency=1 / period_range[1],
            maximum_frequency=1 / period_range[0],
            samples_per_peak=5,
        )

        f_best = frequency[np.argmax(power)]
        f_chosen = f_best
        p_rms = np.nan
    period_in = 2 * (1 / f_chosen)

    return period_in, k_val, p_rms


def plot_periodograms(signal, window, name=None, axis="frequency"):
    if name is not None:
        r = rocks.Rock(name, datacloud="spins")
        bib_estimates = r.spins["period"].values[pd.notna(r.spins["period"].values)]

    fig, ax = plt.subplots(2, 1, figsize=(12, 6))
    if axis == "frequency":
        ax[0].plot(signal[0], signal[1], c="red", linewidth=2)
        ax[1].plot(window[0], window[1], c="black", alpha=1, linewidth=2)

        for i, n in enumerate(signal[2]):
            ax[0].scatter(
                n - 0.2,
                signal[3][i],
                marker="${}$".format(i + 1),
                zorder=1000,
                s=60,
                c="black",
            )

        for i in [0, 1]:
            for j in range(1, 9):
                ax[i].axvline(x=24 / (24 / j), linestyle="-.", c="purple", linewidth=1)
            ax[i].set_xlim(
                1 / (2 + 0.5),
            )
            ax[i].set_ylim(
                0,
            )
        if name is not None:
            for p in bib_estimates:
                ax[0].axvline(x=24 / (p / 2), linestyle="-", c="green", linewidth=1.5)

        for k in [
            int(24 * 2),
            int(12 * 2),
            int(8 * 2),
            int(6 * 2),
        ]:
            ax[0].text(
                x=24 / (k / 2) - 0.1,
                y=max(signal[1]) + 0.05,
                s="{}h".format(k),
                rotation=90,
                fontsize=11,
            )

        ax[0].text(
            x=0.95,
            y=0.95,
            s="Signal",
            fontsize=15,
            transform=ax[0].transAxes,
            ha="right",
            va="top",
        )
        ax[1].text(
            x=0.95,
            y=0.95,
            s="Window",
            fontsize=15,
            transform=ax[1].transAxes,
            ha="right",
            va="top",
        )

        ax[1].set_xlabel(r"Frequency /day$^{-1}$")

        ax[0].set_ylabel("Power")
        ax[1].set_ylabel("Power")

        ax[0].set_xticks([])

        plt.tight_layout()

    if axis == "period":
        ax[0].plot(2 / signal[0], signal[1], c="red", linewidth=2)
        ax[1].plot(2 / window[0], window[1], c="black", alpha=1, linewidth=2)

        for i, n in enumerate(2 / signal[2]):
            ax[0].scatter(
                2 / (n - 0.2),
                signal[3][i],
                marker="${}$".format(i + 1),
                zorder=1000,
                s=60,
                c="black",
            )

        # for i in [0, 1]:
        #     for j in range(1, 9):
        #         ax[i].axvline(x=24 / (24 / j), linestyle="-.", c="purple", linewidth=1)
        #     ax[i].set_xlim(
        #         1 / (2 + 0.5),
        #     )
        #     ax[i].set_ylim(
        #         0,
        #     )
        if name is not None:
            for p in bib_estimates:
                ax[0].axvline(x=p / 24, linestyle="-", c="green", linewidth=1.5)

        for k in [
            int(24 * 2),
            int(12 * 2),
            int(8 * 2),
            int(6 * 2),
        ]:
            ax[0].text(
                x=(k - 0.1) / 24,
                y=max(signal[1]) + 0.05,
                s="{}h".format(k),
                rotation=90,
                fontsize=11,
            )

        ax[0].text(
            x=0.95,
            y=0.95,
            s="Signal",
            fontsize=15,
            transform=ax[0].transAxes,
            ha="right",
            va="top",
        )
        ax[1].text(
            x=0.95,
            y=0.95,
            s="Window",
            fontsize=15,
            transform=ax[1].transAxes,
            ha="right",
            va="top",
        )

        ax[1].set_xlabel(r"Period /day")

        ax[0].set_ylabel("Power")
        ax[1].set_ylabel("Power")

        ax[0].set_xticks([])

        plt.tight_layout()


def perform_residual_resampling(resid_df, p_min, p_max, k=1):
    if k == 1:
        sg, w, _ = get_period_estimate(resid_df)
        Pog = 48 / sg[2][0]  # in hours

        # Bootstrap residuals:
        Pbs = np.zeros(25)
        for n in range(25):
            BS_df = resid_df.sample(n=len(resid_df), replace=True)
            sg, w, _ = get_period_estimate(BS_df)
            Pbs[n] = 48 / sg[2][0]

        cond = np.abs(Pog - Pbs) / Pog < 1e-2
        Nbs = np.sum(np.ones(25)[cond])
    if k > 1:
        Pog, _, _ = 24 / get_multiband_period_estimate(
            resid_df, p_min=p_min, p_max=p_max, k_free=False, k_val=k
        )
        Pbs = np.zeros(25)
        for n in range(25):
            BS_df = resid_df.sample(n=len(resid_df), replace=True)
            Pbs[n], _, _ = 24 / get_multiband_period_estimate(
                BS_df, p_min=p_min, p_max=p_max, k_free=False, k_val=k
            )
        cond = np.abs(Pog - Pbs) / Pog < 1e-2
        Nbs = np.sum(np.ones(25)[cond])
    return BS_df, Nbs
