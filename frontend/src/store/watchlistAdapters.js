export function adaptGroupFromCloud(group) {
  return {
    id: String(group.id),
    name: group.name,
    stocks: (group.stocks || []).map((stock) => ({
      _id: stock.id,
      code: stock.stock_code,
      name: stock.stock_name,
      cost: stock.cost || 0,
      remark: stock.remark || '',
    })),
  }
}

export function adaptGroupsToCloud(groups) {
  return groups.map((group) => ({
    id: String(group.id),
    name: group.name,
    stocks: (group.stocks || []).map((stock) => ({
      stock_code: stock.code,
      stock_name: stock.name,
      cost: stock.cost || 0,
      remark: stock.remark || '',
    })),
  }))
}
