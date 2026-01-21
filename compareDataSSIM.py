from PIL import Image
from io import BytesIO
import databaseConnection
import numpy as np
from skimage.metrics import structural_similarity as ssim


def compare_latest_with_all_ssim():
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

    # Convert reference to grayscale (SSIM works best in gray)
    ref_gray = np.array(ref_image.convert("L"))

    # 2️⃣ Fetch all other images
    cur.execute("""
        SELECT id, image FROM nifty_15min_images
        WHERE id != %s
    """, (ref_id,))
    rows = cur.fetchall()

    if not rows:
        print("Only one image in DB, nothing to compare")
        return

    best_similarity = -1
    best_image = None
    best_id = None

    for img_id, img_bytes in rows:
        img = Image.open(BytesIO(img_bytes)).convert("RGB")

        # Resize if size mismatch
        if img.size != ref_image.size:
            img = img.resize(ref_image.size)

        img_gray = np.array(img.convert("L"))

        # 3️⃣ Compute SSIM
        score, _ = ssim(
            ref_gray,
            img_gray,
            full=True,
            data_range=img_gray.max() - img_gray.min()
        )

        similarity = score * 100  # convert to %

        if similarity > best_similarity:
            best_similarity = similarity
            best_image = img
            best_id = img_id

    # 4️⃣ Show result
    print(
        f"Reference ID: {ref_id}, "
        f"Best Match ID: {best_id}, "
        f"SSIM Similarity: {best_similarity:.2f}%"
    )

    width = ref_image.width + best_image.width
    height = max(ref_image.height, best_image.height)
    combined = Image.new("RGB", (width, height))
    combined.paste(ref_image, (0, 0))
    combined.paste(best_image, (ref_image.width, 0))
    combined.show()
