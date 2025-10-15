"""
北京时间服务器的核心实现
"""

import asyncio
import json
from datetime import UTC, datetime
from typing import Any, Dict, Optional

import pytz
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)


class BeijingTimeServer:
    """北京时间MCP服务器"""

    def __init__(self):
        self.server = Server("beijing-time-mcp")
        self.beijing_tz = pytz.timezone("Asia/Shanghai")
        self._setup_handlers()

    def _setup_handlers(self):
        """设置MCP处理器"""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """列出可用工具"""
            tools = [
                Tool(
                    name="get_beijing_time",
                    description="获取当前北京时间",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "format": {
                                "type": "string",
                                "description": "时间格式字符串",
                                "enum": [
                                    "%Y-%m-%d %H:%M:%S",
                                    "%Y-%m-%d",
                                    "%H:%M:%S",
                                    "%Y年%m月%d日 %H时%M分%S秒",
                                    "%Y-%m-%dT%H:%M:%S%z",
                                ],
                                "default": "%Y-%m-%d %H:%M:%S",
                            }
                        },
                    },
                )
            ]
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Optional[Dict[str, Any]]
        ) -> CallToolResult:
            """处理工具调用"""
            if name == "get_beijing_time":
                return await self._get_beijing_time(arguments or {})
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def _get_beijing_time(
        self, arguments: Dict[str, Any]
    ) -> CallToolResult:
        """获取北京时间"""
        try:
            # 获取当前北京时间
            now_utc = datetime.now(UTC)
            now_beijing = now_utc.astimezone(self.beijing_tz)

            # 获取格式参数
            time_format = arguments.get("format", "%Y-%m-%d %H:%M:%S")

            # 格式化时间
            formatted_time = now_beijing.strftime(time_format)

            # 构建响应数据
            response_data = {
                "time": formatted_time,
                "timezone": "Asia/Shanghai (CST)",
                "timestamp": int(now_beijing.timestamp()),
                "iso_format": now_beijing.isoformat(),
                "utc_offset": now_beijing.strftime("%z"),
                "day_of_week": now_beijing.strftime("%A"),
                "day_of_week_cn": self._get_chinese_day_of_week(
                    now_beijing.weekday()
                ),
                "year": now_beijing.year,
                "month": now_beijing.month,
                "day": now_beijing.day,
                "hour": now_beijing.hour,
                "minute": now_beijing.minute,
                "second": now_beijing.second,
            }

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(
                            response_data, ensure_ascii=False, indent=2
                        ),
                    )
                ]
            )

        except Exception as e:
            error_response = {
                "error": True,
                "message": f"获取北京时间失败: {str(e)}",
            }
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(
                            error_response, ensure_ascii=False, indent=2
                        ),
                    )
                ]
            )

    def _get_chinese_day_of_week(self, weekday: int) -> str:
        """获取中文星期几"""
        days = [
            "星期一",
            "星期二",
            "星期三",
            "星期四",
            "星期五",
            "星期六",
            "星期日",
        ]
        return days[weekday]

    async def run(self):
        """运行服务器"""
        # 使用stdio传输运行服务器
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
InitializationOptions(
                    server_name="beijing-time-mcp",
                    server_version="0.1.1",
                    capabilities=self.server.get_capabilities(
                        notification_options=None, experimental_capabilities={}
                    ),
                ),
            )


async def main():
    """主函数"""
    server = BeijingTimeServer()
    await server.run()


def main_wrapper():
    """同步包装函数，用于命令行入口点"""
    asyncio.run(main())


if __name__ == "__main__":
    main_wrapper()
