"""美股静态股池（universe）加载与 GICS 板块元数据。

方案 B 的核心数据资产：标普500 成分 + GICS 一级行业标签，季频由
backend/scripts/fetch_us_constituents.py 重新生成。本模块只做加载/校验，
不发起任何网络请求。
"""
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "us_sp500_gics.json"

# GICS 11 一级行业 英文 -> 中文（与抓取脚本 EXPECTED_SECTORS 键一致）
GICS_EN_TO_CN = {
    "Information Technology": "信息技术",
    "Health Care": "医疗保健",
    "Financials": "金融",
    "Consumer Discretionary": "非必需消费",
    "Consumer Staples": "必需消费",
    "Industrials": "工业",
    "Energy": "能源",
    "Materials": "原材料",
    "Communication Services": "通信服务",
    "Utilities": "公用事业",
    "Real Estate": "房地产",
}
GICS_CN_TO_EN = {cn: en for en, cn in GICS_EN_TO_CN.items()}

# 固定展示顺序（与官方字母序无关，稳定 UI 排序）
_SECTOR_CN_ORDER = [
    "信息技术", "医疗保健", "金融", "非必需消费", "必需消费", "工业",
    "能源", "原材料", "通信服务", "公用事业", "房地产",
]


@dataclass(frozen=True)
class UsUniverseMember:
    symbol: str
    name_en: str
    sector_en: str

    @property
    def sector_cn(self) -> str:
        return GICS_EN_TO_CN[self.sector_en]


def get_sector_cns() -> list:
    """板块中文名列表，固定顺序，用于遍历与 UI 兜底。"""
    return list(_SECTOR_CN_ORDER)


@lru_cache(maxsize=1)
def load_us_constituents() -> list:
    """读取并校验静态成分表，返回 UsUniverseMember 列表（按 symbol 排序）。

    校验失败（数量/ticker/行业标签异常）直接抛错：宁可启动即失败，
    也不能带着残缺股池聚合出假板块数据。
    """
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    members = []
    seen = set()
    for c in raw["constituents"]:
        sym = c["symbol"]
        if sym in seen:
            raise ValueError(f"成分表重复 ticker: {sym}")
        seen.add(sym)
        if c["sector"] not in GICS_EN_TO_CN:
            raise ValueError(f"成分表含未知 GICS 行业: {c['symbol']} {c['sector']}")
        members.append(UsUniverseMember(symbol=sym, name_en=c["name_en"], sector_en=c["sector"]))
    if not 490 <= len(members) <= 520:
        raise ValueError(f"成分数量异常: {len(members)}")
    return members
