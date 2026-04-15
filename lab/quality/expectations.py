"""
Expectation suite đơn giản (không bắt buộc Great Expectations).

Sinh viên có thể thay bằng GE / pydantic / custom — miễn là có halt có kiểm soát.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from pydantic import BaseModel, Field, field_validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


@dataclass
class ExpectationResult:
    name: str
    passed: bool
    severity: str  # "warn" | "halt"
    detail: str


if HAS_PYDANTIC:
    class CleanedRowModel(BaseModel):
        """Pydantic model for +2 Bonus point (Distinction a)."""
        chunk_id: str = Field(min_length=5)
        doc_id: str
        chunk_text: str = Field(min_length=8)
        effective_date: str
        exported_at: Optional[str] = None

        @field_validator("effective_date")
        @classmethod
        def validate_iso_date(cls, v: str) -> str:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                raise ValueError("effective_date must be YYYY-MM-DD")
            return v


def run_expectations(cleaned_rows: List[Dict[str, Any]]) -> Tuple[List[ExpectationResult], bool]:
    """
    Trả về (results, should_halt).

    should_halt = True nếu có bất kỳ expectation severity halt nào fail.
    """
    results: List[ExpectationResult] = []

    # E0 (Bonus): Pydantic Schema Validation
    if HAS_PYDANTIC:
        pydantic_fails = 0
        for row in cleaned_rows:
            try:
                CleanedRowModel(**row)
            except Exception as e:
                pydantic_fails += 1
        results.append(
            ExpectationResult(
                "pydantic_schema_validation",
                pydantic_fails == 0,
                "halt",
                f"schema_violations={pydantic_fails}",
            )
        )

    # E1: có ít nhất 1 dòng sau clean
    ok = len(cleaned_rows) >= 1
    results.append(
        ExpectationResult(
            "min_one_row",
            ok,
            "halt",
            f"cleaned_rows={len(cleaned_rows)}",
        )
    )

    # E2: không doc_id rỗng
    bad_doc = [r for r in cleaned_rows if not (r.get("doc_id") or "").strip()]
    ok2 = len(bad_doc) == 0
    results.append(
        ExpectationResult(
            "no_empty_doc_id",
            ok2,
            "halt",
            f"empty_doc_id_count={len(bad_doc)}",
        )
    )

    # E3: policy refund không được chứa cửa sổ sai 14 ngày (sau khi đã fix)
    bad_refund = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "policy_refund_v4"
        and "14 ngày làm việc" in (r.get("chunk_text") or "")
    ]
    ok3 = len(bad_refund) == 0
    results.append(
        ExpectationResult(
            "refund_no_stale_14d_window",
            ok3,
            "halt",
            f"violations={len(bad_refund)}",
        )
    )

    # E4: chunk_text đủ dài
    short = [r for r in cleaned_rows if len((r.get("chunk_text") or "")) < 8]
    ok4 = len(short) == 0
    results.append(
        ExpectationResult(
            "chunk_min_length_8",
            ok4,
            "warn",
            f"short_chunks={len(short)}",
        )
    )

    # E5: effective_date đúng định dạng ISO sau clean (phát hiện parser lỏng)
    iso_bad = [
        r
        for r in cleaned_rows
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", (r.get("effective_date") or "").strip())
    ]
    ok5 = len(iso_bad) == 0
    results.append(
        ExpectationResult(
            "effective_date_iso_yyyy_mm_dd",
            ok5,
            "halt",
            f"non_iso_rows={len(iso_bad)}",
        )
    )

    # E6: không còn marker phép năm cũ 10 ngày trên doc HR (conflict version sau clean)
    bad_hr_annual = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "hr_leave_policy"
        and "10 ngày phép năm" in (r.get("chunk_text") or "")
    ]
    ok6 = len(bad_hr_annual) == 0
    results.append(
        ExpectationResult(
            "hr_leave_no_stale_10d_annual",
            ok6,
            "halt",
            f"violations={len(bad_hr_annual)}",
        )
    )

    # E7 (Sprint 2): Không được chứa ngôn ngữ mơ hồ SLA (vague / approximation)
    # Metric_impact: Tránh retrieval câu hỏi về SLA nhận sai commitment.
    vague_sla = [
        r
        for r in cleaned_rows
        if r.get("doc_id") in ("sla_p1_2026",)
        and any(w in (r.get("chunk_text") or "").lower() for w in ["khoảng", "xấp xỉ", "eventually", "approximately", "roughly"])
    ]
    ok7 = len(vague_sla) == 0
    results.append(
        ExpectationResult(
            "sla_no_vague_language",
            ok7,
            "halt",
            f"vague_sla_violations={len(vague_sla)}",
        )
    )

    # E8 (Sprint 2): Tất cả chunk phải có valid chunk_id không rỗng, định dạng doc_id_seq_hash
    # Metric_impact: Đảm bảo idempotent embed và traceability.
    bad_chunk_ids = [
        r
        for r in cleaned_rows
        if not (r.get("chunk_id") or "").strip() or "_" not in (r.get("chunk_id") or "")
    ]
    ok8 = len(bad_chunk_ids) == 0
    results.append(
        ExpectationResult(
            "valid_chunk_id_format",
            ok8,
            "halt",
            f"invalid_chunk_ids={len(bad_chunk_ids)}",
        )
    )

    halt = any(not r.passed and r.severity == "halt" for r in results)
    return results, halt
