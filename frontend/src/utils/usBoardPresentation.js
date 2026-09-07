// 将美股字段映射到板块共用组件，保留原始字段供深链和行情展示使用。
export function toUsBoard(sector) {
  return {
    ...sector,
    leading_stock: sector.leading_symbol,
    rise_count: sector.advancers,
    fall_count: sector.decliners,
    stock_count: sector.constituent_count,
  }
}

export function toUsStock(stock) {
  return { ...stock, code: stock.symbol }
}
