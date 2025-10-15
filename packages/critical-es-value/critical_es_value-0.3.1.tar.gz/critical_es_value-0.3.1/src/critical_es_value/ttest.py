from typing import Optional, Union

import numpy as np
import pandas as pd
import pingouin
from numpy.typing import ArrayLike
from scipy import stats

from critical_es_value import utils


def determine_welch_correction(correction: Union[bool, str], n1: int, n2: int) -> bool:
    """Determine whether to apply Welch's correction for unequal variances.

    Args:
        correction (bool or str): If True, always apply Welch's correction.
                                  If False, never apply Welch's correction.
                                  If "auto", apply Welch's correction only if sample sizes are unequal.
        n1 (int): Sample size of group 1.
        n2 (int): Sample size of group 2.

    Returns:
        bool: Whether to apply Welch's correction.

    Raises:
        ValueError: If `correction` is not one of True, False, or "auto".
    """
    if correction not in (True, False, "auto"):
        raise ValueError("correction must be one of True, False, or 'auto'")
    if correction is True or (correction == "auto" and n1 != n2):
        return True
    return False


def critical_for_one_sample_ttest_from_values(
    t: float,
    n: int,
    dof: int,
    confidence: float = 0.95,
    alternative: str = "two-sided",
    std: Optional[float] = None,
):
    """Calculate critical effect size values for a one-sample t-test given t, sample size and other parameters.

    Args:
        t (float): t-value of the test statistic.
        n (int): Sample size.
        dof (int): Degrees of freedom.
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less". Default is "two-sided".
        std (Optional[float]): Standard deviation of the sample. If None, b_critical will not be calculated. Default is None.

    Returns:
        pd.DataFrame: Returns a DataFrame with the following columns:
            - `T`: t-value of the test statistic
            - `dof`: Degrees of freedom
            - `T_critical`: Critical t-value
            - `d`: Cohen's d
            - `d_critical`: Critical value for Cohen's d
            - `g`: Hedges' g
            - `g_critical`: Critical value for Hedges' g
            - `b_critical`: Critical value for the raw mean difference
    """
    alpha = utils.get_alpha(confidence, alternative)

    factor = np.sqrt(1 / n)
    d = t * factor

    tc = np.abs(stats.t.ppf(alpha, dof))
    if alternative == "less":
        tc *= -1

    dc = tc * factor
    j = utils.get_bias_correction_factor_J(dof)

    result = {
        "T": t,
        "dof": dof,
        "T_critical": tc,
        "d": d,
        "d_critical": dc,
        "g": d * j,
        "g_critical": dc * j,
    }
    if std is not None:
        result["b_critical"] = tc * std / np.sqrt(n)

    return pd.DataFrame([result], index=["critical"])


def critical_for_one_sample_ttest(
    x: ArrayLike,
    confidence: float = 0.95,
    alternative: str = "two-sided",
) -> pd.DataFrame:
    """Calculate critical effect size values for a one-sample t-test.

    Args:
        x (ArrayLike): Sample data.
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less". Default is "two-sided".

    Returns:
        pd.DataFrame: Returns a DataFrame with the following columns:
            - `T`: t-value of the test statistic
            - `dof`: Degrees of freedom
            - `T_critical`: Critical t-value
            - `d`: Cohen's d
            - `d_critical`: Critical value for Cohen's d
            - `g`: Hedges' g
            - `g_critical`: Critical value for Hedges' g
            - `b_critical`: Critical value for the raw mean difference
    """

    t_test_result = pingouin.ttest(
        x=x,
        y=0,
        paired=False,
        correction=False,
        confidence=confidence,
        alternative=alternative,
    ).iloc[0]

    return critical_for_one_sample_ttest_from_values(
        t=t_test_result["T"],
        n=len(x),
        confidence=confidence,
        alternative=alternative,
        dof=t_test_result.dof,
        std=np.std(x, ddof=1),
    )


