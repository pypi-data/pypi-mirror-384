"""
Tests for the Oaxaca-Blinder decomposition implementation.
"""

import numpy as np
import pandas as pd
import pytest
from formulaic import Formula

from oaxaca import Oaxaca
from oaxaca.formulaic_utils import (
    term_dummies,
    term_dummies_gu_adjusted,
)


@pytest.fixture(scope="session")
def sample_data():
    """Load sample data from CSV for testing.

    Returns:
        DataFrame with sample data for testing.
    """
    # Load the sample data using pandas without transformations
    df = pd.read_csv("tests/fixtures/sample_data.csv", na_values="NA")
    return df


def test_oaxaca_fit_invalid_groups():
    """Test fit method with invalid number of groups."""
    # Create data with 3 groups
    data = pd.DataFrame({"group": [0, 1, 2, 0, 1, 2], "var1": [1, 2, 3, 4, 5, 6], "outcome": [1, 2, 3, 4, 5, 6]})

    model = Oaxaca()

    with pytest.raises(ValueError, match="Group variable must have exactly 2 unique"):
        model.fit("outcome ~ var1", data, group_variable="group")


def test_two_fold_invalid_weights(sample_data):
    """Test two-fold decomposition with invalid weights."""
    model = Oaxaca()
    model.fit("ln_real_wage ~ age", sample_data, group_variable="foreign_born")

    # Test with weights that don't sum to 1
    with pytest.raises(ValueError, match="Weights must sum to 1.0"):
        model.two_fold(weights={0: 0.3, 1: 0.5})

    # Test with wrong group keys
    with pytest.raises(ValueError, match="Weights keys must match group values"):
        model.two_fold(weights={2: 0.5, 3: 0.5})

    # Test with non-dictionary weights
    with pytest.raises(TypeError, match="Weights must be a dictionary"):
        model.two_fold(weights=[0.5, 0.5])  # type: ignore[arg-type]


def test_twofold(sample_data):
    """Test that two-fold decomposition results match expected values.

    Expected values are based on R's oaxaca package https://cran.r-project.org/web/packages/oaxaca/index.html
    """
    model = Oaxaca()
    formula = "exp(ln_real_wage) ~ age + female + C(education_level, contr.treatment('high_school'))"
    model.fit(formula, sample_data, group_variable="foreign_born")

    # Run decomposition
    results = model.two_fold(weights={0: 1, 1: 0})

    assert np.isclose(results.total_difference, results.explained + results.unexplained)

    # Test that detailed components sum to their totals
    assert np.isclose(results.explained_detailed.sum(), results.explained, rtol=1e-10)
    assert np.isclose(results.unexplained_detailed.sum(), results.unexplained, rtol=1e-10)

    assert np.isclose(results.total_difference, 3.015574)
    assert np.isclose(results.explained, 0.1822482)
    assert np.isclose(results.unexplained, 2.833326)

    # age (continuous) coefficient
    assert np.isclose(results.explained_detailed["age"], -1.7491472)
    assert np.isclose(results.unexplained_detailed["age"], 7.55853070)

    # female (binary) coefficient
    assert np.isclose(results.explained_detailed["female"], -0.5230820)
    assert np.isclose(results.unexplained_detailed["female"], -1.16526457)


def test_threefold(sample_data):
    """Test that three-fold decomposition results match expected values.

    Expected values are based on R's oaxaca package https://cran.r-project.org/web/packages/oaxaca/index.html
    """
    model = Oaxaca()
    formula = "exp(ln_real_wage) ~ age + female + C(education_level, contr.treatment('high_school'))"
    model.fit(formula, sample_data, group_variable="foreign_born")

    # Run decomposition
    results = model.three_fold()

    # Verify the three-fold decomposition identity: total = endowment + coefficient + interaction
    assert np.isclose(results.total_difference, results.endowment + results.coefficient + results.interaction)

    # Test that detailed components sum to their totals
    assert np.isclose(results.endowment_detailed.sum(), results.endowment, rtol=1e-10)
    assert np.isclose(results.coefficient_detailed.sum(), results.coefficient, rtol=1e-10)
    assert np.isclose(results.interaction_detailed.sum(), results.interaction, rtol=1e-10)

    assert np.isclose(results.total_difference, 3.015574)
    assert np.isclose(results.endowment, 1.6165339)
    assert np.isclose(results.coefficient, 2.8333261)
    assert np.isclose(results.interaction, -1.4342857)

    assert np.isclose(results.endowment_detailed["age"], -0.51677529)
    assert np.isclose(results.coefficient_detailed["age"], 7.55853070)
    assert np.isclose(results.interaction_detailed["age"], -1.23237194)

    assert np.isclose(results.endowment_detailed["female"], -0.27265166)
    assert np.isclose(results.coefficient_detailed["female"], -1.16526457)
    assert np.isclose(results.interaction_detailed["female"], -0.25043038)


