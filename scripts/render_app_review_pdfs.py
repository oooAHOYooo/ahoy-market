#!/usr/bin/env python3
"""Render simple App Review rights PDFs without browser or LaTeX dependencies."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from textwrap import wrap


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "app-review" / "pdf"
SRC = ROOT / "docs" / "app-review"

PAGE_W = 612
PAGE_H = 792
MARGIN = 54
LINE = 14


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class Pdf:
    def __init__(self, title: str):
        self.title = title
        self.pages: list[list[str]] = []
        self.ops: list[str] = []
        self.y = PAGE_H - MARGIN

    def new_page(self):
        if self.ops:
            self.pages.append(self.ops)
        self.ops = []
        self.y = PAGE_H - MARGIN
        self.text(self.title, size=8, x=MARGIN, y=PAGE_H - 28, font="F1")

    def ensure(self, height: int):
        if self.y - height < MARGIN:
            self.new_page()

    def raw(self, op: str):
        self.ops.append(op)

    def text(self, text: str, size: int = 11, x: int = MARGIN, y: float | None = None, font: str = "F1"):
        if y is None:
            y = self.y
        self.raw(f"BT /{font} {size} Tf {x} {y:.2f} Td ({esc(text)}) Tj ET")

    def line(self, x1: int, y1: float, x2: int, y2: float, width: float = 0.5):
        self.raw(f"{width} w {x1} {y1:.2f} m {x2} {y2:.2f} l S")

    def heading(self, text: str, level: int = 1):
        size = 18 if level == 1 else 13
        gap = 26 if level == 1 else 20
        self.ensure(gap + 8)
        if level == 1:
            self.text(text, size=size, font="F2")
            self.y -= 8
            self.line(MARGIN, self.y, PAGE_W - MARGIN, self.y, 1)
            self.y -= 18
        else:
            self.y -= 4
            self.text(text, size=size, font="F2")
            self.y -= gap

    def para(self, text: str, size: int = 10, indent: int = 0):
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            self.y -= 6
            return
        width_chars = 92 if size <= 10 else 76
        for line in wrap(text, width_chars):
            self.ensure(LINE + 2)
            self.text(line, size=size, x=MARGIN + indent)
            self.y -= LINE
        self.y -= 4

    def bullet(self, text: str):
        self.ensure(LINE + 2)
        self.text("-", size=10, x=MARGIN + 6)
        for i, line in enumerate(wrap(text, 86)):
            self.text(line, size=10, x=MARGIN + 22, y=self.y - (i * LINE))
        self.y -= LINE * max(1, len(wrap(text, 86))) + 3

    def field(self, label: str):
        self.ensure(20)
        self.text(f"{label}:", size=10, font="F2")
        self.line(MARGIN + 150, self.y - 2, PAGE_W - MARGIN, self.y - 2)
        self.y -= 20

    def finish(self, path: Path):
        if self.ops:
            self.pages.append(self.ops)
        objects: list[bytes] = []

        def add(obj: str | bytes) -> int:
            if isinstance(obj, str):
                obj = obj.encode("latin-1")
            objects.append(obj)
            return len(objects)

        font1 = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        font2 = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
        page_ids = []
        content_ids = []
        for ops in self.pages:
            stream = "\n".join(ops).encode("latin-1", "replace")
            content_ids.append(add(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"))
            page_ids.append(None)
        pages_id = len(objects) + len(page_ids) + 1
        for idx, content_id in enumerate(content_ids):
            page_ids[idx] = add(
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                f"/Resources << /Font << /F1 {font1} 0 R /F2 {font2} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            )
        kids = " ".join(f"{pid} 0 R" for pid in page_ids)
        add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>")
        catalog_id = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")

        out = bytearray(b"%PDF-1.4\n")
        xref = [0]
        for i, obj in enumerate(objects, start=1):
            xref.append(len(out))
            out.extend(f"{i} 0 obj\n".encode())
            out.extend(obj)
            out.extend(b"\nendobj\n")
        start = len(out)
        out.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
        for offset in xref[1:]:
            out.extend(f"{offset:010d} 00000 n \n".encode())
        out.extend(f"trailer << /Size {len(objects)+1} /Root {catalog_id} 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
        path.write_bytes(out)


def md_to_pdf(md_path: Path, pdf_path: Path, title: str):
    pdf = Pdf(title)
    pdf.new_page()
    for raw_line in md_path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            pdf.para("")
        elif line.startswith("# "):
            pdf.heading(line[2:], 1)
        elif line.startswith("## "):
            pdf.heading(line[3:], 2)
        elif line.startswith("- "):
            pdf.bullet(line[2:])
        elif re.match(r"^\d+\. ", line):
            pdf.bullet(re.sub(r"^\d+\. ", "", line))
        elif line.startswith("|"):
            continue
        elif line.endswith(":") and len(line) < 40:
            pdf.field(line[:-1])
        else:
            pdf.para(line)
    pdf.finish(pdf_path)


def schedule_pdf():
    pdf = Pdf("Ahoy Artist Rights Schedule")
    pdf.new_page()
    pdf.heading("Artist Rights Schedule", 1)
    pdf.para("Generated: May 8, 2026")
    pdf.para("Source: Ahoy production content_artists table")
    pdf.para("Purpose: App Store Review Guidelines 5.2.2 and 5.2.3 support packet")
    pdf.heading("Current Schedule", 2)
    with (SRC / "artist-rights-schedule-2026-05-08.csv").open() as f:
        rows = list(csv.DictReader(f))
    headers = ["Name", "Type", "Slug", "Status"]
    widths = [150, 72, 130, 150]
    x = MARGIN
    pdf.ensure(24)
    for h, w in zip(headers, widths):
        pdf.text(h, size=8, x=x, font="F2")
        x += w
    pdf.y -= 12
    pdf.line(MARGIN, pdf.y, PAGE_W - MARGIN, pdf.y)
    pdf.y -= 10
    for row in rows:
        pdf.ensure(32)
        vals = [row["name"], row["artist_type"], row["slug"], "Authorization claimed; evidence reference to be filled"]
        x = MARGIN
        max_lines = 1
        wrapped = []
        for val, w in zip(vals, widths):
            lines = wrap(val or "", max(8, int(w / 5.2))) or [""]
            wrapped.append(lines[:3])
            max_lines = max(max_lines, len(lines[:3]))
        for lines, w in zip(wrapped, widths):
            for i, line in enumerate(lines):
                pdf.text(line, size=8, x=x, y=pdf.y - (i * 10))
            x += w
        pdf.y -= max_lines * 10 + 8
    pdf.heading("Use", 2)
    pdf.para("Pair this schedule with signed creator terms, authorization emails, contracts, release forms, or company production records.")
    pdf.finish(OUT / "Ahoy_Artist_Rights_Schedule_2026-05-08.pdf")


def rights_packet_pdf():
    pdf = Pdf("Ahoy App Review Rights Packet")
    pdf.new_page()
    pdf.heading("Ahoy Indie Media Content Rights Summary", 1)
    for line in [
        "Date: May 8, 2026",
        "App: Ahoy Indie Media",
        "Submission ID: 4c2c87f4-0b40-4932-8e34-34fcfc1d4171",
        "Version reviewed: 1.0.9 (202605021129)",
        "Company: Little Market LLC / Ahoy Indie Media",
    ]:
        pdf.para(line)
    pdf.heading("Summary", 2)
    pdf.para("Ahoy Indie Media is a direct-to-artist media platform. The app does not provide unauthorized access to third-party streaming services, cable television, IPTV services, broadcast channels, or external discovery catalogs.")
    pdf.para("The content available in the app is either produced by Little Market LLC / Ahoy Indie Media, submitted by creators and rights holders who authorized Ahoy to distribute it, or otherwise cleared for use by Ahoy.")
    pdf.para("The AHOY TV section is a scheduled marketing and discovery surface for Ahoy-controlled video programming. It uses Ahoy catalog videos and organizes them into editorial channels such as Films, Music Videos, Live Shows, and Misc. It is not a retransmission service and does not connect users to third-party TV providers.")
    pdf.heading("Included Records", 2)
    for item in [
        "Master content rights register",
        "Current artist and rights holder schedule exported from Ahoy's production content database",
        "Creator content authorization template for ongoing rights records",
        "Rights controls checklist for future content intake and app review support",
    ]:
        pdf.bullet(item)
    pdf.heading("Platform Rights Position", 2)
    pdf.para("Ahoy's AHOY TV feature is not a third-party cable, broadcast, IPTV, or unauthorized channel aggregation service. It is a marketing-style scheduled viewing surface that presents Ahoy-owned, Ahoy-produced, or Ahoy-authorized video programming from the platform catalog.")
    pdf.heading("Company Statement", 2)
    pdf.para("Little Market LLC / Ahoy Indie Media confirms that the Ahoy app does not provide unauthorized access to third-party streaming services, third-party TV providers, cable channels, or external discovery catalogs.")
    pdf.para("The app presents content produced by Ahoy/Little Market LLC or submitted by artists, creators, hosts, and rights holders who authorized Ahoy to stream, display, promote, and catalog their content in the Ahoy app.")
    pdf.heading("Maintenance Rule", 2)
    pdf.para("No content should be published to Ahoy unless the rights evidence exists first. If rights evidence is missing, the content should stay unpublished, hidden, or internal until the creator or rights holder authorization is complete.")
    pdf.finish(OUT / "Ahoy_App_Review_Rights_Packet_2026-05-08.pdf")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rights_packet_pdf()
    schedule_pdf()
    md_to_pdf(SRC / "creator-content-authorization-template.md", OUT / "Ahoy_Creator_Content_Authorization_Template.pdf", "Ahoy Creator Content Authorization")
    md_to_pdf(SRC / "rights-future-proofing-checklist.md", OUT / "Ahoy_Rights_Controls_Checklist.pdf", "Ahoy Rights Controls Checklist")
    md_to_pdf(SRC / "apple-rights-response-2026-05-08.md", OUT / "Ahoy_App_Review_Response_Note_2026-05-08.pdf", "Ahoy App Review Response Note")


if __name__ == "__main__":
    main()
