"""数据模型和会话管理

包含聊天会话的数据结构和会话管理功能。
"""

import json
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ChatSession:
    """聊天会话数据结构"""
    session_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Dict[str, Any]]
    
    @classmethod
    def create_new(cls, title: str = None) -> 'ChatSession':
        """创建新会话"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_id = str(uuid.uuid4())
        if not title:
            title = f"会话 {datetime.now().strftime('%m-%d %H:%M')}"
        
        return cls(
            session_id=session_id,
            title=title,
            created_at=now,
            updated_at=now,
            messages=[]
        )
    
    def update_messages(self, messages: List[Dict[str, Any]]):
        """更新消息列表"""
        self.messages = messages
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_display_title(self) -> str:
        """获取显示标题"""
        if len(self.messages) > 0:
            # 尝试从第一条用户消息生成标题
            for msg in self.messages:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if content:
                        # 取前20个字符作为标题
                        title = content[:20]
                        if len(content) > 20:
                            title += "..."
                        return title
        return self.title


class SessionManager:
    """会话管理器"""
    
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            # 使用用户主目录下的.ketacli文件夹
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".ketacli", "chat_sessions")
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_session(self, session: ChatSession) -> bool:
        """保存会话"""
        try:
            file_path = os.path.join(self.storage_dir, f"{session.session_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(session), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存会话失败: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[ChatSession]:
        """加载会话"""
        try:
            file_path = os.path.join(self.storage_dir, f"{session_id}.json")
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ChatSession(**data)
        except Exception as e:
            print(f"加载会话失败: {e}")
            return None
    
    def list_sessions(self) -> List[ChatSession]:
        """列出所有会话"""
        sessions = []
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # 移除.json后缀
                    session = self.load_session(session_id)
                    if session:
                        sessions.append(session)
            
            # 按更新时间倒序排列
            sessions.sort(key=lambda x: x.updated_at, reverse=True)
        except Exception as e:
            print(f"列出会话失败: {e}")
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            file_path = os.path.join(self.storage_dir, f"{session_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"删除会话失败: {e}")
            return False