from PIL import Image
from io import BytesIO
import databaseConnection
def selectDayData():
    cur = databaseConnection.conn.cursor()
    cur.execute("SELECT image FROM nifty_15min_images ORDER BY id DESC LIMIT 1")

    img_bytes = cur.fetchone()[0]
    Image.open(BytesIO(img_bytes)).show()

