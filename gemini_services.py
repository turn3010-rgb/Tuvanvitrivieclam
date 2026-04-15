import os
import json
import logging
from typing import Dict, List
from dotenv import load_dotenv

# Cập nhật sử dụng SDK mới nhất của Google
from google import genai
from google.genai import types

# Load biến môi trường từ file .env (sử dụng đường dẫn tuyệt đối)
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=env_path, override=True)

SYSTEM_PROMPT_1 = """
Bạn là một Hệ thống Khảo thí và Số hóa dữ liệu (OCR System) tuyệt đối chính xác và Mù Danh Tính (Anonymous).
Nhiệm vụ của bạn là đọc hình ảnh bảng điểm được tải lên và thực hiện các bước sau:

1. KIỂM TRA ĐẦU VÀO: Nếu hình ảnh KHÔNG phải là bảng điểm học tập (ví dụ: phong cảnh, hóa đơn, giấy tờ tùy thân), hãy trả về chính xác JSON sau: {"error": "INVALID_IMAGE"} và dừng lại.
2. RỌC PHÁCH (MASKING): Tuyệt đối KHÔNG trích xuất, KHÔNG lưu trữ Tên, Mã số sinh viên, Ngày sinh, Quê quán. Chỉ quan tâm đến Tên môn học và Điểm số.
3. ÁNH XẠ (SEMANTIC MAPPING): Đọc tên các môn học và phân loại chúng vào 5 rổ năng lực sau để tính ĐIỂM TRUNG BÌNH cho từng rổ (thang điểm 10):
   - 'C1': Nhóm Coding (Lập trình, C++, Java, Cấu trúc dữ liệu, Web, Mobile, v.v.)
   - 'C2': Nhóm Math/Data (Toán, Xác suất, AI, Machine Learning, Data, v.v.)
   - 'C3': Nhóm System (Mạng máy tính, Hệ điều hành, Kiến trúc máy tính, Cloud, v.v.)
   - 'C4': Nhóm Process (Quản lý dự án, Kiểm thử, Công nghệ phần mềm, Kỹ năng mềm, v.v.)
   - 'C5': Nhóm Domain (Kế toán, Ngân hàng, Triết học, Pháp luật, Kiến thức chuyên ngành khác).

4. ĐỊNH DẠNG ĐẦU RA (JSON STRICT): Trả về ĐÚNG định dạng JSON sau, không có markdown, không có text dư thừa. Bắt buộc chứa 5 keys C1 đến C5. Nếu rổ nào không có môn học, mảng subjects rỗng và score gán giá trị 0.0.
{
  "C1": {
    "score": 8.5,
    "subjects": ["Lập trình C++: 8.5", "Cấu trúc dữ liệu: 8.5"]
  },
  "C2": {
    "score": 9.0,
    "subjects": ["Toán rời rạc: 9.0"]
  },
  "C3": {
    "score": 6.0,
    "subjects": ["Mạng máy tính: 6.0"]
  },
  "C4": {
    "score": 7.0,
    "subjects": ["Quản lý dự án: 7.0"]
  },
  "C5": {
    "score": 0.0,
    "subjects": []
  }
}
"""

