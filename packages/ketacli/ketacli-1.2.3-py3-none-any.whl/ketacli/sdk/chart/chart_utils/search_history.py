import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class SearchHistoryManager:
    """搜索历史管理器 - 负责在本地文件中保存和读取搜索历史"""
    
    def __init__(self, max_history_size: int = 100):
        """初始化搜索历史管理器
        
        Args:
            max_history_size: 最大历史记录数量，超过此数量时会删除最旧的记录
        """
        self.max_history_size = max_history_size
        self.history_dir = Path.home() / ".keta"
        self.history_file = self.history_dir / "search_history.json"
        self._ensure_history_dir()
        
    def _ensure_history_dir(self):
        """确保历史记录目录存在"""
        try:
            self.history_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"创建历史记录目录失败: {e}")
            
    def _load_history(self) -> List[Dict]:
        """从文件加载搜索历史
        
        Returns:
            搜索历史列表，每个元素包含 id, query, timestamp 字段
        """
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    # 确保数据格式正确
                    if isinstance(history_data, list):
                        return history_data
                    else:
                        return []
            else:
                return []
        except Exception as e:
            print(f"加载搜索历史失败: {e}")
            return []
            
    def _save_history(self, history_data: List[Dict]):
        """保存搜索历史到文件
        
        Args:
            history_data: 要保存的搜索历史列表
        """
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存搜索历史失败: {e}")
            
    def add_search(self, query: str) -> bool:
        """添加新的搜索记录
        
        Args:
            query: 搜索查询语句
            
        Returns:
            是否添加成功
        """
        if not query or not query.strip():
            return False
            
        try:
            history_data = self._load_history()
            
            # 检查是否已存在相同的查询，如果存在则更新时间戳
            query_stripped = query.strip()
            existing_index = None
            for i, item in enumerate(history_data):
                if item.get('query', '').strip() == query_stripped:
                    existing_index = i
                    break
                    
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if existing_index is not None:
                # 更新现有记录的时间戳并移到最前面
                existing_item = history_data.pop(existing_index)
                existing_item['timestamp'] = current_time
                history_data.insert(0, existing_item)
            else:
                # 添加新记录
                new_id = max([item.get('id', 0) for item in history_data], default=0) + 1
                new_record = {
                    "id": new_id,
                    "query": query_stripped,
                    "timestamp": current_time
                }
                history_data.insert(0, new_record)
                
            # 限制历史记录数量
            if len(history_data) > self.max_history_size:
                history_data = history_data[:self.max_history_size]
                
            # 重新分配ID以保持连续性
            for i, item in enumerate(history_data):
                item['id'] = i + 1
                
            self._save_history(history_data)
            return True
            
        except Exception as e:
            print(f"添加搜索历史失败: {e}")
            return False
            
    def get_search_history(self) -> List[Dict]:
        """获取搜索历史列表
        
        Returns:
            搜索历史列表，按时间倒序排列（最新的在前）
        """
        return self._load_history()
        
    def clear_history(self) -> bool:
        """清空搜索历史
        
        Returns:
            是否清空成功
        """
        try:
            if self.history_file.exists():
                self.history_file.unlink()
            return True
        except Exception as e:
            print(f"清空搜索历史失败: {e}")
            return False
            
    def remove_search(self, search_id: int) -> bool:
        """删除指定的搜索记录
        
        Args:
            search_id: 要删除的搜索记录ID
            
        Returns:
            是否删除成功
        """
        try:
            history_data = self._load_history()
            
            # 查找并删除指定ID的记录
            updated_history = [item for item in history_data if item.get('id') != search_id]
            
            if len(updated_history) < len(history_data):
                # 重新分配ID
                for i, item in enumerate(updated_history):
                    item['id'] = i + 1
                    
                self._save_history(updated_history)
                return True
            else:
                return False  # 没有找到要删除的记录
                
        except Exception as e:
            print(f"删除搜索历史失败: {e}")
            return False
            
    def search_in_history(self, keyword: str) -> List[Dict]:
        """在搜索历史中查找包含关键词的记录
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的搜索历史列表
        """
        if not keyword:
            return self.get_search_history()
            
        try:
            history_data = self._load_history()
            keyword_lower = keyword.lower()
            
            matched_history = [
                item for item in history_data 
                if keyword_lower in item.get('query', '').lower()
            ]
            
            return matched_history
            
        except Exception as e:
            print(f"搜索历史记录失败: {e}")
            return []
            
    def get_recent_searches(self, count: int = 10) -> List[Dict]:
        """获取最近的搜索记录
        
        Args:
            count: 要获取的记录数量
            
        Returns:
            最近的搜索历史列表
        """
        history_data = self._load_history()
        return history_data[:count]
        
    def export_history(self, export_path: Optional[str] = None) -> bool:
        """导出搜索历史到指定文件
        
        Args:
            export_path: 导出文件路径，如果为None则导出到当前目录
            
        Returns:
            是否导出成功
        """
        try:
            if export_path is None:
                export_path = f"search_history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
            history_data = self._load_history()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            print(f"导出搜索历史失败: {e}")
            return False
            
    def import_history(self, import_path: str, merge: bool = True) -> bool:
        """从文件导入搜索历史
        
        Args:
            import_path: 导入文件路径
            merge: 是否与现有历史合并，False则覆盖现有历史
            
        Returns:
            是否导入成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
                
            if not isinstance(imported_data, list):
                print("导入文件格式不正确")
                return False
                
            if merge:
                # 合并历史记录
                existing_history = self._load_history()
                
                # 创建查询到记录的映射，避免重复
                query_map = {item.get('query', '').strip(): item for item in existing_history}
                
                # 添加导入的记录
                for item in imported_data:
                    query = item.get('query', '').strip()
                    if query and query not in query_map:
                        query_map[query] = item
                        
                # 转换回列表并按时间排序
                merged_history = list(query_map.values())
                merged_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                # 限制数量并重新分配ID
                if len(merged_history) > self.max_history_size:
                    merged_history = merged_history[:self.max_history_size]
                    
                for i, item in enumerate(merged_history):
                    item['id'] = i + 1
                    
                self._save_history(merged_history)
            else:
                # 直接覆盖
                # 重新分配ID
                for i, item in enumerate(imported_data):
                    item['id'] = i + 1
                    
                self._save_history(imported_data)
                
            return True
            
        except Exception as e:
            print(f"导入搜索历史失败: {e}")
            return False