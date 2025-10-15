import pytest

from critical_es_value import corrtest


@pytest.mark.parametrize(
    "dataset, confidence, alternative, variant, expected",
    [
        (
            "test_dataset1",
            0.95,
            "two-sided",
            "ttest",
            {
                "n": 30,
                "r": -0.3171089,
                "dof": 28,
                "r_critical": 0.361006907733233,
                "se_r": 0.179228699226594,
                "se_r_critical": 0.176237868130475,
            },
        ),
        (
            "test_dataset1",
            0.95,
            "two-sided",
            "ztest",
            {
                "n": 30,
                "r": -0.3171089,
                "dof": 28,
                "r_critical": 0.360269222595564,
                "rz_critical": 0.377195244692057,
                "se_r": 0.17922869887800216,
                "se_r_critical": 0.176291771873707,
                "se_rz_critical": 0.192450089729875,
            },
        ),
        (
            "test_dataset2",
            0.90,
            "greater",
            "ttest",
            {
                "n": 50,
                "r": 0.120606,
                "dof": 48,
                "r_critical": 0.184343459048078,
                "se_r": 0.143283968686603,
                "se_r_critical": 0.141863893772795,
            },
        ),
        (
            "test_dataset2",
            0.90,
            "greater",
            "ztest",
            {
                "n": 50,
                "r": 0.120606,
                "dof": 48,
                "r_critical": 0.184786108823673,
                "rz_critical": 0.186933508212277,
                "se_r": 0.14328396800771434,
                "se_r_critical": 0.141851895621352,
                "se_rz_critical": 0.145864991497895,
            },
        ),
        (
            "test_dataset3",
            0.99,
            "less",
            "ttest",
            {
                "n": 30,
                "r": -0.09117187,
                "dof": 28,
                "r_critical": 0.422572101611893,
                "se_r": 0.18819515802568,
                "se_r_critical": 0.171280140094202,
            },
        ),
        (
            "test_dataset3",
            0.99,
            "less",
            "ztest",
            {
                "n": 30,
                "r": -0.09117187,
                "dof": 28,
                "r_critical": 0.42001139326588,
                "rz_critical": 0.447705857102064,
                "se_r": 0.1881951580739162,
                "se_r_critical": 0.171504938446895,
                "se_rz_critical": 0.192450089729875,
            },
        ),
    ],
)
def test_critical_for_correlation_test(
    test_dataset1,
    test_dataset2,
    test_dataset3,
    dataset,
    confidence,
    alternative,
    variant,
    expected,
):
    data = {
        "test_dataset1": test_dataset1,
        "test_dataset2": test_dataset2,
        "test_dataset3": test_dataset3,
    }[dataset]

    result = corrtest.critical_for_correlation_test(
        x=data["x"],
        y=data["y"],
        confidence=confidence,
        alternative=alternative,
        variant=variant,
    ).iloc[0]

    for key, value in expected.items():
        assert result[key] == pytest.approx(value), key
