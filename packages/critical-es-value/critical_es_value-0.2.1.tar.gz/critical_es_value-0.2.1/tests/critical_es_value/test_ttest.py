import pytest

from critical_es_value import ttest


@pytest.mark.parametrize(
    "correction, n1, n2, expected, match",
    [
        (True, 10, 10, True, None),
        (True, 10, 15, True, None),
        (False, 10, 10, False, None),
        (False, 10, 15, False, None),
        ("auto", 10, 10, False, None),
        ("auto", 10, 15, True, None),
        ("auto", 15, 10, True, None),
        ("invalid", 10, 10, None, r"correction must be one of True, False, or 'auto'"),
        ("invalid", 10, 15, None, r"correction must be one of True, False, or 'auto'"),
    ],
)
def test_determine_welch_correction(correction, n1, n2, expected, match):
    if match:
        with pytest.raises(ValueError, match=match):
            ttest.determine_welch_correction(correction, n1=n1, n2=n2)
    else:
        result = ttest.determine_welch_correction(correction, n1=n1, n2=n2)
        assert result == expected


@pytest.mark.parametrize(
    "dataset, alternative, confidence, expected",
    [
        (
            "test_dataset1",
            "two-sided",
            0.95,
            {
                "d": 0.7479307,
                "d_critical": 0.3734061,
                "b_critical": 0.3609507,
                "g": 0.728391,
                "g_critical": 0.3636509,
            },
        ),
        (
            "test_dataset2",
            "two-sided",
            0.95,
            {
                "d": 1.986911,
                "d_critical": 0.2841969,
                "b_critical": 0.3661223,
                "g": 1.956317,
                "g_critical": 0.2798208,
            },
        ),
    ],
)
def test_critical_for_one_sample_ttest(
    test_dataset1, test_dataset2, dataset, alternative, confidence, expected
):
    data = test_dataset1 if dataset == "test_dataset1" else test_dataset2
    result = ttest.critical_for_one_sample_ttest(
        x=data["x"],
        alternative=alternative,
        confidence=confidence,
    ).iloc[0]

    for key, value in expected.items():
        assert result[key] == pytest.approx(value), key


@pytest.mark.parametrize(
    "dataset, paired, alternative, correction, confidence, expected",
    [
        (
            "test_dataset1",
            False,
            "two-sided",
            True,
            0.95,
            {
                "d": 0.5072601,
                "d_critical": 0.5168963,
                "b_critical": 0.5183234,
                "g": 0.5006344,
                "g_critical": 0.5101447,
            },
        ),
        (
            "test_dataset1",
            False,
            "two-sided",
            False,
            0.95,
            {
                "d": 0.5072601,
                "d_critical": 0.5168412,
                "b_critical": 0.5182682,
                "g": 0.5006675,
                "g_critical": 0.5101241,
            },
        ),
        (
            "test_dataset1",
            False,
            "less",
            False,
            0.95,
            {
                "d": 0.5072601,
                "d_critical": -0.4315931,
                "b_critical": -0.4327847,
                "g": 0.5006675,
                "g_critical": -0.4259839,
            },
        ),
        (
            "test_dataset1",
            True,
            "two-sided",
            False,
            0.95,
            {
                "d": 0.5074131,
                "d_critical": 0.6060484,
                "b_critical": 0.6075383,
                "g": 0.494157,
                "g_critical": 0.5902154,
                "dz": 0.3126338,
                "dz_critical": 0.3734061,
                "gz": 0.3044662,
                "gz_critical": 0.3636509,
            },
        ),
        (
            "test_dataset1",
            False,
            "two-sided",
            True,
            0.95,
            {
                "d": 0.5072601,
                "d_critical": 0.5168963,
                "b_critical": 0.5183234,
                "g": 0.5006344,
                "g_critical": 0.5101447,
            },
        ),
        (
            "test_dataset1",
            True,
            "greater",
            False,
            0.90,
            {
                "d": 0.5074131,
                "d_critical": 0.3886078,
                "b_critical": 0.3895632,
                "g": 0.494157,
                "g_critical": 0.3784554,
                "dz": 0.3126338,
                "dz_critical": 0.2394339,
                "gz": 0.3044662,
                "gz_critical": 0.2331787,
            },
        ),
        (
            "test_dataset1",
            True,
            "two-sided",
            False,
            0.99,
            {
                "d": 0.5074131,
                "d_critical": 0.8167803,
                "b_critical": 0.8187883,
                "g": 0.494157,
                "g_critical": 0.7954419,
                "dz": 0.3126338,
                "dz_critical": 0.5032449,
                "gz": 0.3044662,
                "gz_critical": 0.4900976,
            },
        ),
        (
            "test_dataset2",
            False,
            "two-sided",
            True,
            0.95,
            {
                "d": -0.0993843,
                "d_critical": 0.3975426,
                "b_critical": 0.4389254,
                "g": -0.0985214,
                "g_critical": 0.3940911,
            },
        ),
    ],
)
def test_critical_for_two_sample_ttest(
    test_dataset1,
    test_dataset2,
    dataset,
    paired,
    alternative,
    correction,
    confidence,
    expected,
):
    data = test_dataset1 if dataset == "test_dataset1" else test_dataset2
    print(data)
    result = ttest.critical_for_two_sample_ttest(
        x=data["x"],
        y=data["y"],
        paired=paired,
        correction=correction,
        alternative=alternative,
        confidence=confidence,
    ).iloc[0]
    print(result)

    for key, value in expected.items():
        assert result[key] == pytest.approx(value), key
