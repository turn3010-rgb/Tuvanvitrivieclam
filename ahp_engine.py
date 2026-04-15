import pandas as pd
import numpy as np
import logging

class AHPEngine:
    def __init__(self, excel_path: str):
        """
        Decision Support System - Hybrid AHP Engine
        Dùng để tính toán mức độ phù hợp của 8 vị trí việc làm CNTT dựa trên 5 nhóm năng lực.
        """
        self.excel_path = excel_path
        self.criteria_keys = ['[C1] Coding', '[C2] Math/Data', '[C3] System', '[C4] Process', '[C5] Domain']
        self.job_roles = ['[A1] Backend', '[A2] Frontend', '[A3] Mobile', '[A4] Data Analyst', '[A5] AI Engineer', '[A6] Tester', '[A7] BA', '[A8] DevOps']
        
        # Chỉ số Random Index (RI) chuẩn của hệ thống Saaty
        self.SAATY_RI = {1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41}
        self.CR_THRESHOLD = 0.10
        
        # Lưu trữ nội bộ
        self.criteria_matrix = None
        self.criteria_weights = None
        self.job_profile_matrix = None

    def _validate_consistency(self, matrix: np.ndarray) -> tuple[np.ndarray, float]:
        """
        Kiểm tra tỷ số nhất quán (CR) của ma trận so sánh cặp.
        """
        n = matrix.shape[0]
        
        # 1. Tính toán vector trọng số (Eigenvector method - Approx)
        col_sums = matrix.sum(axis=0)
        normalized_matrix = matrix / col_sums
        weights = normalized_matrix.mean(axis=1)
        
        # 2. Tính tỷ số nhất quán (CR)
        weighted_sum = matrix.dot(weights)
        lambda_max = (weighted_sum / weights).mean()
        
        ci = (lambda_max - n) / (n - 1)
        ri = self.SAATY_RI.get(n, 1.12)
        cr = ci / ri if ri > 0 else 0
        
        # 3. Chốt chặn
        if cr > self.CR_THRESHOLD:
            raise ValueError(
                f"❌ [CHẶN LUỒNG] Ma trận KHÔNG nhất quán! "
                f"CR = {cr:.4f} vượt ngưỡng an toàn {self.CR_THRESHOLD}. "
                f"Vui lòng báo chuyên gia xem xét lại bảng trọng số."
            )
            
        return weights, cr

    def _find_row_by_keyword(self, df: pd.DataFrame, keywords: list) -> int:
        """Quét toàn bộ DataFrame để tìm dòng chứa chuỗi keyword."""
        for r in range(df.shape[0]):
            for c in range(df.shape[1]):
                val = str(df.iloc[r, c]).strip().lower()
                for kw in keywords:
                    if kw.lower() in val:
                        return r
        raise ValueError(f"Không tìm thấy mốc dữ liệu chứa nhóm từ khóa: {keywords}")

    def load_expert_knowledge(self):
        """
        Đọc cấu hình 'Luật chơi' từ file excel. 
        Sử dụng logic tìm kiếm chuỗi linh hoạt để xác định tọa độ động.
        """
        try:
            try:
                df = pd.read_excel(self.excel_path, sheet_name="Sheet2", header=None)
            except Exception:
                # Fallback đọc theo index của Sheet thứ 2 (0-indexed) nếu tên bị đổi
                df = pd.read_excel(self.excel_path, sheet_name=1, header=None)
            
            # Quét tìm "BẢNG 3:TỔNG HỢP QUYẾT ĐỊNH"
            try:
                table3_start = self._find_row_by_keyword(df, ["BẢNG 3:TỔNG HỢP QUYẾT ĐỊNH", "BẢNG 3: TỔNG HỢP QUYẾT ĐỊNH"])
            except ValueError:
                table3_start = self._find_row_by_keyword(df, ["BẢNG 3"])
                
            # Dòng dữ liệu bắt đầu sau header 2 dòng (Tùy thuộc file, thường là table3_start + 3)
            # Theo output.csv thì:
            # Dòng 113: BẢNG 3:TỔNG HỢP QUYẾT ĐỊNH
            # Dòng 116: [A1] Backend ... [C1] Coding 0.3597 (tương ứng index data_start_row = table3_start + 3)
            data_start_row = table3_start + 3
            
            # Trích xuất ma trận Job Profile (8 hàng, 5 cột từ cột B (1) -> F (5))
            job_raw = df.iloc[data_start_row : data_start_row + 8, 1 : 6].astype(float).values
            self.job_profile_matrix = job_raw
            
            # Trích xuất Trọng số Tiêu chí (5 hàng nằm ở cột I (8))
            weights_raw = df.iloc[data_start_row : data_start_row + 5, 8].astype(float).values
            self.criteria_weights = weights_raw
            
            logging.info(f"✅ Tải thành công Job Profile (Kích thước: {self.job_profile_matrix.shape})")
            logging.info(f"✅ Tải thành công Trọng số Tiêu chí: {self.criteria_weights}")
            
        except Exception as e:
            raise RuntimeError(f"Lỗi khi đọc dữ liệu từ BẢNG 3, Sheet2: {e}")

    def calculate_personalized_ranking(self, student_scores: dict) -> list:
        """
        Thuật toán Hybrid AHP-Matching
        Tính điểm cơ sở và xếp hạng với cơ chế chống thiếu dữ liệu (Missing Data Handling).
        """
        if self.criteria_weights is None or self.job_profile_matrix is None:
            raise ValueError("Hãy gọi hàm `load_expert_knowledge()` trước khi tính toán!")
            
        # 1. Trích xuất vector điểm (Kèm cơ chế cảnh báo nếu thiếu key)
        s_vector_list = []
        for key in self.criteria_keys:
            if key not in student_scores:
                logging.warning(f"⚠️ [CẢNH BÁO]: Hồ sơ sinh viên thiếu điểm tiêu chí '{key}'. Tự động gán {key} = 0.")
                s_vector_list.append(0.0)
            else:
                s_vector_list.append(float(student_scores[key]))
                
        s_vector = np.array(s_vector_list)
        
        # 2. Xử lý Hybrid AHP-Matching bằng Vectorization
        s_weighted = s_vector * self.criteria_weights
        raw_match_scores = self.job_profile_matrix.dot(s_weighted)
        
        # 3. Chuẩn hóa Matching Score về thang 100%
        sum_scores = raw_match_scores.sum()
        normalized_scores = (raw_match_scores / sum_scores) * 100 if sum_scores > 0 else raw_match_scores
        
        # 4. Gắn kết quả và xếp hạng
        ranking_results = []
        for role, score in zip(self.job_roles, normalized_scores):
            ranking_results.append({
                "Job_Role": role,
                "Matching_Score": round(float(score), 2)
            })
            
        ranking_results = sorted(ranking_results, key=lambda x: x["Matching_Score"], reverse=True)
        return ranking_results[:3]
