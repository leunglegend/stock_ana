"""抓取标普500成分 + GICS 行业标签，生成 backend/app/data/us_sp500_gics.json（数据维护脚本，季频重跑）。

用法:  python scripts/fetch_us_constituents.py
来源:  https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv
CSV 列: Symbol, Security, GICS Sector, GICS Sub-Industry, ...（GICS Sector 为英文一级行业）
本脚本只取 Symbol/Security/GICS Sector；产物 count 应约 503。
"""
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

CSV_URL = ("https://raw.githubusercontent.com/datasets/s-and-p-500-companies/"
           "master/data/constituents.csv")
OUT = Path(__file__).resolve().parents[1] / "app" / "data" / "us_sp500_gics.json"
EXPECTED_SECTORS = {  # GICS 11 一级行业英文名（与 us_universe.GICS_EN_TO_CN 键一致）
    "Information Technology", "Health Care", "Financials",
    "Consumer Discretionary", "Consumer Staples", "Industrials", "Energy",
    "Materials", "Communication Services", "Utilities", "Real Estate",
}


def main() -> int:
    with urllib.request.urlopen(CSV_URL, timeout=20) as resp:
        text = resp.read().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    seen, constituents = set(), []
    for r in rows:
        sym = (r.get("Symbol") or "").strip().upper()
        name = (r.get("Security") or "").strip()
        sector = (r.get("GICS Sector") or "").strip()
        if not sym or not sector:
            continue
        if sector not in EXPECTED_SECTORS:
            print(f"警告: 未知 GICS 行业 {sector!r} @ {sym}，跳过", file=sys.stderr)
            continue
        if sym in seen:
            continue
        seen.add(sym)
        constituents.append({"symbol": sym, "name_en": name, "sector": sector})
    constituents.sort(key=lambda x: x["symbol"])
    if not 490 <= len(constituents) <= 520:
        print(f"错误: 成分数量异常 {len(constituents)}，预期约 503", file=sys.stderr)
        return 1
    OUT.write_text(json.dumps({
        "as_of": "2026-09-03",
        "source": "https://github.com/datasets/s-and-p-500-companies (S&P 500 constituents + GICS Sector)",
        "count": len(constituents),
        "constituents": constituents,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {OUT}，共 {len(constituents)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
