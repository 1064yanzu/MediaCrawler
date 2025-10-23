# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import config
from base.base_crawler import AbstractCrawler
from database import db
from main import CrawlerFactory

# 创建FastAPI应用
app = FastAPI(
    title="MediaCrawler API",
    description="自媒体平台爬虫API接口",
    version="2.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
crawler_instance: Optional[AbstractCrawler] = None
crawler_task: Optional[asyncio.Task] = None
crawler_status = {
    "running": False,
    "platform": None,
    "type": None,
    "progress": {
        "current": 0,
        "total": 0,
        "notes_crawled": 0,
        "comments_crawled": 0
    },
    "start_time": None,
    "last_checkpoint": None,
    "error": None
}


# 请求模型
class CrawlerConfig(BaseModel):
    platform: str = Field(..., description="平台名称: xhs, dy, ks, bili, wb, tieba, zhihu")
    keywords: Optional[str] = Field(None, description="关键词，多个用逗号分隔")
    crawler_type: str = Field(default="search", description="爬取类型: search, detail, creator")
    login_type: str = Field(default="qrcode", description="登录类型: qrcode, phone, cookie")
    max_notes: int = Field(default=15, description="爬取帖子数量")
    max_comments: int = Field(default=10, description="每个帖子的最大评论数")
    enable_comments: bool = Field(default=True, description="是否爬取评论")
    enable_sub_comments: bool = Field(default=False, description="是否爬取二级评论")
    save_data_option: str = Field(default="json", description="保存方式: json, csv, db, sqlite")
    headless: bool = Field(default=False, description="无头模式")
    enable_resume: bool = Field(default=True, description="启用断点续爬")


class ResumeConfig(BaseModel):
    checkpoint_id: str = Field(..., description="检查点ID")


class ConfigPreset(BaseModel):
    name: str = Field(..., description="预设名称")
    config: CrawlerConfig = Field(..., description="配置内容")


# 辅助函数
def get_presets_dir() -> Path:
    """获取配置预设目录"""
    presets_dir = Path("./config_presets")
    presets_dir.mkdir(exist_ok=True)
    return presets_dir


def save_config_preset(name: str, config: CrawlerConfig) -> bool:
    """保存配置预设"""
    try:
        presets_dir = get_presets_dir()
        preset_file = presets_dir / f"{name}.json"
        
        with open(preset_file, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_config_presets() -> List[Dict[str, Any]]:
    """加载所有配置预设"""
    presets_dir = get_presets_dir()
    presets = []
    
    for file in presets_dir.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                presets.append({
                    "name": file.stem,
                    "config": config_data
                })
        except Exception:
            continue
    
    return presets


def analyze_data_files() -> Dict[str, Any]:
    """分析数据文件统计信息"""
    data_dir = Path("./data")
    if not data_dir.exists():
        return {
            "total_files": 0,
            "total_size": 0,
            "by_platform": {},
            "by_type": {}
        }
    
    stats = {
        "total_files": 0,
        "total_size": 0,
        "by_platform": {},
        "by_type": {"json": 0, "csv": 0}
    }
    
    for file in data_dir.rglob("*"):
        if file.is_file() and file.suffix in [".json", ".csv"]:
            stats["total_files"] += 1
            stats["total_size"] += file.stat().st_size
            
            # 统计类型
            file_type = file.suffix[1:]
            stats["by_type"][file_type] = stats["by_type"].get(file_type, 0) + 1
            
            # 统计平台
            for platform in ["xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"]:
                if platform in file.name:
                    stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
                    break
    
    return stats



def get_checkpoint_dir() -> Path:
    """获取检查点目录"""
    checkpoint_dir = Path("./checkpoint")
    checkpoint_dir.mkdir(exist_ok=True)
    return checkpoint_dir


def save_checkpoint(platform: str, data: Dict[str, Any]) -> str:
    """保存检查点"""
    checkpoint_dir = get_checkpoint_dir()
    checkpoint_id = f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    checkpoint_file = checkpoint_dir / f"{checkpoint_id}.json"
    
    checkpoint_data = {
        "id": checkpoint_id,
        "platform": platform,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    
    return checkpoint_id


def load_checkpoint(checkpoint_id: str) -> Optional[Dict[str, Any]]:
    """加载检查点"""
    checkpoint_dir = get_checkpoint_dir()
    checkpoint_file = checkpoint_dir / f"{checkpoint_id}.json"
    
    if not checkpoint_file.exists():
        return None
    
    with open(checkpoint_file, "r", encoding="utf-8") as f:
        return json.load(f)


def list_checkpoints() -> List[Dict[str, Any]]:
    """列出所有检查点"""
    checkpoint_dir = get_checkpoint_dir()
    checkpoints = []
    
    for file in sorted(checkpoint_dir.glob("*.json"), reverse=True):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                checkpoints.append({
                    "id": data.get("id"),
                    "platform": data.get("platform"),
                    "timestamp": data.get("timestamp"),
                    "file": file.name
                })
        except Exception:
            continue
    
    return checkpoints


def get_data_files(platform: Optional[str] = None, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取爬取的数据文件列表"""
    data_dir = Path("./data")
    if not data_dir.exists():
        return []
    
    files = []
    for file in data_dir.rglob("*"):
        if not file.is_file() or file.suffix.lower() not in [".json", ".csv"]:
            continue
        
        rel_path = file.relative_to(data_dir)
        platform_name = rel_path.parts[0] if len(rel_path.parts) > 1 else None
        
        if platform and platform_name != platform:
            continue
        if file_type and file.suffix[1:] != file_type:
            continue
        
        stat = file.stat()
        files.append({
            "name": file.name,
            "path": str(rel_path).replace("\\", "/"),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "type": file.suffix[1:],
            "platform": platform_name,
            "directory": str(rel_path.parent).replace("\\", "/") if rel_path.parent != Path(".") else ""
        })
    
    return sorted(files, key=lambda x: x["modified"], reverse=True)


async def run_crawler_task(crawler_config: CrawlerConfig):
    """运行爬虫任务"""
    global crawler_instance, crawler_status
    
    try:
        # 更新状态
        crawler_status["running"] = True
        crawler_status["platform"] = crawler_config.platform
        crawler_status["type"] = crawler_config.crawler_type
        crawler_status["start_time"] = datetime.now().isoformat()
        crawler_status["error"] = None
        
        # 更新配置
        config.PLATFORM = crawler_config.platform
        config.KEYWORDS = crawler_config.keywords or config.KEYWORDS
        config.CRAWLER_TYPE = crawler_config.crawler_type
        config.LOGIN_TYPE = crawler_config.login_type
        config.CRAWLER_MAX_NOTES_COUNT = crawler_config.max_notes
        config.CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = crawler_config.max_comments
        config.ENABLE_GET_COMMENTS = crawler_config.enable_comments
        config.ENABLE_GET_SUB_COMMENTS = crawler_config.enable_sub_comments
        config.SAVE_DATA_OPTION = crawler_config.save_data_option
        config.HEADLESS = crawler_config.headless
        
        # 创建并启动爬虫
        crawler_instance = CrawlerFactory.create_crawler(platform=crawler_config.platform)
        
        # 如果启用断点续爬，保存初始检查点
        if crawler_config.enable_resume:
            checkpoint_id = save_checkpoint(crawler_config.platform, {
                "config": crawler_config.model_dump(),
                "progress": crawler_status["progress"]
            })
            crawler_status["last_checkpoint"] = checkpoint_id
        
        await crawler_instance.start()
        
        # 任务完成
        crawler_status["running"] = False
        
        # 保存最终检查点
        if crawler_config.enable_resume:
            save_checkpoint(crawler_config.platform, {
                "config": crawler_config.model_dump(),
                "progress": crawler_status["progress"],
                "completed": True
            })
            
    except Exception as e:
        crawler_status["running"] = False
        crawler_status["error"] = str(e)
        raise


# API路由
@app.get("/", response_class=HTMLResponse)
async def root():
    """返回Web UI界面"""
    html_file = Path(__file__).parent / "web_ui" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse(content="<h1>MediaCrawler API Server</h1><p>访问 /docs 查看API文档</p>")


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/platforms")
async def get_platforms():
    """获取支持的平台列表"""
    return {
        "platforms": [
            {"id": "xhs", "name": "小红书", "icon": "🔴"},
            {"id": "dy", "name": "抖音", "icon": "🎵"},
            {"id": "ks", "name": "快手", "icon": "⚡"},
            {"id": "bili", "name": "哔哩哔哩", "icon": "📺"},
            {"id": "wb", "name": "微博", "icon": "🐦"},
            {"id": "tieba", "name": "百度贴吧", "icon": "💬"},
            {"id": "zhihu", "name": "知乎", "icon": "🧠"}
        ]
    }


@app.get("/api/config")
async def get_config():
    """获取当前配置"""
    return {
        "platform": config.PLATFORM,
        "keywords": config.KEYWORDS,
        "crawler_type": config.CRAWLER_TYPE,
        "login_type": config.LOGIN_TYPE,
        "max_notes": config.CRAWLER_MAX_NOTES_COUNT,
        "max_comments": config.CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES,
        "enable_comments": config.ENABLE_GET_COMMENTS,
        "enable_sub_comments": config.ENABLE_GET_SUB_COMMENTS,
        "save_data_option": config.SAVE_DATA_OPTION,
        "headless": config.HEADLESS
    }


@app.post("/api/crawler/start")
async def start_crawler(crawler_config: CrawlerConfig, background_tasks: BackgroundTasks):
    """启动爬虫"""
    global crawler_task, crawler_status
    
    if crawler_status["running"]:
        raise HTTPException(status_code=400, detail="爬虫正在运行中")
    
    # 重置状态
    crawler_status["progress"] = {
        "current": 0,
        "total": crawler_config.max_notes,
        "notes_crawled": 0,
        "comments_crawled": 0
    }
    
    # 在后台启动爬虫任务
    crawler_task = asyncio.create_task(run_crawler_task(crawler_config))
    
    return {
        "status": "started",
        "message": "爬虫任务已启动",
        "config": crawler_config.model_dump()
    }


@app.post("/api/crawler/stop")
async def stop_crawler():
    """停止爬虫"""
    global crawler_task, crawler_status, crawler_instance
    
    if not crawler_status["running"]:
        raise HTTPException(status_code=400, detail="爬虫未在运行")
    
    # 保存检查点
    if crawler_status["platform"]:
        checkpoint_id = save_checkpoint(crawler_status["platform"], {
            "progress": crawler_status["progress"],
            "stopped": True
        })
        crawler_status["last_checkpoint"] = checkpoint_id
    
    # 取消任务
    if crawler_task and not crawler_task.done():
        crawler_task.cancel()
        try:
            await crawler_task
        except asyncio.CancelledError:
            pass
    
    crawler_status["running"] = False
    
    return {
        "status": "stopped",
        "message": "爬虫已停止",
        "checkpoint": crawler_status["last_checkpoint"]
    }


@app.get("/api/crawler/status")
async def get_crawler_status():
    """获取爬虫状态"""
    return crawler_status


@app.get("/api/checkpoints")
async def get_checkpoints():
    """获取检查点列表"""
    return {"checkpoints": list_checkpoints()}


@app.get("/api/checkpoints/download/{checkpoint_id}")
async def download_checkpoint(checkpoint_id: str):
    """下载检查点文件"""
    checkpoint_dir = get_checkpoint_dir()
    target_path = checkpoint_dir / f"{checkpoint_id}.json"
    
    if not target_path.exists():
        # 兼容传入文件名的情况
        alt_path = checkpoint_dir / checkpoint_id
        if alt_path.exists():
            target_path = alt_path
        else:
            raise HTTPException(status_code=404, detail="检查点不存在")
    
    return FileResponse(target_path, filename=target_path.name)


@app.post("/api/crawler/resume")
async def resume_crawler(resume_config: ResumeConfig, background_tasks: BackgroundTasks):
    """从检查点恢复爬虫"""
    global crawler_status
    
    if crawler_status["running"]:
        raise HTTPException(status_code=400, detail="爬虫正在运行中")
    
    # 加载检查点
    checkpoint = load_checkpoint(resume_config.checkpoint_id)
    if not checkpoint:
        raise HTTPException(status_code=404, detail="检查点不存在")
    
    # 恢复配置
    saved_config = checkpoint.get("data", {}).get("config", {})
    crawler_config = CrawlerConfig(**saved_config)
    
    # 恢复进度
    saved_progress = checkpoint.get("data", {}).get("progress", {})
    crawler_status["progress"] = saved_progress
    
    # 启动爬虫
    crawler_task = asyncio.create_task(run_crawler_task(crawler_config))
    
    return {
        "status": "resumed",
        "message": "从检查点恢复爬虫",
        "checkpoint_id": resume_config.checkpoint_id
    }


@app.get("/api/data/files")
async def get_data_files_list(platform: Optional[str] = None):
    """获取数据文件列表"""
    return {"files": get_data_files(platform)}


@app.get("/api/data/download/{file_path:path}")
async def download_data_file(file_path: str):
    """下载数据文件"""
    data_dir = Path("./data")
    target_path = data_dir / file_path
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        target_path.resolve().relative_to(data_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="不允许访问此文件")
    
    return FileResponse(target_path, filename=target_path.name)


@app.get("/api/data/preview/{file_path:path}")
async def preview_data_file(file_path: str, limit: int = 100):
    """预览数据文件"""
    data_dir = Path("./data")
    target_path = data_dir / file_path
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        target_path.resolve().relative_to(data_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="不允许访问此文件")
    
    try:
        if target_path.suffix == ".json":
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    total = len(data)
                    data = data[:limit]
                    return {"data": data, "total": total, "truncated": total > limit}
                else:
                    return {"data": data, "total": 1, "truncated": False}
        elif target_path.suffix == ".csv":
            rows = []
            total = 0
            try:
                import pandas as pd  # type: ignore
                df = pd.read_csv(target_path)
                total = len(df)
                rows = df.head(limit).to_dict(orient="records")
                columns = list(df.columns)
            except ImportError:
                import csv
                with open(target_path, "r", encoding="utf-8-sig", newline="") as csvfile:
                    reader = csv.DictReader(csvfile)
                    for idx, row in enumerate(reader, start=1):
                        if idx <= limit:
                            rows.append(row)
                        total = idx
                    columns = reader.fieldnames or []
            return {
                "data": rows,
                "total": total,
                "columns": columns,
                "truncated": total > limit
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@app.delete("/api/data/delete/{file_path:path}")
async def delete_data_file(file_path: str):
    """删除数据文件"""
    data_dir = Path("./data")
    target_path = data_dir / file_path
    
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 安全检查：确保文件在data目录内
    try:
        target_path.resolve().relative_to(data_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="不允许访问此文件")
    
    try:
        target_path.unlink()
        return {"status": "success", "message": f"文件 {target_path.name} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


@app.get("/api/stats")
async def get_statistics():
    """获取统计信息"""
    try:
        data_stats = analyze_data_files()
        checkpoints = list_checkpoints()
        
        return {
            "data": data_stats,
            "checkpoints_count": len(checkpoints),
            "crawler_status": crawler_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@app.get("/api/presets")
async def get_config_presets():
    """获取配置预设列表"""
    return {"presets": load_config_presets()}


@app.post("/api/presets")
async def save_preset(preset: ConfigPreset):
    """保存配置预设"""
    if save_config_preset(preset.name, preset.config):
        return {"status": "success", "message": f"配置预设 {preset.name} 已保存"}
    else:
        raise HTTPException(status_code=500, detail="保存配置预设失败")


@app.delete("/api/presets/{name}")
async def delete_preset(name: str):
    """删除配置预设"""
    try:
        preset_file = get_presets_dir() / f"{name}.json"
        if preset_file.exists():
            preset_file.unlink()
            return {"status": "success", "message": f"配置预设 {name} 已删除"}
        else:
            raise HTTPException(status_code=404, detail="配置预设不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除配置预设失败: {str(e)}")


@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """获取最近的日志（从日志文件读取）"""
    try:
        log_lines = []
        log_files = sorted(Path("./").glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if log_files:
            with open(log_files[0], "r", encoding="utf-8") as f:
                lines = f.readlines()
                log_lines = lines[-limit:] if len(lines) > limit else lines
        
        return {
            "logs": log_lines,
            "count": len(log_lines)
        }
    except Exception as e:
        return {"logs": [], "count": 0, "error": str(e)}


@app.post("/api/crawler/pause")
async def pause_crawler():
    """暂停爬虫（保存检查点但不停止）"""
    global crawler_status
    
    if not crawler_status["running"]:
        raise HTTPException(status_code=400, detail="爬虫未在运行")
    
    # 保存检查点
    if crawler_status["platform"]:
        checkpoint_id = save_checkpoint(crawler_status["platform"], {
            "progress": crawler_status["progress"],
            "paused": True
        })
        crawler_status["last_checkpoint"] = checkpoint_id
        
        return {
            "status": "paused",
            "message": "已保存检查点",
            "checkpoint": checkpoint_id
        }
    
    raise HTTPException(status_code=500, detail="无法保存检查点")


# 挂载静态文件
web_ui_dir = Path(__file__).parent / "web_ui"
if web_ui_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_ui_dir / "static")), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
