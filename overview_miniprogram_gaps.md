# 小程序缺失功能补齐报告

**日期**: 2026-08-05
**范围**: 补齐 3 个实质功能缺口（登录趋势 / 邀请海报 / 订阅消息）

---

## 缺口 1：登录趋势真实接口（消除首页 mock 假数据）

**问题**：首页"登录趋势"图表是硬编码 mock 数据，后端无对应接口。

| 端 | 文件 | 变更 |
|----|------|------|
| 后端 | `module_monitor/online/schema.py` | +`LoginTrendItem`（day/logins/unique_users/new_users）；`DashboardStatsSchema` +`login_trend` 字段 |
| 后端 | `module_monitor/online/service.py` | +`_build_login_trend()`：近 7 天按日聚合登录次数/独立用户/新增用户（基于登录日志 status=1 + 用户表），日期缺口补 0 |
| 前端 | `api/module_monitor/dashboard.ts` | +`LoginTrendItem` 类型 |
| 前端 | `pages/index/index.vue` | 删除 mock 数组，图表改用 `stats.login_trend` 真实数据，X 轴显示 MM-DD |

## 缺口 2：邀请海报入口（获客功能接线）

**问题**：`useSharePoster` 已实现但无任何页面调用（死代码）。

**方案**：`pages/mine/index.vue` 新增"邀请好友"卡片：
- **立即邀请**：微信原生 `open-type="share"` 转发按钮（分享卡片由 useShare 配置）
- **海报**：调 `generateQrCode({ scene: 'invite_{userId}' })` 生成带参小程序码 → popup 预览（支持**长按识别**）→ **保存到相册**（base64 → 本地文件 → saveImageToPhotosAlbum）

至此获客闭环：好友通过转发卡片或扫海报码进入小程序 → 场景值可追踪来源用户。

## 缺口 3：订阅消息发送能力（后端）

**问题**：前端 `useSubscribeMessage` 只能请求授权，后端无法下发通知。

**方案**：`wx_mini_service.py` 新增：
- `send_subscribe_message()` — 调用微信 `cgi-bin/message/subscribe/send`；**防御性静默**：未配置 AppID / 模板 ID 为空 / 用户未订阅（43101）时跳过，绝不阻断业务主流程
- `extract_openid_from_username()` — 从 `wxmini_*` 用户名提取标识的工具函数

## 验证

- ✅ 后端全部模块导入通过
- ✅ 前端 `vue-tsc --noEmit` 0 错误

## 遗留（需用户配置后接线）

| 事项 | 说明 | 依赖 |
|------|------|------|
| 订阅消息业务触发 | 工单状态变更 → 自动下发通知 | ① 公众平台申请模板 ID ② 用户表扩展存完整 openid（DB 迁移） |
| AppID / AppSecret | 小程序登录/海报/订阅前置 | 微信公众平台申请 |
| 小程序码 | 开发版无法生成，需体验版/上线版 | 提审发布 |
