from typing import Optional

import numpy as np
import pandas as pd
import pingouin
from numpy.typing import ArrayLike
from scipy import stats

from critical_es_value import utils


def critical_for_linear_regression_from_values(
    coeffs: ArrayLike,
    coeffs_se: ArrayLike,
    coeffs_names: ArrayLike,
    dof: Optional[int] = None,
    confidence: float = 0.95,
    alternative: str = "two-sided",
    variant: str = "ttest",
) -> list[float]:
    """Calculate critical effect size values given linear regression coefficients.

    Args:
        coeffs (ArrayLike): Estimated regression coefficients.
        coeffs_se (ArrayLike): Standard errors of the regression coefficients.
        coeffs_names (ArrayLike): Names of the regression coefficients.
        dof (Optional[int]): Degrees of freedom of the model residuals. Only used for "ttest" variant.
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "
        variant (str): The statistical test variant. Either "ttest" or "ztest". Default is "ttest".

    Returns:
        np.ndarray: An array containing critical effect size values for each coefficient.

    Raises:
        ValueError: If variant is not one of "ttest" or "ztest".
    """
    alpha = utils.get_alpha(confidence, alternative)

    if variant not in ["ttest", "ztest"]:
        raise ValueError("variant must be one of 'ttest' or 'ztest'")

    if variant == "ttest" and dof is None:
        raise ValueError("dof must be provided for 'ttest' variant")

    if variant == "ttest":
        qc = np.abs(stats.t.ppf(alpha, dof))
    else:
        qc = np.abs(stats.norm.ppf(alpha))

    return pd.DataFrame(
        {
            "names": coeffs_names,
            "coef": coeffs,
            "coef_critical": qc * np.array(coeffs_se),
        },
        index=list(range(len(coeffs))),
    )


def critical_for_linear_regression(
    X: pd.DataFrame,
    y: pd.Series,
    confidence: float = 0.95,
    alternative: str = "two-sided",
    variant: str = "ttest",
    **kwargs,
):
    """Calculate critical effect size values for linear regression coefficients.

    Args:
        X (pd.DataFrame): DataFrame containing the independent variables.
        y (pd.Series): Series containing the dependent variable.
        confidence (float): Confidence level between 0 and 1 (exclusive). Default is 0.95.
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less". Default is "two-sided".
        variant (str): The statistical test variant. Either "ttest" or "ztest". Default is "ttest".
        \*\*kwargs: Additional keyword arguments to pass to pingouin.linear_regression.

    Returns:
        pd.DataFrame: Returns a DataFrame with the following columns:
            - `names`: Names of the regression coefficients
            - `coef`: Estimated regression coefficients
            - `coef_critical`: Critical value for the regression coefficients
    """
    alpha = utils.get_alpha(confidence, alternative)
    model = pingouin.linear_regression(X=X, y=y, alpha=alpha, **kwargs)

    return critical_for_linear_regression_from_values(
        coeffs=model["coef"].values,
        coeffs_se=model["se"].values,
        coeffs_names=model["names"].values,
        dof=model.df_resid_,
        confidence=confidence,
        alternative=alternative,
        variant=variant,
    )
