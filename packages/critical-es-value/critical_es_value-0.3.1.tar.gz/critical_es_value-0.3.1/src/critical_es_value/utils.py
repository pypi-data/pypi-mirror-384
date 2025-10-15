import numpy as np
from scipy import special as scipy_special


def get_alpha(confidence: float, alternative: str) -> float:
    r"""Calculate the significance level (alpha) corresponding to a given confidence level.

    .. math::

        \alpha = \begin{cases}
            1 - \text{conf} & \text{one-sided} \\
            \frac{1 - \text{conf}}{2} & \text{two-sided}
        \end{cases}

    Args:
        confidence (float): Confidence level between 0 and 1 (exclusive).
        alternative (str): The alternative hypothesis. Either "two-sided", "greater", or "less".

    Returns:
        float: The significance level (alpha).

    Raises:
        ValueError: If `confidence` is not in (0, 1)
        ValueError: If `alternative` is not one of "two-sided", "greater", or "less".

    Examples:
        >>> get_alpha(0.95, "two-sided")
        0.025
        >>> get_alpha(0.95, "less")
        0.05
    """

    if confidence <= 0 or confidence >= 1:
        raise ValueError("confidence must be in (0, 1)")
    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError("alternative must be one of 'two-sided', 'greater', or 'less'")

    alpha = 1 - confidence

    if alternative == "two-sided":
        return alpha / 2
    return alpha


def get_bias_correction_factor_J(dof: int) -> np.float64:
    r"""Calculate the bias correction factor J for Hedges' g.

    .. math::

        J(x) = \frac{\Gamma\left(\frac{x}{2}\right)}{\sqrt{\frac{x}{2}}\Gamma\left(\frac{x-1}{2}\right)}

    Args:
        dof (int): Degrees of freedom.

    Returns:
        np.float64: The bias correction factor J.

    Examples:
        >>> get_bias_correction_factor_J(10)
        0.92274560805
        >>> get_bias_correction_factor_J(20)
        0.96194453374
    """
    if dof <= 1:
        raise ValueError("dof must be greater than 1.")

    num = scipy_special.loggamma(dof / 2)
    denom = np.log(np.sqrt(dof / 2)) + scipy_special.loggamma((dof - 1) / 2)
    return np.exp(num - denom)
