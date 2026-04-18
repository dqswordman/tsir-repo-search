#!/usr/bin/env python3
"""Render updated submission figures with claim-aligned labels.

The current paper uses raster figures. This script regenerates those PNG assets
from code so the internal labels stay synchronized with the locked claim.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"

FIG1_PATH = FIG_DIR / "fig1_tsir_overview.png"
FIG2_PATH = FIG_DIR / "fig2_tsir_flowchart.png"

W = 1600
H = 1024

BG = "#f6f7fb"
INK = "#2f3744"
SUB = "#5a6473"
LINE = "#cfd5df"
BLUE = "#2f6ea5"
BLUE_DARK = "#214f7d"
BLUE_SOFT = "#e8f1fb"
RED = "#c94848"
RED_SOFT = "#fdeaea"
GRAY_BOX = "#eef1f5"
GRAY = "#8590a1"
WHITE = "#ffffff"
GREEN = "#2f8f5b"
GREEN_SOFT = "#e7f6ef"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size=size)


def draw_centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, *,
                  fill: str = INK, size: int = 28, bold: bool = False,
                  spacing: int = 6, align: str = "center") -> None:
    f = font(size, bold)
    bbox = draw.multiline_textbbox((0, 0), text, font=f, spacing=spacing, align=align)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x0, y0, x1, y1 = box
    x = x0 + (x1 - x0 - tw) / 2
    y = y0 + (y1 - y0 - th) / 2
    draw.multiline_text((x, y), text, font=f, fill=fill, spacing=spacing, align=align)


def draw_label(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, *,
               fill: str, outline: str | None = None, text_fill: str = WHITE,
               size: int = 24, bold: bool = True, radius: int = 24) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline or fill, width=2)
    draw_centered(draw, box, text, fill=text_fill, size=size, bold=bold)


def draw_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *,
              fill: str = WHITE, outline: str = LINE, radius: int = 26) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=3)


def draw_doc(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, *,
             fill: str = WHITE, outline: str = GRAY, fold_fill: str = "#d9dee8") -> None:
    fold = 26
    pts = [(x, y), (x + w - fold, y), (x + w, y + fold), (x + w, y + h), (x, y + h)]
    draw.polygon(pts, fill=fill, outline=outline)
    draw.line((x + w - fold, y, x + w - fold, y + fold), fill=outline, width=2)
    draw.line((x + w - fold, y + fold, x + w, y + fold), fill=outline, width=2)
    draw.polygon([(x + w - fold, y), (x + w - fold, y + fold), (x + w, y + fold)], fill=fold_fill, outline=outline)
    for i in range(4):
        yy = y + 34 + i * 18
        draw.rounded_rectangle((x + 20, yy, x + w - 20, yy + 5), radius=3, fill="#b9c3d1")


def draw_folder(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, *,
                fill: str = BLUE, outline: str = BLUE_DARK) -> None:
    tab_w = int(w * 0.34)
    tab_h = int(h * 0.25)
    draw.rounded_rectangle((x + 24, y, x + tab_w, y + tab_h), radius=10, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((x, y + tab_h - 10, x + w, y + h), radius=14, fill=fill, outline=outline, width=3)


def draw_shield(draw: ImageDraw.ImageDraw, cx: int, cy: int, size_px: int, *, fill: str = BLUE, outline: str = BLUE_DARK) -> None:
    s = size_px
    pts = [
        (cx, cy - s),
        (cx + s * 0.72, cy - s * 0.62),
        (cx + s * 0.6, cy + s * 0.25),
        (cx, cy + s),
        (cx - s * 0.6, cy + s * 0.25),
        (cx - s * 0.72, cy - s * 0.62),
    ]
    draw.polygon(pts, fill=fill, outline=outline)
    inner = [
        (cx, cy - s * 0.76),
        (cx + s * 0.48, cy - s * 0.42),
        (cx + s * 0.39, cy + s * 0.17),
        (cx, cy + s * 0.64),
        (cx - s * 0.39, cy + s * 0.17),
        (cx - s * 0.48, cy - s * 0.42),
    ]
    draw.polygon(inner, fill=WHITE)


def draw_search_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=BLUE, width=8, fill=WHITE)
    draw.line((cx + r - 4, cy + r - 4, cx + r + 24, cy + r + 24), fill=BLUE, width=8)


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], *,
               color: str, width: int = 10) -> None:
    x0, y0 = start
    x1, y1 = end
    draw.line((x0, y0, x1, y1), fill=color, width=width)
    if abs(x1 - x0) >= abs(y1 - y0):
        direction = 1 if x1 >= x0 else -1
        head = [(x1, y1), (x1 - 26 * direction, y1 - 16), (x1 - 26 * direction, y1 + 16)]
    else:
        direction = 1 if y1 >= y0 else -1
        head = [(x1, y1), (x1 - 16, y1 - 26 * direction), (x1 + 16, y1 - 26 * direction)]
    draw.polygon(head, fill=color)


def divider(draw: ImageDraw.ImageDraw, y: int) -> None:
    draw.line((24, y, W - 24, y), fill=LINE, width=2)


def render_fig1() -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, (0, 16, W, 78), "Trusted Scope Inheritance Restores Search Authority", size=48, bold=True)
    divider(draw, 88)

    draw_centered(draw, (0, 104, W, 154), "failure mode under mixed provenance", size=28, bold=False, fill=BLUE_DARK)

    # Left inputs.
    draw_card(draw, (48, 182, 276, 378), fill=WHITE)
    draw_shield(draw, 92, 248, 42)
    draw_centered(draw, (118, 212, 250, 320), "Trusted\nMetadata", size=30, bold=True)
    draw_centered(draw, (64, 318, 260, 368), "authorized roots\nflag policy", size=22, fill=SUB)

    draw_card(draw, (48, 402, 276, 550), fill=WHITE)
    draw_centered(draw, (64, 430, 260, 510), "User\nQuery", size=30, bold=True)
    draw_centered(draw, (64, 500, 260, 540), "literal search task", size=22, fill=SUB)

    draw_card(draw, (360, 286, 550, 482), fill=GRAY_BOX, outline="#8f99a8")
    draw_centered(draw, (388, 330, 522, 430), "Repository\nAssistant", size=34, bold=True)

    draw_arrow(draw, (278, 278), (356, 348), color=BLUE, width=7)
    draw_arrow(draw, (278, 468), (356, 412), color=BLUE, width=7)

    # Attack documents.
    attack_boxes = [
        ((838, 164, 1128, 292), "root_widen_hidden"),
        ((838, 334, 1128, 462), "sibling_path_pivot"),
        ((838, 504, 1128, 632), "parent_escape"),
    ]
    for box, label in attack_boxes:
        x0, y0, x1, y1 = box
        draw_doc(draw, x0, y0, x1 - x0, y1 - y0, fill=WHITE, outline=GRAY)
        draw_label(draw, (x0 + 16, y0 + 18, x0 + 240, y0 + 64), label, fill=RED, size=22, radius=18)

    draw_arrow(draw, (550, 384), (690, 384), color=BLUE_DARK, width=8)
    draw_arrow(draw, (690, 384), (834, 228), color=RED, width=7)
    draw_arrow(draw, (690, 384), (834, 398), color=RED, width=7)
    draw_arrow(draw, (690, 384), (834, 568), color=RED, width=7)

    # Unsafe proposal card.
    draw_card(draw, (1214, 236, 1548, 582), fill=WHITE, outline=GRAY)
    draw_label(draw, (1232, 256, 1530, 314), "Unsafe Tool Proposal", fill=RED, size=24)
    draw_centered(
        draw,
        (1244, 338, 1518, 540),
        "\"path\"=\".\"\n\"hidden\"=true\n\"tests/\"\n\"../shared-config/\"",
        size=28,
        bold=False,
        fill=INK,
        spacing=14,
    )
    draw_arrow(draw, (1128, 228), (1208, 298), color=RED, width=7)
    draw_arrow(draw, (1128, 398), (1208, 406), color=RED, width=7)
    draw_arrow(draw, (1128, 568), (1208, 496), color=RED, width=7)

    divider(draw, 674)
    draw_centered(draw, (0, 690, W, 744), "TSIR restores trusted search authority", size=30, bold=False, fill=BLUE_DARK)

    draw_card(draw, (56, 756, 272, 884), fill=WHITE)
    draw_shield(draw, 98, 812, 34)
    draw_centered(draw, (118, 780, 246, 852), "Trusted\nMetadata", size=28, bold=True)
    draw_centered(draw, (72, 842, 256, 874), "authorized roots", size=20, fill=SUB)

    draw_card(draw, (56, 894, 272, 1010), fill=WHITE)
    draw_centered(draw, (84, 924, 244, 990), "User\nQuery", size=28, bold=True)
    draw_arrow(draw, (274, 820), (356, 864), color=BLUE, width=7)
    draw_arrow(draw, (274, 952), (356, 894), color=BLUE, width=7)

    draw_card(draw, (360, 794, 550, 966), fill=GRAY_BOX, outline="#8f99a8")
    draw_centered(draw, (388, 830, 522, 930), "Repository\nAssistant", size=34, bold=True)

    draw_label(draw, (596, 786, 770, 970), "TSIR", fill=BLUE, size=42, radius=32)
    draw_arrow(draw, (550, 880), (590, 880), color=BLUE, width=8)
    draw_arrow(draw, (772, 880), (842, 880), color=BLUE, width=8)

    draw_card(draw, (844, 780, 1132, 964), fill=WHITE, outline=BLUE_DARK)
    draw_label(draw, (860, 804, 1118, 854), "Rewritten Tool Call", fill=BLUE, size=24, radius=18)
    draw_centered(
        draw,
        (872, 874, 1104, 944),
        "\"path\"=\"README.md\"\n\"hidden\"=false",
        size=28,
        bold=False,
        fill=BLUE_DARK,
        spacing=14,
    )

    draw_card(draw, (1182, 780, 1376, 964), fill=WHITE, outline=LINE)
    draw_centered(draw, (1198, 806, 1360, 888), "Authorized\nFile", size=32, bold=True)
    draw_search_icon(draw, 1294, 916, 34)
    draw_arrow(draw, (1134, 880), (1178, 880), color=BLUE, width=8)

    draw_card(draw, (1398, 748, 1578, 986), fill=WHITE, outline=LINE)
    draw_label(draw, (1418, 770, 1558, 830), "RESULT", fill=BLUE, size=30, radius=18)
    draw_centered(
        draw,
        (1410, 842, 1566, 966),
        "3 attack families\n8 real repositories\n2 successful models",
        size=20,
        bold=False,
        fill=INK,
        spacing=16,
    )
    draw_arrow(draw, (1378, 880), (1394, 880), color=BLUE, width=8)

    img.save(FIG1_PATH)


def render_fig2() -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw_centered(draw, (0, 18, W, 80), "Trusted Scope Inheritance for Mixed-Provenance Repository Search Agents", size=42, bold=True)
    divider(draw, 92)
    draw_centered(draw, (0, 104, W, 150), "runtime pipeline", size=30, bold=False, fill=BLUE_DARK)

    y0, y1 = 190, 510
    xs = [40, 270, 492, 716, 962, 1210, 1420]
    boxes = [
        ("Trusted\nMetadata", "authorized roots\nflag policy", BLUE_SOFT, BLUE_DARK),
        ("User\nRequest", "literal search task", WHITE, GRAY),
        ("Untrusted\nRetrieved Text", "mixed provenance", WHITE, GRAY),
        ("Model\nProposal", "attacker-chosen\nscope fields", WHITE, GRAY),
        ("TSIR\nCheck", "inherit trusted scope\nstrip unauthorized flags", BLUE_SOFT, BLUE_DARK),
        ("Final\nrg Call", "executed inside\nauthorized scope", WHITE, GRAY),
        ("Authorized\nHit", "expected file only", WHITE, GRAY),
    ]
    widths = [170, 160, 170, 180, 190, 180, 150]
    centers = []
    for x, (title, sub, fill, outline), width in zip(xs, boxes, widths):
        box = (x, y0, x + width, y1)
        draw_card(draw, box, fill=fill, outline=outline)
        draw_centered(draw, (x + 10, y0 + 18, x + width - 10, y0 + 110), title, size=28, bold=True)
        draw_centered(draw, (x + 16, y0 + 280, x + width - 16, y1 - 20), sub, size=22, bold=False, fill=SUB)
        centers.append((x + width // 2, (y0 + y1) // 2))

    draw_folder(draw, 68, 268, 112, 78)
    draw_doc(draw, 302, 246, 98, 128, fill=WHITE, outline=GRAY)
    draw_doc(draw, 532, 240, 118, 138, fill=WHITE, outline=GRAY)
    draw_label(draw, (500, 386, 652, 432), "attack hints", fill=RED, size=22, radius=18)
    draw_centered(draw, (504, 438, 648, 500), "root widen\nsibling pivot\nparent escape", size=18, bold=False)
    draw_label(draw, (740, 262, 868, 392), "unsafe", fill=RED_SOFT, outline=RED, text_fill=RED, size=24, radius=16)
    draw_card(draw, (736, 300, 886, 418), fill=WHITE, outline=RED)
    draw_centered(draw, (748, 320, 874, 404), "path=\".\"\nhidden=true", size=22, bold=False, fill=RED)
    draw_label(draw, (986, 266, 1128, 402), "TSIR", fill=BLUE, size=38, radius=28)
    draw_card(draw, (1228, 300, 1354, 422), fill=WHITE, outline=BLUE_DARK)
    draw_centered(draw, (1242, 322, 1340, 406), "path=\"README.md\"\nhidden=false", size=20, bold=False, fill=BLUE_DARK)
    draw_folder(draw, 1440, 268, 108, 78)
    draw_search_icon(draw, 1494, 406, 26)

    for idx in range(len(centers) - 1):
        start = (centers[idx][0] + widths[idx] // 2 - 12, centers[idx][1])
        end = (centers[idx + 1][0] - widths[idx + 1] // 2 + 12, centers[idx + 1][1])
        color = RED if idx == 2 else BLUE
        draw_arrow(draw, start, end, color=color, width=8)

    divider(draw, 590)
    draw_centered(draw, (0, 604, W, 646), "evaluation scope", size=30, bold=False, fill=BLUE_DARK)

    draw_card(draw, (28, 670, 1170, 918), fill="#f0f3f8", outline=LINE)
    chips = [
        ("root_widen_hidden", BLUE),
        ("sibling_path_pivot", RED),
        ("parent_escape", BLUE_DARK),
        ("controlled corpus", GREEN),
        ("8 real repositories", BLUE),
        ("Qwen2.5-7B", BLUE_DARK),
        ("Hermes-3-8B", BLUE),
    ]
    x = 70
    y = 728
    for label, color in chips:
        chip_w = max(170, len(label) * 12 + 44)
        draw_label(draw, (x, y, x + chip_w, y + 56), label, fill=color, size=24, radius=18)
        x += chip_w + 22
        if x > 1040:
            x = 70
            y += 82

    draw_card(draw, (1198, 686, 1540, 920), fill=WHITE, outline=GRAY)
    draw_centered(draw, (1220, 708, 1518, 760), "supported claim", size=26, bold=True)
    for idx, line in enumerate(
        [
            "0/40 unsafe final calls",
            "40/40 attacked completion",
            "40/40 clean completion",
        ]
    ):
        yy = 780 + idx * 52
        draw.rounded_rectangle((1234, yy, 1504, yy + 40), radius=12, fill="#f5f7fb", outline=LINE)
        draw_centered(draw, (1240, yy, 1498, yy + 40), line, size=22, bold=False)

    img.save(FIG2_PATH)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    render_fig1()
    render_fig2()


if __name__ == "__main__":
    main()
