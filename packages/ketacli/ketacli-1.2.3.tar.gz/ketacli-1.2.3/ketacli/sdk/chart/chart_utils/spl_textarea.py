"""SPL多行文本输入组件 - 支持实时自动补全功能"""

import pyperclip
from textual.widgets import TextArea
from textual.message import Message
from textual.binding import Binding



# SPL命令列表
SPL_COMMANDS = ['search', 'search2', 'stats', 'eval', 'where', 'fields', 'table', 'sort', 'head', 'tail',
                'top', 'rare', 'chart', 'timechart', 'bin', 'rex', 'replace', 'rename',
                'dedup', 'uniq', 'append', 'appendcols', 'join', 'lookup', 'inputlookup', 'outputlookup',
                'mstats', 'tstats', 'pivot', 'streamstats', 'eventstats', 'diff', 'set', 'map', 'foreach', 
                'addinfo', 'addtotals', 'fillnull', 'filldown',
                'makemv', 'mvexpand', 'nomv', 'convert', 'format']

# SPL函数列表
SPL_FUNCTIONS = ['count', 'count()', 'sum', 'sum()', 'avg', 'avg()', 'mean', 'median', 'mode', 'min', 'max', 'range', 'stdev', 'var',
                 'first', 'first()', 'last', 'last()', 'earliest', 'earliest()', 'latest', 'latest()', 'values', 'values()', 'list', 'list()', 'dc', 'estdc', 'exactperc',
                 'perc', 'upperperc', 'lowerperc', 'rate', 'sparkline', 'c', 'earliest_time',
                 'latest_time', 'per_day', 'per_hour', 'per_minute', 'per_second']

# SPL操作符列表
SPL_OPERATORS = ['AND', 'OR', 'NOT', 'and', 'or', 'not', 'by', 'as', 'in', 'over', 'span', 'bins',
                 'minspan', 'maxspan', 'start', 'end', 'starttime', 'endtime', 'timeformat',
                 'limit', 'maxresults', 'maxtime', 'timeout']

# SPL字段列表
SPL_FIELDS = ['_time', '_raw', '_indextime', '_kv', '_meta', '_sourcetype',
              '_source', '_index', 'repo', 'sourcetype', 'origin', 'host_ip',
              'host', 'source', 'timestamp']

# 正则表达式模式
REGEX_FUNCTION = r"(\w+\(.*\))"


class SearchRequested(Message):
    """搜索请求消息"""
    def __init__(self, spl_text: str):
        super().__init__()
        self.spl_text = spl_text


class SPLSuggester:
    """SPL自动补全建议器"""
    
    def __init__(self):
        self.keywords = SPL_COMMANDS + SPL_FUNCTIONS + SPL_OPERATORS + SPL_FIELDS
    
    def get_suggestions(self, partial_word):
        """获取匹配的建议"""
        if not partial_word:
            return []
        
        suggestions = []
        partial_lower = partial_word.lower()
        
        for keyword in self.keywords:
            if keyword.lower().startswith(partial_lower):
                suggestions.append(keyword)
        
        return sorted(suggestions, key=len)[:10]  # 最多返回10个建议，按长度排序


