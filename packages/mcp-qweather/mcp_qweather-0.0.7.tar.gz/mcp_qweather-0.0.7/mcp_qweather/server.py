from typing import Any
import httpx
import os
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()
QWEATHER_API_BASE = os.getenv("QWEATHER_API_HOST")
QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY")
QW_HEADERS = {
    "X-QW-Api-Key": QWEATHER_API_KEY,
    "Accept-Encoding": "gzip",
}

# Initialize FastMCP server
mcp = FastMCP("weather")


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """发起到和风天气的异步请求，返回 JSON 或 None。"""

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=QW_HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


@mcp.tool()
async def lookup_city(location: str) -> str:
    """查询城市信息并返回格式化文本。Args:

    Args:
        location: 需要查询地区的名称，支持文字、以英文逗号分隔的经度,纬度坐标（十进制，最多支持小数点后两位）
    """
    url = f"https://{QWEATHER_API_BASE}/geo/v2/city/lookup?location={location}&lang=zh"
    data = await make_nws_request(url)

    if not data or "location" not in data or not data["location"]:
        return "Unable to fetch location data."

    loc = data["location"][0]

    return f"City: {loc['name']}\nLocationID: {loc['id']}\nLatitude: {loc['lat']}\nLongitude: {loc['lon']}"


def format_warning(w: dict, default_time: str = "") -> str:
    """格式化单条天气预警为可读中文文本。"""
    title = w.get("title", "未知预警")
    type_name = w.get("typeName") or w.get("type", "未知类型")
    severity = w.get("severity", "未知等级")
    pub_time = w.get("pubTime") or w.get("updateTime") or default_time
    text = w.get("text", "")
    return (
        f"Title: {title}\n"
        f"Type: {type_name}\n"
        f"Severity: {severity}\n"
        f"Time: {pub_time}\n"
        f"Content: {text}"
    )


@mcp.tool()
async def get_warning(location: str) -> str:
    """查询天气预警。

    Args:
        location: 需要查询地区的LocationID或以英文逗号分隔的经度,纬度坐标（十进制，最多支持小数点后两位）
    """
    normalized = location.strip().replace(" ", "").replace("，", ",")
    url = f"https://{QWEATHER_API_BASE}/v7/warning/now?location={normalized}&lang=zh"
    data = await make_nws_request(url)
    code = data.get("code")
    if code and code != "200":
        return f"接口错误 code: {code}"
    warnings = data.get("warning") or []
    if not warnings:
        return "暂无预警"

    default_time = data.get("updateTime", "")
    formatted = "\n---\n".join(format_warning(w, default_time) for w in warnings)
    return formatted


def format_forecast(
    now: dict, update_time: str = "", fx_link: str = "", refer: dict | None = None
) -> str:
    """格式化当前天气数据为可读文本。"""
    refer = refer or {}
    sources = ", ".join(refer.get("sources", [])) if refer else ""
    license_ = ", ".join(refer.get("license", [])) if refer else ""

    return (
        f"UpdateTime: {update_time}\n"
        f"Link: {fx_link}\n"
        f"ObsTime: {now.get('obsTime', '')}\n"
        f"Temp: {now.get('temp', '')}\n"
        f"FeelsLike: {now.get('feelsLike', '')}\n"
        f"Text: {now.get('text', '')}\n"
        f"WindDir: {now.get('windDir', '')}\n"
        f"WindScale: {now.get('windScale', '')}\n"
        f"WindSpeed: {now.get('windSpeed', '')}\n"
        f"Humidity: {now.get('humidity', '')}\n"
        f"Precip: {now.get('precip', '')}\n"
        f"Pressure: {now.get('pressure', '')}\n"
        f"Visibility: {now.get('vis', '')}\n"
        f"Cloud: {now.get('cloud', '')}\n"
        f"Dew: {now.get('dew', '')}\n"
        f"Sources: {sources}\n"
        f"License: {license_}"
    )


@mcp.tool()
async def get_forecast(location: str) -> str:
    """获取一个位置的天气预报。

    Args:
        location: 需要查询地区的LocationID或以英文逗号分隔的经度,纬度坐标（十进制，最多支持小数点后两位）
    """
    normalized = location.strip().replace(" ", "").replace("，", ",")
    forecast_url = (
        f"https://{QWEATHER_API_BASE}/v7/weather/now?location={normalized}&lang=zh"
    )
    forecast_data = await make_nws_request(forecast_url)
    code = forecast_data.get("code")
    if code and code != "200":
        return f"接口错误 code: {code}"
    now = forecast_data.get("now") or []
    if not now:
        return "暂无预报"

    update_time = forecast_data.get("updateTime", "")
    fx_link = forecast_data.get("fxLink", "")
    refer = forecast_data.get("refer", {}) or {}
    formatted = format_forecast(now, update_time, fx_link, refer)
    return formatted


def main():
    # Initialize and run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()