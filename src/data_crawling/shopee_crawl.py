import os
import json
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright # Dùng playwright để crawl dữ liệu 

# Tất cả các keyword cần search để crawl dữ liệu 
cosmetic_map = {
    "Skin Care": [
        "kem chống nắng", "serum dưỡng da", "sữa rửa mặt", "tẩy trang", 
        "mặt nạ dưỡng da", "kem dưỡng ẩm", "nước hoa hồng", "xịt khoáng", 
        "tẩy tế bào chết da mặt", "kem dưỡng mắt", "kem trị mụn", "kem chống lão hóa",
        "gel dưỡng da", "kem phục hồi da", "kem làm trắng da"
    ],
    "Makeup": [
        "son môi", "phấn nước cushion", "kem nền", "phấn phủ", 
        "chì kẻ mày", "mascara", "bút kẻ mắt", "phấn má hồng", "bông tẩy trang"
    ],
    "Body Care": [
        "sữa tắm", "sữa dưỡng thể", "tẩy tế bào chết body", "kem dưỡng da tay",
        "kem dưỡng trắng body", "body lotion", "body oil"
    ],
    "Hair Care": [
        "dầu gội đầu", "dầu xả tóc", "kem ủ tóc", "tinh dầu dưỡng tóc", "xịt dưỡng tóc", "dầu gội trị gàu",
        "dầu gội phục hồi", "kem tạo kiểu tóc", "sáp vuốt tóc", "keo xịt tóc"
    ],
    "Oral Care": [
        "kem đánh răng", "bàn chải đánh răng", "nước súc miệng", "máy tăm nước", "bột tẩy trắng răng",
        "chỉ nha khoa"
    ],
    "Fragrance": [
        "nước hoa nam", "nước hoa nữ", "body mist",
        "nước hoa mini", "nước hoa unisex"
    ],
    "Dermocosmetic": [
        "dược mỹ phẩm", "retinol", "bha", "aha", "azelaic acid"
    ],
    "Beauty_Devices": [
        "máy rửa mặt", "máy triệt lông", "máy tăm nước", "máy uốn tóc", 
        "máy sấy tóc", "máy massage mặt", "máy xông mặt", "lược điện"
    ]
}

def run(playwright):
    user_data_dir = os.path.join(os.getcwd(), "shopee_user_data") # Thư mục lưu cache và thông tin
    output_dir = "Data/Shopee" # Thư mục nơi lưu dữ liệu 
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    context = playwright.chromium.launch_persistent_context(
        user_data_dir, 
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )
    page = context.pages[0]

    print("[KHỞI ĐỘNG] Đang mở Shopee...")
    page.goto("https://shopee.vn", wait_until="domcontentloaded")
    
    print("[USER ACTION] Người dùng vui lòng đăng nhập/giải captcha trên trình duyệt...")
    input("[USER ACTION] Sau khi hoàn thành, nhấn ENTER để bắt đầu...")

    sort_modes = ["relevancy", "sales"] # Tìm kiếm theo hai chế độ: liên quan, bán chạy

    for main_cat, sub_cats in cosmetic_map.items():
        for sub_cat in sub_cats:
            print(f"\n [CRAWL] Category: {main_cat} -> {sub_cat}")
            items_dict = {}

            def handle_response(response):
                # Catch api trên Shopee
                if "api/v4/search/search_items" in response.url and response.status == 200:
                    try:
                        data = response.json()
                        items = data.get('items', [])
                        for item in items:
                            info = item.get('item_basic')
                            if info:
                                p_id = info.get('itemid')
                                s_id = info.get('shopid')
                                
                                # Mỗi sản phẩm định danh bởi cặp thuộc tính (ID, Shop_ID)
                                if (s_id, p_id) not in items_dict:
                                    # 1. Tính toán giá và giảm giá
                                    price = info.get('price') / 100000
                                    raw_price_before = info.get('price_before_discount')
                                    price_before = raw_price_before / 100000 if raw_price_before and raw_price_before > 0 else price
                                    
                                    discount_percent = 0
                                    if price_before > price:
                                        discount_percent = round(((price_before - price) / price_before) * 100, 1)

                                    # 2. Tính số ngày đã đăng (ctime là timestamp)
                                    ctime = info.get('ctime', 0)
                                    created_at_days = 0
                                    if ctime > 0:
                                        delta = datetime.now().timestamp() - ctime
                                        created_at_days = round(delta / 86400, 1)

                                    items_dict[(s_id, p_id)] = {
                                        "Platform": "Shopee",
                                        "Main_Category": main_cat,
                                        "Sub_Category": sub_cat,
                                        "ID": p_id,
                                        "Shop_ID": s_id,
                                        "Name": info.get('name'),
                                        "Brand": info.get('brand', 'No Brand') or 'No Brand',
                                        "Price": price,
                                        "Original_Price": price_before,
                                        "Discount_Percent": discount_percent,
                                        "Rating": info.get('item_rating', {}).get('rating_star'),
                                        "Reviews": info.get('cmt_count'),
                                        "Monthly_Sold": info.get('sold'),
                                        "Total_Sold": info.get('historical_sold'),
                                        "Liked_Count": info.get('liked_count'),
                                        "Shop_Location": info.get('shop_location'),
                                        "Is_Mall": 1.0 if info.get('is_official_shop') else 0.0,
                                        "Is_Verified": 1.0 if info.get('shopee_verified') else 0.0,
                                        "Is_FreeShip": 1.0 if info.get('show_free_shipping') else 0.0,
                                        "Is_Ads": 1.0 if item.get('adsid') else 0.0,
                                        "Created_At_Days": created_at_days
                                    }
                    except Exception as e:
                        print(f"Lỗi phân tích JSON: {e}")
            page.on("response", handle_response)
            
            # Crawl 9 trang mỗi mode 
            for mode in sort_modes:
                for page_num in range(0, 9): 
                    target_url = f"https://shopee.vn/search?keyword={sub_cat}&page={page_num}&sortBy={mode}"
                    print(f"[CRAWL] Đang crawl dữ liệu tại {target_url}")

                    try:
                        page.goto(target_url, wait_until="commit", timeout=60000)
                        
                        # Cuộn trang để đợi API và mô phỏng người dùng
                        for i in range(4):
                            page.mouse.wheel(0, 800)
                            time.sleep(random.uniform(0.5, 1.0))
                        page.wait_for_timeout(2000)

                    except Exception as e:
                        print(f"Lỗi khi tải trang: {e}")
                    time.sleep(random.uniform(3, 7))

            page.remove_listener("response", handle_response)

            if items_dict:
                file_name = f"{main_cat}_{sub_cat}.json".replace(" ", "_").replace("/", "-")
                file_path = os.path.join(output_dir, file_name)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(list(items_dict.values()), f, ensure_ascii=False, indent=4)
                print(f"Đã lưu {len(items_dict)} sản phẩm vào {file_name}")
            time.sleep(random.uniform(5, 10))
    context.close()

if __name__ == "__main__":
    with sync_playwright() as p:
        run(p)