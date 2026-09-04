// 作者接入个人收款码的唯一改点:
//   1) 把码图另存为 src/assets/support/wechat.png 与 alipay.png;
//   2) 取消下面两行 import 并把 QR_IMAGES.wechat / .alipay 指向它们。
// 当前保持 null:组件渲染占位卡,避免缺失图片导致 vite build 失败。
// import wechatImg from '@/assets/support/wechat.png'
// import alipayImg from '@/assets/support/alipay.png'

export const QR_IMAGES = {
  wechat: null,
  alipay: null,
}