def _critical_for_two_sample_ttest_unpaired_from_values(
    t: float,
    n1: int,
    n2: int,
    dof: int,
    std1: Optional[float] = None,
    std2: Optional[float] = None,
    correction: Union[bool, str] = "auto",
    confidence: float = 0.95,
    alternative: str = "two-sided",
) -> pd.DataFrame:
    """Calculate critical effect size values for UNPAIRED two-sample t-test given t, sample sizes and other parameters.

    Args:
        t (float): t-value of the test statistic.
        n1 (int): Sample size of group 1.
        n2 (int): Sample size of group 2.
        dof (int): Degrees of freedom.
        std1 (Optional[float]): Standard deviation of group 1. If None, b_critical will not be calculated. Default is None.
        std2 (Optional[float]): Standard deviation of group 2. If None, b_critical will not be calculated. Default is None.
        correction (bool): Specify whether or not to correct for unequal variances using Welch separate variances
            T-test. If "auto", it will automatically uses Welch T-test when the sample sizes are unequal. Default
            is "auto".
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less". Default is "two-sided".

    Returns:
        pd.DataFrame: Returns a DataFrame with the following columns:
           - `T`: t-value of the test statistic
           - `dof`: Degrees of freedom
           - `T_critical`: Critical t-value
           - `d`: Cohen's d
           - `d_critical`: Critical value for Cohen's d
           - `g`: Hedges' g
           - `g_critical`: Critical value for Hedges' g
           - `b_critical`: Critical value for the raw mean difference (if std1 and std2 are provided)
    """

    alpha = utils.get_alpha(confidence, alternative)

    factor = np.sqrt(1 / n1 + 1 / n2)
    d = t * factor

    tc = np.abs(stats.t.ppf(alpha, dof))
    if alternative == "less":
        tc *= -1
    dc = tc * factor

    if std1 is not None and std2 is not None:
        if determine_welch_correction(correction, n1=n1, n2=n2):
            se = np.sqrt((std1**2 / n1) + (std2**2 / n2))
        else:
            se = np.sqrt((std1**2 * (n1 - 1) + std2**2 * (n2 - 1)) / (n1 + n2 - 2))
            se *= factor

    j = utils.get_bias_correction_factor_J(dof)

    result = {
        "T": t,
        "dof": dof,
        "T_critical": tc,
        "d": d,
        "d_critical": dc,
        "g": d * j,
        "g_critical": dc * j,
    }
    if std1 is not None and std2 is not None:
        result["b_critical"] = tc * se

    return pd.DataFrame([result], index=["critical"])


def _critical_for_two_sample_ttest_paired_from_values(
    t: float,
    n: int,
    dof: int,
    r12: float,
    confidence: float = 0.95,
    alternative: str = "two-sided",
    std_diff: Optional[float] = None,
) -> pd.DataFrame:
    """Calculate critical effect size values for a PAIRED two-sample t-test given t, sample sizes and other parameters.

    Args:
        t (float): t-value of the test statistic.
        n (int): Sample sizes of both groups.
        dof (int): Degrees of freedom.
        r12 (float): Pearson correlation between the two groups.
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less". Default is "two-sided".
        std_diff (Optional[float]): Standard deviation of the difference scores. If None, b_critical will not be calculated. Default is None.

    Returns:
        pd.DataFrame: Returns a DataFrame with the following columns:
            - `T`: t-value of the test statistic
            - `dof`: Degrees of freedom
            - `T_critical`: Critical t-value
            - `d`: Cohen's d
            - `d_critical`: Critical value for Cohen's d
            - `g`: Hedges' g
            - `g_critical`: Critical value for Hedges' g
            - `dz`: Cohen's dz
            - `dz_critical`: Critical value for Cohen's dz
            - `gz`: Hedges' gz
            - `gz_critical`: Critical value for Hedges' gz
            - `b_critical`: Critical value for the raw mean difference (if std_diff is provided)
    """

    alpha = utils.get_alpha(confidence, alternative)

    factor1 = np.sqrt(1 / n)
    factor2 = np.sqrt(2 * (1 - r12))

    dz = t * factor1
    d = dz * factor2

    tc = np.abs(stats.t.ppf(alpha, dof))
    if alternative == "less":
        tc *= -1

    dzc = tc * factor1
    dc = dzc * factor2

    j = utils.get_bias_correction_factor_J(dof)

    result = {
        "T": t,
        "dof": dof,
        "T_critical": tc,
        "d": d,
        "d_critical": dc,
        "g": d * j,
        "g_critical": dc * j,
        "dz": dz,
        "dz_critical": dzc,
        "gz": dz * j,
        "gz_critical": dzc * j,
    }
    if std_diff is not None:
        result["b_critical"] = tc * std_diff / np.sqrt(n)

    return pd.DataFrame([result], index=["critical"])


