# 微信小程序后端接口实现 — 交付说明

**日期**: 2026-08-05
**范围**: 打通小程序完整登录闭环（微信一键登录 / 手机号登录 / 小程序码生成）

---

## 一、新增后端接口（3个）

| 接口 | 方法 | 功�� | 依赖 |
|------|------|------|------|
| `/system/auth/wx-login` | POST | uni.login code → code2Session → openid → 查建用户 → JWT | WX_MINI_APP_ID/SECRET |
| `/system/auth/wx-phone-login` | POST | getPhoneNumber code → getuserphonenumber → 手机号 → 查建用户 → JWT | 同上 |
| `/system/auth/wx-qrcode/generate` | POST | scene/page/width → getwxacodeunlimit → base64 PNG | 同上 |

## 二、文件变更清单

### 后端（5个）
| 文件 | 变更 |
|------|------|
| `backend/app/config/setting.py` | +`WX_MINI_APP_ID` / `WX_MINI_APP_SECRET` / `WX_MINI_ACCESS_TOKEN_CACHE_TTL=7000` |
| `backend/app/common/enums.py` | +`WX_MINI_ACCESS_TOKEN` Redis key |
| `backend/app/api/v1/module_system/auth/schema.py` | +`WxLoginSchema` / `WxPhoneLoginSchema` / `WxQrCodeSchema` / `WxQrCodeOutSchema` |
| `backend/app/api/v1/module_system/auth/wx_mini_service.py` | **新增**，核心服务层 |
| `backend/app/api/v1/module_system/auth/controller.py` | +3 个端点及所需 import |

### 前端（5个）
| 文件 | 变更 |
|------|------|
| `frontend/app/src/api/module_system/auth.ts` | `wxPhoneLogin` 改为仅传 code；+`generateWxQrCode` 及类型 |
| `frontend/app/src/composables/useWxLogin.ts` | `wxPhoneLogin` 接收 `e.detail.code` |
| `frontend/app/src/pages/login/index.vue` | 手机号登录传 code；移除废弃 `getUserProfile` |
| `frontend/app/src/store/userStore.ts` | `wxPhoneLogin` 类型改为 `{ code: string }` |
| `frontend/app/src/composables/useSharePoster.ts` | 改用 `AuthAPI.generateWxQrCode`（修复错误路径） |

### 顺带修复（2个既有 TS 错误）
| 文件 | 修复 |
|------|------|
| `frontend/app/src/composables/useShare.ts` | 移除不存在的 `ShareAppMessageOptions` / `ShareTimelineOptions` 类型导入 |
| `frontend/app/src/composables/useSubscribeMessage.ts` | `requestSubscribeMessage` 返回值先转 `unknown` 再断言 |

## 三、关键技术决策

1. **手机号登录用 2023+ 新方案**：前端 `getPhoneNumber` 回调的 `e.detail.code` 直传后端，后端调 `wxa/business/getuserphonenumber` 换手机号。**无需 AES 解密**，避免引入 pycryptodome 依赖（旧方案 encryptedData+iv 已废弃）。
2. **access_token 用 stable_token 接口**：`POST cgi-bin/stable_token`，比传统 `cgi-bin/token` 更稳定（并发不互相覆盖）；Redis 缓存 7000s（微信上限 7200 留 200s 余量），多实例共享。
3. **小程序码返回 base64 data URI**：`data:image/png;base64,...`，前端可直接作为 `<image>` src 或 Canvas 图片来源，无需中转存储。
4. **用户名规则**：微信登录自动注册 `wxmini_{openid前20位}`；手机号登录 `wxphone_{尾号4位}_{随机8hex}`，风格与 OAuth 模块 `oauth_{provider}_{id}` 一致。
5. **登录类型标记**：`login_type` 分别记录 `wx_mini` / `wx_mini_phone`，便于会话审计。

## 四、验证结果

- ✅ 后端全模块导入无错误，3 个新路由断言通过
- ✅ Schema 字段校验通过（默认值、边界）
- ✅ 前端 `vue-tsc --noEmit` 通过（0 错误）

## 五、上线前置条件（待用户配置）

| 事项 | 说明 |
|------|------|
| 申请小程序 AppID/AppSecret | 微信公众平台 → 开发管理，填入环境变量 `WX_MINI_APP_ID` / `WX_MINI_APP_SECRET` |
| 配置订阅消息模板 | 公众平台 → 订阅消息，将模板 ID 填入 `useSubscribeMessage.ts` 的 `TEMPLATE_IDS` |
| 域名白名单 | 微信公众平台配置 request 合法域名指向后端 API 地址 |
| 小程序码配额 | 有数量限制（getwxacodeunlimit 每日上限），生产需注意缓存 |

## 六、测试建议

配置好密钥后，可用以下命令快速自测（需 Redis 与数据库就绪）：
```bash
# 微信登录（code 需真实小程序 code，可用微信开发者工具获取）
curl -X POST http://localhost:8000/api/v1/system/auth/wx-login \
  -H "Content-Type: application/json" \
  -d '{"code": "REAL_CODE"}'
```
