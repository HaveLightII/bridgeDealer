#!/usr/bin/env python3
"""
staticDealer.py
--------------------------------
為純文字瀏覽器（例如 w3m，不執行 JavaScript）預先產生一批「靜態、已發好的」
橋牌牌局頁面。

背景：GitHub Pages 是純靜態託管，沒有伺服器可以在使用者請求當下計算亂數，
所以無法像 index.html 那樣「每次點擊都即時發一副新牌」。
折衷做法：在建置階段（開發者電腦上，或用 GitHub Actions）先產生大量獨立
洗牌過的牌局，輸出成純 HTML（不依賴任何 CSS/JS 才能讀取內容），
使用者在 w3m 裡用方向鍵挑一個「自己還沒看過內容」的連結點開，
即可達到近似隨機的體驗。

用法範例：
    python3 staticDealer.py --out boards --random-count 200 \
        --with-duplicate --with-three-player

輸出結構：
    boards/index.html                總索引
    boards/random/board-0001.html    純隨機 4 人局
    boards/duplicate/board-01.html   複式橋牌 16 局（固定莊家／有利方）
    boards/three-player/board-0001.html   3 人局（北家固定夢家）
"""

import argparse
import html
import os
import random

SUITS = [
    ("C", "♣"),
    ("D", "♦"),
    ("H", "♥"),
    ("S", "♠"),
]
SUIT_COLOR = {"C": "black", "D": "red", "H": "red", "S": "black"}
DISPLAY_ORDER = ["S", "H", "D", "C"]
RANKS = ["A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"]
HCP_VALUE = {"A": 4, "K": 3, "Q": 2, "J": 1}

SEAT_LABEL = {"N": "北", "E": "東", "S": "南", "W": "西"}

DUPLICATE_TABLE = [
    ("N", "none"), ("E", "ns"),   ("S", "ew"),   ("W", "both"),
    ("N", "ns"),   ("E", "ew"),   ("S", "both"), ("W", "none"),
    ("N", "ew"),   ("E", "both"), ("S", "none"), ("W", "ns"),
    ("N", "both"), ("E", "none"), ("S", "ns"),   ("W", "ew"),
]
VUL_LABEL = {"none": "無", "ns": "南北", "ew": "東西", "both": "雙方"}


def build_deck():
    return [(suit, rank) for suit, _ in SUITS for rank in RANKS]


def deal_4p(rng):
    deck = build_deck()
    rng.shuffle(deck)
    return {
        "N": deck[0:13],
        "E": deck[13:26],
        "S": deck[26:39],
        "W": deck[39:52],
    }


def group_by_suit(cards):
    grouped = {"C": [], "D": [], "H": [], "S": []}
    for suit, rank in cards:
        grouped[suit].append(rank)
    for s in grouped:
        grouped[s].sort(key=lambda r: RANKS.index(r))
    return grouped


def calc_hcp(cards):
    return sum(HCP_VALUE.get(rank, 0) for _, rank in cards)


def shape_string(grouped):
    return "-".join(str(len(grouped[k])) for k in DISPLAY_ORDER)


PAGE_CSS = """
body{font-family:monospace;max-width:640px;margin:24px auto;padding:0 12px;
line-height:1.6;background:#0f2e21;color:#f4ecd8;}
h1{font-size:1.1em;}
.hand{margin:0 0 18px;padding:10px 12px;border:1px solid #4a453d;}
.hand h2{margin:0 0 6px;font-size:1em;}
.suit-line{margin:0;}
.red{color:#e08a76;}
.meta{color:#c9a227;}
a{color:#c9a227;}
"""


def render_hand_html(seat_key, cards, is_dummy=False):
    grouped = group_by_suit(cards)
    hcp = calc_hcp(cards)
    label = SEAT_LABEL[seat_key]
    lines = [f'<div class="hand">']
    title = f"{label}（{seat_key}）"
    if is_dummy:
        title += " · 夢家"
    lines.append(f"<h2>{html.escape(title)}　<span class=\"meta\">HCP={hcp}　牌型={shape_string(grouped)}</span></h2>")
    for suit_key, glyph in [(k, dict(SUITS)[k]) for k in DISPLAY_ORDER]:
        cards_str = " ".join(grouped[suit_key]) if grouped[suit_key] else "-"
        css_class = "suit-line red" if SUIT_COLOR[suit_key] == "red" else "suit-line"
        lines.append(f'<p class="{css_class}">{glyph} {html.escape(cards_str)}</p>')
    lines.append("</div>")
    return "\n".join(lines)


def render_board_page(board_id, hands, dealer=None, vul=None, board_no=None,
                       is_three_player=False, back_href="../index.html"):
    parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-Hant-TW"><head><meta charset="UTF-8">',
        f"<title>Board {board_id}</title>",
        f"<style>{PAGE_CSS}</style></head><body>",
        f"<p><a href=\"{back_href}\">← 回列表</a></p>",
        f"<h1>Board #{board_no if board_no is not None else board_id}</h1>",
    ]

    if is_three_player:
        dummy = hands["N"]
        seats = ["E", "S", "W"]
        views = {seat: dummy[i * 4:(i + 1) * 4] for i, seat in enumerate(seats)}
        glyph = dict(SUITS)
        suit, rank = dummy[12]
        parts.append(f'<p class="meta">北家夢家的公開牌：{glyph[suit]}{rank}</p>')
        for seat, cards in views.items():
            shown = " ".join(glyph[suit] + rank for suit, rank in cards)
            parts.append(f'<p>{SEAT_LABEL[seat]}家查看：{shown}（HCP={calc_hcp(cards)}）</p>')
        best_seat = max(seats, key=lambda seat: calc_hcp(views[seat]))
        parts.append(f'<p class="meta">首叫（查看夢家 HCP 最高）：{SEAT_LABEL[best_seat]}（{best_seat}）</p>')
    else:
        if dealer:
            parts.append(f'<p class="meta">莊家：{SEAT_LABEL[dealer]}（{dealer}）</p>')
        if vul:
            parts.append(f'<p class="meta">有利方：{VUL_LABEL[vul]}</p>')

    for seat_key in ["N", "E", "S", "W"]:
        is_dummy = is_three_player and seat_key == "N"
        parts.append(render_hand_html(seat_key, hands[seat_key], is_dummy=is_dummy))

    parts.append("</body></html>")
    return "\n".join(parts)


