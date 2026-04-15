# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Huỳnh Lê Xuân Ánh
**Vai trò:** Docs Owner
**Ngày nộp:** 15/04/2026
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

---



## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `quality_report.md`, `group_report.md`

**Kết nối với thành viên khác:**

Tôi đảm nhận vai trò **Docs Owner**. Tôi phụ trách soạn thảo báo cáo chất lượng và báo cáo nhóm để đồng bộ các chỉ số từ tất cả thành viên. Tôi làm việc chặt chẽ với Hưng (Cleaning) để lấy số liệu `quarantine_records` và Duy (Ingestion) để xác thực run_id và nguồn dữ liệu CSV.

**Bằng chứng (commit / comment trong code):**

- Trực tiếp viết kịch bản "Corruption inject" và bảng `metric_impact` trong `quality_report.md`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Tôi quyết định áp dụng mức độ **HALT (Dừng pipeline)** cho Expectation `sla_no_vague_language`. Trong bối cảnh quản lý chính sách nhân sự (HR) và hoàn tiền (Refund), các từ ngữ mơ hồ như "khoảng", "xấp xỉ" là rủi ro cực lớn. Nếu cho phép dữ liệu này lọt vào Knowledge Base, AI Agent có thể cung cấp thông tin không chắc chắn hoặc sai luật cho nhân viên. Quyết định HALT thay vì WARN giúp đảm bảo tính "Source of Truth" tuyệt đối cho hệ thống. Ngoài ra, việc chọn SLA Freshness là 24 giờ cũng là một quyết định cân đối giữa chi phí vận hành pipeline và nhu cầu cập nhật chính sách hàng ngày của doanh nghiệp.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Trong quá trình vận hành với tập dữ liệu `policy_export_dirty.csv`, tôi phát hiện anomaly `freshness_boundary=ingest (FAIL)`. Qua việc soi log và file manifest, tôi nhận thấy `latest_exported_at` của bản ghi cuối cùng là `2026-04-10T08:00:00Z` trong khi run timestamp là `2026-04-15`. Triệu chứng này cho thấy hệ thống thượng nguồn (Upstream Export) đang gặp trục trặc và không đẩy dữ liệu mới. Tôi đã xử lý bằng cách ghi nhận lỗi này vào `quality_report.md` để cảnh báo Admin, đồng thời đề xuất thêm logic kiểm tra watermark để phân biệt rõ giữa "Lỗi Pipeline" và "Lỗi dữ liệu Stale".

---

## 4. Bằng chứng trước / sau (80–120 từ)

Sử dụng `run_id: distinction-ready`.
- **Trước khi fix (Inject):** `hits_forbidden=yes`. Dữ liệu retrieval bị nhiễu bởi record stale 14 ngày.
- **Sau khi fix (Healed):** `hits_forbidden=no`, `top1_doc_matches=true`. 
- **Chỉ số thay đổi:**
  - `quarantine_records`: tăng từ 4 lên 5 (do đẩy bản record năm 2018 cực cũ vào quarantine).
  - `cleaned_records`: 5 (đã deduplicate và fix refund window).

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ tích hợp **Slack/Telegram Hook** vào module `monitoring`. Khi bước `check_manifest_freshness` phát hiện `FAIL` hoặc `HALT`, hệ thống sẽ tự động bắn thông báo kèm 5 dòng log lỗi cuối cùng đến kênh của đội O&M. Điều này giúp rút ngắn thời gian phản ứng (MTTR) thay vì đợi admin kiểm tra file log thủ công trong folder `artifacts/logs`.

