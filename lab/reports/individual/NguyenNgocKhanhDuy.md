# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Ngọc Khánh Duy  
**Vai trò:** Ingestion Owner  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** 400–650 từ

---

## 1. Tôi phụ trách phần nào?

Tôi đảm nhận vai trò **Ingestion Owner** trong Sprint 1, chịu trách nhiệm toàn bộ tầng đầu vào của pipeline: đọc raw data, thiết lập môi trường, định nghĩa nguồn dữ liệu trong contract, và chạy pipeline lần đầu để xác nhận luồng hoạt động end-to-end.

**File / module cụ thể:**

- `etl_pipeline.py` — hàm `cmd_run()`: khởi tạo `run_id`, gọi `load_raw_csv()`, ghi log `raw_records` / `cleaned_records` / `quarantine_records`
- `transform/cleaning_rules.py` — hàm `load_raw_csv()`: đọc file CSV, strip whitespace từng field
- `docs/data_contract.md` — điền source map 4 nguồn (Policy system, HR system, IT Helpdesk, SLA Policy) với failure mode và metric tương ứng
- `contracts/data_contract.yaml` — điền `owner_team`, `alert_channel`

**Kết nối với thành viên khác:**

Sau khi tôi xác nhận log Sprint 1 hợp lệ (`PIPELINE_OK`, exit 0), Cleaning & Quality Owner (Nguyễn Ngọc Hưng) tiếp nhận để bổ sung rule và expectation trong Sprint 2.

**Bằng chứng:**

File log `artifacts/logs/run_sprint1.log` — run_id `sprint1`, do tôi tạo ra khi chạy `python etl_pipeline.py run --run-id sprint1`.

---

## 2. Một quyết định kỹ thuật

**Quyết định: định nghĩa chính sách retention quarantine ≥ 7 ngày trong data contract.**

Khi viết `docs/data_contract.md` mục "Quy tắc quarantine vs drop", tôi phải quyết định **giữ file quarantine bao lâu** trước khi purge. Tôi chọn **≥ 7 ngày** — ghi rõ trong contract: *"Quarantine file được giữ ≥ 7 ngày trước khi purge."*

Lý do: nếu hệ nguồn fix lỗi (ví dụ HR cập nhật effective_date, hoặc catalog bổ sung doc_id mới vào allowlist), data steward cần có đủ thời gian để xem xét, xác nhận và quyết định có re-ingest dòng đó không. Nếu purge quá sớm (ví dụ 24 giờ), cơ hội recovery bị mất trước khi ai kịp xử lý.

Đánh đổi: giữ lâu hơn tốn storage và có thể gây nhầm lẫn nếu file quarantine tích luỹ nhiều run. Tôi chấp nhận đánh đổi này vì trong lab quy mô nhỏ, chi phí storage không đáng kể so với giá trị traceability.

---

## 3. Một lỗi hoặc anomaly đã xử lý

**Anomaly: row 10 trong raw CSV có ngày sai định dạng `01/02/2026` (dd/mm/yyyy).**

Khi đọc `policy_export_dirty.csv` để lập source map, tôi phát hiện row 10 (`it_helpdesk_faq`) có `effective_date = 01/02/2026` — khác định dạng ISO của tất cả dòng còn lại. Đây là lỗi phổ biến khi hệ nguồn export theo locale Việt Nam (dd/mm/yyyy) thay vì ISO (yyyy-mm-dd).

Tôi kiểm tra `transform/cleaning_rules.py` và xác nhận hàm `_normalize_effective_date()` đã có sẵn regex cho pattern này (`_DMY_SLASH`). Tôi ghi lại failure mode này vào `docs/data_contract.md` (cột "Failure mode chính" của nguồn IT Helpdesk) để nhóm biết đây là vấn đề có hệ thống, không phải lỗi ngẫu nhiên.

Bằng chứng rule hoạt động — trích `artifacts/cleaned/cleaned_sprint1.csv`:

```
it_helpdesk_faq_6_76d38c1b20d4459f,it_helpdesk_faq,...,2026-02-01,2026-04-10T08:00:00
```

Ngày được chuẩn hoá thành `2026-02-01`, dòng vào cleaned thay vì quarantine. Quarantine log xác nhận không có dòng nào bị loại vì `invalid_effective_date_format` trong run này.

---

## 4. Bằng chứng trước / sau

**Trước (raw input)** — `data/raw/policy_export_dirty.csv`:
```
10 dòng, gồm: duplicate, date sai format, chunk rỗng, HR bản 2025, doc_id lạ
```

**Sau (cleaned output)** — `artifacts/logs/run_sprint1.log` (run_id = `sprint1`):
```
raw_records=10
cleaned_records=6
quarantine_records=4
```

Delta: 4 dòng bị quarantine — 1 `duplicate_chunk_text`, 1 `missing_effective_date`, 1 `stale_hr_policy_effective_date`, 1 `unknown_doc_id`. Quarantine file tại `artifacts/quarantine/quarantine_sprint1.csv` ghi rõ `reason` từng dòng, manifest tại `artifacts/manifests/manifest_sprint1.json` lưu toàn bộ số liệu để trace lại.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ bổ sung **log chi tiết theo từng dòng bị quarantine** ngay trong bước ingest — hiện tại log chỉ ghi tổng `quarantine_records=4` mà không nêu `run_id` + số thứ tự dòng gốc. Cụ thể: thêm dòng `quarantine_detail[row=<n>] reason=<reason>` vào log để data steward tra cứu nhanh mà không cần mở file CSV quarantine.
