# 更新日志 / Changelog

## [2.0.0] - 2024-01-XX

### 🎉 新增功能 / New Features

#### 现代化 Web UI 控制面板
- ✨ 添加了基于 FastAPI 的现代化 Web UI 控制面板
- 🎨 美观的可视化界面，支持一键启动/停止爬虫
- 📊 实时监控爬虫运行状态和进度
- 📁 在线浏览、预览和下载数据文件
- 🌐 通过 `uv run python api_server.py` 启动服务，访问 `http://localhost:8000`

#### RESTful API 接口
- 🔌 完整的 RESTful API 接口，方便外部应用调用
- 📖 自动生成的交互式 API 文档（`/docs` 和 `/redoc`）
- 🔐 支持跨域请求（CORS）
- 🚀 支持所有爬虫功能的远程调用

#### 断点续爬功能
- 💾 自动保存爬取进度，支持中断后继续执行
- 🔄 智能去重，避免重复爬取已获取的数据
- 📝 保存检查点信息，包括已爬取ID、当前页码等
- ⚡ 可从任意检查点恢复爬取任务
- 📊 详细的进度统计信息

### 📂 新增文件 / New Files

- `api_server.py` - FastAPI 服务器主文件
- `checkpoint_manager.py` - 断点续爬管理器
- `web_ui/index.html` - Web UI 主页面
- `web_ui/static/styles.css` - 现代化样式表
- `web_ui/static/main.js` - 前端交互逻辑
- `API_GUIDE.md` - API 和 Web UI 使用指南
- `start_web_ui.sh` - Linux/Mac 启动脚本
- `start_web_ui.bat` - Windows 启动脚本

### 🔧 功能增强 / Enhancements

#### Web UI 功能
- 平台选择器：支持所有7个平台的快速切换
- 配置面板：可视化配置所有爬虫参数
- 状态监控：实时显示爬取进度和统计信息
- 日志查看器：实时查看爬虫运行日志
- 检查点管理：查看和恢复所有保存的检查点
- 数据中心：浏览、预览、下载和删除数据文件

#### API 接口功能
- `GET /api/health` - 健康检查
- `GET /api/platforms` - 获取支持的平台列表
- `GET /api/config` - 获取当前配置
- `POST /api/crawler/start` - 启动爬虫
- `POST /api/crawler/stop` - 停止爬虫
- `GET /api/crawler/status` - 获取爬虫状态
- `GET /api/checkpoints` - 获取检查点列表
- `POST /api/crawler/resume` - 从检查点恢复
- `GET /api/data/files` - 获取数据文件列表
- `GET /api/data/preview/{filename}` - 预览数据
- `GET /api/data/download/{filename}` - 下载数据
- `DELETE /api/data/delete/{filename}` - 删除数据

#### 断点续爬功能
- 自动保存：每爬取10个内容自动保存一次检查点
- 智能去重：基于内容ID的去重机制
- 进度统计：记录已爬取帖子数、评论数、错误数等
- 状态恢复：完整恢复爬取状态，包括配置和进度
- 文件管理：检查点文件存储在 `./checkpoint/` 目录

### 📝 文档更新 / Documentation

- 更新 `README.md`，添加新功能说明
- 新增 `API_GUIDE.md`，提供详细的使用指南
- 添加 Python、JavaScript、cURL 的调用示例
- 提供断点续爬功能的详细说明

### 🎨 界面设计 / UI Design

- 采用现代化设计风格
- 使用 Inter 字体，提升可读性
- 响应式布局，支持移动端访问
- 优雅的动画和过渡效果
- 清晰的信息层级
- 直观的操作反馈

### 🔒 安全性 / Security

- CORS 配置，支持跨域访问（可自定义限制）
- 建议生产环境添加身份验证
- 支持 HTTPS 部署
- 提供安全配置指南

### ⚡ 性能优化 / Performance

- 异步处理，提升响应速度
- 轻量级前端，无需额外构建工具
- 高效的检查点保存机制
- 优化的文件读写操作

### 🔄 兼容性 / Compatibility

- ✅ 完全兼容原有命令行功能
- ✅ 不影响现有爬虫逻辑
- ✅ 支持所有平台（小红书、抖音、快手、B站、微博、贴吧、知乎）
- ✅ 支持所有存储方式（JSON、CSV、SQLite、MySQL）
- ✅ 支持所有爬取类型（搜索、详情、创作者）

### 📦 依赖更新 / Dependencies

- FastAPI 和 Uvicorn 已包含在 requirements.txt 中
- 无需额外安装依赖

### 🚀 使用方式 / Usage

#### 命令行方式（原有功能）
```bash
uv run main.py --platform xhs --lt qrcode --type search
```

#### Web UI 方式（新增功能）
```bash
# 启动 Web UI 服务
uv run python api_server.py
# 或使用启动脚本
./start_web_ui.sh  # Linux/Mac
start_web_ui.bat   # Windows

# 访问 http://localhost:8000
```

#### API 调用方式（新增功能）
```python
import requests
response = requests.post('http://localhost:8000/api/crawler/start', json={
    'platform': 'xhs',
    'keywords': '编程副业',
    'crawler_type': 'search'
})
```

### 💡 注意事项 / Notes

1. Web UI 和命令行模式可以并存，互不影响
2. 启动 Web UI 需要确保 8000 端口未被占用
3. 断点续爬文件存储在 `./checkpoint/` 目录
4. 检查点文件可以手动管理和备份
5. 详细使用说明请参考 `API_GUIDE.md`

### 🐛 已知问题 / Known Issues

- 当前版本一次只能运行一个爬虫任务
- Web UI 的实时日志功能需要手动刷新状态
- 大数据量预览可能较慢（可通过 limit 参数限制）

### 🔮 计划中的功能 / Planned Features

- [ ] 支持多任务并发执行
- [ ] WebSocket 实时日志推送
- [ ] 用户认证和权限管理
- [ ] 数据分析和可视化图表
- [ ] 定时任务和自动化调度
- [ ] 邮件/消息通知
- [ ] 导出报告功能
- [ ] 更多的数据存储选项

---

## 历史版本 / Previous Versions

### [1.x.x] - 之前的版本

请参考 Git 提交历史查看详细的更新记录。
