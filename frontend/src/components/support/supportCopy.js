// 「点赞为股 · 打赏」全站文案集中改稿点。人设:股东情怀(适度)。
// 红线由契约测试守护:SUPPORT_COPY 全量文案受 tests/tip-support-contract.test.js
// 的 FORBIDDEN / mustHave 锁定;任何改稿须同步该测试,勿在此重复罗列禁词。
export const SUPPORT_COPY = {
  // —— 顶栏入口 ——
  entryAriaLabel: '给析股研究台点赞',
  entryTitleIdle: '点赞:免费给研究台投一票,不伤本金',
  entryTitleLiked: '你已是本机股东 · 再点开股东卡',
  labelIdle: '点赞',
  labelLiked: '已一票',
  // —— 确认卡(点亮后) ——
  confirmHead: '表决成功。本机股东名册 +1。',
  confirmSub: '你持股『鼓励』1 股:行权价 0 元,不盯盘、不套牢、随时可撤。',
  confirmLocalNote: '此票记在本机浏览器:换设备或清缓存不随行——属彩蛋,不属实缴登记。',
  inviteLead: '这票研究员收下了。若哪天想让它更有分量:',
  inviteAction: '顺带增资?',
  inviteDecline: '先不了,白嫖也是股东权益。',
  inviteGhost: '想让它更有分量?顺带增资 →',
  revokeAction: '收回这一票',
  suppressAction: '以后别再提增资',
  snoozeAction: '暂时收起这个入口',
  revokeNote: '票已收回,研究台照常营业,欢迎随时再投。',
  // —— 打赏卡 ——
  dialogEyebrow: '股东增资 · 自愿支持',
  dialogHead: '研究不收费,服务器要养;各位股东,量力增资。',
  dialogSub: '析股研究台由一个人维护:行情、服务器、AI 的电费都自费。这笔钱不拿去扩产,只够请这个 AI 打工仔多喝几杯咖啡。',
  amountNote: '金额随缘:一杯奶茶区间(6.66 / 8.88 / 18.88)刚刚好;超过 99 请三思——这里不搞大额集资。',
  scanHint: '长按识别二维码,或用对应 App 扫一扫',
  qrWechatLabel: '微信',
  qrAlipayLabel: '支付宝',
  qrPlaceholder: '收款码占位:作者把图放进\nsrc/assets/support/ 并接线 qrImages.js',
  thanksCollective: '扫码即赠,无需截图回传;每一笔增资都会出现在作者的微信 / 支付宝收款记录里。作者会挑个交易日,在复盘里向全体股东集体道谢。',
  payeeMask: '收款方:析股台 · *哥(支付前请核对,认准这一行)',
  compliance1: '打赏是自愿赠与:非购买、非投资,不构成任何收益承诺,也不解锁任何功能。',
  compliance2: '本页「股东 / 增资 / 表决权」均为戏称,不构成任何股权、收益分配或公司治理权利。',
  compliance3: '未成年人请勿打赏——把零花钱先投资给自己,就是最好的复利。',
  actionPrimary: '继续看盘',
  actionLater: '下次一定',
  snoozedTip: '已收起 30 天。想回来?入口 30 天后自动复出。',
  // —— 页脚 ——
  footerSiteName: '析股研究台',
  footerDisclaimer: '数据仅供研究参考,不构成任何投资建议 · 内容不构成买卖依据',
  footerTipEntry: '股东可顺手增资 ↗',
  footerTipAria: '打开股东增资入口(打赏支持)',
}