def critical_for_two_sample_ttest_from_values(
    t: float,
    n1: int,
    n2: int,
    dof: int,
    std1: Optional[float] = None,
    std2: Optional[float] = None,
    paired: bool = False,
    correction: Union[bool, str] = "auto",
    confidence: float = 0.95,
    alternative: str = "two-sided",
) -> pd.DataFrame:
    """Calculate critical effect size values for a paired or an unpaired two-sample t-test given t, sample sizes and other parameters.

    Args:
        t (float): t-value of the test statistic.
        n1 (int): Sample size of group 1.
        n2 (int): Sample size of group 2.
        dof (int): Degrees of freedom.
        std1 (Optional[float]): Standard deviation of group 1. If None, b_critical will not be calculated. Default is None.
        std2 (Optional[float]): Standard deviation of group 2. If None, b_critical will not be calculated. Default is None.
        paired (bool): Whether the samples are paired. Default is False.
        correction (bool): For unpaired two sample T-tests, specify whether or not to correct for unequal variances
            using Welch separate variances T-test. If "auto", it will automatically uses Welch T-test when the sample
            sizes are unequal. For paired T-tests, this parameter is ignored and no correction is performed. Default
            is "auto".
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less". Default is "two-sided".

    Returns:
        pd.DataFrame: Returns a DataFrame with the following columns:
           - `T`: t-value of the test statistic
           - `dof`: Degrees of freedom
           - `T_critical`: Critical t-value
           - `d`: Cohen's d
           - `d_critical`: Critical value for Cohen's d
           - `g`: Hedges' g
           - `g_critical`: Critical value for Hedges' g
           - `dz`: Cohen's dz (only for paired tests)
           - `dz_critical`: Critical value for Cohen's dz (only for paired tests)
           - `gz`: Hedges' gz (only for paired tests)
           - `gz_critical`: Critical value for Hedges' gz (only for paired tests)
           - `b_critical`: Critical value for the raw mean difference
    """
    if paired:
        return _critical_for_two_sample_ttest_paired_from_values(
            t=t,
            n1=n1,
            n2=n2,
            dof=dof,
            confidence=confidence,
            alternative=alternative,
        )

    return _critical_for_two_sample_ttest_unpaired_from_values(
        t=t,
        n1=n1,
        n2=n2,
        dof=dof,
        std1=std1,
        std2=std2,
        confidence=confidence,
        alternative=alternative,
        correction=correction,
    )


def critical_for_two_sample_ttest(
    x: ArrayLike,
    y: ArrayLike,
    paired: bool = False,
    correction: Union[bool, str] = "auto",
    confidence: float = 0.95,
    alternative: str = "two-sided",
) -> pd.DataFrame:
    """Calculate critical effect size values for a paired or an unpaired two-sample t-test.

    Args:
        x (ArrayLike): Sample data for group 1.
        y (ArrayLike): Sample data for group 2.
        paired (bool): Whether the samples are paired. Default is False.
        correction (bool): For unpaired two sample T-tests, specify whether or not to correct for unequal variances
            using Welch separate variances T-test. If "auto", it will automatically uses Welch T-test when the sample
            sizes are unequal. For paired T-tests, this parameter is ignored and no correction is performed. Default
            is "auto".
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less". Default is "two-sided".

    Returns:
        pd.DataFrame: Returns a DataFrame with the following columns:
           - `T`: t-value of the test statistic
           - `dof`: Degrees of freedom
           - `T_critical`: Critical t-value
           - `d`: Cohen's d
           - `d_critical`: Critical value for Cohen's d
           - `g`: Hedges' g
           - `g_critical`: Critical value for Hedges' g
           - `b_critical`: Critical value for the raw mean difference
    """
    if paired:
        if len(x) != len(y):
            raise ValueError("For paired tests, x and y must have the same length.")

        t_test_result = pingouin.ttest(
            x=x,
            y=y,
            paired=True,
            correction=False,
            confidence=confidence,
            alternative=alternative,
        ).iloc[0]

        return _critical_for_two_sample_ttest_paired_from_values(
            t=t_test_result["T"],
            n=len(x),
            dof=t_test_result.dof,
            r12=np.corrcoef(x, y)[0, 1],
            confidence=confidence,
            alternative=alternative,
            std_diff=np.std(x - y, ddof=1),
        )

    n1 = len(x)
    n2 = len(y)
    correction = determine_welch_correction(correction, n1=n1, n2=n2)

    t_test_result = pingouin.ttest(
        x=x,
        y=y,
        paired=False,
        correction=correction,
        confidence=confidence,
        alternative=alternative,
    ).iloc[0]

    return _critical_for_two_sample_ttest_unpaired_from_values(
        t=t_test_result["T"],
        n1=n1,
        n2=n2,
        dof=t_test_result.dof,
        std1=np.std(x, ddof=1),
        std2=np.std(y, ddof=1),
        confidence=confidence,
        alternative=alternative,
        correction=correction,
    )
