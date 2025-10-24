# MediaCrawler API & Web UI 使用指南

## 📖 简介

MediaCrawler 现在支持现代化的 Web 界面和 RESTful API，提供可视化管理、实时监控和断点续爬功能！

### ✨ 新功能

1. **现代化 Web UI 控制面板** 🎨
   - 美观的可视化界面
   - 实时状态监控
   - 一键启动/停止爬虫
   - 数据预览和下载

2. **RESTful API 接口** 🔌
   - 完整的 API 文档
   - 支持外部应用调用
   - JSON 格式数据交互

3. **断点续爬功能** 💾
   - 自动保存爬取进度
   - 支持从任意检查点恢复
   - 防止数据丢失

## 🚀 快速开始

### 启动 API 服务器

```bash
# 使用 uv（推荐）
uv run python api_server.py

# 或使用普通 Python
python api_server.py
```

服务器将在 `http://localhost:8000` 启动。

### 访问 Web UI

在浏览器中打开：

```
http://localhost:8000
```

您将看到现代化的控制面板界面。

### 查看 API 文档

访问自动生成的交互式 API 文档：

```
http://localhost:8000/docs
```

## 🎯 Web UI 功能说明

### 1. 爬虫控制面板

- **选择平台**：支持小红书、抖音、快手、B站、微博、贴吧、知乎
- **配置参数**：
  - 关键词：搜索的关键词（多个用逗号分隔）
  - 爬取类型：关键词搜索 / 帖子详情 / 创作者主页
  - 登录方式：二维码 / 短信验证码 / Cookie
  - 数据量控制：最大帖子数、每帖最大评论数
  - 功能开关：爬取评论、二级评论、断点续爬、无头模式
  - 数据存储：JSON / CSV / SQLite / MySQL

- **操作按钮**：
  - 启动爬虫：开始执行爬取任务
  - 停止爬虫：停止当前任务并保存检查点

### 2. 运行状态监控

实时显示：
- 当前运行状态
- 开始时间
- 已爬取帖子数
- 已爬取评论数
- 进度条
- 日志查看器

### 3. 断点续爬管理

- 查看所有保存的检查点
- 显示平台、时间和进度信息
- 一键恢复到指定检查点
- 下载检查点数据

### 4. 数据中心

- 浏览所有爬取的数据文件
- 按类型筛选（JSON / CSV）
- 在线预览数据内容
- 下载数据文件
- 删除不需要的文件

## 📡 API 接口说明

### 基础接口

#### 健康检查
```http
GET /api/health
```

返回服务器状态。

#### 获取支持的平台列表
```http
GET /api/platforms
```

返回所有支持的平台及其信息。

#### 获取当前配置
```http
GET /api/config
```

返回当前的爬虫配置参数。

### 爬虫控制接口

#### 启动爬虫
```http
POST /api/crawler/start
Content-Type: application/json

{
  "platform": "xhs",
  "keywords": "编程副业,编程兼职",
  "crawler_type": "search",
  "login_type": "qrcode",
  "max_notes": 15,
  "max_comments": 10,
  "enable_comments": true,
  "enable_sub_comments": false,
  "save_data_option": "json",
  "headless": false,
  "enable_resume": true
}
```

#### 停止爬虫
```http
POST /api/crawler/stop
```

停止正在运行的爬虫并保存检查点。

#### 获取爬虫状态
```http
GET /api/crawler/status
```

返回当前爬虫的运行状态和进度。

### 断点续爬接口

#### 获取检查点列表
```http
GET /api/checkpoints
```

返回所有保存的检查点。

#### 从检查点恢复
```http
POST /api/crawler/resume
Content-Type: application/json

{
  "checkpoint_id": "xhs_search_20240123_120000"
}
```

### 数据管理接口

#### 获取数据文件列表
```http
GET /api/data/files?platform=xhs
```

#### 预览数据文件
```http
GET /api/data/preview/{filename}?limit=100
```

#### 下载数据文件
```http
GET /api/data/download/{filename}
```

#### 删除数据文件
```http
DELETE /api/data/delete/{filename}
```

## 💡 使用示例

### Python 调用 API

```python
import requests

API_BASE = "http://localhost:8000/api"

# 1. 启动爬虫
config = {
    "platform": "xhs",
    "keywords": "编程副业",
    "crawler_type": "search",
    "max_notes": 20,
    "enable_resume": True
}

response = requests.post(f"{API_BASE}/crawler/start", json=config)
print(response.json())

# 2. 查看状态
status = requests.get(f"{API_BASE}/crawler/status")
print(status.json())

# 3. 获取数据文件
files = requests.get(f"{API_BASE}/data/files")
print(files.json())

# 4. 下载数据
filename = files.json()["files"][0]["name"]
data = requests.get(f"{API_BASE}/data/download/{filename}")
with open(filename, 'wb') as f:
    f.write(data.content)
```

