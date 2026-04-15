# 📦 HƯỚNG DẪN CÀI ĐẶT & CHẠY DỰ ÁN TRÊN LAPTOP MỚI
**DSS - Hệ thống Tư vấn Hướng nghiệp CNTT (AHP + Gemini AI)**

---

## 🗂️ BƯỚC 0: Chuẩn bị - Copy dự án sang laptop

Sao chép **toàn bộ thư mục** dự án (bao gồm tất cả file bên dưới) sang laptop:

```
📁 Tư vấn vị trí việc làm/
  ├── app.py
  ├── ahp_engine.py
  ├── gemini_services.py
  ├── data_prep.py
  ├── .env                       ← QUAN TRỌNG! Chứa API Key
  ├── CTĐT.xlsx
  ├── Nhóm 2_Tính toán tiêu chí AHP môn HHTRQĐ.xlsx
  ├── course_database.xlsx       ← Nếu chưa có, xem Bước 3
  └── requirements.txt
```

> **Cách copy nhanh nhất:** Dùng USB, Google Drive, hoặc nén thành file `.zip` → gửi qua email/Drive → giải nén trên laptop.

---

## 🐍 BƯỚC 1: Cài đặt Python

1. Truy cập **https://www.python.org/downloads/** → tải Python **3.10, 3.11, hoặc 3.12**
2. Khi cài đặt: **BẮT BUỘC** tick chọn ✅ `Add Python to PATH`
3. Mở Command Prompt (cmd), kiểm tra:
   ```
   python --version
   ```
   Nếu hiển thị `Python 3.x.x` → OK ✅

---

## 📦 BƯỚC 2: Cài đặt thư viện

Mở **Command Prompt** → `cd` vào thư mục dự án, rồi chạy:

```bash
# Ví dụ nếu dự án ở Desktop:
cd "C:\Users\TênUser\Desktop\Tư vấn vị trí việc làm"

# Cài toàn bộ thư viện một lần:
pip install -r requirements.txt
```

> ⏳ Quá trình này mất khoảng **5-10 phút** tùy tốc độ mạng.

---

## 🔑 BƯỚC 3: Kiểm tra file .env (API Key)

Mở file `.env` trong thư mục dự án, đảm bảo nội dung đúng:
```
GEMINI_API_KEY=AIzaSy...  (API Key thật của bạn)
```

> ⚠️ Nếu quên copy file `.env`, hệ thống sẽ **chạy ở chế độ MOCK** (không gọi AI thật).  
> Tạo lại file `.env` tay với nội dung trên là được.

---

## 🗄️ BƯỚC 4: Tạo lại course_database.xlsx (Nếu chưa có)

Nếu thư mục không có file `course_database.xlsx`, chạy lệnh sau **một lần duy nhất**:

```bash
python data_prep.py
```

File `course_database.xlsx` sẽ được tạo tự động.

---

## 🚀 BƯỚC 5: Chạy ứng dụng

```bash
python app.py
```

Ứng dụng sẽ **tự động mở trình duyệt** tại `http://localhost:8501` 🎉

---

## ❓ XỬ LÝ LỖI THƯỜNG GẶP

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `ModuleNotFoundError: No module named 'xxx'` | Thiếu thư viện | Chạy lại `pip install -r requirements.txt` |
| `FileNotFoundError: Nhóm 2_Tính toán...xlsx` | Quên copy file Excel AHP | Copy file `.xlsx` vào cùng thư mục |
| `ValueError: Thiếu cấu hình API Key` | Thiếu file `.env` | Tạo lại file `.env` với API Key |
| `kaleido` lỗi khi xuất PDF | Thư viện kaleido chưa cài đúng | Chạy `pip install kaleido==0.2.1` |
| Font lỗi khi xuất PDF | Laptop thiếu font Arial | Hệ thống tự fallback sang Helvetica, **không ảnh hưởng** |

---

## 💡 Lưu ý

- Chạy lại `pip install -r requirements.txt` mỗi khi chuyển máy để đảm bảo đủ thư viện.
- Không cần cài đặt Streamlit riêng – đã có trong `requirements.txt`.
- Dự án **hoàn toàn offline** sau khi cài, chỉ cần mạng để gọi Gemini AI API.
