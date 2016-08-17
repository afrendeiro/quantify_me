import pandas as pd

with open("data/sleep-export.csv", "r") as handle:
    data = handle.read()

starts = list()
for i, line in enumerate(data.split("\n")):
    if line.startswith("Id,Tz,From,To"):
        starts.append(i)

sleep = pd.DataFrame()
activity = pd.DataFrame()
events = pd.DataFrame()
noise = pd.DataFrame()

data = data.replace("\"", "").split("\n")
for i, start in enumerate(starts):
    print(start)
    series = pd.Series(data[start + 1].strip().split(","), data[start].strip().split(","))

    # Split data

    # general
    s = series[~(series.index.str.contains(":")) & ~(series.index == "Event")]
    sleep = sleep.append(s, ignore_index=True)

    # activity
    a = pd.DataFrame(series[series.index.str.contains(":")].astype(float), columns=["activity"])
    a["timestamp"] = s["Id"]
    activity = activity.append(a)

    # events
    if "Event" in series.index:
        e = series.ix["Event"].str.split("-").apply(pd.Series)
        e.columns = ["event", "timestamp"]
        events = events.append(e)

    if start != starts[-1]:
        if starts[i + 1] - start == 3:
            # noise
            n = pd.DataFrame(data[start + 2].split(","), columns=["noise"])
            n = n[n["noise"] != ""].reset_index(drop=True)
            n["timestamp"] = s["Id"]
            noise = noise.append(n)

sleep.to_csv("data/sleep_summary.csv", index=False)
activity.to_csv("data/sleep_activity.csv", index=True)
events.to_csv("data/sleep_events.csv", index=False)
noise.to_csv("data/sleep_noise.csv", index=False)
