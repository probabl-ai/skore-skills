# Deployment

How a new row arrives, so later evaluation can copy that.

- `iid` — a new row is exchangeable with the rows already seen.
- `time` — a new row is later than the rows used to fit.
- `groups` — a new row belongs to an id that was not in the fit.

Ask with these three tokens only. Do not define a horizon, a
gap, a time column, a feature, or the column to generalize to
in this question.
