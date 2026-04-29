"""Diagnostic script: dump all horizontal line segments from specified PDF pages.

Usage:
    python scripts/debug_double_underlines.py path/to/file.pdf [page_numbers...]

Examples:
    python scripts/debug_double_underlines.py doc.pdf          # all pages
    python scripts/debug_double_underlines.py doc.pdf 3 4 5    # pages 3-5 (1-indexed)
"""

import sys
import fitz  # PyMuPDF


def dump_lines(pdf_path: str, page_numbers=None) -> None:
    doc = fitz.open(pdf_path)

    for page_index, page in enumerate(doc):
        page_num = page_index + 1
        if page_numbers and page_num not in page_numbers:
            continue

        page_height = page.rect.height
        page_width = page.rect.width
        print(f"\n{'='*70}")
        print(f"PAGE {page_num}  (size: {page_width:.1f} x {page_height:.1f} pt)")
        print(f"{'='*70}")

        drawings = page.get_drawings()
        h_lines = []
        for d in drawings:
            r = d.get("rect")
            if r:
                height = r.y1 - r.y0
                width = r.x1 - r.x0
                if height < 5 and width > 10:  # thin horizontal segments
                    h_lines.append({
                        "y0": r.y0, "y1": r.y1,
                        "x0": r.x0, "x1": r.x1,
                        "h": height, "w": width,
                        "color": d.get("color") or d.get("fill"),
                    })

        h_lines.sort(key=lambda l: (l["y0"], l["x0"]))

        print(f"Thin horizontal segments ({len(h_lines)} total):")
        print(f"{'idx':>4}  {'y0':>7}  {'y1':>7}  {'gap_h':>6}  {'x0':>7}  {'x1':>7}  {'width':>7}  {'y_frac':>7}")
        print(f"{'-'*4}  {'-'*7}  {'-'*7}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*7}  {'-'*7}")
        for i, ln in enumerate(h_lines):
            prev_y1 = h_lines[i - 1]["y1"] if i > 0 else ln["y0"]
            gap = ln["y0"] - prev_y1
            y_frac = (ln["y0"] + ln["y1"]) / 2 / page_height
            print(
                f"{i:>4}  {ln['y0']:>7.2f}  {ln['y1']:>7.2f}  "
                f"{gap:>6.2f}  {ln['x0']:>7.2f}  {ln['x1']:>7.2f}  "
                f"{ln['w']:>7.2f}  {y_frac:>7.4f}"
            )

        # Stage 1: collapse coincident paths (gap <= 0.1pt) into logical lines
        logical = []
        skip: set[int] = set()
        for i, a in enumerate(h_lines):
            if i in skip:
                continue
            merged = dict(a)
            for j, b in enumerate(h_lines[i + 1:], start=i + 1):
                if j in skip:
                    continue
                if b["y0"] - merged["y1"] > 0.1:
                    break
                merged["y0"] = min(merged["y0"], b["y0"])
                merged["y1"] = max(merged["y1"], b["y1"])
                merged["x0"] = min(merged["x0"], b["x0"])
                merged["x1"] = max(merged["x1"], b["x1"])
                skip.add(j)
            logical.append(merged)

        print(f"\nLogical lines after collapsing coincident paths ({len(logical)} total):")
        for i, ln in enumerate(logical):
            y_frac = (ln["y0"] + ln["y1"]) / 2 / page_height
            print(f"  {i:>3}: y={ln['y0']:.2f}–{ln['y1']:.2f}  x={ln['x0']:.1f}–{ln['x1']:.1f}  y_frac={y_frac:.4f}")

        # Stage 2: find logical-line pairs 0.3–3pt apart (accounting double underlines)
        print(f"\nDetected double underlines (logical-line gap 0.3–3pt, x-overlap >= 70%):")
        used2: set[int] = set()
        pairs_found = 0
        for i, a in enumerate(logical):
            if i in used2:
                continue
            for j, b in enumerate(logical[i + 1:], start=i + 1):
                if j in used2:
                    continue
                gap = b["y0"] - a["y1"]
                if gap > 3:
                    break
                if gap < 0.3:
                    continue
                overlap = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
                span = max(a["x1"] - a["x0"], b["x1"] - b["x0"])
                if span > 0 and overlap / span > 0.7:
                    center_y = (a["y0"] + b["y1"]) / 2
                    print(
                        f"  logical {i}&{j}: "
                        f"y={a['y0']:.2f} — y={b['y0']:.2f}  "
                        f"gap={gap:.2f}pt  "
                        f"x-overlap={overlap/span*100:.0f}%  "
                        f"center_y_frac={center_y/page_height:.4f}"
                    )
                    used2.add(i)
                    used2.add(j)
                    pairs_found += 1
                    break
        if pairs_found == 0:
            print("  (none)")

    doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    pdf_path = sys.argv[1]
    pages = [int(p) for p in sys.argv[2:]] if len(sys.argv) > 2 else None
    dump_lines(pdf_path, pages)
