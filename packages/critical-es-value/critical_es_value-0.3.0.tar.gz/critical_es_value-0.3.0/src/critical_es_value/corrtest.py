import numpy as np
import pandas as pd
import pingouin
from numpy.typing import ArrayLike
from scipy import stats

from critical_es_value import utils


def critical_for_correlation_test_from_values(
    r: float,
    n: int,
    confidence: float = 0.95,
    alternative: str = "two-sided",
    variant: str = "ttest",
) -> pd.DataFrame:
    """
    Calculate critical effect size values given pearson correlation coefficient, sample size and significance level.

    Args:
        r (float): Pearson correlation coefficient.
        n (int): Sample size.
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "
        variant (str): The statistical test variant. Either "ttest" or "ztest". Default is "ttest".

    Returns:
        pd.DataFrame: A DataFrame with the following columns:
            - `r`: Pearson correlation coefficient
            - `n`: Sample size
            - `dof`: Degrees of freedom
            - `r_critical`: Critical value for the correlation coefficient
            - `rz_critical`: Critical value for Fisher's z-transformed correlation coefficient (only for "ztest" variant)
            - `se_r`: Standard error of the correlation coefficient
            - `se_r_critical`: Standard error of the critical correlation coefficient
            - `se_rz_critical`: Standard error of the critical Fisher's z-transformed correlation coefficient (only for "ztest" variant)

    Raises:
        ValueError: If `variant` is not one of "ttest" or "ztest".
    """
    if variant not in ["ttest", "ztest"]:
        raise ValueError("variant must be one of 'ttest' or 'ztest'")

    alpha = utils.get_alpha(confidence, alternative)
    dof = n - 2

    if variant == "ttest":
        tc = np.abs(stats.t.ppf(alpha, dof))
        rc = np.sqrt(tc**2 / (tc**2 + dof))
    else:
        zc = np.abs(stats.norm.ppf(alpha))
        rc = np.tanh(zc / np.sqrt(n - 3))

    result = {
        "n": n,
        "r": r,
        "dof": dof,
        "r_critical": rc,
        "se_r": np.sqrt((1 - r**2) / dof),
        "se_r_critical": np.sqrt((1 - rc**2) / dof),
    }
    if variant == "ztest":
        result["rz_critical"] = np.atanh(rc)
        result["se_rz_critical"] = 1 / np.sqrt(n - 3)

    return pd.DataFrame([result], index=["critical"])


def critical_for_correlation_test(
    x: ArrayLike,
    y: ArrayLike,
    confidence: float = 0.95,
    alternative: str = "two-sided",
    variant: str = "ttest",
) -> pd.DataFrame:
    """
    Calculate critical effect size values for a pearson correlation test.

    Args:
        x (ArrayLike): Sample data for group 1.
        y (ArrayLike): Sample data for group 2.
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less". Default is "two-sided".
        variant (str): The statistical test variant. Either "ttest" or "ztest". Default is "ttest".

    Returns:
        pd.DataFrame: A DataFrame with the following columns:
            - `r`: Pearson correlation coefficient
            - `n`: Sample size
            - `dof`: Degrees of freedom
            - `r_critical`: Critical value for the correlation coefficient
            - `rz_critical`: Critical value for Fisher's z-transformed correlation coefficient (only for "ztest" variant)
            - `se_r`: Standard error of the correlation coefficient
            - `se_r_critical`: Standard error of the critical correlation coefficient
            - `se_rz_critical`: Standard error of the critical Fisher's z-transformed correlation coefficient (only for "ztest" variant)
    """
    corr = pingouin.corr(x, y, alternative=alternative, method="pearson").iloc[0]

    return critical_for_correlation_test_from_values(
        r=corr["r"],
        n=corr["n"],
        confidence=confidence,
        alternative=alternative,
        variant=variant,
    )
