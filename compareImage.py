from PIL import Image
import numpy as np
import databaseConnection
from PIL import Image
from io import BytesIO
import imagehash
def get_image_hash(image_bytes):
    image = Image.open(BytesIO(image_bytes)).convert("L")
    return imagehash.phash(image)


def compare_latest_with_all():
    cur = databaseConnection.conn.cursor()

    # Get latest image
    cur.execute("""
        SELECT id, image, candle_date FROM nifty_15min_images
        ORDER BY id DESC LIMIT 1
    """)
    row = cur.fetchone()
    if row is None:
        print("No images in DB yet.")
        return
    ref_id, ref_img_bytes, ref_date = row
    ref_hash = get_image_hash(ref_img_bytes)
    ref_image = Image.open(BytesIO(ref_img_bytes))

    # Get all other images
    cur.execute("""
        SELECT id, image,candle_date FROM nifty_15min_images
        WHERE id != %s
    """, (ref_id,))
    rows = cur.fetchall()
    results = []
    if not rows:
        print("Only one image in DB, nothing to compare.")
        return

        # 3️⃣ Compare hashes
    best_similarity = -1
    best_image = None
    best_id = None
    for img_id, img_bytes in cur.fetchall():
        img_hash = get_image_hash(img_bytes)
        distance = ref_hash - img_hash  # Hamming distance
        similarity = 100 - (distance * 100 / len(ref_hash.hash.flatten()))

        results.append((img_id, round(similarity, 2)))

    # Sort by similarity
    results.sort(key=lambda x: x[1], reverse=True)

    print(f"Reference image ID: {ref_id}")
    for img_id, score in results:
        print(f"Image {img_id} → Similarity: {score}%")
    for img_id, img_bytes, candle_date in rows:
        img_hash = get_image_hash(img_bytes)
        distance = ref_hash - img_hash
        similarity = 100 - (distance * 100 / len(ref_hash.hash.flatten()))

        if similarity > best_similarity:
            best_similarity = similarity
            best_image = Image.open(BytesIO(img_bytes))
            best_id = img_id

        # 4️⃣ Show both images
    if best_image is not None:
        print(f"Reference ID: {ref_id}, Best Match ID: {best_id}, Similarity: {best_similarity:.2f}%")
        # Combine images side by side
        width = ref_image.width + best_image.width
        height = max(ref_image.height, best_image.height)
        combined = Image.new("RGB", (width, height))
        combined.paste(ref_image, (0, 0))
        combined.paste(best_image, (ref_image.width, 0))
        combined.show()