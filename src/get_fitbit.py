#!/usr/bin/env python

"""

"""

import json
from pathlib import Path
import datetime
import glob
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import fitbit
import src.gather_keys_oauth2 as Oauth2


def camel_case(st: str) -> str:
    output = "".join(x for x in st.title() if x.isalnum())
    return output[0].lower() + output[1:]


def flatten_dict_to_cammel_case(
    my_dict: dict, existing_dict: dict = None, previous_key: str = ""
) -> dict:
    if existing_dict is None:
        existing_dict = {}
    for k, v in my_dict.items():
        if isinstance(v, dict):
            flatten_dict_to_cammel_case(
                v,
                existing_dict,
                previous_key=previous_key + k[0].upper() + k[1:],
            )
        elif isinstance(v, list):
            # pass
            # assumes each list element is a dict
            for i, v2 in enumerate(v):
                name = camel_case(v2["name"]) if "name" in v2 else str(i)
                flatten_dict_to_cammel_case(
                    v2, existing_dict, previous_key=k + name
                )
        else:
            nk = previous_key + (
                k[0].upper() + k[1:] if previous_key != "" else k
            )
            existing_dict[nk] = v
    return existing_dict


def parse_distances(activities, prefix=""):
    return {
        prefix + a["activity"][0].upper() + a["activity"][1:]: a["distance"]
        for a in activities
    }


def get_daily_data(start: datetime.datetime, results: dict, min_wait: int = 15):
    def get_data(start: datetime.datetime, results: dict):
        for day in range((datetime.datetime.now() - start).days):
            date = datetime.datetime.now() - datetime.timedelta(days=day)
            if date.strftime("%Y%m%d") in results:
                continue
            print(date.strftime("%Y%m%d"))
            # daily
            # # activity
            act = auth2_client.activities(date)
            act["activities"]  # -> list
            res = flatten_dict_to_cammel_case(
                {k: v for k, v in act["summary"].items() if k != "distances"}
            )
            res.update(
                parse_distances(act["summary"]["distances"], prefix="distance")
            )

            # # sleep
            sleep = auth2_client.get_sleep(date)
            res.update(
                flatten_dict_to_cammel_case(
                    sleep["summary"], previous_key="sleep"
                )
            )
            results[date.strftime("%Y%m%d")] = res
        return results

    def save(results: dict):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        pd.DataFrame(results).T.to_csv(f"data/raw/fitbit.{today}.csv")

    while True:
        try:
            results = get_data(start, results)
        except fitbit.exceptions.HTTPTooManyRequests:
            print(f"Too many requests. Waiting {min_wait} minutes!")
            save(results)
            time.sleep(min_wait * 60)
        except KeyboardInterrupt:
            print(f"User interrupted! Saving current progress.")
            save(results)
            return results
        else:
            break
    print("Finished successfully!")
    save(results)
    return results


creds = json.load(open(Path("~/.fitbit.auth.json").expanduser()))

server = Oauth2.OAuth2Server(**creds)
server.browser_authorize()
ACCESS_TOKEN = str(server.fitbit.client.session.token["access_token"])
REFRESH_TOKEN = str(server.fitbit.client.session.token["refresh_token"])
auth2_client = fitbit.Fitbit(
    **creds, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN
)


# Take any existing data to avoid re-querying it
try:
    f = sorted(glob.glob("data/raw/fitbit.*-*-*.csv"))[-1]
    results = pd.read_csv(f, index_col=0)
    results.index = results.index.astype(str)
    results = results.T.to_dict()
except (KeyError, IndexError):
    results = dict()

# Earliest date for fitbit usage
# start = datetime.datetime(2014, 10, 19)
start = datetime.datetime(2014, 9, 15)


# Update query
results = get_daily_data(start, results)


# Plot
f = sorted(glob.glob("data/raw/fitbit.*-*-*.csv"))[-1]
results = pd.read_csv(f, index_col=0)
results.index = results.index.astype(str)
results.index = pd.to_datetime(results.index)

results = results.loc[
    :, (results.dtypes == "float64") & (results.nunique() > 2)
]

# # # sleep
for keyword, variables, direction in [
    ("sleep", "sleep", None),
    ("distance", "distance", None),
    ("heartRate", "heartRate", None),
    ("activity", "sleep|distance|heartRate", "invert"),
]:
    func = np.invert if direction is not None else lambda x: x
    vars_ = results.columns[func(results.columns.str.contains(variables))]
    p = results.loc[results[vars_].sum(1) != 0, vars_].sort_index()

    fig, axis = plt.subplots(len(vars_), 1, figsize=(8, 3 * len(vars_)))
    for ax, var_ in zip(axis.flatten(), vars_):
        ax.plot(p.index, p[var_], "-o", alpha=0.9, label=var_)
        ax.set_ylabel(var_)
    ax.set_xlabel("Date")
    fig.savefig(f"viz/{keyword}.daily.svg", dpi=300, bbox_inches="tight")
    plt.close(fig)

# Explore
p = results.sort_index()

m = p["restingHeartRate"].mean()
vmin = m - p["restingHeartRate"].std() * 3
vmax = m + p["restingHeartRate"].std() * 3


fig, axes = plt.subplots(
    1,
    2,
    figsize=(3 * 2, 3 * 1),
    gridspec_kw=dict(width_ratios=(0.7, 0.3)),
    sharey=True,
)
axes[0].set(ylabel="Resting heart rate")
axes[0].plot(p.index, p["restingHeartRate"], "--", alpha=0.1, c="grey")
axes[0].scatter(
    p.index,
    p["restingHeartRate"],
    c=p["restingHeartRate"],
    alpha=0.5,
    cmap="coolwarm",
    vmin=vmin,
    vmax=vmax,
    s=2,
)
axes[1].plot(p.index, p["restingHeartRate"], "--", alpha=0.1, c="grey")
axes[1].scatter(
    p.index,
    p["restingHeartRate"],
    c=p["restingHeartRate"],
    alpha=0.75,
    cmap="coolwarm",
    vmin=vmin,
    vmax=vmax,
    s=5,
)
axes[1].set_xlim((datetime.datetime(2020, 10, 15), datetime.datetime.today()))
# for ax in axes:
#     ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
fig.savefig("viz/202011.illness.svg", bbox_inches="tight")

# # intraday

# # # heart rate
# today = datetime.date.today()

# heart = auth2_client.intraday_time_series(
#     "activities/heart", base_date=today, detail_level="1sec"
# )
# heart["activities-heart"][0]["value"]["restingHeartRate"]


# # # sleep
# sleep = auth2_client.get_sleep(datetime.datetime.now())
# sleep["sleep"]  # -> list
# {
#     "awakeCount",
#     "awakeDuration",
#     "awakeningsCount",
#     "dateOfSleep",
#     "duration",
#     "efficiency",
#     "endTime",
#     "isMainSleep",
#     "logId",
#     "minutesAfterWakeup",
#     "minutesAsleep",
#     "minutesAwake",
#     "minutesToFallAsleep",
#     "restlessCount",
#     "restlessDuration",
#     "startTime",
#     "timeInBed",
# }
