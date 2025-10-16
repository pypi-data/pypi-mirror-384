"""Capture a PNG screenshot and structured report from a local HTML file using Playwright.

Usage (with uvx):

    uvx --with playwright python html_snapshot.py path/to/file.html --output slide.png

Before first run, install the Playwright browser binaries:

    uvx playwright install chromium
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import Page, sync_playwright


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a local HTML file to PNG (and optional JSON report) via Playwright",
    )
    parser.add_argument("html_path", type=Path, help="Path to the local HTML file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="PNG output path (defaults to <html_path>.png)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional path to write a JSON layout analysis report",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1400,
        help="Viewport width in pixels",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=900,
        help="Viewport height in pixels",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait after load before capturing",
    )
    parser.add_argument(
        "--no-full-page",
        action="store_true",
        help="Capture only the viewport instead of the full page",
    )
    parser.add_argument(
        "--no-auto-install",
        action="store_true",
        help="Skip automatic Playwright browser install (requires Chromium to be pre-installed)",
    )
    return parser.parse_args(argv)


def default_browsers_path() -> Path:
    env_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if env_path:
        return Path(env_path)

    home = Path.home()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
        return base / "ms-playwright"
    if sys.platform == "darwin":
        return home / "Library/Caches/ms-playwright"
    return home / ".cache/ms-playwright"


def chromium_installed() -> bool:
    browsers_dir = default_browsers_path()
    if not browsers_dir.exists():
        return False
    return any(browsers_dir.glob("chromium-*/")) or any(browsers_dir.glob("chromium-*"))


def ensure_chromium_installed(auto_install: bool) -> None:
    if chromium_installed():
        return
    if not auto_install:
        raise RuntimeError(
            "Chromium browser binaries are missing. "
            "Run `uvx playwright install chromium` and try again."
        )
    if not shutil.which("playwright"):
        raise RuntimeError(
            "Playwright CLI not found. Install dependencies or set PLAYWRIGHT_BROWSERS_PATH."
        )
    print(
        "Chromium runtime not found; installing via `playwright install chromium`...",
        file=sys.stderr,
    )
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Automatic Chromium install failed. Run `uvx playwright install chromium` manually."
        ) from exc


def bbox_overlap(a: List[float], b: List[float], tolerance: float = 2.0) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh

    horizontal_overlap = min(ax2, bx2) - max(ax, bx)
    vertical_overlap = min(ay2, by2) - max(ay, by)

    return horizontal_overlap > tolerance and vertical_overlap > tolerance


def extract_slide_data(page: Page, html_path: Path) -> Dict[str, Any]:
    slide_locator = page.locator(".ppt-slide")
    slide_count = slide_locator.count()
    slides: List[Dict[str, Any]] = []
    fonts: set[str] = set()
    colors: set[str] = set()
    warnings: List[str] = []

    for index in range(slide_count):
        slide_locator_item = slide_locator.nth(index)
        slide_element = slide_locator_item.element_handle()
        if slide_element is None:
            continue
        slide_bbox = slide_element.bounding_box()
        if slide_bbox is None:
            continue

        slide_js = slide_element.evaluate(
            r"""
            (el) => {
                const items = [];
                const walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT);
                while (walker.nextNode()) {
                    const node = walker.currentNode;
                    if (!node || node === el) continue;
                    if (node.offsetParent === null) continue; // hidden
                    const text = node.innerText ? node.innerText.trim() : "";
                    if (!text) continue;
                    const hasChildText = Array.from(node.children).some(
                        (child) => child.innerText && child.innerText.trim().length > 0
                    );
                    if (hasChildText) continue;
                    const rect = node.getBoundingClientRect();
                    if (!rect || rect.width === 0 || rect.height === 0) continue;
                    const style = window.getComputedStyle(node);
                    items.push({
                        tag: node.tagName.toLowerCase(),
                        text,
                        words: text.split(/\s+/).filter(Boolean).length,
                        classes: node.className || "",
                        bbox: [rect.left, rect.top, rect.width, rect.height],
                        color: style.color,
                        backgroundColor: style.backgroundColor,
                        fontSize: style.fontSize,
                        fontFamily: style.fontFamily,
                        fontWeight: style.fontWeight,
                        overflow: node.scrollHeight > node.clientHeight + 1
                    });
                }
                const slideStyle = window.getComputedStyle(el);
                return {
                    items,
                    backgroundColor: slideStyle.backgroundColor,
                };
            }
            """
        )

        items: List[Dict[str, Any]] = slide_js["items"]
        slide_background = slide_js["backgroundColor"]

        for item in items:
            bbox = item.pop("bbox")
            item["bbox_viewport"] = [round(v, 3) for v in bbox]
            item["bbox_slide"] = [
                round(bbox[0] - slide_bbox["x"], 3),
                round(bbox[1] - slide_bbox["y"], 3),
                round(bbox[2], 3),
                round(bbox[3], 3),
            ]
            fonts.add(item["fontFamily"])
            colors.add(item["color"])

        total_words = sum(item["words"] for item in items)
        left_words = sum(
            item["words"]
            for item in items
            if item["bbox_slide"][0] + item["bbox_slide"][2] / 2 <= slide_bbox["width"] / 2
        )
        right_words = total_words - left_words

        density_warnings: List[str] = []
        if total_words > 260:
            density_warnings.append(
                f"Slide {index + 1} has {total_words} words (limit 260)."
            )
        if left_words > 160:
            density_warnings.append(
                f"Slide {index + 1} left half has {left_words} words (>160)."
            )
        if right_words > 160:
            density_warnings.append(
                f"Slide {index + 1} right half has {right_words} words (>160)."
            )

        overflow_items = [
            {
                "text": item["text"],
                "tag": item["tag"],
                "bbox_slide": item["bbox_slide"],
            }
            for item in items
            if item.get("overflow")
        ]

        overlaps = [
            {
                "a_text": a["text"],
                "b_text": b["text"],
                "a_bbox": a["bbox_slide"],
                "b_bbox": b["bbox_slide"],
            }
            for a, b in combinations(items, 2)
            if bbox_overlap(a["bbox_slide"], b["bbox_slide"])
        ]

        slide_summary = {
            "index": index + 1,
            "bbox": {k: round(v, 3) for k, v in slide_bbox.items()},
            "backgroundColor": slide_background,
            "word_count": {
                "total": total_words,
                "left": left_words,
                "right": right_words,
            },
            "item_count": len(items),
            "overflow_items": overflow_items,
            "overlaps": overlaps,
            "density_warnings": density_warnings,
        }

        acc_snapshot = page.accessibility.snapshot(root=slide_element)

        slides.append(
            {
                "summary": slide_summary,
                "items": items,
                "accessibility": acc_snapshot,
            }
        )

        warnings.extend(density_warnings)
        if overflow_items:
            warnings.append(
                f"Slide {index + 1} has {len(overflow_items)} text blocks with potential overflow."
            )
        if overlaps:
            warnings.append(
                f"Slide {index + 1} has {len(overlaps)} overlapping text regions."
            )

    return {
        "source": str(html_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "slides": slides,
        "fonts": sorted(fonts),
        "colors": sorted(colors),
        "warnings": warnings,
    }


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    html_path = args.html_path.resolve()
    if not html_path.exists():
        print(f"Error: HTML file not found: {html_path}", file=sys.stderr)
        return 1

    output_path = args.output.resolve() if args.output else html_path.with_suffix(".png")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ensure_chromium_installed(auto_install=not args.no_auto_install)

    report_data: Optional[Dict[str, Any]] = None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        if args.delay > 0:
            page.wait_for_timeout(int(args.delay * 1000))

        if args.report:
            report_data = extract_slide_data(page, html_path)

        page.screenshot(path=output_path, full_page=not args.no_full_page)
        page.close()
        browser.close()

    print(f"Saved screenshot to {output_path}")

    if args.report:
        report_path = args.report.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as fh:
            json.dump(report_data, fh, indent=2, ensure_ascii=False)
        print(f"Wrote layout report to {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
