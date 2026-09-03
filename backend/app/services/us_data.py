"""美股收盘行情服务（方案 B 主链路 = 新浪静态日线）。

新浪静态日线在美股盘中也不更新当日 bar（实测 ET 午间请求仍返回上一
交易日完整日量），天然是"最近已入库交易日收盘"口径 —— 与美股页"收盘
复盘"定位一致。板块聚合依赖静态成分表（us_universe）。
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app.models.schemas import UsConstituent, UsIndexQuote, UsSector, UsSummary
from app.services import stock_data, us_universe

# (新浪代码, 展示 symbol, 中文名)；前 3 为 3 大指数，路由取 .DJI/.INX/.IXIC
US_INDEX_SYMBOLS = (
    (".INX", "SPX", "标普500"),
    (".IXIC", "IXIC", "纳斯达克"),
    (".DJI", "DJI", "道琼斯"),
    (".NDX", "NDX", "纳斯达克100"),
    (".SOX", "SOX", "费城半导体"),
)
_MAJOR_INDEX_SYMBOLS = ("DJI", "SPX", "IXIC")  # 摘要/卡片展示用 3 大指数


def _close_pct(price: float, prev_close: float) -> tuple:
    change = price - prev_close
    pct = (price / prev_close - 1) * 100 if prev_close else 0.0
    return change, pct


@stock_data._retry(max_retries=2, delay=1)
def _index_frame(ak, symbol: str):
    return ak.index_us_stock_sina(symbol=symbol)


def _frame_latest(frame):
    """frame 按 date 升序排序后返回 (date, close, prev_close)；不足两根返回 None。"""
    df = frame.sort_values("date").reset_index(drop=True)
    if len(df) < 2:
        return None
    last, prev = df.iloc[-1], df.iloc[-2]
    return str(last["date"]), float(last["close"]), float(prev["close"])


def fetch_index_quotes(ak=None) -> list:
    """拉 5 个美股指数的收盘涨跌（单指数失败跳过，不拖垮整体）。"""
    ak = ak or stock_data._get_ak()
    quotes = []
    for code, symbol, cn in US_INDEX_SYMBOLS:
        try:
            latest = _frame_latest(_index_frame(ak, code))
            if not latest:
                continue
            date, close, prev = latest
            change, pct = _close_pct(close, prev)
            quotes.append(UsIndexQuote(symbol=symbol, name=cn, value=close,
                                       change_amount=change, change_pct=pct))
        except Exception as e:
            print(f"[us] 指数 {code} 拉取失败: {e}")
    return quotes


def fetch_index_asof(ak=None) -> Optional[str]:
    """轻量探测最新美东交易日（标普500 日线最近 bar date，1 个请求）。"""
    ak = ak or stock_data._get_ak()
    try:
        latest = _frame_latest(_index_frame(ak, ".INX"))
        return latest[0] if latest else None
    except Exception as e:
        print(f"[us] as_of 探测失败: {e}")
        return None


def parse_us_daily(frame) -> Optional[dict]:
    """静态日线末两根 bar 收盘自算；返回 date/price/change_amount/change_pct。"""
    latest = _frame_latest(frame)
    if not latest:
        return None
    date, close, prev = latest
    change, pct = _close_pct(close, prev)
    return {"date": date, "price": close,
            "change_amount": change, "change_pct": pct}


@stock_data._retry(max_retries=2, delay=1)
def _stock_daily_frame(ak, symbol: str):
    return ak.stock_us_daily(symbol=symbol)


def _fetch_single(member, ak):
    """单成分拉取。失败打日志但不抛出（个股失败不影响整体）。"""
    try:
        parsed = parse_us_daily(_stock_daily_frame(ak, member.symbol))
    except Exception as e:
        print(f"[us] 成分 {member.symbol} 拉取失败: {e}")
        return None, None
    if not parsed:
        return None, None
    q = UsConstituent(symbol=member.symbol, name=member.name_en,
                      price=parsed["price"], change_amount=parsed["change_amount"],
                      change_pct=parsed["change_pct"])
    return q, parsed["date"]


def fetch_constituent_quotes(members, ak=None, max_workers=16) -> tuple:
    """并发拉成分日线；返回 (成功 quotes 列表, as_of)。

    as_of = 成功成分 bar date 的众数（多数成分共有的最晚 bar date，即最近已入库
    美东交易日；避免个别停牌/退市股把日期带偏）。整体失败返回 ([], None)。
    """
    ak = ak or stock_data._get_ak()
    quotes, dates = [], []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_fetch_single, m, ak): m.symbol for m in members}
        for fut in as_completed(futs):
            try:
                q, date = fut.result()
            except Exception as e:  # 防御：线程层未预期异常不拖垮整体
                print(f"[us] 成分线程异常: {e}")
                continue
            if q is not None:
                quotes.append(q)
                dates.append(date)
    if not quotes:
        return [], None
    as_of = max(set(dates), key=dates.count) if dates else None
    return quotes, as_of


def aggregate_sectors(members, quotes) -> list:
    """成员按 GICS 中文板块等权聚合。缺失行情的成员剔除，不计入任何统计。"""
    quote_by_symbol = {q.symbol: q for q in quotes}
    groups = {}
    for m in members:
        q = quote_by_symbol.get(m.symbol)
        if q is None:
            continue  # 无有效行情（停牌/退市/拉取失败）——不计入，避免假数据
        groups.setdefault(m.sector_cn, []).append((m, q))

    sectors = []
    for cn in us_universe.get_sector_cns():
        rows = groups.get(cn)
        if not rows:
            continue
        pcts = [q.change_pct for _, q in rows]
        avg = sum(pcts) / len(pcts)
        leader = max(rows, key=lambda r: r[1].change_pct)
        _, lq = leader
        advancers = sum(1 for p in pcts if p > 0)
        decliners = sum(1 for p in pcts if p < 0)
        sectors.append(UsSector(
            name=cn,
            name_en=us_universe.GICS_CN_TO_EN[cn],
            change_pct=round(avg, 4),
            leading_symbol=lq.symbol,
            leading_name=lq.name,
            leading_change_pct=round(lq.change_pct, 4),
            advancers=advancers,
            decliners=decliners,
            constituent_count=len(pcts),
            method="equal_weight",
        ))
    return sorted(sectors, key=lambda s: s.change_pct, reverse=True)


def sector_constituents(members, quotes, sector_cn: str) -> list:
    """板块成分按涨跌幅降序（用于右栏下钻）。"""
    quote_by_symbol = {q.symbol: q for q in quotes}
    rows = [(m, quote_by_symbol[m.symbol]) for m in members
            if m.sector_cn == sector_cn and m.symbol in quote_by_symbol]
    return [q for _, q in sorted(rows, key=lambda r: r[1].change_pct, reverse=True)]


def compose_summary(indices, sectors, as_of: Optional[str]):
    """合成 UsSummary：3 大指数 + 成分口径广度 + 领涨/领跌 Top3。"""
    from datetime import datetime
    major = {i.symbol: i for i in indices}
    indices_3 = [major[s] for s in _MAJOR_INDEX_SYMBOLS if s in major]
    advancers = sum(s.advancers for s in sectors)
    decliners = sum(s.decliners for s in sectors)
    unchanged = sum(s.constituent_count for s in sectors) - advancers - decliners
    return UsSummary(
        as_of=as_of or "",
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        indices=indices_3,
        advancers=advancers,
        decliners=decliners,
        unchanged=unchanged,
        top_gainers=sectors[:3],
        top_losers=sectors[-3:][::-1] if sectors else [],
    )