class SPLTextArea(TextArea):
    """SPL多行文本输入组件 - 支持自动补全功能"""
    
    # 添加输入框专用的快捷键绑定
    BINDINGS = [
        Binding("ctrl+backspace", "clear_input", "清空输入"),
        Binding("shift+enter", "insert_newline", "插入换行"),
        Binding("ctrl+slash", "toggle_comment", "注释/取消注释"),
    ]
    
    def __init__(self, suggester=None, **kwargs):
        super().__init__(**kwargs)
        self.suggester = suggester or SPLSuggester()
        self.spl_input = []
        self.spl_input_cursor = 0
        self.suggestions = []  # 所有匹配的建议
        self.suggestion_index = -1
        self.show_suggestions = False
        self.current_suggestion = ""
        self.suggestion_start_pos = 0
        self.spl_input = ""
        self.language = "sql"
        
    def on_mount(self) -> None:
        """组件挂载时的初始化"""
        pass

    def insert_newline(self) -> None:
        """插入换行符"""
        cursor_pos = self.cursor_location
        lines = self.text.split('\n')
        
        if cursor_pos[0] < len(lines):
            current_line = lines[cursor_pos[0]]
            # 在当前光标位置插入换行符
            new_line = current_line[:cursor_pos[1]] + "\n" + current_line[cursor_pos[1]:]
            lines[cursor_pos[0]] = new_line
            self.text = '\n'.join(lines)
            # 将光标移动到新行的开始位置
            self.cursor_location = (cursor_pos[0] + 1, 0)
        else:
            # 如果光标位置超出范围，则在文本末尾添加换行符
            self.text += "\n"
            # 移动光标到新行
            new_lines = self.text.split('\n')
            self.cursor_location = (len(new_lines) - 1, 0)
        
    def on_text_area_changed(self, event) -> None:
        """文本变化时的处理"""
        # event是TextArea.Changed事件对象，包含text_area属性
        self.spl_input = list(event.text_area.text)
        self.spl_input_cursor = len(event.text_area.text)
        
        # 实时获取自动补全建议
        self._update_auto_suggestion()
    
    def watch_text(self, text: str) -> None:
        """监听文本变化"""
        self.spl_input = list(text)
        self.spl_input_cursor = len(text)
        
        # 实时获取自动补全建议
        self._update_auto_suggestion()
    
    def _update_auto_suggestion(self):
        """更新自动补全建议"""
        current_word, start, end = self.get_current_word()
        
        if current_word and len(current_word) > 0:
            suggestions = self.get_suggestions(current_word)
            if suggestions:
                self.suggestions = suggestions  # 保存所有建议
                self.current_suggestion = suggestions[0]  # 第一个作为默认选择
                self.suggestion_start_pos = start
                self.show_suggestions = True
            else:
                self.suggestions = []
                self.current_suggestion = ""
                self.show_suggestions = False
        else:
            self.suggestions = []
            self.current_suggestion = ""
            self.show_suggestions = False
            
        # 更新建议显示
        self._update_suggestion_display()
            
    def get_current_word(self):
        """获取光标位置的当前单词"""
        text = self.text
        cursor_pos = self.cursor_location
        
        # 获取当前行的文本
        lines = text.split('\n')
        if cursor_pos[0] >= len(lines):
            return "", 0, 0
            
        current_line = lines[cursor_pos[0]]
        col_pos = cursor_pos[1]
        
        # 找到当前单词的开始和结束位置
        start = col_pos
        end = col_pos
        
        # 向前找到单词开始（包括下划线）
        while start > 0 and (current_line[start - 1].isalnum() or current_line[start - 1] == '_'):
            start -= 1
            
        # 向后找到单词结束（包括下划线）
        while end < len(current_line) and (current_line[end].isalnum() or current_line[end] == '_'):
            end += 1
            
        return current_line[start:col_pos], start, end
        
    def get_suggestions(self, partial_word):
        """根据部分单词获取建议"""
        return self.suggester.get_suggestions(partial_word)
        
    def insert_suggestion(self, suggestion):
        """插入选中的建议"""
        current_word, start, end = self.get_current_word()
        cursor_pos = self.cursor_location
        
        # 获取当前行和替换文本
        lines = self.text.split('\n')
        if cursor_pos[0] >= len(lines):
            return
            
        current_line = lines[cursor_pos[0]]
        new_line = current_line[:start] + suggestion + current_line[cursor_pos[1]:]
        lines[cursor_pos[0]] = new_line
        
        # 更新文本
        self.text = '\n'.join(lines)
        
        # 移动光标到建议词的末尾
        new_cursor_pos = (cursor_pos[0], start + len(suggestion))
        self.cursor_location = new_cursor_pos
        self.show_suggestions = False
        
    def on_key(self, event) -> None:
        """处理键盘事件"""
        key = event.key
        
        # 管道符处理 - 自动换行并添加空格
        if key == "|" or (hasattr(event, 'character') and event.character == "|"):
            cursor_pos = self.cursor_location
            lines = self.text.split('\n')
            if cursor_pos[0] < len(lines):
                current_line = lines[cursor_pos[0]]
                # 在光标位置插入换行符和管道符
                new_line = current_line[:cursor_pos[1]] + "\n| "
                if cursor_pos[1] < len(current_line):
                    new_line += current_line[cursor_pos[1]:]
                lines[cursor_pos[0]] = new_line
                self.text = '\n'.join(lines)
                # 移动光标到管道符后的空格位置
                self.cursor_location = (cursor_pos[0] + 1, 2)
            event.prevent_default()
            return
        
        # Ctrl+Enter键处理 - 执行搜索
        if key == "enter":
            spl_text = self.get_spl_text()
            if spl_text.strip():
                # 发送搜索请求消息
                self.notify(f"开始搜索: {spl_text[:50]}...", severity="info")
                self.post_message(SearchRequested(spl_text))
            else:
                self.notify("搜索文本为空", severity="error")
            event.prevent_default()
            
            return
            
        # 右键处理 - 应用当前自动补全建议
        if key == "right" and self.show_suggestions and self.current_suggestion:
            self._apply_current_suggestion()
            event.prevent_default()
            return
            
        # Tab键处理 - 接受当前建议
        if key == "tab" and self.show_suggestions and self.suggestions:
            if 0 <= self.suggestion_index < len(self.suggestions):
                self.insert_suggestion(self.suggestions[self.suggestion_index])
            event.prevent_default()
            return
            
        # 其他键盘事件让TextArea组件自动处理
    
    def toggle_line_comment(self):
        """切换当前行的注释状态"""
        cursor_pos = self.cursor_location
        lines = self.text.split('\n')
        
        if cursor_pos[0] < len(lines):
            current_line = lines[cursor_pos[0]]
            stripped_line = current_line.lstrip()
            
            # 检查是否已经被注释
            if stripped_line.startswith('//'):
                # 取消注释 - 移除 // 和后面的空格（如果有）
                comment_start = current_line.find('//')
                new_line = current_line[:comment_start]
                remaining = current_line[comment_start + 2:]
                # 如果 // 后面有空格，也一起移除
                if remaining.startswith(' '):
                    remaining = remaining[1:]
                new_line += remaining
                lines[cursor_pos[0]] = new_line
                # 调整光标位置
                new_cursor_col = max(0, cursor_pos[1] - 3)  # 减去 "// " 的长度
            else:
                # 添加注释
                indent = len(current_line) - len(stripped_line)
                new_line = current_line[:indent] + '// ' + stripped_line
                lines[cursor_pos[0]] = new_line
                # 调整光标位置
                new_cursor_col = cursor_pos[1] + 3  # 加上 "// " 的长度
            
            self.text = '\n'.join(lines)
            self.cursor_location = (cursor_pos[0], new_cursor_col)
    
    def on_click(self, event) -> None:
        """处理鼠标点击事件"""
        # 右键应用第一个建议
        if event.button == 2 and self.current_suggestion and self.show_suggestions:  # 右键
            current_word, start, end = self.get_current_word()
            if current_word and self.current_suggestion.startswith(current_word):
                self._apply_current_suggestion()
                event.prevent_default()
                return
    
    def _apply_current_suggestion(self):
        """应用当前的自动补全建议"""
        if not self.current_suggestion:
            return
            
        current_word, start, end = self.get_current_word()
        cursor_pos = self.cursor_location
        
        # 获取当前行和替换文本
        lines = self.text.split('\n')
        if cursor_pos[0] >= len(lines):
            return
            
        current_line = lines[cursor_pos[0]]
        # 替换当前单词为完整的建议
        new_line = current_line[:start] + self.current_suggestion + current_line[cursor_pos[1]:]
        lines[cursor_pos[0]] = new_line
        
        # 更新文本
        self.text = '\n'.join(lines)
        
        # 移动光标到建议词的末尾
        new_cursor_pos = (cursor_pos[0], start + len(self.current_suggestion))
        self.cursor_location = new_cursor_pos
        
        # 清除建议状态
        self.current_suggestion = ""
        self.show_suggestions = False
    
    def _update_suggestion_display(self):
        """更新建议显示"""
        # 查找建议显示组件并更新
        try:
            suggestion_display = self.app.query_one("#suggestion-display")
            if self.suggestions and self.show_suggestions:
                current_word, start, end = self.get_current_word()
                if current_word:
                    # 显示所有匹配的建议，用逗号分隔
                    suggestion_texts = []
                    for i, suggestion in enumerate(self.suggestions[:10]):  # 最多显示5个建议
                        if suggestion.startswith(current_word):
                            suggestion_suffix = suggestion[len(current_word):]
                            if i == 0:  # 第一个建议高亮显示
                                suggestion_texts.append(f"[bold cyan]{current_word}{suggestion_suffix}[/bold cyan]")
                            else:
                                suggestion_texts.append(f"[dim]{current_word}{suggestion_suffix}[/dim]")
                    
                    if suggestion_texts:
                        display_text = " | ".join(suggestion_texts) + " (右键应用第一个)"
                        suggestion_display.update(display_text)
                    else:
                        suggestion_display.update("")
                else:
                    suggestion_display.update("")
            else:
                suggestion_display.update("")
        except Exception:
            # 如果找不到建议显示组件，忽略错误
            pass
            
    # SearchRequested消息类已移到模块级别
        
    def get_spl_text(self):
        """获取SPL文本"""
        return self.text
        
    def set_spl_text(self, text):
        """设置SPL文本"""
        # 处理Rich Text对象，提取纯文本
        if hasattr(text, 'plain'):
            text = text.plain
        elif not isinstance(text, str):
            text = str(text)
        
        # 去除每行末尾的空格
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        cleaned_text = '\n'.join(cleaned_lines)
        
        self.text = cleaned_text
        
    def clear_input(self):
        """清空输入"""
        self.text = ""
        
    def handle_paste(self):
        """处理粘贴操作"""
        try:
            clipboard_content = pyperclip.paste()
            self.text += clipboard_content
        except Exception:
            pass
    
    def action_clear_input(self) -> None:
        """清空输入"""
        self.clear_input()
        
    def action_insert_newline(self) -> None:
        """插入换行符"""
        self.insert_newline()
        
    def action_toggle_comment(self) -> None:
        """切换注释"""
        self.toggle_line_comment()