### JavaScript 调用 API

```javascript
const API_BASE = 'http://localhost:8000/api';

// 启动爬虫
async function startCrawler() {
  const config = {
    platform: 'xhs',
    keywords: '编程副业',
    crawler_type: 'search',
    max_notes: 20,
    enable_resume: true
  };

  const response = await fetch(`${API_BASE}/crawler/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });

  const result = await response.json();
  console.log(result);
}

// 查看状态
async function getStatus() {
  const response = await fetch(`${API_BASE}/crawler/status`);
  const status = await response.json();
  console.log(status);
}

startCrawler();
```

### cURL 调用 API

```bash
# 启动爬虫
curl -X POST "http://localhost:8000/api/crawler/start" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "xhs",
    "keywords": "编程副业",
    "crawler_type": "search",
    "max_notes": 15,
    "enable_resume": true
  }'

# 查看状态
curl "http://localhost:8000/api/crawler/status"

# 停止爬虫
curl -X POST "http://localhost:8000/api/crawler/stop"

# 获取检查点
curl "http://localhost:8000/api/checkpoints"

# 获取数据文件
curl "http://localhost:8000/api/data/files"
```

## 🔧 断点续爬功能详解

### 工作原理

1. **自动保存**：爬虫在运行过程中会自动保存进度
2. **检查点记录**：包含已爬取的内容ID、当前页码、统计信息等
3. **去重机制**：恢复后自动跳过已爬取的内容
4. **错误恢复**：即使程序崩溃，也可以从最后的检查点恢复

### 检查点存储

检查点文件存储在 `./checkpoint/` 目录下，格式为：

```
{platform}_{type}_{timestamp}.json
```

例如：`xhs_search_20240123_120000.json`

### 手动管理检查点

```python
from checkpoint_manager import CheckpointManager

# 创建管理器
manager = CheckpointManager()

# 列出所有检查点
checkpoints = manager.list_checkpoints(platform='xhs')
for cp in checkpoints:
    print(f"{cp['id']}: {cp['total_notes']} 帖子, {cp['total_comments']} 评论")

# 加载特定检查点
progress = manager.load_checkpoint('xhs_search_20240123_120000')
print(f"已爬取 {len(progress.crawled_ids)} 个内容")

# 删除检查点
manager.delete_checkpoint('xhs_search_20240123_120000')
```

## 🛡️ 原有功能保持

所有原有的命令行功能完全保留，您仍然可以使用：

```bash
# 原有的命令行方式
uv run main.py --platform xhs --lt qrcode --type search

# 新增的 Web UI 方式
uv run python api_server.py
```

两种方式可以并存使用！

## 📊 技术栈

- **后端**：FastAPI - 现代化的 Python Web 框架
- **前端**：原生 HTML/CSS/JavaScript - 无需额外构建工具
- **样式**：现代化 CSS，支持深色模式
- **数据交互**：RESTful API + JSON

## ⚙️ 配置选项

在 `api_server.py` 中可以修改：

```python
# 修改服务器端口
uvicorn.run(app, host="0.0.0.0", port=8000)

# 修改检查点存储目录
checkpoint_dir = "./checkpoint"
```

## 🎨 自定义 UI

Web UI 的样式文件位于 `/web_ui/static/styles.css`，您可以：

- 修改颜色主题
- 调整布局
- 添加自定义样式

JavaScript 逻辑位于 `/web_ui/static/main.js`，可以：

- 添加新功能
- 修改交互逻辑
- 集成第三方库

## 🔒 安全建议

1. **生产环境部署**：
   - 添加身份验证
   - 使用 HTTPS
   - 限制访问 IP

2. **API 密钥**：
   ```python
   from fastapi import Header, HTTPException
   
   async def verify_token(x_token: str = Header(...)):
       if x_token != "your-secret-token":
           raise HTTPException(status_code=401, detail="Invalid token")
   ```

3. **CORS 配置**：
   修改 `api_server.py` 中的 CORS 设置限制允许的域名

## 📝 常见问题

### Q: API 服务器启动失败？
A: 检查端口 8000 是否被占用，可以修改端口号。

### Q: 检查点文件过多？
A: 可以定期清理 `./checkpoint/` 目录下的旧文件。

### Q: 如何在远程服务器使用？
A: 修改 host 为 `0.0.0.0`，然后访问 `http://服务器IP:8000`

### Q: 能否同时运行多个爬虫？
A: 当前版本一次只能运行一个爬虫任务，未来版本会支持多任务。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

本项目遵循 MIT 许可证。仅供学习研究使用。

---

**享受现代化的爬虫体验！** 🎉
