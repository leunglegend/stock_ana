// 个人收款码接线点:微信「二维码收款」/ 支付宝「收钱」导出的码图存于
// src/assets/support/。经 Vite import 处理为资源 URL;组件在有值时渲染真码,
// 保持 null 则渲染占位卡。
import wechatQr from '@/assets/support/wechat-qr.jpg'
import alipayQr from '@/assets/support/alipay-qr.jpg'

export const QR_IMAGES = {
  wechat: wechatQr,
  alipay: alipayQr,
}
