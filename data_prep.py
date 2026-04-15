"""
============================================================
DATA PREP SCRIPT - ETL Pipeline
============================================================
Mục đích: Trích xuất, Biến đổi và Nạp dữ liệu Chương trình 
Đào tạo (CTĐT) từ file gốc của trường thành Cơ sở Tri thức 
(Knowledge Base) cho Hệ thống Tư vấn Hướng nghiệp AI.

Input:  CTĐT.xlsx (nhiều Sheet, mỗi Sheet = 1 Khóa)
Output: course_database.xlsx (5 cột chuẩn hóa: Mã HP, Tên HP, Nhóm NL, Loại môn, Học kỳ)
============================================================
"""
import pandas as pd
import os
import sys
import re
import logging

# === CẤU HÌNH ===
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "CTĐT.xlsx")
OUTPUT_FILE = os.path.join(BASE_DIR, "course_database.xlsx")

# Các giá trị hợp lệ của cột "Khối kiến thức" cần giữ lại
VALID_KNOWLEDGE_BLOCKS = [
    'Kiến thức Cơ sở ngành',
    'Kiến thức ngành',
    'Kiến thức chuyên ngành',
]

# Bộ từ điển gán nhãn Nhóm năng lực (String Matching)
CRITERIA_KEYWORDS = {
    'C1': [
        'lập trình', 'cấu trúc dữ liệu và giải thuật', 'thuật toán',
        'web', 'game', 'di động', 'java', 'c++', 'python',
        'phần mềm', 'cấu trúc dữ liệu', '.net', 'android',
        'mobile', 'ứng dụng', 'ngôn ngữ',
    ],
    'C2': [
        'dữ liệu', 'data', 'máy học', 'trí tuệ nhân tạo',
        'xử lý ảnh', 'toán', 'xác suất', 'thống kê',
        'khai thác', 'olap', 'học sâu', 'deep learning',
        'mô hình hóa', 'đồ thị', 'rời rạc',
    ],
    'C3': [
        'hệ điều hành', 'kiến trúc', 'mạng', 'bảo mật',
        'đám mây', 'hệ thống', 'phần cứng', 'nhúng', 'iot',
        'cloud', 'an toàn', 'điện tử', 'internet of things',
        'viễn thám', 'linux', 'server',
    ],
    'C4': [
        'quản lý', 'dự án', 'kiểm thử', 'chất lượng',
        'phân tích', 'thiết kế', 'phương pháp', 'đồ án',
        'uml', 'agile', 'scrum', 'hỗ trợ ra quyết định',
        'tìm kiếm', 'tối ưu',
    ],
}


def classify_criteria(subject_name: str) -> str:
    """
    Gán nhãn Nhóm năng lực (C1-C5) cho một môn học 
    dựa trên String Matching với tên môn.
    """
    if not isinstance(subject_name, str):
        return 'C5'
    
    name_lower = subject_name.lower().strip()
    
    for criteria, keywords in CRITERIA_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return criteria
    
    return 'C5'  # Mặc định: Kiến thức Nghiệp vụ Chuyên ngành


def classify_course_type(tu_chon_value) -> str:
    """
    Phân loại Loại môn (Bắt buộc / Tự chọn) dựa trên 
    giá trị cột 'Tự chọn theo khối KT'.
    """
    if pd.isna(tu_chon_value) or str(tu_chon_value).strip() == '':
        return 'Bắt buộc'
    return 'Tự chọn'


