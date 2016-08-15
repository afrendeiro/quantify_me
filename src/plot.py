import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("white")


# Git


# Read in git data
output = pd.read_csv("data/git_log.csv")


# Filter
# chose which file types to exclude
file_types = [
    "py", "R", "sh", "Makefile",
    "ipynb", "md", "yaml", "yml"]

output = output[output["file_name"].str.contains("|".join(["\." + x + "$" for x in file_types]))]

# chose which authors to keep
authors = ["rendeiro"]
output = output[output["author"].str.contains("|".join(authors))]

# keep only repos with more than X commits
min_commits = 2
counts = output.groupby("repository")['hash'].count()
output = output[output["repository"].isin(counts[counts > min_commits].index)]

output.to_csv("data/git_log.filtered.csv", index=False)


# Work with the data
output["change"] = output["change"].astype(pd.np.int64)
output["date"] = pd.to_datetime(output["date"])
output["time"] = pd.to_datetime(output["date"]).dt.time
output["day"] = pd.to_datetime(output["date"]).dt.date


pivot = pd.pivot_table(output, index="day", columns="repository", aggfunc=sum)
pivot.columns = pivot.columns.droplevel(0)
pivot.index = pivot.index.to_datetime()


# plot
pivot.plot(kind="line")
pivot.plot(kind="bar")


# fill with previous entry
pivot.asfreq(pd.DateOffset(), method="pad")

# resample
pivot.resample("1D", how="mean")


# limit to start date
pivot = pivot[pivot.index > "2014-09-15"]

# heatmap
df = pivot.T.sort_values(by=pivot.T.columns.tolist(), ascending=False)

g = sns.clustermap(pd.np.log2(1 + df.fillna(0)), col_cluster=False, row_cluster=False, robust=True)
for i, tick in enumerate(g.ax_heatmap.yaxis.get_majorticklabels()):
    tick.set_rotation(0)
for i, tick in enumerate(g.ax_heatmap.xaxis.get_majorticklabels()):
    if i % 30 == 0:
        tick.set_rotation(45)
    else:
        tick.set_visible(False)
g.fig.savefig("clustermap.resampled.sorted.svg", bbox_inches="tight")


# line plot on top
fig, axis = plt.subplots(2, 2)
pivot.plot(kind="line", ax=axis[0][0])
pd.np.log2(pivot).plot(kind="line", ax=axis[0][1])
pivot.plot(kind="bar", ax=axis[1][0])
pd.np.log2(pivot).plot(kind="bar", ax=axis[1][1])
for ax in axis.flatten():
    ax.set_xticklabels([])
fig.savefig("lineplot.svg", bbox_inches="tight")

# with total too
fig, axis = plt.subplots(2, 2)
pivot.sum(1).plot(kind="line", ax=axis[0][0])
pd.np.log2(pivot.sum(1)).plot(kind="line", ax=axis[0][1])
pivot.sum(1).plot(kind="bar", ax=axis[1][0])
pd.np.log2(pivot.sum(1)).plot(kind="bar", ax=axis[1][1])
for ax in axis.flatten():
    ax.set_xticklabels([])
fig.savefig("lineplot.total.svg", bbox_inches="tight")


# with cumsum
fig, axis = plt.subplots(1)
pivot.sum(1).cumsum().plot(kind="line", ax=axis)
fig.savefig("lineplot.total.cumsum.svg", bbox_inches="tight")


# Work hours


work_deltas = pd.read_csv("data/work_log.deltas.csv", index_col=0)
work_deltas.index = work_deltas.index.to_datetime()
work_deltas = pd.to_timedelta(work_deltas.delta)

# Filter out "just passing by" days
work_deltas = work_deltas[work_deltas > pd.Timedelta("15 minutes")]

fig, axis = plt.subplots(1)
sns.distplot((work_deltas.dropna().dt.seconds / 60. / 60.).values, kde=False, bins=100)
fig.savefig("work.distplot.svg", bbox_inches="tight")

fig, axis = plt.subplots(1)
(work_deltas / pd.np.timedelta64(1, 'h')).plot(ax=axis)
axis.set_ylabel("Time per day (hours)")
sns.despine(fig)
fig.savefig("work.timeline.svg", bbox_inches="tight")