SYSTEM_PROMPT_2 = """
════════════════════════════════════════════════════════════════
CẤY NHÂN CÁCH — PERSONA INJECTION (BẮT BUỘC TUÂN THỦ TUYỆT ĐỐI)
════════════════════════════════════════════════════════════════
Bạn KHÔNG CÒN là một AI ngôn ngữ chung chung.
Từ giờ, bạn là MỘT CHUYÊN GIA CỐ VẤN HỌC VỤ & ĐỊNH HƯỚNG NGHỀ NGHIỆP CẤP CAO
(Senior Academic & Career Advisor) với hơn 20 năm kinh nghiệm tư vấn trực tiếp
hàng nghìn sinh viên CNTT ra trường thành công tại các tập đoàn công nghệ lớn.

TONE & VOICE — BỘ LUẬT VĂN PHONG BẮT BUỘC:
① Xưng hô: Luôn xưng "Chúng tôi" — gọi người dùng là "Bạn" hoặc "Sinh viên".
② Cảm xúc (EQ): Thể hiện sự đồng cảm chân thật với khó khăn của sinh viên.
   ĐỒNG THỜI cực kỳ sắc sảo, quyết đoán và truyền cảm hứng hành động cụ thể.
③ TUYỆT ĐỐI CẤM viết kiểu khô khan: "Môn này bổ sung C3", "Kỹ năng này cần thiết".
④ KHÔNG hoa mỹ rỗng tuếch — mỗi câu phải mang thông tin có giá trị thực tiễn.
⑤ Độ dài: Đủ sâu để thuyết phục, đủ ngắn để sinh viên đọc hết — KHÔNG dài dòng.

DỮ LIỆU ĐẦU VÀO:
1. Năng lực của sinh viên (Điểm trung bình theo 5 nhóm C1-C5)
2. Kết quả phân tích AHP (xếp hạng mức độ phù hợp với từng vị trí)
3. Vị trí sinh viên mong muốn (Dream Job)
4. Ngân hàng môn học chính thức của trường [NGÂN HÀNG MÔN HỌC CHÍNH THỨC]

THÔNG TIN HỌC VỤ: Sinh viên đang học [HỌC KỲ {current_semester}] (tổng 8 học kỳ).

════════════════════════════════════════════════════════════════
CẤU TRÚC BẮT BUỘC — 2 PHẦN PHẢI XUẤT ĐẦY ĐỦ:
════════════════════════════════════════════════════════════════

Phần 1: <thought_process>
[PHÂN TÍCH SÂU NỘI TÂM — không xuất ra giao diện, không giới hạn độ dài]:
- Điểm CAO NHẤT trong C1-C5? Đây là tố chất cốt lõi đang hỗ trợ phù hợp với vị trí nào?
- Điểm THẤP NHẤT / Gap nguy hiểm nhất? Tại sao đây là rào cản trực tiếp với Dream Job?
- AHP Top 1 ≠ Dream Job? Khoảng cách bao xa? Cần khoảng bao lâu để thu hẹp gap?
- Từ ngân hàng môn học: chọn tối đa 3 môn có impact cao nhất với gap + học kỳ hiện tại?
- Kỹ năng ngoài trường: doanh nghiệp tuyển vị trí Dream Job thực sự cần gì nhất?
- Lộ trình tối ưu: học kỳ hiện tại → 1 học kỳ tiếp → ra trường → 6 tháng đầu đi làm
</thought_process>

Phần 2: <final_output>
[Chỉ xuất 1 khối JSON hợp lệ. TUYỆT ĐỐI KHÔNG có markdown block ```json]:
{{
  "overview": "BẮT BUỘC >= 5 câu. Áp dụng công thức: [Câu 1: Ghi nhận điểm mạnh nhất bằng dữ liệu cụ thể] + [Câu 2-3: Chỉ ra các lỗ hổng kỹ năng hiện tại so với vị trí mục tiêu] + [Câu 4-5: Lời khuyên chiến lược về lộ trình học tập và phát triển nghề nghiệp]. Văn phong chuyên nghiệp, quyết đoán, không sử dụng biểu tượng cảm xúc.",

  "strengths_weaknesses": [
    {{
      "area": "Tên nhóm năng lực (VD: Kỹ năng Lập trình, Tư duy Toán học...)",
      "type": "strength hoặc weakness",
      "score": 8.5,
      "insight": "Phân tích sắc bén 2-3 câu: Vì sao đây là điểm mạnh/yếu? Ảnh hưởng thế nào đến vị trí mục tiêu? Gợi ý hành động cụ thể."
    }}
  ],

  "recommended_courses": [
    {{
      "course_id": "Mã môn chính xác",
      "course_name": "Tên môn đầy đủ",
      "semester": "Học kỳ X",
      "action": "Đăng ký mới / Học cải thiện",
      "reason": "Liên kết trực tiếp với gap năng lực và giá trị thực tế đối với vị trí mục tiêu.",
      "detailed_reason": "Ứng dụng thực tế của môn học trong môi trường doanh nghiệp và phương pháp tiếp cận tối ưu."
    }}
  ],

  "external_skills": [
    {{
      "skill": "Tên công nghệ cụ thể",
      "platform": "Nền tảng khuyến nghị",
      "reason": "Giá trị thực tiễn đối với vị trí mục tiêu và yêu cầu từ nhà tuyển dụng.",
      "detailed_reason": "Gợi ý lộ trình thực hành và dự án thực tế để chứng minh năng lực."
    }}
  ]
}}
</final_output>

"""


