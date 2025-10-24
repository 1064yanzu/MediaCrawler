# MediaCrawler 使用示例

本文档提供详细的使用示例，帮助您快速上手 MediaCrawler 的所有功能。

## 目录

1. [命令行方式（原有功能）](#命令行方式)
2. [Web UI 方式（新增功能）](#web-ui-方式)
3. [API 调用方式（新增功能）](#api-调用方式)
4. [断点续爬示例](#断点续爬示例)
5. [高级用法](#高级用法)

---

## 命令行方式

### 1. 小红书爬虫示例

```bash
# 关键词搜索 - 使用二维码登录
uv run main.py --platform xhs --lt qrcode --type search

# 指定帖子ID爬取
uv run main.py --platform xhs --lt qrcode --type detail

# 创作者主页数据
uv run main.py --platform xhs --lt qrcode --type creator
```

### 2. 抖音爬虫示例

```bash
# 关键词搜索
uv run main.py --platform dy --lt qrcode --type search

# 指定视频爬取
uv run main.py --platform dy --lt qrcode --type detail
```

### 3. 配置关键词和帖子ID

编辑 `config/base_config.py` 或对应平台的配置文件：

```python
# 基础配置
PLATFORM = "xhs"  # 平台选择
KEYWORDS = "编程副业,编程兼职"  # 搜索关键词
CRAWLER_TYPE = "search"  # 爬取类型

# 小红书特定配置（在 config/xhs_config.py）
XHS_SPECIFIED_NOTE_URL_LIST = [
    "https://www.xiaohongshu.com/explore/...",
    # 添加更多帖子URL
]
```

### 4. 数据存储选项

```bash
# 保存为 JSON（默认）
uv run main.py --platform xhs --lt qrcode --type search --save_data_option json

# 保存为 CSV
uv run main.py --platform xhs --lt qrcode --type search --save_data_option csv

# 保存到 SQLite
uv run main.py --init_db sqlite  # 初始化数据库
uv run main.py --platform xhs --lt qrcode --type search --save_data_option sqlite

# 保存到 MySQL
uv run main.py --init_db mysql  # 初始化数据库
uv run main.py --platform xhs --lt qrcode --type search --save_data_option db
```

---

## Web UI 方式

### 1. 启动 Web UI

```bash
# 方式 1：直接运行
uv run python api_server.py

# 方式 2：使用启动脚本（Linux/Mac）
./start_web_ui.sh

# 方式 3：使用启动脚本（Windows）
start_web_ui.bat
```

### 2. 访问 Web UI

打开浏览器，访问：
- 主控制面板：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 交互式文档：http://localhost:8000/redoc

### 3. 使用 Web UI 启动爬虫

1. 在平台选择区域选择目标平台（如小红书）
2. 填写关键词（例如：编程副业,编程兼职）
3. 选择爬取类型（关键词搜索/帖子详情/创作者主页）
4. 配置参数：
   - 最大帖子数：15
   - 每帖最大评论数：10
   - 勾选"爬取评论"
   - 勾选"断点续爬"
5. 选择数据存储方式（JSON/CSV/SQLite/MySQL）
6. 点击"启动爬虫"按钮

### 4. 监控爬虫状态

Web UI 会实时显示：
- 运行状态（运行中/已停止）
- 开始时间
- 已爬取帖子数
- 已爬取评论数
- 进度条
- 实时日志

### 5. 管理数据文件

在"数据中心"区域：
1. 查看所有爬取的数据文件
2. 点击"预览"按钮在线查看数据
3. 点击"下载"按钮下载文件
4. 点击"删除"按钮删除不需要的文件

---

## API 调用方式

### 1. Python 调用示例

```python
import requests
import json

API_BASE = "http://localhost:8000/api"

# 1. 检查服务状态
response = requests.get(f"{API_BASE}/health")
print("服务状态:", response.json())

# 2. 获取支持的平台列表
response = requests.get(f"{API_BASE}/platforms")
platforms = response.json()["platforms"]
for platform in platforms:
    print(f"{platform['icon']} {platform['name']} ({platform['id']})")

# 3. 启动爬虫
config = {
    "platform": "xhs",
    "keywords": "编程副业,自媒体运营",
    "crawler_type": "search",
    "login_type": "qrcode",
    "max_notes": 20,
    "max_comments": 15,
    "enable_comments": True,
    "enable_sub_comments": False,
    "save_data_option": "json",
    "headless": False,
    "enable_resume": True
}

response = requests.post(f"{API_BASE}/crawler/start", json=config)
result = response.json()
print("启动结果:", result)

# 4. 查询爬虫状态
import time
while True:
    response = requests.get(f"{API_BASE}/crawler/status")
    status = response.json()
    
    print(f"运行状态: {status['running']}")
    print(f"已爬帖子: {status['progress']['notes_crawled']}")
    print(f"已爬评论: {status['progress']['comments_crawled']}")
    
    if not status['running']:
        break
    
    time.sleep(5)  # 每5秒查询一次

# 5. 获取数据文件列表
response = requests.get(f"{API_BASE}/data/files?platform=xhs")
files = response.json()["files"]
print(f"找到 {len(files)} 个数据文件")

# 6. 下载最新的数据文件
if files:
    latest_file = files[0]
    filename = latest_file['name']
    
    response = requests.get(f"{API_BASE}/data/download/{filename}")
    with open(f"downloaded_{filename}", 'wb') as f:
        f.write(response.content)
    print(f"已下载: {filename}")

# 7. 预览数据
if files:
    filename = files[0]['name']
    response = requests.get(f"{API_BASE}/data/preview/{filename}?limit=10")
    preview_data = response.json()
    print("数据预览:")
    print(json.dumps(preview_data['data'][:2], ensure_ascii=False, indent=2))
```

### 2. JavaScript 调用示例

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

    try {
        const response = await fetch(`${API_BASE}/crawler/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        console.log('爬虫已启动:', result);
        
        // 开始监控状态
        monitorStatus();
    } catch (error) {
        console.error('启动失败:', error);
    }
}

// 监控爬虫状态
async function monitorStatus() {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/crawler/status`);
            const status = await response.json();
            
            console.log(`状态: ${status.running ? '运行中' : '已停止'}`);
            console.log(`进度: ${status.progress.notes_crawled} 帖子, ${status.progress.comments_crawled} 评论`);
            
            if (!status.running) {
                clearInterval(interval);
                console.log('爬虫已完成');
                listDataFiles();
            }
        } catch (error) {
            console.error('查询状态失败:', error);
            clearInterval(interval);
        }
    }, 5000); // 每5秒查询一次
}

// 获取数据文件列表
async function listDataFiles() {
    try {
        const response = await fetch(`${API_BASE}/data/files`);
        const data = await response.json();
        console.log('数据文件:', data.files);
    } catch (error) {
        console.error('获取文件列表失败:', error);
    }
}

// 执行
startCrawler();
```

### 3. cURL 调用示例

```bash
# 1. 健康检查
curl "http://localhost:8000/api/health"

# 2. 获取平台列表
curl "http://localhost:8000/api/platforms"

# 3. 启动爬虫
curl -X POST "http://localhost:8000/api/crawler/start" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "xhs",
    "keywords": "编程副业",
    "crawler_type": "search",
    "max_notes": 15,
    "enable_resume": true
  }'

# 4. 查询状态
curl "http://localhost:8000/api/crawler/status"

# 5. 停止爬虫
curl -X POST "http://localhost:8000/api/crawler/stop"

# 6. 获取数据文件
curl "http://localhost:8000/api/data/files"

# 7. 下载数据文件
curl -O "http://localhost:8000/api/data/download/xhs_search_contents_20240123.json"

# 8. 预览数据（限制前100条）
curl "http://localhost:8000/api/data/preview/xhs_search_contents_20240123.json?limit=100"
```

---

## 断点续爬示例

### 1. 使用 Web UI 进行断点续爬

1. 在启动爬虫时，确保勾选"断点续爬"选项
2. 如果爬虫中断，在"断点续爬"区域会显示最近的检查点
3. 点击检查点卡片上的"恢复"按钮，即可从中断处继续

### 2. 使用 API 进行断点续爬

```python
import requests

API_BASE = "http://localhost:8000/api"

# 1. 获取所有检查点
response = requests.get(f"{API_BASE}/checkpoints")
checkpoints = response.json()["checkpoints"]

print("可用的检查点:")
for cp in checkpoints:
    print(f"- {cp['id']} ({cp['platform']}) - {cp['timestamp']}")

# 2. 选择一个检查点恢复
if checkpoints:
    checkpoint_id = checkpoints[0]['id']  # 选择最新的
    
    response = requests.post(f"{API_BASE}/crawler/resume", json={
        "checkpoint_id": checkpoint_id
    })
    
    result = response.json()
    print(f"已从检查点 {checkpoint_id} 恢复")
```

### 3. 手动管理检查点

```python
from checkpoint_manager import CheckpointManager

# 创建管理器
manager = CheckpointManager()

# 列出所有检查点
checkpoints = manager.list_checkpoints(platform='xhs')
print(f"找到 {len(checkpoints)} 个检查点")

for cp in checkpoints:
    print(f"ID: {cp['id']}")
    print(f"平台: {cp['platform']}")
    print(f"类型: {cp['crawler_type']}")
    print(f"关键词: {cp['keywords']}")
    print(f"帖子数: {cp['total_notes']}")
    print(f"评论数: {cp['total_comments']}")
    print(f"当前页: {cp['current_page']}")
    print(f"完成状态: {cp['completed']}")
    print("---")

# 加载特定检查点
checkpoint_id = "xhs_search_20240123_120000"
progress = manager.load_checkpoint(checkpoint_id)

if progress:
    print(f"已加载检查点: {checkpoint_id}")
    print(f"已爬取内容数: {len(progress.crawled_ids)}")
    print(f"当前页码: {progress.current_page}")

# 删除旧的检查点
old_checkpoint_id = "xhs_search_20240101_100000"
if manager.delete_checkpoint(old_checkpoint_id):
    print(f"已删除检查点: {old_checkpoint_id}")
```

---

## 高级用法

### 1. 批量爬取多个关键词

```python
import requests
import time

API_BASE = "http://localhost:8000/api"

keywords_list = [
    "编程副业",
    "自媒体运营",
    "Python教程",
    "数据分析"
]

for keyword in keywords_list:
    print(f"开始爬取关键词: {keyword}")
    
    config = {
        "platform": "xhs",
        "keywords": keyword,
        "crawler_type": "search",
        "max_notes": 50,
        "enable_resume": True
    }
    
    # 启动爬虫
    response = requests.post(f"{API_BASE}/crawler/start", json=config)
    print(response.json())
    
    # 等待完成
    while True:
        status_response = requests.get(f"{API_BASE}/crawler/status")
        status = status_response.json()
        
        if not status['running']:
            break
        
        time.sleep(10)
    
    print(f"关键词 {keyword} 爬取完成")
    print("---")
```

### 2. 定时任务

```python
import schedule
import requests
import time

API_BASE = "http://localhost:8000/api"

def run_daily_crawl():
    """每日定时爬取"""
    print("开始每日爬取任务...")
    
    config = {
        "platform": "xhs",
        "keywords": "今日热点",
        "crawler_type": "search",
        "max_notes": 100,
        "enable_resume": True
    }
    
    response = requests.post(f"{API_BASE}/crawler/start", json=config)
    print(response.json())

# 设置每天早上9点运行
schedule.every().day.at("09:00").do(run_daily_crawl)

print("定时任务已启动，等待执行...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. 数据分析示例

```python
import requests
import json
import pandas as pd

API_BASE = "http://localhost:8000/api"

# 1. 获取数据文件
response = requests.get(f"{API_BASE}/data/files?platform=xhs")
files = response.json()["files"]

# 2. 下载并分析最新的 JSON 文件
if files:
    filename = files[0]['name']
    
    # 预览数据（获取全部）
    response = requests.get(f"{API_BASE}/data/preview/{filename}?limit=10000")
    data = response.json()['data']
    
    # 转换为 DataFrame
    df = pd.DataFrame(data)
    
    # 基本统计
    print("数据统计:")
    print(f"总帖子数: {len(df)}")
    print(f"平均点赞数: {df['liked_count'].mean():.0f}")
    print(f"平均评论数: {df['comment_count'].mean():.0f}")
    print(f"平均收藏数: {df['collected_count'].mean():.0f}")
    
    # 找出热门帖子
    top_posts = df.nlargest(10, 'liked_count')[['title', 'liked_count', 'comment_count']]
    print("\n热门帖子 TOP 10:")
    print(top_posts)
    
    # 导出为 Excel
    df.to_excel("analysis_result.xlsx", index=False)
    print("\n分析结果已保存到 analysis_result.xlsx")
```

### 4. 多平台对比爬取

```python
import requests
import time

API_BASE = "http://localhost:8000/api"

platforms = ['xhs', 'dy', 'ks']
keyword = "编程教程"

results = {}

for platform in platforms:
    print(f"爬取平台: {platform}")
    
    config = {
        "platform": platform,
        "keywords": keyword,
        "crawler_type": "search",
        "max_notes": 30,
        "enable_resume": True
    }
    
    # 启动爬虫
    requests.post(f"{API_BASE}/crawler/start", json=config)
    
    # 等待完成
    while True:
        status = requests.get(f"{API_BASE}/crawler/status").json()
        if not status['running']:
            results[platform] = status['progress']['notes_crawled']
            break
        time.sleep(5)

print("\n爬取结果对比:")
for platform, count in results.items():
    print(f"{platform}: {count} 个帖子")
```

---

## 常见问题

### Q1: 如何设置代理？
在 `config/base_config.py` 中：
```python
ENABLE_IP_PROXY = True
IP_PROXY_POOL_COUNT = 2
IP_PROXY_PROVIDER_NAME = "kuaidaili"  # 或 "wandouhttp"
```

### Q2: 如何开启无头模式？
```python
HEADLESS = True  # 在配置文件中设置
# 或在 Web UI 中勾选"无头模式"
```

### Q3: 数据保存在哪里？
- CSV/JSON: `data/{platform}/csv|json/` 目录
- SQLite: 项目根目录的 `media_crawler.db`
- MySQL: 配置的 MySQL 数据库中

### Q4: 检查点文件在哪里？
在项目根目录的 `checkpoint/` 目录下。

### Q5: 如何清理旧数据？
使用 Web UI 的"数据中心"功能，或直接删除 `data/` 目录下的文件。

---

## 结语

更多详细信息请参考：
- [API & Web UI 使用指南](API_GUIDE.md)
- [更新日志](CHANGELOG.md)
- [项目 README](README.md)

如有问题，欢迎提交 Issue！
