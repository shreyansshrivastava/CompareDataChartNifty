import compareDataHybrid
import compareDataPixel
import compareDataSSIM
import databaseConnection
import checkDbTable
import SelectDataFromDb
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import os
from io import BytesIO
import insertDataDb
import compareImage
import compareDataHybrid

# Fetch NIFTY daily data
# df = yf.download("^NSEI", period="1mo", interval="1d", auto_adjust=False,
#     progress=False)

df = yf.download("^NSEI", period="30d", interval="15m", auto_adjust=False,
    progress=False)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)


df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

df = df.apply(pd.to_numeric, errors='coerce')

df.dropna(inplace=True)

df.index = pd.to_datetime(df.index)
df['date'] = df.index.date
grouped = df.groupby('date')
interval = '15m'
checkDbTable.checkTable()
for date, day_df in df.groupby('date'):
    day_df = day_df.drop(columns=['date'])

    if len(day_df) < 5:  # skip partial days
        continue

    # Save image to BytesIO (in memory)
    image_buffer = BytesIO()

    mpf.plot(
        day_df,
        type='candle',
        volume=True,
        style='yahoo',
        title=f"NIFTY 15-Min Candlestick ({date})",
        savefig=image_buffer
    )
    image_buffer.seek(0)  # go to start of buffer
    image_bytes = image_buffer.read()
    # Insert into DB
    print(f"Saved image for {date} to DB")
    close_bytes = day_df['Close'].values.tobytes()
    insertDataDb.insertData(date, interval,close_bytes, image_bytes)
print("Candlestick image saved")

#compareDataPixel.compare_latest_with_all_pixel()
#SelectDataFromDb.selectDayData()
#compareDataSSIM.compare_latest_with_all_ssim()
compareDataHybrid.compare_latest_with_all_hybrid()
databaseConnection.conn.commit()





