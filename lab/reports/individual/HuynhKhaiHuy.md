# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Huỳnh Khải Huy  
**Vai trò:** Monitoring / Docs Owner (Sprint 4)  
**Ngày nộp:** 15/04/2026 

---

## 1. Tôi phụ trách phần nào?

Trong Day 10, tôi phụ trách nhóm việc **Monitoring + Documentation**, tập trung vào việc biến pipeline từ "chạy được" thành "vận hành được". Cụ thể, tôi hoàn thiện hai tài liệu vận hành chính: `lab/docs/pipeline_architecture.md` và `lab/docs/runbook.md` trong commit `1d6a28f`.

Ở `pipeline_architecture.md`, tôi chuyển từ mô tả khung sang luồng thực thi chi tiết bằng sơ đồ Mermaid, thể hiện rõ các điểm `run_id`, quarantine, validate, embed, manifest và freshness check. Ở `runbook.md`, tôi bổ sung quy trình incident theo 5 phần: Symptom -> Detection -> Diagnosis -> Mitigation -> Prevention, để team có thể xử lý lỗi theo checklist thay vì debug ngẫu hứng.

Tôi phối hợp với Embed Owner để xác thực hành vi `upsert + prune` và với Cleaning Owner để bảo đảm phần expectation trong runbook phản ánh đúng log runtime.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật quan trọng nhất của tôi là đặt **freshness là một checkpoint vận hành độc lập** trong tài liệu kiến trúc và runbook, thay vì coi đó là "chỉ số tham khảo". Lý do là trong bối cảnh policy nội bộ (refund, HR leave, SLA), dữ liệu đúng nội dung nhưng quá cũ vẫn gây ra kết quả sai trong thực tế.

Tôi chốt cách đo freshness dựa trên `latest_exported_at` trong manifest và SLA 24 giờ, đồng thời quy định rõ ngữ nghĩa cảnh báo trong runbook: PASS (an toàn), WARN (thiếu timestamp), FAIL (quá SLA). Cách viết này giúp người trực ca hiểu rằng lỗi freshness không nhất thiết do model hay vector DB, mà có thể do upstream export bị kẹt. Điều này giảm thời gian chẩn đoán và tránh sửa nhầm tầng.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly tôi theo dõi là **stale data lan vào retrieval khi chạy kịch bản inject-bad**. Dấu hiệu đầu tiên nằm ở log `run_inject-bad.log`: expectation `refund_no_stale_14d_window` FAIL nhưng pipeline vẫn tiếp tục vì có `--skip-validate`. Sau đó, kết quả eval trong `eval_during_inject.csv` cho câu `q_refund_window` cho thấy `contains_expected=yes` nhưng `hits_forbidden=yes`, nghĩa là top-k đang chứa cả ngữ cảnh đúng và ngữ cảnh cấm.

Tôi xử lý bằng cách chuẩn hóa hướng dẫn incident trong runbook: kiểm tra manifest -> kiểm tra quarantine -> chạy lại eval -> đối chiếu log expectation. Khi chuyển sang run `healed`, log xác nhận expectation refund PASS, và eval chuyển về trạng thái sạch (không còn forbidden hit). Việc này chứng minh tài liệu vận hành có giá trị thực thi, không chỉ là phần mô tả.

---

## 4. Bằng chứng trước / sau

Hai bằng chứng tôi dùng trong báo cáo:

- `run_id=inject-bad` (file `lab/artifacts/eval/eval_during_inject.csv`):
	- `q_refund_window,...,contains_expected=yes,hits_forbidden=yes,...`

- `run_id=healed` (file `lab/artifacts/eval/eval_after_heal.csv`):
	- `q_refund_window,...,contains_expected=yes,hits_forbidden=no,...`

Kèm theo đó, manifest của hai run tại `manifest_inject-bad.json` và `manifest_healed.json` đều ghi nhận cùng đầu vào nhưng khác cờ vận hành (`no_refund_fix`, `skipped_validate`), đủ để truy vết nguyên nhân sự cố theo đúng tư duy observability.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ bổ sung một script tổng hợp "ops summary" tự động đọc log + manifest + eval rồi xuất 1 bảng markdown duy nhất cho ca trực. Mục tiêu là người vận hành chỉ cần xem một file là biết run nào FAIL vì freshness, run nào FAIL vì quality gate, và mức ảnh hưởng retrieval tương ứng.

