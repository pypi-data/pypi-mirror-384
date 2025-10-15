import numpy as np
import pandas as pd
import pingouin
from numpy.typing import ArrayLike
from scipy import stats

from critical_es_value import utils


def critical_for_linear_regression_se_coefficients(
    se_coefficients: ArrayLike,
    dof: int,
    confidence: float,
    alternative: str,
    variant: str = "ttest",
) -> list[float]:
    """Calculate critical effect size values for linear regression coefficients.

    Args:
        se_coefficients (ArrayLike): Standard errors of the regression coefficients.
        dof (int): Degrees of freedom of the model residuals.
        confidence (float): Confidence level between 0 and 1 (exclusive).
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less".
        variant (str): The statistical test variant. Either "ttest" or "ztest". Default is "ttest".

    Returns:
        np.ndarray: An array containing critical effect size values for each coefficient.

    Raises:
        ValueError: If variant is not one of "ttest" or "ztest".
    """
    if variant not in ["ttest", "ztest"]:
        raise ValueError("variant must be one of 'ttest' or 'ztest'")

    alpha = utils.get_alpha(confidence, alternative)

    if variant == "ttest":
        qc = np.abs(stats.t.ppf(alpha, dof))
    else:
        qc = np.abs(stats.norm.ppf(alpha))

    return qc * np.array(se_coefficients)


def critical_for_linear_regression(
    X: pd.DataFrame,
    y: pd.Series,
    alternative: str = "two-sided",
    confidence: float = 0.95,
    variant: str = "ttest",
    **kwargs,
):
    """Calculate critical effect size values for linear regression coefficients.

    Returns a DataFrame with the following columns:
     - names: Names of the regression coefficients
     - coef: Estimated regression coefficients
     - coef_critical: Critical value for the regression coefficients

    Args:
        X (pd.DataFrame): DataFrame containing the independent variables.
        y (pd.Series): Series containing the dependent variable.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less". Default is "two-sided".
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        variant (str): The statistical test variant. Either "ttest" or "ztest". Default is "ttest".
        **kwargs: Additional keyword arguments to pass to pingouin.linear_regression.

    Returns:
        pd.DataFrame: A DataFrame containing critical effect size values.

    Raises:
        ValueError: If variant is not one of "ttest" or "ztest".
    """
    if variant not in ["ttest", "ztest"]:
        raise ValueError("variant must be one of 'ttest' or 'ztest'")

    alpha = utils.get_alpha(confidence, alternative)

    model = pingouin.linear_regression(X=X, y=y, alpha=alpha, **kwargs)
    coef = model["coef"].values

    coef_critical = critical_for_linear_regression_se_coefficients(
        se_coefficients=model["se"].values,
        dof=model.df_resid_,
        confidence=confidence,
        alternative=alternative,
        variant=variant,
    )

    return pd.DataFrame(
        {
            "names": model["names"].values,
            "coef": coef,
            "coef_critical": coef_critical,
        },
        index=list(range(len(coef))),
    )
