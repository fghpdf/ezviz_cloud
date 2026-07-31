<p align="center">
  <img src="https://raw.githubusercontent.com/fghpdf/ezviz_cloud/main/icon.png" width="128" height="128" alt="Ezviz Cloud Logo">
</p>

<h1 align="center">萤石云 (Ezviz Cloud) Home Assistant 集成</h1>

<p align="center">
  专为在<b>日本及海外地区</b>使用<b>中国区萤石云摄像头/门铃</b>打造的 Home Assistant 原生自定义集成。
</p>

<p align="center">
  <a href="https://github.com/hacs/default"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS Custom"></a>
  <a href="https://github.com/fghpdf/ezviz_cloud/releases"><img src="https://img.shields.io/github/v/release/fghpdf/ezviz_cloud" alt="GitHub Release"></a>
  <a href="https://github.com/fghpdf/ezviz_cloud/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
</p>

---

## 📖 项目简介

在日本或海外使用国内版萤石摄像头设备时，由于萤石官方 APP 存在**区域限制**与**跨国登录受限**等痛点，且实时视频流拉取在日常安防中并不实用。

本集成直接通过**萤石云官方开放平台 (`open.ys7.com`)** 的开放 API，绕过 APP 区域限制，提供：
- ⚡ **实时告警推送**：发生人体侦测/移动事件时派发 HA 原生事件 `ezviz_cloud_alarm`，并自动抓取下载现场高精截图。
- 🔑 **内置 AES 自动解密**：支持填入设备验证码密码（支持多台设备），告警图片下到本地自动解密为高清正常 JPG 图像。
- 📊 **每日安全回顾 (Daily Recap)**：内置 HA 服务 `ezviz_cloud.generate_daily_recap`，自动汇总全天告警频次、各设备统计与精选图集发送通知。
- 📷 **Camera 与传感器实体**：支持在 HA 界面中随时查看设备抓图快照与在线状态。
- ⚙️ **原生 UI 配置**：全 GUI 配置与选项修改，无需手动编写配置 YAML。

---

## ✨ 核心特色与功能

| 功能模块 | 说明 |
| --- | --- |
| **绕过区域限制** | 直接走 `open.ys7.com` Open API 接口，海外访问稳定通畅 |
| **实时告警 & 去重** | 高效轮询算法与去重引擎，告警触发时派发 `ezviz_cloud_alarm` 原生事件 |
| **图像自动解密** | 内置 AES-128 解密模块，支持多台设备密码统一解密，保存即为普通 JPG 图片 |
| **每日总结服务** | 注册 `ezviz_cloud.generate_daily_recap` 自定义服务，发送全天汇总图文简报 |
| **全 GUI 配置** | 在 HA 界面「设置 -> 设备与服务」中通过向导完成 AppKey、Secret 和密码填入 |

---

## 🛠️ 安装方法

### 方法一：通过 HACS 自动安装（推荐 ⭐️）

1. 打开 Home Assistant 的 **HACS** 界面。
2. 点击右上角的三个点 ➔ 选择 **自定义存储库 (Custom repositories)**。
3. 在存储库 URL 中填入：`https://github.com/fghpdf/ezviz_cloud`
4. 类别选择 **集成 (Integration)** ➔ 点击 **添加 (Add)**。
5. 在 HACS 列表中找到 **萤石云 (Ezviz Cloud)** 并点击 **下载**。
6. 重启 Home Assistant。

### 方法二：手动安装

1. 下载本仓库源码压缩包。
2. 将 `custom_components/ezviz_cloud` 文件夹解压并拷贝至您 HA 配置目录下的 `custom_components/` 中（路径例：`/config/custom_components/ezviz_cloud`）。
3. 重启 Home Assistant。

---

## ⚙️ 配置指南

