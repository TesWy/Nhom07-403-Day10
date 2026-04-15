# Data contract — Lab Day 10

> Đồng bộ với `contracts/data_contract.yaml`.  
> Owner: **Nhom07-403** · Cập nhật: 2026-04-15

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| **Policy & SLA system** — export CSV (`policy_export_dirty.csv`) | Batch export định kỳ, đọc qua `load_raw_csv()` | Duplicate chunk, ngày `effective_date` sai định dạng (dd/mm/yyyy), chunk text rỗng, doc_id không hợp lệ (catalog lỗi) | `raw_records`, `quarantine_records`, `quarantine_rate = quarantine/raw × 100%` |
| **HR system** — bản ghi policy nhân sự (`hr_leave_policy`) | Merge vào cùng CSV export theo doc_id | Conflict version (2025 vs 2026), bản HR cũ effective_date < 2026-01-01 còn lọt export | `stale_hr_policy_effective_date` count trong quarantine log |
| **IT Helpdesk FAQ** (`it_helpdesk_faq`) | Cùng batch export, embed thành chunk riêng | Ngày không đúng ISO format (phổ biến: dd/mm/yyyy), chunk trùng nội dung | `invalid_effective_date_format` count, `duplicate_chunk_text` count |
| **SLA Policy** (`sla_p1_2026`) | Cùng batch export | Thiếu effective_date khi editor quên điền | `missing_effective_date` count |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | SHA-256 hash 16 ký tự đầu của `doc_id\|chunk_text\|seq` — ổn định qua các run |
| doc_id | string | Có | Phải thuộc `ALLOWED_DOC_IDS` trong `cleaning_rules.py` và `contracts/data_contract.yaml` |
| chunk_text | string | Có | Tối thiểu 8 ký tự; đã loại BOM, trim whitespace; refund window đã fix 14→7 ngày |
| effective_date | date | Có | Định dạng YYYY-MM-DD (ISO 8601); chuyển đổi từ dd/mm/yyyy nếu cần |
| exported_at | datetime | Có | ISO 8601 datetime từ hệ nguồn; dùng để tính freshness SLA |

---

## 3. Quy tắc quarantine vs drop

Record bị flag **quarantine** (không bị xoá hoàn toàn) và lưu tại `artifacts/quarantine/`:

| Lý do quarantine | Mô tả | Hành động tiếp theo |
|-----------------|-------|---------------------|
| `unknown_doc_id` | doc_id không thuộc allowlist | Data steward kiểm tra catalog, update allowlist nếu hợp lệ |
| `missing_effective_date` | effective_date rỗng | Kiểm tra hệ nguồn, điền lại ngày hoặc dùng ngày tài liệu mặc định |
| `invalid_effective_date_format` | Định dạng ngày không parse được | Fix ở hệ nguồn hoặc mở rộng parser |
| `stale_hr_policy_effective_date` | HR policy có effective_date < 2026-01-01 | Chỉ dùng version 2026 — liên hệ HR để decommission bản cũ |
| `missing_chunk_text` | chunk_text rỗng sau trim | Kiểm tra export script, tái export |
| `duplicate_chunk_text` | Nội dung trùng hoàn toàn với chunk đã xử lý | Bỏ qua, giữ bản đầu tiên |

**Ai approve merge lại:** Data owner (Nhom07-403) sau khi xác nhận nguyên nhân. Quarantine file được giữ ≥ 7 ngày trước khi purge.

---

## 4. Phiên bản & canonical

| Tài liệu | Source of truth | Version hiện hành | Ghi chú |
|----------|----------------|-------------------|---------|
| Policy hoàn tiền | `data/docs/policy_refund_v4.txt` | v4 (7 ngày làm việc) | Chunk nào vẫn ghi 14 ngày → lỗi migration từ v3, cần fix |
| SLA P1 | `data/docs/sla_p1_2026.txt` | 2026 | 15 phút phản hồi, 4 giờ resolution |
| HR Leave | `data/docs/hr_leave_policy.txt` | 2026 (12 ngày) | Bản 2025 (10 ngày) bị quarantine |
| IT Helpdesk FAQ | `data/docs/it_helpdesk_faq.txt` | Hiện hành | Cập nhật theo ticket thực tế |

---

## 5. Monitoring & SLA

- **Freshness SLA:** < 24 giờ (tính từ `latest_exported_at` tới thời điểm run pipeline).
- **Quality Alert:**
  - **HALT:** Nếu `quarantine_count > 0` cho các lỗi nghiêm trọng (`unknown_doc_id`, `stale_hr_policy`).
  - **WARN:** Nếu `short_chunks` hoặc `duplicate_chunks` chiếm tỷ lệ đáng kể (>10%).
- **Ownership:** Nhóm 07 chịu trách nhiệm xử lý các bản ghi trong thư mục `quarantine/` trong vòng 48 giờ làm việc.
