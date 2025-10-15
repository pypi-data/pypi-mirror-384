import pytest

from critical_es_value import utils


@pytest.mark.parametrize(
    "confidence, alternative, expected, match",
    [
        (0.90, "less", 0.10, None),
        (0.95, "greater", 0.05, None),
        (0.90, "two-sided", 0.05, None),
        (0.95, "two-sided", 0.025, None),
        (0, "one-sided", 0, r"confidence must be in \(0, 1\)"),
        (1, "one-sided", 0, r"confidence must be in \(0, 1\)"),
        (
            0.95,
            "invalid",
            0,
            r"alternative must be one of 'two-sided', 'greater', or 'less'",
        ),
    ],
)
def test_get_alpha(confidence, alternative, expected, match):
    if match:
        with pytest.raises(ValueError, match=match):
            utils.get_alpha(confidence, alternative)
    else:
        alpha = utils.get_alpha(confidence, alternative)
        assert alpha == pytest.approx(expected)


@pytest.mark.parametrize(
    "dof, expected, match",
    [
        (-1, 0, "dof must be greater than 1."),
        (0, 0, "dof must be greater than 1."),
        (1, 0, "dof must be greater than 1."),
        (2, 0.56418958354, None),
        (5, 0.84074868245, None),
        (7, 0.888202907672, None),
        (10, 0.92274560805, None),
        (20, 0.96194453374, None),
        (30, 0.97475437821, None),
    ],
)
def test_get_bias_correction_factor_J(dof, expected, match):
    if match:
        with pytest.raises(ValueError, match=match):
            utils.get_bias_correction_factor_J(dof)
    else:
        assert utils.get_bias_correction_factor_J(dof) == pytest.approx(expected)
