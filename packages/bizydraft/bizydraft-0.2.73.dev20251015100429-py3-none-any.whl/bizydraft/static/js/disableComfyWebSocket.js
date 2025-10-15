// 保存原始的 WebSocket 构造函数
const OriginalWebSocket = window.WebSocket;

class FakeWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;  // 核心：保持 CONNECTING 状态
    console.warn('[BizyDraft] 已阻止 WebSocket 连接:', url);
  }
  send() {}
  close() {}
  addEventListener() {}
  removeEventListener() {}
}

window.WebSocket = function(url, protocols) {
  //精确拦截/ws请求
  if (typeof url === 'string' && /^wss?:\/\/[^/]+\/ws(\?.*)?$/.test(url)) {
    return new FakeWebSocket(url);
  }
  // 其他连接正常创建，不影响
  return new OriginalWebSocket(url, protocols);
};

// 保留 WebSocket 的静态属性和原型
Object.setPrototypeOf(window.WebSocket, OriginalWebSocket);
window.WebSocket.prototype = OriginalWebSocket.prototype;

// 复制静态常量（使用 defineProperty 避免只读属性错误）
['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'].forEach(prop => {
  Object.defineProperty(window.WebSocket, prop, {
    value: OriginalWebSocket[prop],
    writable: false,
    enumerable: true,
    configurable: true
  });
});
