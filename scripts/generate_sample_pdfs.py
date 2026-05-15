"""Generate synthetic federal-style sample PDFs under sample_data/policies/pdf.

Run from repo root:
  cd backend && uv run --with fpdf2 python ../scripts/generate_sample_pdfs.py
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos


class Doc(FPDF):
    def header(self) -> None:  # noqa: N802
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(30, 58, 95)
        # Core fonts are latin-1 only; keep header/footer ASCII-only.
        self.cell(0, 8, "GovFlow AI - Synthetic federal-style sample (not official)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def footer(self) -> None:  # noqa: N802
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(90, 90, 90)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def write_pdf(path: Path, title: str, paragraphs: list[str]) -> None:
    pdf = Doc()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(20, 45, 82)
    pdf.multi_cell(0, 8, title)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(30, 30, 30)
    for block in paragraphs:
        pdf.multi_cell(0, 6, block)
        pdf.ln(2)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "sample_data" / "policies" / "pdf"

    specs: list[tuple[str, str, list[str]]] = [
        (
            "OMB-MEMO-REMOTE-WORK.pdf",
            "Memorandum: Remote work eligibility (excerpt)",
            [
                "Subject: Eligibility and documentation for routine telework.",
                "Employees must meet position suitability, Fully Successful performance, "
                "and security/privacy workspace minimums.",
                "Supervisors retain signed telework agreements, risk acknowledgments for CUI, "
                "and quarterly attestations.",
            ],
        ),
        (
            "NARA-RECORDS-RETENTION.pdf",
            "General Records Schedule excerpt",
            [
                "Transitory messages without substantive decisions: destroy at 90 days.",
                "Substantive policy memoranda: six years after superseded; may be permanent.",
                "Electronic copies follow the retention of the record copy in the DMS.",
            ],
        ),
        (
            "CISO-CLOUD-BASELINE.pdf",
            "CIO directive: Cloud collaboration baseline",
            [
                "Phishing-resistant MFA for privileged roles; deny-by-default external sharing.",
                "Centralized audit logs: 90 days online, one year cold storage.",
                "Exceptions require AO approval and POA&M tracking.",
            ],
        ),
        (
            "FAR-MICRO-PURCHASE.pdf",
            "Micro-purchase desk guide",
            [
                "Document price reasonableness; avoid artificial splitting of requirements.",
                "Above micro-purchase threshold: obtain quotes when practicable.",
                "Route software purchases through enterprise software review.",
            ],
        ),
        (
            "EEO-ANTI-HARASSMENT.pdf",
            "EEO anti-harassment directive excerpt",
            [
                "Harassment based on protected classes is prohibited.",
                "Formal EEO counseling generally within 45 calendar days of the alleged incident.",
                "Supervisors must notify EEO promptly and prevent retaliation.",
            ],
        ),
    ]

    for filename, title, paras in specs:
        write_pdf(out / filename, title, paras)

    print(f"Wrote {len(specs)} PDFs to {out}")


if __name__ == "__main__":
    main()
