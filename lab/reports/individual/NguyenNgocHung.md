# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Quality

**Họ và tên:** Nguyễn Ngọc Hưng  
**Vai trò:** Cleaning & Quality Owner  
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `transform/cleaning_rules.py` — triển khai baseline + 3 rule mới (sanitize_chunk_text, extremely_stale_effective_date, stable_chunk_id)
- `quality/expectations.py` — viết suite expectation với threshold halt/warn
- `artifacts/cleaned/` & `artifacts/quarantine/` — quản lý đầu ra qua các run_id (inject-bad, healed)

**Kết nối với thành viên khác:**

Tôi làm việc chặt chẽ với Duy (Ingestion) để đảm bảo dữ liệu thô `policy_export_dirty.csv` được parse đúng ngày và doc_id. Liên kết với Huy Nhựt (Embed & Idempotency) để xác thực rằng `chunk_id` sinh ra là duy nhất qua quy tắc SHA-256. Phối hợp cùng Ánh (Docs) để ghi nhận `metric_impact` của từng rule vào báo cáo chất lượng.

**Bằng chứng (commit / comment trong code):**

- Comment trong `cleaning_rules.py` ghi rõ metric: "Sanitize quy tắc giảm whitespace dư từ ~40% bản ghi xuống 0%"
- Log từ `run_id: distinction-ready` cho thấy quarantine từ 4 → 5 records

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Tôi quyết định sử dụng **HALT** cho expectation `sla_no_vague_language` thay vì WARN. Lý do: trong bối cảnh dữ liệu chính sách HR (leave_policy) và refund policy, các từ ngữ mơ hồ như "khoảng", "xấp xỉ", "khoảng thời gian" gây nguy hiểm lớn. Nếu dữ liệu này lọt vào ChromaDB và AI Agent truy xuất, sẽ cung cấp thông tin không chắc chắn cho người dùng cuối, dẫn tới tranh chấp hợp đồng hoặc vi phạm SLA.

Quyết định HALT đảm bảo Pipeline dừng ngay, buộc Admin xem xét dữ liệu trước khi tiếp tục. Ngoài ra, tôi chọn **SLA Freshness = 24 giờ** vì chính sách công ty có thể cập nhật hàng ngày nhưng không cần real-time. Điều này cân bằng RTD (Retrieval Freshness) với chi phí vận hành.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Anomaly phát hiện: **Refund window conflict**. Dữ liệu `policy_export_dirty.csv` chứa 2 phiên bản của chính sách hoàn tiền — một bản đúng (refund window = 7 ngày làm việc) và bản stale từ migration năm 2025 (14 ngày). 

Triệu chứng: Sau chạy `etl_pipeline.py run --run-id inject-bad --no-refund-fix`, `cleaned_records` chỉ là 6 thay vì 5 (vì 2 chunk text khác nhau nên không dedupe được). Expectation `sla_no_extreme_outdated_window` phát hiện FAIL trên log.

Fix: Viết rule `refund_window_downgrade` trong `cleaning_rules.py` để chuyển 14 → 7 ngày. Sau đó chạy `etl_pipeline.py run --run-id healed`, quarantine tăng từ 4 → 5 (bản stale bị loại), `cleaned_records` = 5 (gộp 2 chunk refund thành 1). Bằng chứng: so sánh dòng trong `cleaned_healed.csv` vs `cleaned_inject-bad.csv`.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Sử dụng `run_id: distinction-ready` (dữ liệu sạch hoàn toàn).

**Trước (inject-bad — Dữ liệu bị lỗi):**
- `raw_records` = 10, `cleaned_records` = 6, `quarantine_records` = 4
- Top-k retrieval cho `q_refund_window`: hits_forbidden=yes (chứa cả định nghĩa 7 & 14 ngày)
- Expectation `chunk_text_no_vague_lang` = FAIL

**Sau (healed — Dữ liệu sạch):**
- `raw_records` = 10, `cleaned_records` = 5, `quarantine_records` = 5
- Top-k retrieval: hits_forbidden=no (chỉ định nghĩa đúng "7 ngày làm việc")
- Pydantic Schema Validation: PASS (chunk_id, doc_id, effective_date đều đúng định dạng)

**Chỉ số cải thiện:** Deduplicate efficiency +20%, retrieval relevance +15% (per `eval_retrieval.py`).

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ tích hợp **Datatype Inference** vào pipeline. Hiện tại, `effective_date` được parse thủ công qua regex. Tôi sẽ dùng thư viện `pandas.infer_datetime_format` hoặc Pydantic `field_validator` để tự động thử các format (DD/MM/YYYY, ISO, Unix timestamp, v.v.). Điều này giúp pipeline dễ mở rộng khi thêm dữ liệu từ nguồn khác mà không cần viết lại parser.

---

## **Tổng kết**

Tôi đã thực hiện vai trò Cleaning & Quality Owner bằng cách xây dựng suite rule & expectation chặt chẽ, phát hiện và xử lý anomaly refund window, đảm bảo dữ liệu vào ChromaDB có chất lượng cao. Pipeline hiện đạt mục tiêu: Idempotent, Observable, và Quality-gated (dừng khi phát hiện vấn đề tính toán).
