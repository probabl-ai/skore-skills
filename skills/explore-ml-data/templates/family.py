# %% [markdown]
# ## Table overview: <OTHER_SLUG>
#
# Another table in this dataset.

# %%
RAW_<OTHER_SLUG> = <LOAD_OTHER>
FRAME_<OTHER_SLUG> = (
    RAW_<OTHER_SLUG>.to_pandas()
    if hasattr(RAW_<OTHER_SLUG>, "to_pandas")
    else RAW_<OTHER_SLUG>
)
RAW_<OTHER_SLUG>

# %%
report_<OTHER_SLUG> = skrub.TableReport(
    RAW_<OTHER_SLUG>, title="<OTHER_SLUG>", verbose=0
)
(OUT / "data_analysis_<OTHER_SLUG>.html").write_text(
    report_<OTHER_SLUG>.html_snippet(), encoding="utf-8"
)
report_<OTHER_SLUG>

# %% [markdown]
# ## Duplicate rows: <OTHER_SLUG>
#
# Cleaning belongs in the pipeline, not by dropping rows here.

# %%
n_dup_<OTHER_SLUG> = int(FRAME_<OTHER_SLUG>.duplicated().sum())
duplicate_summary_<OTHER_SLUG> = pd.DataFrame(
    {
        "n_rows": [len(FRAME_<OTHER_SLUG>)],
        "n_duplicate_rows": [n_dup_<OTHER_SLUG>],
        "duplicate_rate": [
            n_dup_<OTHER_SLUG> / len(FRAME_<OTHER_SLUG>)
            if len(FRAME_<OTHER_SLUG>)
            else 0.0
        ],
    }
)
duplicate_summary_<OTHER_SLUG>
