# %% [markdown]
# # Exploratory data analysis: <project / dataset name>
#
# Overview of <dataset> before choosing a learner and splitter.
# TableReport owns dtypes, missingness, univariate distributions,
# cardinality, and top pairwise associations — do not re-plot those.

# %%
import pandas as pd
import seaborn as sns
import skrub

from <pkg> import PROJECT_ROOT

OUT = PROJECT_ROOT / "data_analysis"
OUT.mkdir(parents=True, exist_ok=True)

RAW = <LOAD_RAW_DATA>
FRAME = RAW.to_pandas() if hasattr(RAW, "to_pandas") else RAW
RAW

# %% [markdown]
# ## Table overview
#
# Column types, missingness, cardinality, and pairwise associations.

# %%
report = skrub.TableReport(RAW, title="<slug>", verbose=0)
(OUT / "data_analysis_<slug>.html").write_text(
    report.html_snippet(), encoding="utf-8"
)
report

# %% [markdown]
# ## Duplicate rows
#
# Exact duplicates inflate counts and can leak across a later split.
# Cleaning belongs in the pipeline, not by dropping rows here.

# %%
n_dup = int(FRAME.duplicated().sum())
duplicate_summary = pd.DataFrame(
    {
        "n_rows": [len(FRAME)],
        "n_duplicate_rows": [n_dup],
        "duplicate_rate": [n_dup / len(FRAME) if len(FRAME) else 0.0],
    }
)
duplicate_summary