def extract_data(file_path: str) -> pd.DataFrame:
    """
    BƯỚC 1 - EXTRACT: Trích xuất dữ liệu từ tất cả các Sheet.
    Lọc chỉ giữ các môn thuộc khối kiến thức chuyên ngành.
    """
    logging.info(f"[EXTRACT] Đang mở file: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
    
    # Đọc danh sách Sheet
    xl = pd.ExcelFile(file_path, engine='openpyxl')
    sheet_names = xl.sheet_names
    logging.info(f"[EXTRACT] Tìm thấy {len(sheet_names)} Sheet: {sheet_names}")
    
    all_frames = []
    
    for sheet_name in sheet_names:
        logging.info(f"[EXTRACT] Đang đọc Sheet: '{sheet_name}'...")
        
        try:
            # Đọc raw data, skip dòng sub-header (Row 1 trong Excel)
            # Header nằm ở Row 0
            df = pd.read_excel(
                xl, 
                sheet_name=sheet_name, 
                header=0,     # Row 0 là header
                skiprows=[1], # Skip sub-header (LT, BT, TH...)
                engine='openpyxl'
            )
            
            # Chuẩn hóa tên cột (loại bỏ khoảng trắng thừa)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Kiểm tra các cột bắt buộc
            required_cols = ['Mã học phần', 'Tên học phần mới', 'Khối kiến thức', 'Học kỳ']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                logging.warning(f"  -> Sheet '{sheet_name}' thiếu cột: {missing}. Bỏ qua!")
                continue
            
            # Lọc theo Khối kiến thức
            df_filtered = df[
                df['Khối kiến thức'].isin(VALID_KNOWLEDGE_BLOCKS)
            ].copy()
            
            # Thêm cột nguồn để debug
            df_filtered['_source_sheet'] = sheet_name
            
            logging.info(f"  -> Giữ lại {len(df_filtered)}/{len(df)} môn từ Sheet '{sheet_name}'")
            all_frames.append(df_filtered)
            
        except Exception as e:
            logging.error(f"  -> Lỗi khi đọc Sheet '{sheet_name}': {e}")
            continue
    
    xl.close()
    
    if not all_frames:
        raise RuntimeError("Không trích xuất được dữ liệu nào từ file Excel!")
    
    combined = pd.concat(all_frames, ignore_index=True)
    logging.info(f"[EXTRACT] Tổng cộng: {len(combined)} bản ghi sau khi gộp tất cả Sheet.")
    return combined


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    BƯỚC 2 - TRANSFORM: Làm sạch, gán nhãn và chuẩn hóa dữ liệu.
    """
    logging.info(f"[TRANSFORM] Bắt đầu biến đổi {len(df)} bản ghi...")
    
    # --- 2.1: Loại bỏ dòng rác (nếu Mã học phần hoặc Tên bị NaN) ---
    df = df.dropna(subset=['Mã học phần', 'Tên học phần mới']).copy()
    
    # --- 2.2: Làm sạch cột Học kỳ ---
    if 'Học kỳ' in df.columns:
        # Ép kiểu về số, các giá trị không hợp lệ sẽ thành NaN
        df['Học kỳ'] = pd.to_numeric(df['Học kỳ'], errors='coerce')
        # Tạo cột phụ đánh dấu dòng có Học kỳ rõ ràng (không NaN)
        df['_hk_valid'] = df['Học kỳ'].notna().astype(int)
    else:
        logging.warning("  -> Không tìm thấy cột 'Học kỳ'. Gán mặc định NaN.")
        df['Học kỳ'] = pd.NA
        df['_hk_valid'] = 0
    
    # --- 2.3: Drop Duplicate thông minh ---
    # Sắp xếp ưu tiên dòng có Học kỳ rõ ràng lên đầu trước khi dedup
    before_dedup = len(df)
    df = df.sort_values(by=['Mã học phần', '_hk_valid'], ascending=[True, False])
    df = df.drop_duplicates(subset=['Mã học phần'], keep='first').copy()
    logging.info(f"  -> Xóa trùng lặp: {before_dedup} -> {len(df)} bản ghi (loại {before_dedup - len(df)} môn trùng)")
    
    # --- 2.4: Chuẩn hóa Học kỳ thành số nguyên hoặc chuỗi rõ ràng ---
    df['Học kỳ'] = df['Học kỳ'].apply(
        lambda x: str(int(x)) if pd.notna(x) else ''
    )
    
    # --- 2.5: Gán nhãn Nhóm năng lực ---
    df['Nhóm năng lực'] = df['Tên học phần mới'].apply(classify_criteria)
    
    # --- 2.6: Gán nhãn Loại môn ---
    tu_chon_col = 'Tự chọn theo khối KT'
    if tu_chon_col in df.columns:
        df['Loại môn'] = df[tu_chon_col].apply(classify_course_type)
    else:
        logging.warning(f"  -> Không tìm thấy cột '{tu_chon_col}'. Mặc định tất cả là 'Bắt buộc'.")
        df['Loại môn'] = 'Bắt buộc'
    
    # --- 2.7: Chuẩn hóa kiểu dữ liệu ---
    df['Mã học phần'] = df['Mã học phần'].astype(str).str.strip()
    df['Tên học phần mới'] = df['Tên học phần mới'].astype(str).str.strip()
    
    # --- 2.8: Chọn 5 cột output ---
    output_cols = ['Mã học phần', 'Tên học phần mới', 'Nhóm năng lực', 'Loại môn', 'Học kỳ']
    result = df[output_cols].copy()
    
    # --- 2.9: Log thống kê ---
    logging.info(f"[TRANSFORM] Kết quả phân nhóm năng lực:")
    for c in ['C1', 'C2', 'C3', 'C4', 'C5']:
        count = len(result[result['Nhóm năng lực'] == c])
        logging.info(f"  -> {c}: {count} môn")
    
    type_stats = result['Loại môn'].value_counts()
    logging.info(f"[TRANSFORM] Thống kê Loại môn:")
    for t, count in type_stats.items():
        logging.info(f"  -> {t}: {count} môn")
    
    hk_filled = len(result[result['Học kỳ'] != ''])
    logging.info(f"[TRANSFORM] Học kỳ: {hk_filled}/{len(result)} môn có thông tin HK rõ ràng.")
    
    return result


def load_data(df: pd.DataFrame, output_path: str):
    """
    BƯỚC 3 - LOAD: Xuất DataFrame ra file Excel.
    """
    logging.info(f"[LOAD] Đang xuất {len(df)} bản ghi ra: {output_path}")
    
    try:
        df.to_excel(output_path, index=False, engine='openpyxl')
        logging.info(f"[LOAD] THÀNH CÔNG! File đã được tạo: {output_path}")
        logging.info(f"[LOAD] Preview 10 dòng đầu tiên:")
        print(df.head(10).to_string(index=False))
    except Exception as e:
        raise RuntimeError(f"Lỗi khi ghi file output: {e}")


# === MAIN PIPELINE ===
if __name__ == "__main__":
    print("=" * 60)
    print("  DATA PREP PIPELINE - ETL for Course Knowledge Base")
    print("=" * 60)
    
    try:
        # Step 1: Extract
        raw_data = extract_data(INPUT_FILE)
        
        # Step 2: Transform
        clean_data = transform_data(raw_data)
        
        # Step 3: Load
        load_data(clean_data, OUTPUT_FILE)
        
        print("\n" + "=" * 60)
        print(f"  HOÀN TẤT! Output: {OUTPUT_FILE}")
        print(f"  Tổng số môn học: {len(clean_data)}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        logging.error(f"FILE NOT FOUND: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logging.error(f"RUNTIME ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
