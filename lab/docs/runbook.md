# Runbook — Lab Day 10 (Incident Response & Troubleshooting)

**Cập nhật:** 2026-04-15
**Nhóm:** 07

---

## 1. Symptom (Triệu chứng)

- Người dùng cuối hoặc AI Agent cung cấp thông tin cũ (Stale) hoặc sai lệch.
- Ví dụ: Khách hàng được thông báo thời hạn hoàn tiền là 14 ngày, nhưng thực tế công ty đã đổi sang 7 ngày.
- Pipeline bị dừng đột ngột (HALT) mà không rõ nguyên nhân.

---

## 2. Detection (Phát hiện)

1.  **Freshness Alert:** Lệnh `python etl_pipeline.py freshness --manifest <path>` báo **FAIL** hoặc **WARN** (dữ liệu nạp vào quá cũ > 24h).
2.  **Expectation FAIL:** Log pipeline hiển thị `PIPELINE_HALT` do vi phạm các rule cực yếu (VD: `refund_no_stale_14d_window`).
3.  **Eval Metrics:** File eval CSV hiển thị `hits_forbidden=yes` cho các câu hỏi golden.

---

## 3. Diagnosis (Chẩn đoán)

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` | Xác định `latest_exported_at` để biết dữ liệu nguồn có bị kẹt (stale) không. |
| 2 | Mở `artifacts/quarantine/*.csv` | Xem cột `reason`. Nếu có nhiều `unknown_doc_id`, có thể catalog hệ thống vừa cập nhật nhưng pipeline chưa update allowlist. |
| 3 | Chạy `python eval_retrieval.py` | Xác nhận xem dữ liệu sai đã thực sự lọt vào Vector Store chưa. |
| 4 | Kiểm tra Log chạy gần nhất | Tìm kiếm các cảnh báo `WARN` hoặc lỗi kết nối tới ChromaDB. |

---

## 4. Mitigation (Xử lý tạm thời)

1.  **Dữ liệu stale:** Nếu nguyên nhân do hệ nguồn chưa export bản mới, hãy liên hệ Ingestion Team để yêu cầu Batch Export khẩn cấp.
2.  **Bỏ qua Halt (Chỉ khi khẩn cấp):** Sử dụng flag `--skip-validate` nếu xác định lỗi expectation là do thay đổi format vô hại, nhằm khôi phục dịch vụ trước khi sửa code.
3.  **Sửa lỗi thủ công:** Chỉnh sửa file `data/raw/policy_export_dirty.csv` nếu có record rác nghiêm trọng, sau đó chạy lại `python etl_pipeline.py run`.

---

## 5. Prevention (Phòng ngừa)

1.  **Mở rộng Expectation:** Thêm các rule kiểm tra mâu thuẫn dữ liệu chéo (cross-check).
2.  **Tự động hóa Monitoring:** Tích hợp `freshness_check` vào hệ thống Alerting (Slack/Email).
3.  **Data Contract:** Thường xuyên review `data_contract.md` với các stakeholder để cập nhật allowlist và quy định về versioning.
