# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Huỳnh Nhựt Huy  
**Vai trò:** Embed & Idempotency Owner (Sprint 3) — Nhóm 07  
**Ngày nộp:** 2026-04-15  
**Mã học viên**: 2A202600084

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

Trong dự án Lab Day 10, tôi chịu trách nhiệm chính về tầng **Storage & Retrieval**, bao gồm việc thiết kế cơ chế nạp dữ liệu (Embedding) và đảm bảo tính **Idempotency** (tính nhất quán khi chạy lại nhiều lần). Tôi là người trực tiếp vận hành **Sprint 3 (Corruption & Healing)** để chứng minh khả năng "tự chữa lành" của Pipeline. 

Sản phẩm chính của tôi nằm trong module `etl_pipeline.py` (hàm `embed_upsert_and_prune`) và các kịch bản đánh giá retrieval trong `eval_retrieval.py`. Tôi phối hợp chặt chẽ với Cleaning Owner để đảm bảo ID của mỗi mảnh dữ liệu (chunk) luôn ổn định và không bị trùng lặp trong ChromaDB.

**Bằng chứng:**
- Hàm: `embed_upsert_and_prune` trong `etl_pipeline.py`.
- Artifact: `artifacts/eval/before_after_eval.csv` (Evidence cho Sprint 3).
- Log: `artifacts/logs/run_distinction-ready.log` (Xác nhận embed_upsert count=6).

---

## 2. Một quyết định kỹ thuật (100–150 từ)

**Quyết định: Sử dụng SHA-256 Content-based ID cho Idempotency thay vì Sequential ID.**

Khi thiết kế cơ chế nạp dữ liệu lên Vector Store, một rủi ro lớn là nếu chạy lại pipeline, dữ liệu cũ vẫn tồn tại và tạo ra các bản sao (Duplicates), dẫn đến việc AI trả lời mâu thuẫn. Tôi quyết định tạo `chunk_id` bằng cách băm (hash) toàn bộ nội dung của chunk (`chunk_text`). 

Quyết định này mang lại hai lợi ích cực hạn: 
1. **Deduplication:** Nếu hai dòng dữ liệu thô có nội dung giống hệt nhau, chúng sẽ có cùng ID và ChromaDB sẽ coi đó là một bản cập nhật (Upsert) thay vì tạo record mới. 
2. **Stable Tracking:** Giúp Monitoring có thể theo dõi chính xác vòng đời của một mảnh nội dung qua nhiều phiên bản export khác nhau của hệ thống nguồn.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

**Vấn đề: "Bóng ma" dữ liệu cũ (Stale Vectors) sau khi cập nhật chính sách.**

Trong quá trình thực hiện Sprint 3, tôi phát hiện ra một Anomaly: Khi chúng ta fix chính sách từ 14 ngày sang 7 ngày, ID của chunk thay đổi (do nội dung thay đổi), dẫn đến việc bản ghi "14 ngày" cũ vẫn còn sót lại trong ChromaDB và lọt vào kết quả top-k. 

**Xử lý:** Tôi đã triển khai thuật toán **Vector Pruning**. Ngay sau khi thực hiện nạp batch mới, hệ thống sẽ lấy toàn bộ danh sách `id` hiện có trong collection, so sánh với các `id` vừa được nạp. Những `id` cũ không còn tồn tại trong batch mới sẽ bị lệnh `collection.delete(ids=...)` xóa bỏ hoàn toàn. Kết quả là trong file `grading_run.jsonl`, chỉ số `hits_forbidden` đã được đưa về `false` tuyệt đối.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Tôi đã chạy khảo sát bằng `eval_retrieval.py` cho kịch bản Refund Policy:
- **Trạng thái Inject (Lỗi):** Chạy với flag `--no-refund-fix`. 
  - Kết quả: `hits_forbidden=yes`, `contains_expected=yes`. AI tìm thấy cả 7 ngày và 14 ngày, gây nhiễu cho nhân viên hỗ trợ khách hàng.
- **Trạng thái Healed (Đã sửa):** Chạy lại pipeline chuẩn. 
  - Kết quả: `hits_forbidden=no`. Nhờ cơ chế băm ID và Pruning của tôi, mảnh dữ liệu "14 ngày" đã bị quét sạch khỏi bộ nhớ.
- **Run ID:** `distinction-ready`

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ nâng cấp giải thuật băm ID để bao gồm cả `doc_id` và `version` trong salt. Điều này giúp hệ thống hỗ trợ tốt hơn cho việc lưu trữ đa phiên bản (Multi-version storage), cho phép user có thể truy vấn đồng thời chính sách năm 2025 và 2026 một cách tường minh mà không sợ bị ghi đè dữ liệu.
