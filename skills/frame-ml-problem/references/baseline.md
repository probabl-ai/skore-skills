# Baseline

The baseline is the comparison point, named in words. It is not an
estimator configuration. Ask for one of the tokens below. A later
comparison is the next experiment.

- `seasonal_naive` — on a time-series forecast, repeat the last
  observed season, not the mean of the whole series. The season
  follows the data's own cycle: the same day of week last week for
  daily retail sales, the same hour yesterday for hourly demand, the
  same month last year for monthly revenue. Where there is no
  seasonal cycle, the note names the last observed value instead
  (a persistence forecast) — a stock's most recent close, a
  sensor's last reading. This must respect the prediction horizon -- the past
  values used must not be more recent than what is available at prediction time.
- `group_mean` — predict the mean of a column that is known at prediction time:
  an item's average rating across other users, a customer's own past average
  order value, a zip code's average home price. Do not use the generalize-to
  column: those ids are unseen, so their mean does not exist
- `logistic` — a simple model that emits probabilities, fit on one
  or two obviously predictive raw columns (income and existing debt
  for credit risk, tenure alone for churn), when that is the goal
- `production` — whatever is already used in deployment; name it
  in the note: a manual underwriting rule, a fixed threshold (flag
  any transaction over $10,000), or a vendor score already live
- `dummy` — a global mean or majority class, when none of the
  above fits: always predict the majority label, always predict the
  training set's overall mean or median, or always predict the
  historical base rate for an imbalanced class

The note is one short phrase: the season, the known column, or the
production system.
