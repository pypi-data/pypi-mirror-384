# CosyVoice Python SDK Examples

本目录包含 CosyVoice Python SDK 的使用示例。

## 环境配置

### 1. 安装依赖

```bash
# 安装基础依赖
uv sync

# 安装开发依赖（包含示例运行所需的 python-dotenv）
uv sync --extra dev
```

### 2. 配置环境变量

创建 `.env` 文件并配置你的 CosyVoice 服务信息：

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

`.env` 文件示例：
```env
# CosyVoice 服务配置
COSYVOICE_BASE_URL=http://your-cosyvoice-server.com/
COSYVOICE_API_KEY=your-api-key

# 连接配置（可选）
COSYVOICE_CONNECTION_TIMEOUT=30.0
COSYVOICE_READ_TIMEOUT=60.0
COSYVOICE_MAX_RECONNECT_ATTEMPTS=3
```

## 运行示例

确保已安装开发依赖并配置了 `.env` 文件后，可以运行以下示例：

### 音色管理（无需 WebSocket 连接）
```bash
python examples/speaker_management.py
```

此示例演示：
- 创建音色
- 获取音色信息
- 检查音色是否存在
- 更新音色
- 所有操作均无需 WebSocket 连接

### 基础语音合成
```bash
python examples/basic_synthesis.py
```

### 实时流式合成
```bash
python examples/realtime_streaming.py
```

## 故障排除

### 控制台无输出

如果运行示例时看不到任何输出：

1. 检查环境变量是否正确设置：
   ```bash
   python -c "import os; print('BASE_URL:', os.environ.get('COSYVOICE_BASE_URL')); print('API_KEY:', os.environ.get('COSYVOICE_API_KEY'))"
   ```

2. 确保已安装 python-dotenv：
   ```bash
   pip install python-dotenv
   # 或
   uv sync --extra dev
   ```

3. 检查 .env 文件是否存在且配置正确

4. 尝试手动设置环境变量：
   ```bash
   export COSYVOICE_BASE_URL="https://your-server.com"
   export COSYVOICE_API_KEY="your-key"
   python examples/speaker_management.py
   ```

### 连接问题

- 验证服务器 URL 是否正确
- 检查 API 密钥是否有效
- 确保网络能访问 CosyVoice 服务器
