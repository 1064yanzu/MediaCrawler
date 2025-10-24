# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。

"""
定时任务调度管理器
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import uuid
import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger


class SchedulerManager:
    def __init__(self, task_manager, storage_path: str = "./runtime/schedules.json"):
        self.task_manager = task_manager
        self.scheduler = AsyncIOScheduler()
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.jobs: Dict[str, Dict[str, Any]] = {}
        
    async def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
        await self._load_jobs()
    
    async def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        await self._save_jobs()
    
    async def _load_jobs(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for job in data:
                        await self.add_job(job, restore=True)
            except Exception:
                pass
    
    async def _save_jobs(self):
        data = list(self.jobs.values())
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    async def add_job(self, job_data: Dict[str, Any], restore: bool = False) -> Dict[str, Any]:
        job_id = job_data.get("job_id") or str(uuid.uuid4())
        job_data["job_id"] = job_id
        
        trigger = job_data.get("trigger", "cron")
        trigger_args = job_data.get("trigger_args", {})
        
        if trigger == "cron":
            trigger_obj = CronTrigger(**trigger_args)
        elif trigger == "interval":
            trigger_obj = IntervalTrigger(**trigger_args)
        elif trigger == "date":
            run_date = trigger_args.get("run_date")
            trigger_obj = DateTrigger(run_date=run_date)
        else:
            raise ValueError("Unsupported trigger type")
        
        async def job_wrapper():
            config = job_data.get("config", {})
            metadata = {
                "schedule_id": job_id,
                "schedule_name": job_data.get("name", "未命名"),
                "trigger": trigger
            }
            await self.task_manager.submit_process_task(config, metadata=metadata)
        
        self.scheduler.add_job(job_wrapper, trigger=trigger_obj, id=job_id, replace_existing=True)
        
        job_data["created_at"] = job_data.get("created_at") or datetime.now().isoformat()
        job_data["next_run_time"] = str(self.scheduler.get_job(job_id).next_run_time) if self.scheduler.get_job(job_id) else None
        self.jobs[job_id] = job_data
        
        if not restore:
            await self._save_jobs()
        
        return job_data
    
    async def remove_job(self, job_id: str):
        job = self.scheduler.get_job(job_id)
        if job:
            job.remove()
        if job_id in self.jobs:
            del self.jobs[job_id]
            await self._save_jobs()
    
    async def trigger_job(self, job_id: str):
        job_data = self.jobs.get(job_id)
        if not job_data:
            raise ValueError("Job not found")
        
        config = job_data.get("config", {})
        metadata = {
            "schedule_id": job_id,
            "schedule_name": job_data.get("name", "未命名"),
            "trigger": job_data.get("trigger")
        }
        await self.task_manager.submit_process_task(config, metadata=metadata)
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        results = []
        for job_id, job_data in self.jobs.items():
            scheduler_job = self.scheduler.get_job(job_id)
            job_data["next_run_time"] = str(scheduler_job.next_run_time) if scheduler_job else None
            results.append(job_data)
        return results


scheduler_manager: SchedulerManager | None = None  # 将在 api_server 中初始化
