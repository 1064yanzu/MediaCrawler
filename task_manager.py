# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 4. 不得进行大规模爬取或对平台造成运营干扰。
# 5. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 6. 不得用于任何非法或不当的用途。

"""
多任务管理器
负责任务生命周期管理、日志采集、进度统计
"""

import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from websocket_manager import websocket_manager

TEMP_CONFIG_DIR = Path("./temp_configs")
TEMP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

LOG_HISTORY_LIMIT = 2000


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CrawlerTask:
    job_id: str
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    progress: Dict[str, Any] = field(default_factory=lambda: {
        "current": 0,
        "total": 0,
        "notes_crawled": 0,
        "comments_crawled": 0
    })
    created_at: datetime = field(default_factory=datetime.utcnow)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    checkpoint_id: Optional[str] = None
    config_path: Optional[Path] = None
    process: Optional[asyncio.subprocess.Process] = None
    log_history: List[str] = field(default_factory=list)
    report_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "config": self.config,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error,
            "checkpoint_id": self.checkpoint_id,
            "progress": self.progress,
            "log_lines": self.log_history[-100:],  # 返回最近100条
            "report_path": self.report_path
        }


class TaskManager:
    def __init__(self, max_concurrent_tasks: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, CrawlerTask] = {}
        self._lock = asyncio.Lock()

    async def submit_process_task(
        self,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> CrawlerTask:
        """提交新的爬虫任务，使用子进程运行"""
        metadata = metadata or {}
        job_id = metadata.get("job_id", str(uuid.uuid4()))

        config_path = TEMP_CONFIG_DIR / f"{job_id}.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({"job_id": job_id, **config}, f, ensure_ascii=False, indent=2)

        task = CrawlerTask(job_id=job_id, config=config, metadata=metadata)
        task.config_path = config_path
        self.tasks[job_id] = task

        asyncio.create_task(self._run_task(task))
        return task

    async def _run_task(self, task: CrawlerTask):
        """运行爬虫任务"""
        running_count = self.get_running_count()
        if running_count >= self.max_concurrent_tasks:
            await websocket_manager.broadcast_system(
                f"⚠️ 当前已有 {running_count} 个任务在运行，任务 {task.job_id} 将排队等待"
            )
            while self.get_running_count() >= self.max_concurrent_tasks:
                await asyncio.sleep(1)

        try:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.utcnow()
            await websocket_manager.broadcast(task.job_id, f"🚀 任务 {task.job_id} 已启动")

            cmd = [sys.executable, "-m", "task_runner", "--config", str(task.config_path)]
            task.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            await asyncio.gather(
                self._stream_output(task, task.process.stdout),
                self._monitor_process(task)
            )
        except Exception as exc:  # noqa: BLE001
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            task.end_time = datetime.utcnow()
            await websocket_manager.broadcast(task.job_id, f"❌ 任务失败: {exc}")
        finally:
            if task.config_path and task.config_path.exists():
                try:
                    task.config_path.unlink()
                except Exception:
                    pass

    async def _stream_output(self, task: CrawlerTask, stream: asyncio.StreamReader):
        """读取子进程输出"""
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode(errors="ignore").rstrip()
            task.log_history.append(text)
            if len(task.log_history) > LOG_HISTORY_LIMIT:
                task.log_history = task.log_history[-LOG_HISTORY_LIMIT:]
            await websocket_manager.broadcast(task.job_id, text)

    async def _monitor_process(self, task: CrawlerTask):
        code = await task.process.wait()
        task.end_time = datetime.utcnow()
        if code == 0:
            task.status = TaskStatus.COMPLETED
            await websocket_manager.broadcast(task.job_id, f"✅ 任务 {task.job_id} 已完成")
        else:
            task.status = TaskStatus.FAILED
            task.error = f"进程退出，返回码 {code}"
            await websocket_manager.broadcast(task.job_id, f"❌ 任务 {task.job_id} 异常退出，代码 {code}")

    def get_task(self, job_id: str) -> Optional[CrawlerTask]:
        return self.tasks.get(job_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        tasks = sorted(self.tasks.values(), key=lambda t: t.created_at, reverse=True)
        return [task.to_dict() for task in tasks]

    def get_running_count(self) -> int:
        return sum(1 for task in self.tasks.values() if task.status == TaskStatus.RUNNING)

    async def stop_task(self, job_id: str):
        task = self.get_task(job_id)
        if not task or not task.process:
            return
        if task.status not in (TaskStatus.RUNNING, TaskStatus.PAUSED):
            return

        task.process.terminate()
        await asyncio.sleep(0.5)
        if task.process.returncode is None:
            task.process.kill()
        task.status = TaskStatus.CANCELLED
        task.end_time = datetime.utcnow()
        await websocket_manager.broadcast(task.job_id, f"⏹️ 任务 {task.job_id} 已停止")

    async def append_report(self, job_id: str, report_path: str):
        task = self.get_task(job_id)
        if not task:
            return
        task.report_path = report_path

    async def update_checkpoint(self, job_id: str, checkpoint_id: str):
        task = self.get_task(job_id)
        if not task:
            return
        task.checkpoint_id = checkpoint_id


# 全局任务管理器
task_manager = TaskManager(max_concurrent_tasks=3)
