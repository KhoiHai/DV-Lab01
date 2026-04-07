import json
import os
from collections import Counter

def check_duplicate(folder_path):
    if not os.path.exists(folder_path):
        print(f"Lỗi: Không tìm thấy thư mục tại {folder_path}")
        return

    all_products = []
    json_files = []

    # Quét toàn bộ file json trong folder (kể cả subfolder)
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))

    print(f"Tìm thấy {len(json_files)} file JSON\n")

    # Đọc từng file
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                products = data if isinstance(data, list) else [data]
                all_products.extend(products)
        except Exception as e:
            print(f"Lỗi đọc file {file_path}: {e}")

    print(f"Tổng số record (gộp tất cả file): {len(all_products)}")

    # Tạo danh sách (Shop_ID, ID)
    id_pairs = []
    for item in all_products:
        s_id = item.get("Shop_ID")
        p_id = item.get("ID")
        if s_id and p_id:
            id_pairs.append((s_id, p_id))

    counts = Counter(id_pairs)
    unique_pairs = len(counts)

    print(f"Số lượng (Shop_ID, ID) unique: {unique_pairs}")
    print(f"Tỷ lệ duplicate: {round((1 - unique_pairs/len(all_products)) * 100, 2)}%")

    print("-" * 60)
    print(f"{'STT':<5} | {'Shop_ID':<15} | {'Product_ID':<15} | {'Số lần lặp'}")
    print("-" * 60)

    for i, ((s_id, p_id), count) in enumerate(counts.items(), 1):
        print(f"{i:<5} | {s_id:<15} | {p_id:<15} | {count}")

        if i >= 50:
            print(f"... và {len(counts) - 50} cặp khác")
            break

folder_path = "Data/New_Shopee"
check_duplicate(folder_path)