import pandas as pd
import rpy2.robjects as robjects
import rpy2.robjects.numpy2ri
import pandas.rpy.common as com

rpy2.robjects.numpy2ri.activate()

robjects.r('require("fitbitScraper")')
login = robjects.r('login')
get_daily_data = robjects.r('get_daily_data')
get_intraday_data = robjects.r('get_intraday_data')


params = [
    "distance", "floors", "minutesVery",
    "caloriesBurnedVsIntake"]

params2 = ["steps", "distance", "floors", "active-minutes", "calories-burned", "heart-rate"]

cookie = login(email="afrendeiro@gmail.com", password="")

fitbit = pd.DataFrame()
for param in params2[3:]:
    for date in pd.date_range(start="2015-01-01", end="2016-08-20"):
        print(param, date)
        df = pd.DataFrame(
            com.convert_robj(
                get_intraday_data(cookie, what=param, date=str(date.date())))[param])
        df.index = date + pd.timedelta_range(start="00:00:00", periods=4 * 24, freq="15Min")
        df["param"] = param
        df.columns = ["value", "param"]
        fitbit = fitbit.append(df)


fitbit.to_csv("data/fitbit.csv", index=True)