def test_threefold_gu_adjustment(sample_data):
    """Test three-fold decomposition with GU adjustment produces expected results.

    Expected values are based on R's oaxaca package https://cran.r-project.org/web/packages/oaxaca/index.html
    """
    model = Oaxaca()
    formula = "exp(ln_real_wage) ~ age + female + C(education_level, contr.treatment('high_school'))"
    model.fit(formula, sample_data, group_variable="foreign_born")

    # Run decomposition with GU adjustment
    results = model.three_fold(gu_adjustment="unweighted")

    # Verify the three-fold decomposition identity still holds
    total_check = results.endowment + results.coefficient + results.interaction
    assert np.isclose(results.total_difference, total_check)

    # Test that detailed components sum to their totals with GU adjustment
    assert np.isclose(results.endowment_detailed.sum(), results.endowment, rtol=1e-10)
    assert np.isclose(results.coefficient_detailed.sum(), results.coefficient, rtol=1e-10)
    assert np.isclose(results.interaction_detailed.sum(), results.interaction, rtol=1e-10)

    # Check detailed endowment components for specific coefficients
    assert np.isclose(results.endowment_detailed["age"], -0.51677529)
    assert np.isclose(results.endowment_detailed["female"], -0.27265166)
    lths_label = "C(education_level, contr.treatment('high_school'))[LTHS]"
    college_label = "C(education_level, contr.treatment('high_school'))[college]"
    assert np.isclose(results.endowment_detailed[lths_label], 2.17644672)
    assert np.isclose(results.endowment_detailed[college_label], -0.07907587)

    # Check detailed coefficient components for specific coefficients
    assert np.isclose(results.coefficient_detailed["age"], 7.55853070)
    assert np.isclose(results.coefficient_detailed["female"], -1.16526457)
    assert np.isclose(results.coefficient_detailed[lths_label], 0.06459830)
    assert np.isclose(results.coefficient_detailed[college_label], 0.58246411)

    # Check detailed interaction components for specific coefficients
    assert np.isclose(results.interaction_detailed["age"], -1.23237194)
    assert np.isclose(results.interaction_detailed["female"], -0.25043038)
    assert np.isclose(results.interaction_detailed[lths_label], -0.04486771)
    assert np.isclose(results.interaction_detailed[college_label], 0.33558627)

    # Check intercept, which should be adjusted by GU adjustment
    assert np.isclose(results.endowment_detailed["Intercept"], 0.0)
    assert np.isclose(results.coefficient_detailed["Intercept"], -4.26374940)
    assert np.isclose(results.interaction_detailed["Intercept"], 0.0)

    # Verify GU adjustment was applied by checking variable names include base categories
    assert "C(education_level, contr.treatment('high_school'))[high_school]" in results.endowment_detailed.index


