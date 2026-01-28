import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
import cv2

from io import BytesIO
from PIL import Image
from fastdtw import fastdtw
from flask import jsonify, Flask
from skimage.metrics import structural_similarity as ssim
import databaseConnection
from compareImage import get_image_hash
import base64

cur = databaseConnection.conn.cursor()


def dtw_price_similarity(series1, series2):
    s1 = (series1 - series1.min()) / (series1.max() - series1.min())
    s2 = (series2 - series2.min()) / (series2.max() - series2.min())

    min_len = min(len(s1), len(s2))
    s1, s2 = s1[:min_len], s2[:min_len]

    distance, _ = fastdtw(s1, s2)
    return 100 / (1 + distance)


def edge_ssim_similarity(img_bytes1, img_bytes2, size=(800, 600)):
    img1 = Image.open(BytesIO(img_bytes1)).convert("L").resize(size)
    img2 = Image.open(BytesIO(img_bytes2)).convert("L").resize(size)

    img1 = np.array(img1)
    img2 = np.array(img2)

    edges1 = cv2.Canny(img1, 50, 150)
    edges2 = cv2.Canny(img2, 50, 150)

    score, _ = ssim(
        edges1,
        edges2,
        full=True,
        data_range=edges2.max() - edges2.min()
    )

    return score * 100


def hybrid_similarity(ref_close, cmp_close, ref_img, cmp_img):
    dtw_score = dtw_price_similarity(ref_close, cmp_close)
    edge_score = edge_ssim_similarity(ref_img, cmp_img)

    hybrid = (0.7 * dtw_score) + (0.3 * edge_score)

    return round(dtw_score, 2), round(edge_score, 2), round(hybrid, 2)


def hybrid_similarity(ref_close, cmp_close, ref_img, cmp_img):
    dtw_score = dtw_price_similarity(ref_close, cmp_close)
    edge_score = edge_ssim_similarity(ref_img, cmp_img)

    hybrid = (0.7 * dtw_score) + (0.3 * edge_score)

    return round(dtw_score, 2), round(edge_score, 2), round(hybrid, 2)

app = Flask(__name__)
@app.route("/get-best-15m-image", methods=["GET"])
def compare_latest_with_all_hybrid():
    cur.execute("""
        SELECT id, close_price, image
        FROM nifty_15min_images
        ORDER BY id DESC
        LIMIT 1
    """)
    ref_id, ref_close_bytes, ref_img = cur.fetchone()
    ref_close = np.frombuffer(ref_close_bytes, dtype=np.float64)
    ref_img_bytes = bytes(ref_img)
    # ref_image = Image.open(BytesIO(ref_img_bytes)).convert("RGB")
    cur.execute("""
        SELECT id, close_price, image
        FROM nifty_15min_images
        WHERE id != %s
    """, (ref_id,))
    rows = cur.fetchall()

    best_id = None
    best_score = -1

    for img_id, close_bytes, img in rows:
        close_arr = np.frombuffer(close_bytes, dtype=np.float64)

        dtw_s, edge_s, hybrid_s = hybrid_similarity(
            ref_close, close_arr, ref_img, img
        )

        print(f"ID {img_id} → DTW {dtw_s}% | Edge {edge_s}% | Hybrid {hybrid_s}%")

        if hybrid_s > best_score:
            best_score = hybrid_s
            best = (img_id, hybrid_s)

    print(f"\nBEST MATCH → ID {best[0]} | Hybrid Score {best[1]}%")

    print(f"Reference ID: {ref_id}, Best Match ID: {best[0]}, Similarity: {best[1]:.2f}%")
    # Combine images side by side
    cur.execute(f"""
            SELECT image FROM nifty_15min_images
            where Id = %s
        """, (best[0],))
    row1 = cur.fetchone()
    best_img_bytes = bytes(row1[0])
    best_image = Image.open(BytesIO(best_img_bytes)).convert("RGB")
    buffer = BytesIO()
    best_image.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    best_hash = get_image_hash(best_img_bytes)
    return jsonify({
        "image": img_base64,
        "best_id": best_id,
        "score": best_score
    })
    # width = ref_image.width + best_image.width
    # height = max(ref_image.height, best_image.height)
    #
    # combined = Image.new("RGB", (width, height))
    # combined.paste(ref_image, (0, 0))
    # combined.paste(best_image, (ref_image.width, 0))
    #
    # combined.show()
