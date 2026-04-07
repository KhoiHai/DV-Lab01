import requests
import pandas as pd
import time
import json
import os

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'accept': 'application/json, text/plain, */*',
    'referer': 'https://tiki.vn/',
}

def get_product_detail(product_id):
    '''
    Lấy thông tin chi tiết sản phẩm
        Shop_Name: Tên shop
        Origin: Nguồn gốc
        Created_At_Days: Số ngày mở bán từ trước đến hiện nay
        Sold_From_Detail: Số lượng bán, crawl để so sánh 
    '''
    detail_url = f"https://tiki.vn/api/v2/products/{product_id}"
    try:
        response = requests.get(detail_url, headers=headers, timeout=15)
        if response.status_code == 200:
            p = response.json()

            # Check freeship
            is_freeship = 0
            
            if p.get('is_free_delivery'):
                is_freeship = 1
            else:
                badges = p.get('badges_v3', []) or p.get('badges', [])
                for b in badges:
                    code = str(b.get('code', '')).lower()
                    if 'free' in code:
                        is_freeship = 1
                        break 
            
            for b in badges:
                code = str(b.get('code', '')).lower()
                if 'freeship' in code:
                    is_freeship = 1
            
            # Xuất xứ
            origin = "Không xác định"
            specs = p.get('specifications', [])
            for group in specs:
                for attr in group.get('attributes', []):
                    if 'xuất xứ' in attr.get('name', '').lower():
                        origin = attr.get('value')
                        
            # Lấy số lượng bán
            qs = p.get('quantity_sold', {})
            sold_detail = qs.get('value', 0) if isinstance(qs, dict) else p.get('all_time_quantity_sold', 0)
            if sold_detail is None: sold_detail = 0

            return {
                'Shop_Name': p.get('current_seller', {}).get('name', 'N/A'),
                'Origin': origin,
                'Is_FreeShip': is_freeship,
                'Created_At_Days': p.get('day_ago_created'),
                'Sold_From_Detail': sold_detail 
            }
    except Exception:
        return {}
    return {}

def crawling_tiki(categories_dict, pages_per_kw=5):
    '''
    Crawl dữ liệu từ Tiki:
        Platform: Nền tảng
        Main_Category: Danh mục chính
        Sub_Category: Phân loại sản phẩm
        ID: ID của sản phẩm
        Name: Tên sản phẩm
        Brand: Thương hiệu
        Price: Giá tiền bán ra
        Original_Price: Giá tiền gốc
        Discount: Giảm giá
        Rating: Đánh giá trung bình
        Reviews: Tổng số đánh giá
    '''
    all_results = []
    
    for main_cat, keywords in categories_dict.items():
        print(f"\n>>>> BẮT ĐẦU NHÓM: {main_cat.upper()} <<<<")
        
        for kw in keywords:
            print(f"--- Đang lấy từ khóa: {kw} ---")
            for page in range(1, pages_per_kw + 1):
                search_url = f"https://tiki.vn/api/v2/products?limit=40&q={kw}&page={page}&sort=top_seller"
                
                try:
                    res = requests.get(search_url, headers=headers, timeout=15)
                    if res.status_code != 200: break
                    
                    data = res.json()
                    products = data.get('data', [])
                    if not products: break
                    
                    for count, item in enumerate(products):
                        p_id = item.get('id')
                        print(f"[CRAWL][Trang {page}][{count + 1}] Lấy chi tiết SP {p_id}")
                        
                        # Lấy thông tin số lượng
                        qs_search = item.get('quantity_sold', {})
                        sold_search = qs_search.get('value', 0) if isinstance(qs_search, dict) else item.get('all_time_quantity_sold', 0)
                        if sold_search is None: sold_search = 0

                        # Xử lý giá gốc
                        price = item.get('price', 0)
                        list_price = item.get('list_price', 0)
                        if not list_price or list_price == 0:
                            list_price = price

                        base_data = {
                            'Platform': 'Tiki',
                            'Main_Category': main_cat,
                            'Sub_Category': kw,
                            'ID': p_id,
                            'Name': item.get('name'),
                            'Brand': item.get('brand_name', 'No Brand'),
                            'Price': price,
                            'Original_Price': list_price,
                            'Discount': item.get('discount_rate', 0),
                            'Rating': item.get('rating_average', 0),
                            'Reviews': item.get('review_count', 0),
                        }
                        
                        # Lấy thông tin chi tiết sản phẩm
                        details = get_product_detail(p_id)
                        
                        # So sánh để chọn số lớn nhất là số sản phẩm bán ra
                        sold_detail = details.get('Sold_From_Detail', 0)
                        base_data['Total_Sold'] = max(sold_search, sold_detail) # Thêm trường total sold
                        
                        # Xóa trường tạm
                        if 'Sold_From_Detail' in details: del details['Sold_From_Detail']
                        
                        base_data.update(details)
                        all_results.append(base_data)
                        
                        time.sleep(0.3) 
                except Exception as e:
                    print(f"Lỗi tại trang {page}: {e}")
                    continue        
    return all_results


# --- ĐỊNH NGHĨA DANH MỤC ---
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
    ]
}

# -------------------
# THỰC THI
# -------------------

# Tạo thư mục dữ liệu
if not os.path.exists("./Data/Tiki"):
    os.makedirs("./Data/Tiki")

raw_data = crawling_tiki(cosmetic_map, pages_per_kw = 5)

# Chuyển sang dataframe xử lý trùng lắp tạm
df = pd.DataFrame(raw_data)
df = df.drop_duplicates(subset=['ID'])

# Lưu CSV
df.to_csv("./Data/Tiki/cosmetic_data.csv", index=False, encoding='utf-8-sig')

# Lưu Json
df.to_json("./Data/Tiki/cosmetic_data.json", orient='records', force_ascii=False, indent=4)

print(f"\n=== HOÀN THÀNH ===")
print(f"Tổng số sản phẩm độc nhất: {len(df)}")
print(f"Dữ liệu đã được lưu tại ./Data/Tiki/beauty_mega_data.json")