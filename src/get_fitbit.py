import pandas as pd
import rpy2.robjects as robjects
import rpy2.robjects.numpy2ri
import pandas.rpy.common as com

rpy2.robjects.numpy2ri.activate()

robjects.r('require("fitbitScraper")')
get_daily_data = robjects.r('get_daily_data')
login = robjects.r('login')


params = [
    "distance", "floors", "minutesVery",
    "caloriesBurnedVsIntake"]


cookie = login(email="afrendeiro@gmail.com", password="")

fitbit = pd.DataFrame()
for param in params:
    df = com.convert_robj(
        get_daily_data(cookie, what=param, start_date="2015-01-01", end_date="2016-08-20")).icol(1)
    fitbit = pd.concat([fitbit, df], axis=1)

fitbit.index = pd.date_range(start="2015-01-01", end="2016-08-20")
fitbit.to_csv("data/fitbit.csv", index=True)
