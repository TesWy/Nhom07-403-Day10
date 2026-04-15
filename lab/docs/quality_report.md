# Quality report — Lab Day 10 (Nhóm 07)

**run_id:** inject-bad (corruption) & healed (fixed)
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (Inject-bad) | Sau (Healed) | Ghi chú |
|--------|-------|-----|---------|
| raw_records | 10 | 10 | Dữ liệu đầu vào không đổi |
| cleaned_records | 6 | 5 | Sau khi fix, 2 chunk refund trùng lặp được gộp thành 1 |
| quarantine_records | 4 | 5 | Bản refund lỗi bị fix/merge nên quarantine có sự thay đổi |
| Expectation halt? | FAIL (skip) | OK | Inject-bad cố tình bỏ qua halt để embed |
| Pydantic Validation? | No | OK | Đã tích hợp Schema Validation (+2 Bonus) |

---

## 2. Before / after retrieval (bắt buộc)

> Bằng chứng so sánh kết quả retrieval giữa trạng thái dữ liệu lỗi và dữ liệu đã qua xử lý.

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
- **Trước (Bị lỗi):** `hits_forbidden=yes`. Top-k chứa cả thông tin "7 ngày" và "14 ngày làm việc" (do bản stale từ migration bị lọt vào DB).
- **Sau (Đã fix):** `hits_forbidden=no`. Chỉ còn thông tin "7 ngày làm việc" đồng nhất. 

**Merit (khuyến nghị):** versioning HR — `q_leave_version` 
- **Trước:** `top1_doc_id=hr_leave_policy`, `hits_forbidden=no`. (Rule HR đã chặn được bản 2025 ngay từ đầu).
- **Sau:** `top1_doc_id=hr_leave_policy`, `hits_forbidden=no`. Duy trì độ chính xác cao nhất (12 ngày phép).

---

## 3. Freshness & monitor

- **Kết quả:** `freshness_boundary=ingest` (FAIL) & `freshness_boundary=publish` (FAIL) trên data mẫu.
- **SLA chọn:** 24 giờ.
- **Đặc trưng Bonus (+1):** Pipeline thực hiện đo lường tại **2 ranh giới** (Ingest và Publish) để phát hiện trễ dữ liệu từ sớm.
- **Giải thích:** Dữ liệu chính sách (Policy) cần độ tươi mới cao để tránh nhân viên tư vấn sai cho khách hàng. Nếu `latest_exported_at` quá cũ, hệ thống sẽ cảnh báo để Admin kiểm tra lại pipeline.

---

## 4. Corruption inject (Sprint 3)

**Mô tả kịch bản:**
1.  Sử dụng dữ liệu `policy_export_dirty.csv` chứa đồng thời bản record đúng (7 ngày) và record stale (14 ngày).
2.  Chạy pipeline với tham số `--no-refund-fix --skip-validate`. 
    -   `--no-refund-fix`: Ngăn chặn rule chuyển đổi 14 -> 7 ngày, dẫn đến việc không thể deduplicate (do 2 text khác nhau).
    -   `--skip-validate`: Bỏ qua việc Expectation `refund_no_stale_14d_window` bị Fail để tiến hành Embed dữ liệu lỗi lên hệ thống.
3.  **Cách phát hiện:** Sử dụng `eval_retrieval.py` với bộ đề golden. Hệ thống đã đánh dấu `hits_forbidden=yes` ngay khi phát hiện chuỗi "14 ngày làm việc" trong kết quả trả về.

---

## 5. Hạn chế & việc chưa làm

- Hiện tại hệ thống mới chỉ detect được stale refund window dựa trên keyword cố định, chưa phát hiện được các lỗi logic tinh vi hơn (ví dụ: ngày hiệu lực mâu thuẫn giữa hai tài liệu khác nhau).
- Cần bổ sung thêm Metric về Latency của bước Embedding trong báo cáo sau.