def render_index(title, entries, back_href=None, note=""):
    parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-Hant-TW"><head><meta charset="UTF-8">',
        f"<title>{html.escape(title)}</title>",
        f"<style>{PAGE_CSS}</style></head><body>",
    ]
    if back_href:
        parts.append(f'<p><a href="{back_href}">← 回總索引</a></p>')
    parts.append(f"<h1>{html.escape(title)}</h1>")
    if note:
        parts.append(f'<p class="meta">{html.escape(note)}</p>')
    parts.append("<ul>")
    for label, href in entries:
        parts.append(f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>')
    parts.append("</ul></body></html>")
    return "\n".join(parts)


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    ap = argparse.ArgumentParser(description="產生純靜態橋牌牌局頁面（供無 JS 文字瀏覽器使用）")
    ap.add_argument("--out", default="boards", help="輸出資料夾（預設 boards）")
    ap.add_argument("--random-count", type=int, default=200, help="純隨機 4 人局數量（預設 200）")
    ap.add_argument("--with-duplicate", action="store_true", help="額外產生複式橋牌 16 局固定組")
    ap.add_argument("--with-three-player", action="store_true", help="額外產生 3 人橋牌局")
    ap.add_argument("--three-player-count", type=int, default=100, help="3 人局數量（預設 100）")
    ap.add_argument("--seed", type=int, default=None, help="整批產生用的主亂數種子（可重現）")
    args = ap.parse_args()

    master_rng = random.Random(args.seed)
    sections = []

    # ---- 純隨機 4 人局 ----
    random_entries = []
    for i in range(1, args.random_count + 1):
        rng = random.Random(master_rng.random())
        hands = deal_4p(rng)
        dealer = rng.choice(["N", "E", "S", "W"])
        board_id = f"{i:04d}"
        page = render_board_page(board_id, hands, dealer=dealer, vul=None,
                                  back_href="index.html")
        write(os.path.join(args.out, "random", f"board-{board_id}.html"), page)
        random_entries.append((f"Board {board_id}", f"board-{board_id}.html"))
    write(
        os.path.join(args.out, "random", "index.html"),
        render_index("純隨機 4 人局", random_entries, back_href="../index.html",
                      note="任選一份尚未看過內容的連結，即可獲得一副隨機牌局。"),
    )
    sections.append(("純隨機 4 人局", f"random/index.html", f"{args.random_count} 份"))

    # ---- 複式橋牌 16 局固定組 ----
    if args.with_duplicate:
        dup_entries = []
        for board_no in range(1, 17):
            dealer, vul = DUPLICATE_TABLE[board_no - 1]
            rng = random.Random(master_rng.random())
            hands = deal_4p(rng)
            board_id = f"{board_no:02d}"
            page = render_board_page(board_id, hands, dealer=dealer, vul=vul,
                                      board_no=board_no, back_href="index.html")
            write(os.path.join(args.out, "duplicate", f"board-{board_id}.html"), page)
            dup_entries.append((f"Board {board_no}（莊家 {SEAT_LABEL[dealer]}／{VUL_LABEL[vul]}）",
                                 f"board-{board_id}.html"))
        write(
            os.path.join(args.out, "duplicate", "index.html"),
            render_index("複式橋牌 16 局", dup_entries, back_href="../index.html",
                          note="莊家與有利方依標準 16 局循環表固定，牌型仍為隨機發牌。"),
        )
        sections.append(("複式橋牌 16 局", "duplicate/index.html", "16 份（固定莊家／有利方）"))

    # ---- 3 人橋牌 ----
    if args.with_three_player:
        tp_entries = []
        for i in range(1, args.three_player_count + 1):
            rng = random.Random(master_rng.random())
            hands = deal_4p(rng)
            board_id = f"{i:04d}"
            page = render_board_page(board_id, hands, is_three_player=True,
                                      back_href="index.html")
            write(os.path.join(args.out, "three-player", f"board-{board_id}.html"), page)
            tp_entries.append((f"Board {board_id}", f"board-{board_id}.html"))
        write(
            os.path.join(args.out, "three-player", "index.html"),
            render_index("三人橋牌局（北家固定夢家）", tp_entries, back_href="../index.html",
                          note="每家 13 張。北家為夢家，公開 1 張，其餘由東、南、西各查看 4 張。"),
        )
        sections.append(("三人橋牌局", "three-player/index.html", f"{args.three_player_count} 份"))

    write(
        os.path.join(args.out, "index.html"),
        render_index(
            "橋牌牌局（純文字瀏覽器版）",
            [(f"{label} — {count}", href) for label, href, count in sections],
            note="此區為預先產生的靜態頁面，供 w3m 等不支援 JavaScript 的瀏覽器使用；"
                 "若你的瀏覽器支援 JavaScript，建議改用上一層的互動版 index.html。",
        ),
    )

    total = args.random_count + (16 if args.with_duplicate else 0) + \
        (args.three_player_count if args.with_three_player else 0)
    print(f"完成，共產生 {total} 份牌局頁面於「{args.out}/」。")


if __name__ == "__main__":
    main()
