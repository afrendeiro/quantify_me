import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("white")

pd.set_option("date_dayfirst", True)

# Git

# Read in git data
git = pd.read_csv("data/git_log.filtered.anonymized.csv")

# Work with the data
git["change"] = git["change"].astype(pd.np.int64)
git["date"] = pd.to_datetime(git["date"])
git["time"] = pd.to_datetime(git["date"]).dt.time
git["day"] = pd.to_datetime(git["date"]).dt.date


git_pivot = pd.pivot_table(git, index="day", columns="repository", aggfunc=sum)
git_pivot.columns = git_pivot.columns.droplevel(0)
git_pivot.index = git_pivot.index.to_datetime()


# plot
git_pivot.plot(kind="line")
git_pivot.plot(kind="bar")


# fill with previous entry
git_pivot.asfreq(pd.DateOffset(), method="pad")

# resample
git_pivot.resample("1D", how="mean")


# limit to start date
git_pivot = git_pivot[git_pivot.index > pd.to_datetime("2014-09-15")]

# heatmap
df = git_pivot.T.sort_values(by=git_pivot.T.columns.tolist(), ascending=False)

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
git_pivot.plot(kind="line", ax=axis[0][0])
pd.np.log2(git_pivot).plot(kind="line", ax=axis[0][1])
git_pivot.plot(kind="bar", ax=axis[1][0])
pd.np.log2(git_pivot).plot(kind="bar", ax=axis[1][1])
for ax in axis.flatten():
    ax.set_xticklabels([])
fig.savefig("lineplot.svg", bbox_inches="tight")

# with total too
fig, axis = plt.subplots(2, 2)
git_pivot.sum(1).plot(kind="line", ax=axis[0][0])
pd.np.log2(git_pivot.sum(1)).plot(kind="line", ax=axis[0][1])
git_pivot.sum(1).plot(kind="bar", ax=axis[1][0])
pd.np.log2(git_pivot.sum(1)).plot(kind="bar", ax=axis[1][1])
for ax in axis.flatten():
    ax.set_xticklabels([])
fig.savefig("lineplot.total.svg", bbox_inches="tight")


# with cumsum
fig, axis = plt.subplots(1, figsize=(6, 1.5))
git_pivot.sum(1).cumsum().plot(kind="line", ax=axis, linewidth=4)
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


# Fitbit

fitbit = pd.read_csv("data/fitbit.csv")
fitbit = pd.pivot_table(fitbit, index="Unnamed: 0", columns="param")
fitbit.columns = fitbit.columns.droplevel(0)
fitbit.index = fitbit.index.to_datetime()


fig, axis = plt.subplots(1)
fitbit.plot(ax=axis)
axis.set_ylabel("Steps per 15 minutes")
sns.despine(fig)
fig.savefig("fitbit.timeline.svg", bbox_inches="tight")


# sleep

sleep = pd.read_csv("data/sleep_summary.csv")
sleep["From"] = pd.to_datetime(sleep["From"], dayfirst=True)
sleep["To"] = pd.to_datetime(sleep["To"], dayfirst=True)
sleep["Sched"] = pd.to_datetime(sleep["Sched"], dayfirst=True)

for i in sleep.index:
    sleep.loc[i, "date_range"] = pd.date_range(start=sleep["From"].ix[i], end=sleep["To"].ix[i])


# website

web = pd.read_csv("data/website_analytics.csv", index_col=0)
web.index = web.index.to_datetime()


# twitter
twitter = pd.read_csv("data/twiter_metrics.csv").set_index("time")
twitter.index = twitter.index.to_datetime()


fig, axis = plt.subplots(1)
twitter.drop(['Tweet id', 'Tweet permalink', 'Tweet text'], axis=1).plot(ax=axis)

twitter_resampled = twitter.drop(['Tweet id'], axis=1).groupby(pd.TimeGrouper('D')).transform(sum).resample('D').head(-1)  # , how='ohlc')
twitter_resampled["count_per_day"] = twitter.groupby(pd.TimeGrouper('D'))["Tweet id"].count().resample('D').head(-1)

twitter_resampled['count_per_day'].plot()
