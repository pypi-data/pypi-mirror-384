"""应用样式定义"""

CSS = """
/* 主容器样式 */
.chat-container {
    height: 100%;
    width: 100%;
}

.chat-header {
    height: 2;
    background: $primary;
    color: $text;
    text-align: center;
    padding: 0 1;
}

.chat-main {
    height: 1fr;
    width: 100%;
}

/* 模型选择器区域 - 占比2/12 */
#model-selector {
    height: 1fr;
    min-height: 5;
    border: solid $primary;
    margin: 0 0;
    padding: 0;
}

/* 聊天历史区域 - 占比7/12 */
.chat-history {
    height: 9fr;
    border: solid $secondary;
    margin: 0 1;
    padding: 1;
}

/* 输入框区域 - 占比3/12 */
.chat-input-container {
    height: 2fr;
    min-height: 10;
    border: solid $primary;
    margin: 0 1 1 1;
    padding: 1;
}

/* 消息样式 - 减少间距，自适应高度 */
.message-container {
    margin-bottom: 1;
    padding: 0 1;
    border-left: solid $accent;
    width: 100%;
    height: auto;
}

.user-message {
    border-left: solid $primary;
}

.assistant-message {
    border-left: solid $success;
}

.message-header {
    text-style: bold;
    margin-bottom: 0;
    margin-top: 0;
    padding: 0;
    height: auto;
    width: 100%;
}

.message-content {
    margin-left: 1;
    margin-bottom: 0;
    margin-top: 0;
    padding: 0;
    width: 100%;
    max-width: 100%;
    height: auto;
    text-wrap: wrap;
    overflow: auto;
}

/* 工具调用样式 - 减少间距 */
.tool-call-container {
    margin: 1 0;
    padding: 1;
    border: solid $warning;
    background: $surface;
    width: 100%;
    height: auto;
}

.tool-header {
    text-style: bold;
    margin-bottom: 1;
    height: auto;
    width: 100%;
}

.tool-args, .tool-result {
    margin-left: 1;
    margin-bottom: 1;
    padding: 0 1;
    background: $panel;
    width: 100%;
    max-width: 100%;
    height: auto;
    text-wrap: wrap;
    overflow: auto;
}

/* 消息操作区域样式 */
.message-actions {
    height: auto;
    margin: 0;
    padding: 0;
    width: 100%;
}

/* Token统计样式 */
.token-stats {
    height: auto;
    margin: 0;
    padding: 0;
    width: 100%;
}

/* 展开按钮样式 */
.expand-button {
    margin: 0 0 0 1;
    width: auto;
    height: 1;
    background: $accent;
    color: $text;
    border: none;
    text-align: center;
}

.expand-button:hover {
    background: $primary;
}

/* 复制按钮样式 */
.copy-button {
    margin: 0 0 0 1;
    width: auto;
    height: 1;
    background: $primary;
    color: $text;
    border: none;
    text-align: center;
    min-width: 8;
}

.copy-button:hover {
    background: $success 80%;
}

/* 输入区域样式 - 适应3fr高度 */
.input-row {
    height: 1fr;
    width: 100%;
    margin: 0;
}

.message-input {
    width: 1fr;
    height: 1fr;
    border: solid $primary;
    margin-right: 1;
    min-width: 30vw;
    max-width: 80vw;
}

.input-buttons {
    width: auto;
    height: 1fr;
    margin-left: 0;
    min-width: 12vw;
    max-width: 25vw;
}

.input-buttons Button {
    width: 1fr;
    height: 1fr;
    margin-right: 0;
    min-width: 4vw;
    max-width: 12vw;
    padding: 0 0;
}

.input-buttons Button:last-child {
    margin-right: 0;
}

/* 模型选择器样式 - 适应2fr高度 */
.model-selector-row {
    height: 1fr;
    width: 100%;
    margin: 0;
}

.model-label {
    width: 8;
    height: 1fr;
    text-align: right;
    margin-right: 1;
}

.model-select {
    width: 1fr;
    height: 1fr;
    margin-right: 1;
}

.model-selector-row Button {
    width: auto;
    min-width: 8;
    height: 1fr;
    min-height: 3;
    margin-left: 1;
    padding: 0 1;
}

/* 工具列表弹窗样式 - 优化间距 */
.tools-modal {
    width: 100%;
    height: 100%;
    background: $surface;
    border: solid $primary;
    margin: 0;
}

.tools-content {
    width: 100%;
    height: 100%;
    padding: 1;
}

.modal-title {
    text-align: center;
    text-style: bold;
    height: 2;
    margin-bottom: 1;
}

.tools-list {
    height: 1fr;
    border: solid $secondary;
    margin-bottom: 1;
    padding: 1;
    width: 100%;
}

.tool-item {
    margin-bottom: 1;
    padding: 1;
    border: solid $accent;
    background: $surface; /* 提升文字对比度 */
    height: auto;
}

/* 选中工具项高亮：绿色边框更直观 */
.tool-item.tool-item-selected {
    border: solid $success;
}

/* 工具项内控件可见性与布局优化 */
.tool-item Checkbox {
    width: auto;
    height: auto;
}
.tool-item-header {
    height: auto;
    margin-bottom: 1;
}
.tool-item .tool-item-title {
    color: $text;
    text-style: bold;
    margin-left: 1;
    width: 1fr; /* 保证标题占据可视宽度 */
}
.tool-item .tool-item-info {
    color: $text;
    margin-top: 1;
    text-wrap: wrap;
}

.tool-item .tool-item-desc {
    color: $text;
    margin-top: 1;
    text-wrap: wrap;
}

.tool-item .tool-item-params {
    color: $text;
    text-wrap: wrap;
}

/* 折叠容器样式 */
.tool-item .tool-item-details {
    width: 100%;
    margin-top: 1;
    border: solid $secondary;
    background: $panel;
}

.tool-item .tool-item-header {
    width: 100%;
}

/* 历史会话弹窗样式 */
.session-history-modal {
    width: 100%;
    height: 100%;
    background: $surface;
    border: solid $primary;
    margin: 0;
}

.session-history-content {
    width: 100%;
    height: 100%;
    padding: 1;
}

.session-list {
    height: 1fr;
    border: solid $secondary;
    margin-bottom: 1;
    padding: 1;
}

.session-item-content {
        padding: 1;
        margin-bottom: 1;
        border: solid $accent;
        background: $panel;
    }

.session-item-content:hover {
    background: $primary 20%;
}

.session-item-content.selected {
    background: $primary 40%;
    border-left: thick $accent;
}

/* 焦点状态样式 */
SessionItemWidget:focus .session-item-content {
    border: thick $success;
    background: $success 10%;
}

SessionItemWidget.focused .session-item-content {
    border: thick $success;
    background: $success 10%;
}

.modal-buttons {
    height: auto;
    margin-top: 1;
}

.modal-buttons Button {
    margin-right: 1;
}

.empty-message {
    text-align: center;
    padding: 2;
    color: $text-muted;
}

/* 上下文弹窗样式 */
.context-modal {
    width: 100%;
    height: 100%;
    background: $surface;
    border: solid $primary;
    margin: 0;
}

.context-content {
    width: 100%;
    height: 100%;
    padding: 1;
}

.context-sections {
    height: 1fr;
    border: solid $secondary;
    margin-bottom: 1;
    padding: 1;
}

.context-block {
    margin-bottom: 1;
    padding: 1;
    border: solid $accent;
    background: $panel;
}

/* 图表相关样式：确保容器和绘图组件有可视高度 */
.chart-content {
    width: 100%;
    height: 1fr;
    min-height: 15;
    border: none;
}

.chart-widget {
    width: 100%;
    height: 1fr;
    min-height: 15;
}

/* 聊天消息中的图表：限制为聊天区域的80%宽高 */
#chat-chart-content {
    width: 100%;
    height: 100%;
    min-height: 15;
    border: none;
    align: center middle;
}

#chat-plot {
    width: 100%;
    height: 100%;
    min-height: 15;
}

/* 工具调用结果的居中包装容器 */
.tool-result-wrapper {
    width: 100%;
    height: auto;
    align: center middle;
}

/* 通用隐藏样式：用于隐藏字段选择器等 */
.hidden {
    display: none;
}
"""