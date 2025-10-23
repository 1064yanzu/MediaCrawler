# 声明:本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

"""
断点续爬管理器
Checkpoint Manager for Resume Crawling
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class CrawlProgress:
    """爬取进度数据类"""
    platform: str
    crawler_type: str
    keywords: Optional[str] = None
    checkpoint_id: Optional[str] = None
    crawled_ids: List[str] = None  # 已爬取的内容ID
    total_notes_crawled: int = 0
    total_comments_crawled: int = 0
    current_page: int = 1
    last_update: str = None
    completed: bool = False
    error_count: int = 0
    
    def __post_init__(self):
        if self.crawled_ids is None:
            self.crawled_ids = []
        if self.last_update is None:
            self.last_update = datetime.now().isoformat()


class CheckpointManager:
    """断点续爬管理器"""
    
    def __init__(self, checkpoint_dir: str = "./checkpoint"):
        """
        初始化检查点管理器
        
        Args:
            checkpoint_dir: 检查点存储目录
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.current_checkpoint: Optional[CrawlProgress] = None
        self.current_checkpoint_id: Optional[str] = None
        self.checkpoint_file: Optional[Path] = None
        
    def create_checkpoint(self, platform: str, crawler_type: str, keywords: Optional[str] = None) -> CrawlProgress:
        """
        创建新的检查点
        
        Args:
            platform: 平台名称
            crawler_type: 爬取类型
            keywords: 关键词
            
        Returns:
            CrawlProgress: 爬取进度对象
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_id = f"{platform}_{crawler_type}_{timestamp}"
        
        self.current_checkpoint = CrawlProgress(
            platform=platform,
            crawler_type=crawler_type,
            keywords=keywords,
            checkpoint_id=checkpoint_id
        )
        
        self.current_checkpoint_id = checkpoint_id
        self.checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        self.save_checkpoint()
        
        return self.current_checkpoint
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[CrawlProgress]:
        """
        加载检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            Optional[CrawlProgress]: 爬取进度对象，如果不存在返回None
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault('checkpoint_id', checkpoint_id)
                self.current_checkpoint = CrawlProgress(**data)
                self.current_checkpoint_id = checkpoint_id
                self.checkpoint_file = checkpoint_file
                return self.current_checkpoint
        except Exception as e:
            print(f"加载检查点失败: {e}")
            return None
    
    def save_checkpoint(self):
        """保存当前检查点"""
        if not self.current_checkpoint or not self.checkpoint_file:
            return
        
        self.current_checkpoint.last_update = datetime.now().isoformat()
        
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.current_checkpoint), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存检查点失败: {e}")
    
    def update_progress(
        self,
        note_id: Optional[str] = None,
        notes_count: int = 0,
        comments_count: int = 0,
        page: Optional[int] = None,
        completed: bool = False,
        error_increment: int = 0
    ):
        """
        更新爬取进度
        
        Args:
            note_id: 帖子ID
            notes_count: 增加的帖子数
            comments_count: 增加的评论数
            page: 当前页码
            completed: 是否完成
            error_increment: 错误计数增量
        """
        if not self.current_checkpoint:
            return
        
        if note_id and note_id not in self.current_checkpoint.crawled_ids:
            self.current_checkpoint.crawled_ids.append(note_id)
        
        self.current_checkpoint.total_notes_crawled += notes_count
        self.current_checkpoint.total_comments_crawled += comments_count
        self.current_checkpoint.error_count += error_increment
        
        if page is not None:
            self.current_checkpoint.current_page = page
        
        if completed:
            self.current_checkpoint.completed = True
        
        # 每更新10次保存一次检查点
        if self.current_checkpoint.total_notes_crawled % 10 == 0 or completed:
            self.save_checkpoint()
    
    def is_crawled(self, note_id: str) -> bool:
        """
        检查内容是否已爬取
        
        Args:
            note_id: 帖子ID
            
        Returns:
            bool: 如果已爬取返回True
        """
        if not self.current_checkpoint:
            return False
        return note_id in self.current_checkpoint.crawled_ids
    
    def get_crawled_ids(self) -> Set[str]:
        """
        获取已爬取的ID集合
        
        Returns:
            Set[str]: 已爬取的ID集合
        """
        if not self.current_checkpoint:
            return set()
        return set(self.current_checkpoint.crawled_ids)
    
    def list_checkpoints(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有检查点
        
        Args:
            platform: 可选的平台过滤
            
        Returns:
            List[Dict]: 检查点信息列表
        """
        checkpoints = []
        
        for file in sorted(self.checkpoint_dir.glob("*.json"), reverse=True):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        continue
                    
                    if platform and data.get('platform') != platform:
                        continue
                    
                    checkpoint_id = data.get('checkpoint_id') or file.stem
                    checkpoints.append({
                        'id': checkpoint_id,
                        'file': file.name,
                        'platform': data.get('platform'),
                        'crawler_type': data.get('crawler_type'),
                        'keywords': data.get('keywords'),
                        'total_notes': data.get('total_notes_crawled', 0),
                        'total_comments': data.get('total_comments_crawled', 0),
                        'current_page': data.get('current_page', 1),
                        'completed': data.get('completed', False),
                        'last_update': data.get('last_update'),
                        'error_count': data.get('error_count', 0)
                    })
            except Exception as e:
                print(f"读取检查点文件 {file} 失败: {e}")
                continue
        
        return checkpoints
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        删除检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            bool: 是否成功删除
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        try:
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"删除检查点失败: {e}")
            return False
    
    def get_current_page(self) -> int:
        """获取当前页码"""
        if not self.current_checkpoint:
            return 1
        return self.current_checkpoint.current_page
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取当前检查点统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.current_checkpoint:
            return {}
        
        return {
            'platform': self.current_checkpoint.platform,
            'crawler_type': self.current_checkpoint.crawler_type,
            'keywords': self.current_checkpoint.keywords,
            'total_notes_crawled': self.current_checkpoint.total_notes_crawled,
            'total_comments_crawled': self.current_checkpoint.total_comments_crawled,
            'current_page': self.current_checkpoint.current_page,
            'completed': self.current_checkpoint.completed,
            'error_count': self.current_checkpoint.error_count,
            'last_update': self.current_checkpoint.last_update,
            'crawled_ids_count': len(self.current_checkpoint.crawled_ids)
        }


# 全局检查点管理器实例
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """获取全局检查点管理器实例"""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager
