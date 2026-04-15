# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Nhóm 07 (VinUni)  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Huỳnh Khải Huy | Monitoring / Docs Owner | 26ai.huyhk@vinuni.edu.vn |
| Nguyễn Ngọc Hưng | Cleaning & Quality Owner | hungnguyenngoc714@gmail.com |
| Nguyễn Ngọc Khánh Duy | Ingestion / Raw Owner | nguyenngockhanhduy1@gmail.com |
| Huỳnh Nhựt Huy | Embed & Idempotency Owner | huy40580@gmail.com |
| Huỳnh Lê Xuân Ánh | Docs Owner | huynhlexuananh2002@gmail.com |

**Ngày nộp:** 2026-04-15  
**Repo:** https://github.com/TesWy/Nhom07-403-Day10

---

## 1. Pipeline tổng quan (150–200 từ)

Hệ thống sử dụng dữ liệu nguồn từ bản export CSV (`policy_export_dirty.csv`) mô phỏng các lỗi phổ biến từ hệ thống legacy. Quy trình bao gồm 4 giai đoạn chính: Ingest (đọc file), Transform (áp dụng rule làm sạch), Quality (kiểm tra kỳ vọng dữ liệu) và Embed (nạp vào ChromaDB).

Điểm nổi bật của pipeline là tính **Idempotency** (chạy lại nhiều lần không trùng dữ liệu) thông qua việc sử dụng `chunk_id` dựa trên SHA-256 mã hóa nội dung. Pipeline được vận hành và giám sát qua hệ thống Manifest giúp đo lường độ tươi mới (Freshness) của dữ liệu tại 2 ranh giới (Ingest & Publish).

**Lệnh chạy một dòng:**
```bash
python etl_pipeline.py run --run-id distinction-ready && python eval_retrieval.py --out artifacts/eval/before_after_eval.csv
```

---

## 2. Cleaning & expectation (150–200 từ)

Nhóm đã kế thừa các rule baseline (dedupe, date normalize) và bổ sung 3 rule mới tập trung vào trải nghiệm người dùng cuối: chuẩn hóa khoảng trắng (Sanitize), kiểm tra dải ngày hợp lệ (Date range check) và tái tạo ID ổn định.

Về kiểm định chất lượng, nhóm bổ sung 2 Expectation mới quan trọng:
- `sla_no_vague_language` (Halt): Ngăn chặn các từ ngữ mơ hồ như "xấp xỉ", "khoảng" trong tài liệu SLA để đảm bảo AI Agent không cung cấp thông tin không chắc chắn.
- `valid_chunk_id_format` (Halt): Đảm bảo tính nhất quán của ID phục vụ cho việc tracking.

### 2a. Bảng metric_impact

| Rule / Expectation mới | Trước (số liệu) | Sau / khi inject | Chứng cứ |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| `sanitize_chunk_text` | Nhiều khoảng trắng dư | 100% text gọn gàng | `cleaned_healed.csv` |
| `extremely_stale_effective_date` | Lọt bản ghi 2018 | Bị đẩy vào Quarantine | `quarantine_healed.csv` |
| `sla_no_vague_language` | Cho phép từ "khoảng" | Pipeline HALT (Lỗi SLA) | `run_inject-bad.log` |

---

## 3. Before / after ảnh hưởng retrieval hoặc agent

Nhóm đã thực hiện kịch bản **Inject Corruption** bằng cách chạy pipeline với `--no-refund-fix`.

**Kịch bản inject:** Cố tình đưa bản ghi chính sách hoàn tiền cũ (14 ngày) vào Knowledge Base.
**Kết quả định lượng:**
- **Trước khi fix (Inject):** `hits_forbidden=yes`. Hệ thống retrieval trả về cả thông tin 7 ngày (đúng) và 14 ngày (sai), gây nhiễu cho Agent.
- **Sau khi fix (Heal):** `hits_forbidden=no`. Pipeline tự động chuyển đổi chuỗi "14 ngày" thành "7 ngày" và thực hiện deduplication. Kết quả retrieval chỉ còn duy nhất thông tin 7 ngày chính xác.
- **Grading Run:** Đã hoàn thành bộ đề `grading_questions.json` (17:00). Kết quả đạt 100% tiêu chí (`contains_expected=true`, `hits_forbidden=false`, `top1_doc_matches=true`).

---

## 4. Freshness & monitoring

- **SLA chọn:** 24 giờ.
- **Ý nghĩa:**
    - `PASS`: Dữ liệu được export và embed trong vòng 24h qua.
    - `FAIL`: Dữ liệu đã cũ hơn 1 ngày, Admin cần kiểm tra pipeline export ở thượng nguồn (Upstream).
- **Kết quả thực tế:** Hệ thống báo `FAIL` trên dữ liệu mẫu (do timestamp 2026-04-10), giúp nhóm phát hiện ngay vấn đề "Data Stale" từ bước đầu tiên.

---

## 5. Liên hệ Day 09

Dữ liệu sau khi qua Pipeline Day 10 trở nên "sạch" và tin cậy hơn. Toàn bộ `doc_id` và `chunk_text` đã được chuẩn hóa, giúp hệ thống Multi-agent ở Day 09 không bị nhầm lẫn giữa các phiên bản chính sách năm 2025 và 2026 (đặc biệt là chính sách nghỉ phép).

---

## 6. Rủi ro còn lại & việc chưa làm

- Hiện tại hệ thống fix 14->7 ngày bằng cách thay thế chuỗi cứng, cần nâng cấp lên regex linh hoạt hơn.
- Chưa tích hợp Dashboard trực quan để theo dõi `quarantine_rate` theo thời gian thực.
