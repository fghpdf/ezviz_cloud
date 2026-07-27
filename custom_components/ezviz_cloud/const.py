"""Constants for the Ezviz Cloud integration."""

DOMAIN = "ezviz_cloud"
TITLE = "萤石云 (Ezviz Cloud)"

CONF_APP_KEY = "app_key"
CONF_APP_SECRET = "app_secret"
CONF_VERIFICATION_CODE = "verification_code"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 10  # 默认 10 秒轮询一次报警列表

EVENT_EZVIZ_ALARM = "ezviz_cloud_alarm"

# API Endpoints
BASE_URL = "https://open.ys7.com/api/lcn"
TOKEN_URL = f"{BASE_URL}/token/get"
DEVICE_LIST_URL = f"{BASE_URL}/device/list"
CAPTURE_URL = f"{BASE_URL}/device/capture"
ALARM_LIST_URL = f"{BASE_URL}/device/alarm/list"

# Alarm Types Mapping
ALARM_TYPES = {
    10000: "移动侦测报警",
    10002: "人体识别报警",
    10005: "人脸识别报警",
    10015: "车辆检测报警",
    10020: "门铃呼叫",
    10030: "区域入侵报警",
}
