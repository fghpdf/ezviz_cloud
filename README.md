# 萤石云 Home Assistant 自定义集成 (Ezviz Cloud HA Integration)

专为在日本（或海外地区）使用中国区萤石云摄像头设备打造的 Home Assistant 原生自定义集成。

无需手机 APP 区域限制，直接通过**萤石开放平台 (open.ys7.com)** 接入您的摄像头（如 C8C 户外版、智能门铃等），提供：
- ⚡ **实时告警推送**：发生人体识别/移动事件时派发 HA 原生事件 `ezviz_cloud_alarm`，并自动抓取保存现场高精截图。
- 📊 **每日回顾 (Daily Recap)**：注册 HA 内置服务 `ezviz_cloud.generate_daily_recap`，自动汇总全天告警频次、各设备统计与精选图集发送通知。
- 📷 **Camera 实体与 Snapshot**：支持在 HA 中查看实时抓图与设备在线状态。
- ⚙️ **原生 UI 配置**：全 GUI 配置，无需手动编写配置 YAML。

---

## 目录结构

安装时只需要将 `custom_components/ezviz_cloud` 文件夹复制到您的 Home Assistant 目录下的 `custom_components/` 中即可：

```text
/config/
└── custom_components/
    └── ezviz_cloud/
        ├── __init__.py
        ├── api.py
        ├── binary_sensor.py
        ├── camera.py
        ├── config_flow.py
        ├── const.py
        ├── coordinator.py
        ├── manifest.json
        ├── sensor.py
        ├── services.py
        ├── services.yaml
        └── translations/
```

---

## 1. 准备工作

1. 登录 [萤石开放平台 (open.ys7.com)](https://open.ys7.com/)。
2. 在「应用管理」中创建一个应用，获取 **AppKey** 和 **AppSecret**。
3. 在「设备管理」中确认您的摄像头（如 C8C、门铃）已经在开放平台绑定并处于在线状态（如您之前截图所示）。
4. （可选）记录设备机身上的验证码/解密密钥（如设备加密）。

---

## 2. 安装与配置

### 手动安装步骤
1. 将本项目的 `custom_components/ezviz_cloud` 拷贝至 HA 的 `/config/custom_components/` 目录下。
2. 重启 Home Assistant。
3. 进入 HA 的 **设置 -> 设备与服务 -> 添加集成**。
4. 搜索 **萤石云 (Ezviz Cloud)**。
5. 填入您的 `AppKey` 和 `AppSecret`，点击提交即可完成接入。

---

## 3. 自动化配置示例 (Automation Examples)

集成会自动生成 `ezviz_cloud_alarm` 事件。您可以直接复制以下 YAML 配置放到 HA 的自动化中：

### 示例 1：实时告警提醒 (发送带现场截图的通知)

以 Telegram / HA Companion App 为例，当检测到人/车或移动告警时，自动推送带现场图片的卡片通知：

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

每天晚上 20:00 自动调用集成注册的服务，统计全天告警频率与截图，发送每日回顾：

```yaml
alias: "萤石摄像头：每日安全回顾"
description: "定时生成全天告警总结并发送消息报告"
trigger:
  - platform: time
    at: "20:00:00"
action:
  - service: ezviz_cloud.generate_daily_recap
    data:
      target_notify_service: "notify.notify" # 更改为您常用的 notification 服务
      title: "📹 户外摄像头每日安全总结"
```

---

## 4. 实体说明

- **Camera 实体** (`camera.c8c_bc9174122`): 实时抓图与摄像头状态。
- **Binary Sensor 实体** (`binary_sensor.c8c_bc9174122_motion`): 报警触发状态传感器。
- **Sensor 实体** (`sensor.ezviz_today_alarm_count`): 今日告警总次数统计及属性中的全天事件列表。

---

## 5. 常见问题 (FAQ)

- **Q: 为什么不直接用 App？**  
  A: 国内版萤石摄像头及 App 在日本使用时，日区 App 无法直接接入国行设备，且跨国连接 App 常遇到网络延迟与登录受限问题。本集成直接走 open.ys7.com 开放 API，稳定且无区域限制。

- **Q: 告警截图存在哪里？**  
  A: 自动保存在 HA 的 `/config/www/ezviz_alarms/` 目录下，对应 HA 内部静态资源 URL `/local/ezviz_alarms/`，方便在所有 notify 插件和 Dashboard 卡片中引用。
