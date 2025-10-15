# Beijing Time MCP Server

一个用于查询北京时间的MCP（Model Context Protocol）服务器。

mcp-name: io.github.archerlliu/beijing-time-mcp

## 功能

- 获取当前北京时间
- 格式化时间输出
- 支持多种时间格式
- 提供时区信息

## 安装

### 从 PyPI 安装

```bash
pip install beijing-time-mcp
```

### 从源码安装

```bash
git clone https://github.com/archerliu/beijing-time-mcp.git
cd beijing-time-mcp
pip install -e .
```

## 使用方法

### 作为 MCP 服务器运行

```bash
beijing-time-mcp
```

### 在 Claude Desktop 中使用

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "beijing-time": {
      "command": "beijing-time-mcp"
    }
  }
}
```

## 可用工具

### `get_beijing_time`

获取当前北京时间。

**参数：**
- `format` (可选): 时间格式，默认为 "%Y-%m-%d %H:%M:%S"
  - "%Y-%m-%d %H:%M:%S" - 标准格式 (如: 2024-01-15 14:30:25)
  - "%Y-%m-%d" - 日期格式 (如: 2024-01-15)
  - "%H:%M:%S" - 时间格式 (如: 14:30:25)
  - "%Y年%m月%d日 %H时%M分%S秒" - 中文格式 (如: 2024年01月15日 14时30分25秒)

**返回：**
- `time`: 格式化后的北京时间字符串
- `timezone`: 时区信息
- `timestamp`: Unix时间戳
- `iso_format`: ISO 8601格式的时间

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black .
isort .
```

### 类型检查

```bash
mypy beijing_time_mcp
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！