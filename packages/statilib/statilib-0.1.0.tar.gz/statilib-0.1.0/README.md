# statlib

A small statistics library providing common descriptive and inferential statistics functions, grouped-data helpers, and basic probability utilities. The package appears authored by Abdulrahman F. Alosaimi.

## Project layout

- `statlib/formula.py` - main implementation of statistical functions
- `statlib/unit_tests.py` - unit tests for several core functions

## Usage

Import the functions you need from `statlib`:

```python
from statlib import formula

print(formula.mean([1,2,3,4,5], 5))
```

### Key functions (summary)

The `formula.py` module implements many functions. Highlights:

- Data description
  - `mean(x, n)` — sample mean
  - `medine(data)` — median (handles even/odd lengths)
  - `mid_range(highest, lowest)`
  - `mid_point(h_limit, l_limit)`
  - `mod(data)` — mode (returns list with mode and its frequency when applicable)

- Grouped data helpers
  - `mean_for_grouped_data(x, f, n)` — mean for grouped data using class midpoints
  - `medine_for_grouped_data(f, cumulative_f)` — median for grouped data (expects class rows `[lower, upper, freq, cumulative_freq]`)

- Variation & dispersion
  - `rnge(high, low)` — range
  - `pop_variance`, `standard_deviation_pop`
  - `sample_variance`, `standard_deviation_sample`
  - `variance_grouped`
  - `coff_of_variation_sample`, `coff_of_variation_pop`

- Percentiles & z-scores
  - `percent`, `relative_frequncy`, `coumulative_frequncy_percentile`, `percentile`, `percentile_to_value`
  - `z_scores_pop`, `z_scores_sample`

- Outliers & quartiles
  - `quar_of(data)` — returns [Q1, Q2, Q3]
  - `outlier(data)` — returns [lower_limit, upper_limit, list_of_outliers]

- Correlation & regression
  - `correlation_coefficient(data, n)`
  - `regression_line(data, n, x)` — predicts y for given x using linear regression

- Probability & counting
  - `prob`, `emprical_prob`, `event_comp`, `Bayes_prob`, `independ_intersect_prob`, `depend_intersect_prob`
  - `permu_count`, `comb_count`

## Contributing

Feel free to open issues or PRs. Small improvements I'd prioritize:

- Fix arithmetic bugs and replace `=+` with `+=` where needed
- Add more unit tests and type hints
- Standardize naming and export a cleaner public API