import yfinance as yf
import pandas as pd 

#for Turkey .IS on yfinance
hisse = input("key")
dailydata = yf.Ticker(hisse+".IS)
history = pd.DataFrame(dailydata.history(period="max"))

with pd.ExcelWriter("{}.xlsx".format(hisse),mode="a") as writer:
  history.to_excel(writer, sheet_name="Technical Daily Data")