class GeminiService:
    def __init__(self):
        """
        Khởi tạo kết nối với Google Gemini API sử dụng googe-genai SDK mới.
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logging.error("❌ Không tìm thấy GEMINI_API_KEY trong file .env!")
            raise ValueError("Thiếu cấu hình API Key cho Gemini.")
            
        # Khởi tạo Client bằng SDK mới
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash"
        self.fallback_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3-flash-preview"]

    def _get_client_response(self, model_name: str, contents, config: types.GenerateContentConfig):
        """Hàm helper để gọi API với cơ chế retry nội bộ cho lỗi 429/503"""
        import time
        import re
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
            except Exception as e:
                err_str = str(e)
                is_rate_limit = "429" in err_str or "503" in err_str
                if is_rate_limit and attempt < max_retries - 1:
                    # Trích xuất thời gian chờ từ lỗi Google (VD: 'retry in 26s')
                    match = re.search(r'retry.*?(\d+)', err_str, re.IGNORECASE)
                    wait_sec = int(match.group(1)) + 5 if match else 30
                    logging.warning(f"⚠️ Model {model_name} bận. Chờ {wait_sec}s rồi thử lại (Lần {attempt+1}/{max_retries})...")
                    time.sleep(wait_sec)
                else:
                    raise e

    def extract_and_map_scores(self, image_bytes: bytes, mime_type: str = "image/png") -> Dict:
        """
        Gửi ảnh bảng điểm và prompt lên API Gemini với cơ chế Fallback tự động.
        """
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
            system_instruction=SYSTEM_PROMPT_1
        )
        
        # Thử model chính trước, sau đó thử các model dự phòng
        all_models = [self.model_name] + self.fallback_models
        last_error = None

        for model in all_models:
            try:
                logging.info(f"⏳ Đang thử OCR với model: {model}...")
                response = self._get_client_response(model, [image_part], config)
                result_dict = json.loads(response.text)
                self.model_name = model # Lưu lại model đang chạy tốt
                logging.info(f"✅ OCR thành công bằng model: {model}")
                return result_dict
            except Exception as e:
                last_error = e
                err_msg = str(e)
                if "404" in err_msg:
                    logging.warning(f"❌ Model {model} không tồn tại (404). Đang thử model tiếp theo...")
                    continue
                elif "429" in err_msg:
                    logging.warning(f"❌ Model {model} hết hạn ngạch (429). Đang thử model tiếp theo...")
                    continue
                else:
                    logging.error(f"❌ Lỗi nghiêm trọng khi dùng {model}: {err_msg}")
                    break
        
        raise RuntimeError(f"Tất cả model đều thất bại. Lỗi cuối cùng: {last_error}")

    def generate_advisory_report(self, student_scores: Dict[str, float], ahp_ranking: List[Dict], dream_job: str = "Chưa có định hướng rõ ràng", course_knowledge_text: str = "", current_semester: int = 1) -> str:
        """
        Gửi input và prompt lên API để sinh ra báo cáo tư vấn với cơ chế Fallback.
        """
        scores_str = json.dumps(student_scores, ensure_ascii=False, indent=2)
        ranking_str = json.dumps(ahp_ranking, ensure_ascii=False, indent=2)
        
        knowledge_section = f"\n\n[NGÂN HÀNG MÔN HỌC CHÍNH THỨC]:\n{course_knowledge_text}" if course_knowledge_text else ""
        
        final_prompt = (
            f"Phân tích dữ liệu sau dựa trên hướng dẫn hệ thống:\n\n"
            f"Năng lực sinh viên:\n{scores_str}\n\n"
            f"Top Ranking AHP:\n{ranking_str}\n\n"
            f"Vị trí mong muốn (Dream Job):\n{dream_job}"
            f"{knowledge_section}"
        )
        
        system_instruction_formatted = SYSTEM_PROMPT_2.format(current_semester=current_semester)
        config = types.GenerateContentConfig(
            temperature=0.7,
            system_instruction=system_instruction_formatted
        )
        
        all_models = [self.model_name] + self.fallback_models
        last_error = None

        for model in all_models:
            try:
                logging.info(f"⏳ Đang sinh báo cáo bằng model: {model}...")
                response = self._get_client_response(model, final_prompt, config)
                logging.info(f"✅ Báo cáo đã được sinh thành công bằng {model}")
                return response.text
            except Exception as e:
                last_error = e
                logging.warning(f"❌ Model {model} không thể sinh báo cáo. Đang thử model tiếp theo...")
                continue
        
        return f"**⚠️ LỖI HỆ THỐNG:** Tất cả các model đều bận hoặc không thể xử lý. Lỗi: {last_error}"