1. 登录 [萤石开放平台 (open.ys7.com)](https://open.ys7.com/) 注册并获取应用的 **AppKey** 和 **AppSecret**。
2. 在 Home Assistant 进入 **设置 (Settings)** ➔ **设备与服务 (Devices & Services)**。
3. 点击右下角 **添加集成 (Add Integration)** ➔ 搜索 **萤石云 (Ezviz Cloud)**。
4. 填入您的 `AppKey` 与 `AppSecret`。
5. （可选）如果开启了视频/图片加密，可在界面中填入您的 6 位设备验证码：
   - **多台设备密码相同**：直接填入一个（如 `EZUUYP`）。
   - **多台设备密码不同**：可用逗号分隔填入（如 `EZUUYP, CODEB`），或按 `序列号:密码` 填入（如 `BC9174122:EZUUYP, BC9266870:CODEB`）。
6. 如果后续需要修改密码或轮询频率，点击集成卡片上的 **齿轮 ⚙️ 图标** 即可随时修改！

---

## 📦 实体说明

集成成功加载后，会自动创建以下类型的 HA 实体：

| 实体类型 | 实体 ID 示例 | 功能说明 |
| --- | --- | --- |
| **Camera** | `camera.c8c_bc9174122` | 实时抓图快照与摄像头在线/离线状态 |
| **Binary Sensor** | `binary_sensor.c8c_bc9174122_motion` | 告警二值传感器，发生移动/人体告警时变为 `ON` |
| **Sensor** | `sensor.ezviz_today_alarm_count` | 统计今日发生的告警总次数，展开属性可查阅全天事件队列 |

---

## 🔔 自动化 YAML 示例

### 示例 1：实时告警提醒 (发送带现场图片的通知)

当检测到人/车或移动告警时，自动向手机、Telegram 或 Bark 发送带有现场高清截图的通知：

```yaml
alias: "萤石摄像头：实时告警提醒"
description: "收到萤石摄像头告警事件时发送带图通知"
trigger:
  - platform: event
    event_type: ezviz_cloud_alarm
action:
  - service: notify.notify  # 可替换为 notify.telegram 或 notify.mobile_app_your_phone
    data:
      title: "⚠️ {{ trigger.event.data.device_name }} - {{ trigger.event.data.alarm_type }}"
      message: "时间: {{ trigger.event.data.alarm_time }}"
      data:
        image: "{{ trigger.event.data.relative_image_path }}"
```

### 示例 2：每日安全回顾 (每日 20:00 自动推全天总结)

每天晚上 20:00 自动调用内置服务，统计全天告警频率与焦点图片，发送总结简报：

```yaml
alias: "萤石摄像头：每日安全回顾"
description: "定时生成全天告警总结并发送消息报告"
trigger:
  - platform: time
    at: "20:00:00"
action:
  - service: ezviz_cloud.generate_daily_recap
    data:
      target_notify_service: "notify.notify"
      title: "📹 户外摄像头每日安全总结"
```

---

## ❓ 常见问题 (FAQ)

<details>
<summary><b>Q: 为什么不直接使用萤石 APP？</b></summary>
国内版萤石摄像头在海外（如日本）使用时，日区 APP 无法添加国行设备，且跨国登录连接延迟高。本集成走 open.ys7.com 官方 Open API，响应极快且不受区域限制。
</details>

<details>
<summary><b>Q: 告警截图存在哪里？</b></summary>
自动保存在 HA 的 `/config/www/ezviz_alarms/` 目录下，对应 HA 内部静态资源 URL `/local/ezviz_alarms/`，方便在所有 notify 插件和 Dashboard 卡片中引用。
</details>

<details>
<summary><b>Q: 多台设备的解密验证码如何填？</b></summary>
支持在集成配置/齿轮设置中直接用逗号分隔写入多个验证码（如 <code>CODEA, CODEB</code>），系统在下载解密时会自动测试并匹配成功！
</details>

---

## 📄 开源许可证

本项目基于 [MIT 许可证](LICENSE) 开源发布。