def test_twofold_gu_adjustment(sample_data):
    """Test two-fold decomposition with GU adjustment produces expected results.

    Expected values are based on R's oaxaca package https://cran.r-project.org/web/packages/oaxaca/index.html"""
    model = Oaxaca()
    formula = "exp(ln_real_wage) ~ age + female + C(education_level, contr.treatment('high_school'))"
    model.fit(formula, sample_data, group_variable="foreign_born")

    # Run decomposition with GU adjustment
    results = model.two_fold(weights={0: 1, 1: 0}, gu_adjustment="unweighted")

    # Verify total decomposition still holds
    total_check = results.explained + results.unexplained
    assert np.isclose(results.total_difference, total_check)

    # Test that detailed components sum to their totals with GU adjustment
    assert np.isclose(results.explained_detailed.sum(), results.explained, rtol=1e-10)
    assert np.isclose(results.unexplained_detailed.sum(), results.unexplained, rtol=1e-10)

    # Check detailed explained components for specific coefficients
    assert np.isclose(results.explained_detailed["age"], -1.7491472)
    assert np.isclose(results.explained_detailed["female"], -0.5230820)
    assert np.isclose(
        results.explained_detailed["C(education_level, contr.treatment('high_school'))[high_school]"], 0.3396283
    )
    assert np.isclose(
        results.explained_detailed["C(education_level, contr.treatment('high_school'))[college]"], 0.2565104
    )

    # Check detailed unexplained components for specific coefficients
    assert np.isclose(results.unexplained_detailed["age"], 7.55853070)
    assert np.isclose(results.unexplained_detailed["female"], -1.16526457)
    assert np.isclose(
        results.unexplained_detailed["C(education_level, contr.treatment('high_school'))[high_school]"], 0.25712310
    )
    assert np.isclose(
        results.unexplained_detailed["C(education_level, contr.treatment('high_school'))[college]"], 0.58246411
    )

    # Check intercept, which was also adjusted by GU adjustment
    assert np.isclose(results.explained_detailed["Intercept"], 0.0)
    assert np.isclose(results.unexplained_detailed["Intercept"], -4.26374940)

    # Verify GU adjustment was applied by checking variable names include base
    assert "C(education_level, contr.treatment('high_school'))[high_school]" in results.explained_detailed.index


