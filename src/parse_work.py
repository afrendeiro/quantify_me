import pandas as pd


def disentangle((date, events)):
    """
    Calculates timedelta of work hours in a day
    """
    time = pd.Timedelta('0')
    start = pd.NaT
    for i, event in enumerate(sorted(events)):
        if work.ix[event].squeeze() == "entered":
            if pd.isnull(start):
                start = event
        elif work.ix[event].squeeze() == "exited":
            end = event
            try:
                time += end - start
            except UnboundLocalError:
                return (date, pd.NaT)
            start = pd.NaT
    return (date, time)


work = pd.read_csv("data/work_log.csv")
work["datetime"] = pd.to_datetime(work["datetime"], dayfirst=True)
work = work.set_index("datetime")
work.index = work.index.to_datetime()

# work.groupby(work.index.date).apply(disentangle)
deltas = pd.DataFrame(map(disentangle, work.groupby(work.index.date).groups.items()), columns=["date", "delta"]).set_index("date").sort_index().squeeze()

deltas = deltas.replace(pd.Timedelta('0'), pd.NaT)
deltas.to_csv("data/work_log.deltas.csv", header=True)
