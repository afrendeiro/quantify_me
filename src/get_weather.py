import pandas as pd
import forecastio

api_key = ""

# read in sleep data
sleep = pd.read_csv("data/sleep_summary.csv").set_index("From")
sleep.index = sleep.index.to_datetime(dayfirst=True)
sleep = sleep.sort_index()

# Let's resample the data every day with backward fill (assumes data until next observation is same as before)
sleep = sleep.resample("D", base=7).bfill()

# make dict with timezones and probable coordinates
mapping = {
    'Europe/Amsterdam': (48.226182, 16.353188),
    'Europe/Vienna': (48.226182, 16.353188),
    'Europe/Lisbon': (40.739146, -8.649522),
    'Atlantic/Madeira': (40.739146, -8.649522),
    'Europe/London': (40.739146, -8.649522),
    'GMT': (48.226182, 16.353188),
}

# Get weather for each time/location
forecasts = [forecastio.load_forecast(api_key, *mapping[sleep.ix[t]["Tz"]], time=t.to_datetime()) for t in sleep.index]


daily_attrs = ["time", "icon", "sunriseTime", "sunsetTime", "moonPhase"]
hourly_attrs = [
    "time",
    "temperature", "apparentTemperature", "precipIntensity", "windSpeed",
    "windBearing", "cloudCover", "humidity", "pressure", "dewPoint", "visibility"]

weather = list()
for i, forecast in enumerate(forecasts):
    ids = [i, forecast.json['timezone'], forecast.json['latitude'], forecast.json['longitude']]

    daily = forecast.daily().data[0]
    d = [getattr(daily, attr) if hasattr(daily, attr) else pd.np.nan for attr in daily_attrs]

    hourly = forecast.hourly().data
    for hour in hourly:
        h = [getattr(hour, attr) if hasattr(hour, attr) else pd.np.nan for attr in hourly_attrs]
        weather.append(ids + d + h)

weather = pd.DataFrame(weather, columns=['record', 'timezone', 'latitude', 'longitude'] + daily_attrs + hourly_attrs)
weather.to_csv("data/weather.csv", index=False)
