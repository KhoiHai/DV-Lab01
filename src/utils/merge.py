import json
import os
import glob

def merge_data(input_folder, output_file):
    seen_keys = set()
    unique_products = []

    file_pattern = os.path.join(input_folder, "*.json")
    files = sorted(glob.glob(file_pattern))

    print(f"--- BẮT ĐẦU DEDUPLICATE ---")
    print(f"Tìm thấy: {len(files)} file\n")

    total_records = 0
    duplicate_count = 0

    for index, file_path in enumerate(files, 1):
        file_name = os.path.basename(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                products = data if isinstance(data, list) else [data]

                for item in products:
                    total_records += 1

                    s_id = item.get("Shop_ID")
                    p_id = item.get("ID")

                    if s_id is None or p_id is None:
                        continue

                    key = (s_id, p_id)

                    if key not in seen_keys:
                        seen_keys.add(key)
                        unique_products.append(item)  # giữ nguyên item
                    else:
                        duplicate_count += 1

                print(f"[{index}/{len(files)}] {file_name} | Tổng unique: {len(unique_products)}")

            except Exception as e:
                print(f"[LỖI] {file_name}: {e}")

    # Lưu file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_products, f, ensure_ascii=False, indent=4)

    print(f"\n--- KẾT QUẢ ---")
    print(f"Tổng record ban đầu: {total_records}")
    print(f"Số record unique: {len(unique_products)}")
    print(f"Số duplicate bị loại: {duplicate_count}")
    print(f"Tỷ lệ duplicate: {round(duplicate_count / total_records * 100, 2)}%")
    print(f"Lưu tại: {output_file}")


# --- CHẠY ---
merge_data('Data/New_Shopee', 'shopee_deduplicated.json')