def test_common_support():
    """Test that the common support problem is handled correctly."""
    # Create data where categorical variable has different categories across groups
    np.random.seed(42)
    n = 100

    # Group 0 has categories A, B, C
    group_0_data = pd.DataFrame({
        "group": [0] * (n // 2),
        "category": np.random.choice(["A", "B", "C"], n // 2),
        "continuous_var": np.random.normal(0, 1, n // 2),
        "outcome": np.random.normal(10, 2, n // 2),
    })

    # Group 1 has categories B, C, D (missing A, has extra D)
    group_1_data = pd.DataFrame({
        "group": [1] * (n // 2),
        "category": np.random.choice(["B", "C", "D"], n // 2),
        "continuous_var": np.random.normal(0, 1, n // 2),
        "outcome": np.random.normal(12, 2, n // 2),
    })

    # Combine the data
    data = pd.concat([group_0_data, group_1_data], ignore_index=True)

    # Fit the model - this should work without assertion error
    model = Oaxaca()
    model.fit("outcome ~ continuous_var + C(category)", data, group_variable="group")

    # Check that rows_to_remove correctly identifies rows with categories not in common support
    # Category A only appears in group 0, category D only appears in group 1
    rows_with_A = data[data["category"] == "A"].index.tolist()
    rows_with_D = data[data["category"] == "D"].index.tolist()

    assert hasattr(model, "dummy_removal_result_"), "Model should have dummy_removal_result_ attribute after fitting"

    # Check group 0: should remove rows with category A (exclusive to group 0)
    assert set(model.dummy_removal_result_[0]["rows_to_remove"]) == set(rows_with_A), (
        f"Group 0 should remove rows with category A. "
        f"Expected: {set(rows_with_A)}, Got: {set(model.dummy_removal_result_[0]['rows_to_remove'])}"
    )

    # Check group 1: should remove rows with category D (exclusive to group 1)
    assert set(model.dummy_removal_result_[1]["rows_to_remove"]) == set(rows_with_D), (
        f"Group 1 should remove rows with category D. "
        f"Expected: {set(rows_with_D)}, Got: {set(model.dummy_removal_result_[1]['rows_to_remove'])}"
    )

    # Run decomposition - this should work without dimension mismatch
    results = model.two_fold(weights={0: 0.5, 1: 0.5})
    assert np.isclose(results.total_difference, results.explained + results.unexplained, rtol=1e-10)
    # Verify that categorical variables from common support (B and C) are present in results
    # B is the base category, so we check for C
    category_vars = [col for col in results.explained_detailed.index if "C(category)" in col]
    assert any("C(category)[T.C]" in var for var in category_vars), "Category C should be present in results"
    # Verify that categories A and D (exclusive to one group) are NOT in results
    assert not any("C(category)[T.A]" in var for var in category_vars), "Category A should not be present in results"
    assert not any("C(category)[T.D]" in var for var in category_vars), "Category D should not be present in results"

    # Run decomposition with GU adjustment as well - this should not crash due to dimension mismatch
    results_gu = model.two_fold(weights={0: 0.5, 1: 0.5}, gu_adjustment="unweighted")
    assert results_gu is not None


def test_common_support_with_gu_adjustment():
    """Test common support problem handling with GU adjustment."""
    # Create data where categorical variable has different categories across groups
    np.random.seed(42)
    n = 100

    # Group 0 has categories A, B, C
    group_0_data = pd.DataFrame({
        "group": [0] * (n // 2),
        "category": np.random.choice(["A", "B", "C"], n // 2),
        "outcome": np.random.normal(10, 2, n // 2),
    })

    # Group 1 has categories B, C, D (missing A, has extra D)
    group_1_data = pd.DataFrame({
        "group": [1] * (n // 2),
        "category": np.random.choice(["B", "C", "D"], n // 2),
        "outcome": np.random.normal(12, 2, n // 2),
    })

    data = pd.concat([group_0_data, group_1_data], ignore_index=True)

    # Fit the model
    model = Oaxaca()
    model.fit("outcome ~ C(category)", data, group_variable="group")

    # Run decomposition with GU adjustment - should not crash
    results = model.two_fold(weights={0: 0.5, 1: 0.5}, gu_adjustment="unweighted")

    # Verify decomposition holds
    assert np.isclose(results.total_difference, results.explained + results.unexplained, rtol=1e-10)

    # Verify that base categories are included in results
    categorical_vars = [col for col in results.explained_detailed.index if "C(category)" in col]
    assert len(categorical_vars) == 2  # Should have both B, C (the 2 common categories)

    # Verify that both B and C are present in the results after GU adjustment
    category_b_present = any("B" in var for var in categorical_vars)
    category_c_present = any("C" in var for var in categorical_vars)
    assert category_b_present, "Category B should be present in results after GU adjustment"
    assert category_c_present, "Category C should be present in results after GU adjustment"


def test_gu_adjustment():
    """Test the _apply_gu_adjustment method."""
    model = Oaxaca()
    data = pd.DataFrame({
        "group": [0, 0, 0, 1, 1, 1],
        "category": ["A", "B", "C", "A", "B", "C"],
        "outcome": [1, 2, 3, 4, 5, 6],
    })
    model.fit("outcome ~ C(category)", data, group_variable="group")
    original_coef = model.coef_[0].copy()

    # Apply GU adjustment
    adjusted_coef = model._apply_gu_adjustment(original_coef)

    # Test that base category is included
    assert len(adjusted_coef) == len(original_coef) + 1
    assert "Intercept" in adjusted_coef.index

    # Test that categorical variables have the expected format (without [T.])
    categorical_vars = [col for col in adjusted_coef.index if "C(category)" in col]
    for var in categorical_vars:
        assert "[T." not in var  # Should be reformatted to remove [T.]


def test_term_dummies_gu_adjusted():
    """Test the categorical_to_dummy_mapping_gu_adjusted method."""
    data = pd.DataFrame({
        "group": [0, 0, 0, 1, 1, 1],
        "category": ["A", "B", "C", "A", "B", "C"],
        "outcome": [1, 2, 3, 4, 5, 6],
    })

    _, X = Formula("outcome ~ C(category)").get_model_matrix(data)

    # Test GU-adjusted mapping
    mapping_gu = term_dummies_gu_adjusted(X.model_spec)
    regular_mapping = term_dummies(X.model_spec)

    # GU mapping should include base categories
    for term in mapping_gu:
        if term in regular_mapping:
            assert len(mapping_gu[term]) > len(regular_mapping[term])

    # Variable names should be reformatted (no [T.])
    for _, dummies in mapping_gu.items():
        for dummy in dummies:
            assert "[T." not in dummy


def test_direction_with_gu_adjustment(sample_data):
    """Test that direction argument works correctly with GU adjustment.
    Passing this test highly likely means passing the non-GU-adjusted case as well.
    """
    model = Oaxaca()
    formula = "ln_real_wage ~ age + female + C(education_level, contr.treatment('high_school'))"
    model.fit(formula, sample_data, group_variable="foreign_born")

    # Test default direction with GU adjustment
    results_default = model.two_fold(weights={0: 1, 1: 0}, gu_adjustment="unweighted")

    # Test reverse direction with GU adjustment
    results_reverse = model.two_fold(weights={0: 1, 1: 0}, gu_adjustment="unweighted", direction="group1 - group0")

    # Reverse direction should be negative of default
    assert np.isclose(results_default.total_difference, -results_reverse.total_difference)
    assert np.isclose(results_default.explained, -results_reverse.explained)
    assert np.isclose(results_default.unexplained, -results_reverse.unexplained)

    # Detailed components should also be negated
    for var in results_default.explained_detailed.index:
        assert np.isclose(results_default.explained_detailed[var], -results_reverse.explained_detailed[var])
        assert np.isclose(results_default.unexplained_detailed[var], -results_reverse.unexplained_detailed[var])

    # Verify decomposition still holds for both directions
    assert np.isclose(results_default.total_difference, results_default.explained + results_default.unexplained)
    assert np.isclose(results_reverse.total_difference, results_reverse.explained + results_reverse.unexplained)


def test_weighted_gu_adjustment_intercept_equals_mean_outcome():
    """Test that weighted GU adjustment produces intercept coefficients equal to mean outcomes
    when there are only categorical variables."""
    # Create test data with only categorical variables (no continuous ones)
    n = 50

    # Create two categorical variables
    categories_1 = ["A", "B", "C"]
    categories_2 = ["X", "Y"]

    # Generate data for both groups
    group_0_data = pd.DataFrame({
        "group": [0] * (n // 2),
        "cat1": np.random.choice(categories_1, n // 2),
        "cat2": np.random.choice(categories_2, n // 2),
    })

    group_1_data = pd.DataFrame({
        "group": [1] * (n // 2),
        "cat1": np.random.choice(categories_1, n // 2),
        "cat2": np.random.choice(categories_2, n // 2),
    })
    data = pd.concat([group_0_data, group_1_data], ignore_index=True)

    group_0_outcomes = np.random.normal(10, 2, n // 2)
    group_1_outcomes = np.random.normal(15, 2, n // 2)
    data["outcome"] = np.concatenate([group_0_outcomes, group_1_outcomes])

    # Fit the model with only categorical variables
    model = Oaxaca().fit("outcome ~ C(cat1) + C(cat2)", data, group_variable="group")
    results = model.two_fold(weights={0: 0.5, 1: 0.5}, gu_adjustment="weighted")

    mean_outcome_group_0 = data[data["group"] == 0]["outcome"].mean()
    mean_outcome_group_1 = data[data["group"] == 1]["outcome"].mean()

    # Apply weighted GU adjustment to get the adjusted coefficients
    coef_0_adjusted = model._apply_gu_adjustment(model.coef_[0], weight=model.group_stats_all_categories_[0]["mean_X"])
    coef_1_adjusted = model._apply_gu_adjustment(model.coef_[1], weight=model.group_stats_all_categories_[1]["mean_X"])

    # The main assertion: adjusted intercept should equal mean outcome for each group
    assert np.isclose(coef_0_adjusted["Intercept"], mean_outcome_group_0, rtol=1e-10), (
        f"Group 0 adjusted intercept {coef_0_adjusted['Intercept']} should equal mean outcome {mean_outcome_group_0}"
    )

    assert np.isclose(coef_1_adjusted["Intercept"], mean_outcome_group_1, rtol=1e-10), (
        f"Group 1 adjusted intercept {coef_1_adjusted['Intercept']} should equal mean outcome {mean_outcome_group_1}"
    )

    # Verify that the decomposition still holds
    assert np.isclose(results.total_difference, results.explained + results.unexplained, rtol=1e-10)


def test_detailed_contributions_method():
    """Test detailed_contributions returns correct structure and values with mock data."""
    from oaxaca.results import TwoFoldResults

    mock_oaxaca = type("MockOaxaca", (), {"groups_": [0, 1], "group_variable": "group"})()
    explained_detailed = pd.Series({"Intercept": 1.0, "x": 2.0, "C(cat)[B]": 0.5, "C(cat)[C]": -0.3})
    unexplained_detailed = pd.Series({"Intercept": -0.5, "x": 1.5, "C(cat)[B]": 0.2, "C(cat)[C]": 0.1})

    results = TwoFoldResults(
        oaxaca_instance=mock_oaxaca,
        total_difference=4.5,
        explained=3.2,
        unexplained=1.3,
        explained_detailed=explained_detailed,
        unexplained_detailed=unexplained_detailed,
        coef_nondiscriminatory=pd.Series({"Intercept": 1, "x": 1, "C(cat)[B]": 1, "C(cat)[C]": 1}),
        weights={0: 0.5, 1: 0.5},
        mean_X_0=pd.Series({"Intercept": 1, "x": 2, "C(cat)[B]": 0.5, "C(cat)[C]": 0}),
        mean_X_1=pd.Series({"Intercept": 1, "x": 0, "C(cat)[B]": 0, "C(cat)[C]": 0.3}),
        categorical_to_dummy={"C(cat)": ["C(cat)[B]", "C(cat)[C]"]},
        direction="group0 - group1",
    )

    # Get actual result
    detailed = results.detailed_contributions()

    # Create expected DataFrame
    index = pd.MultiIndex.from_tuples(
        [("Intercept", "Intercept"), ("x", "x"), ("C(cat)", "C(cat)[B]"), ("C(cat)", "C(cat)[C]")],
        names=("variable_group", "category"),
    )

    expected = pd.DataFrame(
        {
            "explained_detailed": [1.0, 2.0, 0.5, -0.3],
            "explained_detailed_pct": [22.222222, 44.444444, 11.111111, -6.666667],
            "unexplained_detailed": [-0.5, 1.5, 0.2, 0.1],
            "unexplained_detailed_pct": [-11.111111, 33.333333, 4.444444, 2.222222],
            "total": [0.5, 3.5, 0.7, -0.2],
            "total_pct": [11.111111, 77.777778, 15.555556, -4.444444],
            "variable_type": ["continuous", "continuous", "categorical", "categorical"],
        },
        index=index,
    )

    # Compare DataFrames
    pd.testing.assert_frame_equal(detailed, expected, check_dtype=False, atol=1e-5)


def test_contributions_method():
    """Test contributions method aggregates detailed_contributions correctly with mock data."""
    from oaxaca.results import TwoFoldResults

    mock_oaxaca = type("MockOaxaca", (), {"groups_": [0, 1], "group_variable": "group"})()
    explained_detailed = pd.Series({"Intercept": 1.0, "x": 2.0, "C(cat)[B]": 0.5, "C(cat)[C]": -0.3})
    unexplained_detailed = pd.Series({"Intercept": -0.5, "x": 1.5, "C(cat)[B]": 0.2, "C(cat)[C]": 0.1})

    results = TwoFoldResults(
        oaxaca_instance=mock_oaxaca,
        total_difference=4.5,
        explained=3.2,
        unexplained=1.3,
        explained_detailed=explained_detailed,
        unexplained_detailed=unexplained_detailed,
        coef_nondiscriminatory=pd.Series({"Intercept": 1, "x": 1, "C(cat)[B]": 1, "C(cat)[C]": 1}),
        weights={0: 0.5, 1: 0.5},
        mean_X_0=pd.Series({"Intercept": 1, "x": 2, "C(cat)[B]": 0.5, "C(cat)[C]": 0}),
        mean_X_1=pd.Series({"Intercept": 1, "x": 0, "C(cat)[B]": 0, "C(cat)[C]": 0.3}),
        categorical_to_dummy={"C(cat)": ["C(cat)[B]", "C(cat)[C]"]},
        direction="group0 - group1",
    )

    # Get actual result
    contrib = results.contributions()

    # Create expected DataFrame
    expected = pd.DataFrame({
        "variable": ["Intercept", "x", "C(cat)"],
        "explained_detailed": [1.0, 2.0, 0.2],  # 0.5 + (-0.3) for categorical
        "explained_detailed_pct": [22.222222, 44.444444, 4.444444],
        "unexplained_detailed": [-0.5, 1.5, 0.3],  # 0.2 + 0.1 for categorical
        "unexplained_detailed_pct": [-11.111111, 33.333333, 6.666667],
        "total": [0.5, 3.5, 0.5],
        "total_pct": [11.111111, 77.777778, 11.111111],
    })

    # Compare DataFrames
    pd.testing.assert_frame_equal(contrib, expected, check_dtype=False, atol=1e-5)
