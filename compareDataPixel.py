from PIL import Image, ImageChops
from io import BytesIO
import databaseConnection
import numpy as np

def compare_latest_with_all_pixel():
    cur = databaseConnection.conn.cursor()

    # 1️⃣ Get latest image
    cur.execute("""
        SELECT id, image FROM nifty_15min_images
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row is None:
        print("No images in DB")
        return

    ref_id, ref_img_bytes = row
    ref_image = Image.open(BytesIO(ref_img_bytes)).convert("RGB")

    # 2️⃣ Fetch all other images
    cur.execute("""
        SELECT id, image FROM nifty_15min_images
        WHERE id != %s
    """, (ref_id,))
    rows = cur.fetchall()

    if not rows:
        print("Only one image in DB, nothing to compare")
        return

    # 3️⃣ Compare pixel-by-pixel
    best_similarity = -1
    best_image = None
    best_id = None

    ref_array = np.array(ref_image)

    for img_id, img_bytes in rows:
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        img_array = np.array(img)

        # Resize to reference size if different
        if img_array.shape != ref_array.shape:
            img = img.resize(ref_image.size)
            img_array = np.array(img)

        # Compute similarity
        diff = np.abs(ref_array.astype(int) - img_array.astype(int))
        total_pixels = ref_array.shape[0] * ref_array.shape[1] * ref_array.shape[2]
        similarity = 100 - (diff.sum() / (255 * total_pixels) * 100)

        if similarity > best_similarity:
            best_similarity = similarity
            best_image = img
            best_id = img_id

    # 4️⃣ Show reference and best match side by side
    print(f"Reference ID: {ref_id}, Best Match ID: {best_id}, Similarity: {best_similarity:.2f}%")
    width = ref_image.width + best_image.width
    height = max(ref_image.height, best_image.height)
    combined = Image.new("RGB", (width, height))
    combined.paste(ref_image, (0, 0))
    combined.paste(best_image, (ref_image.width, 0))
    combined.show()
