# Báo cáo cá nhân — mẫu GV (Nhóm 07)

**Họ và tên:** Huỳnh Nhựt Huy  
**Mã học viên:** 2A202600084  
**Vai trò:** Embed & Idempotency Owner (Sprint 3)  

---

## 1. Phụ trách

Tôi phụ trách triển khai cơ chế nạp dữ liệu (Embedding) trong `etl_pipeline.py` và chịu trách nhiệm chính về bài toán **Idempotency** (tính nhất quán). Tôi cũng là người trực tiếp thực hiện kịch bản **Sprint 3 (Corruption & Healing)** để chứng minh khả năng tự khắc phục của pipeline.

**Bằng chứng:** Hàm `embed_upsert_and_prune` trong repo và các artifact log `run_distinction-ready.log`.

---

## 2. Quyết định kỹ thuật

**Content-based ID:** Để đảm bảo không bị trùng lặp dữ liệu khi chạy lại nhiều lần, tôi quyết định không dùng Sequential ID (1, 2, 3) mà dùng **SHA-256 hash** nội dung của chunk làm `chunk_id`. Điều này giúp ChromaDB tự động thực hiện Upsert nếu nội dung không đổi.

**Auto-Pruning:** Để đạt hạng Distinction, tôi bổ sung giải thuật soát xét ID cũ. Sau mỗi batch nạp mới, hệ thống sẽ xóa (delete) các vector ID cũ không còn nằm trong Manifest để triệt tiêu dữ liệu "bóng ma" sau khi fix lỗi.

---

## 3. Sự cố / anomaly

Trong quá trình thực hiện Sprint 3, khi bỏ qua fix refund (`--no-refund-fix`), tôi nhận thấy kết quả retrieval bị nhiễu do bản stale "14 ngày" trộn lẫn với dữ liệu đúng. Nguyên nhân là do thay đổi nội dung làm thay đổi ID băm, khiến bản cũ không bị ghi đè. Tôi đã xử lý triệt để lỗi này bằng giải thuật **Pruning** nhắc đến ở mục 2.

---

## 4. Before/after

**Log:** `embed_upsert count=6` (Xác nhận số record nạp vào khớp với file Cleaned).
**Grading:** Kết quả `grading_run.jsonl` báo `hits_forbidden=false` cho câu hỏi về refund, chứng minh kịch bản "Chữa lành" (Heal) đã hoạt động hoàn hảo sau khi inject lỗi ở Sprint 3.

---

## 5. Cải tiến thêm 2 giờ

Tích hợp **Hybrid Search** (Dense + Sparse) bằng cách kết hợp ChromaDB và BM25 để nâng cao độ chính xác của tầng Retrieval cho các thuật ngữ kỹ thuật đặc thù trong Knowledge Base của Day 10.
