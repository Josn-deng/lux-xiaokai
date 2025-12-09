from PyQt5 import QtWidgets, QtCore, QtGui
import os
from typing import Optional

try:
    import markdown as _markdown
except ImportError:  # 运行环境尚未安装 markdown 包时的降级处理
    _markdown = None

# Pygments 用于代码高亮（可选）
try:
    import pygments.formatters
except ImportError:
    pygments = None


class ChatMessageWidget(QtWidgets.QFrame):
    """可渲染 Markdown 的聊天消息组件，自动根据内容调整高度。"""

    def __init__(self, role: str, raw_text: str, max_width: int, user_style: str, ai_style: str, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.role = role
        self.raw_text = raw_text
        # 使用更低的最小宽度以支持超短消息紧凑显示
        self.max_width = max(80, max_width)  # 提高最小宽度到80，确保可读性
        # 代码块增强相关状态
        self._code_blocks = []  # list[dict]: {'html': str, 'plain': str, 'lines': int, 'collapsed': bool}
        self._base_html = ""  # 最近一次渲染的原始（未增强）HTML
        self._enhanced_html = ""  # 包含工具与折叠包装后的HTML
        self._collapse_line_threshold = 20
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        # 去除自身背景，避免形成白色矩形遮挡
        self.setStyleSheet("QFrame{background:transparent;}")
        self.setAttribute(getattr(QtCore.Qt, 'WA_TranslucentBackground'), True)
        # 恢复可扩展策略：由父布局与 max_width 控制最终显示宽度
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # 角色标识
        self.role_label = QtWidgets.QLabel("U" if role == "user" else "AI")
        self.role_label.setFixedSize(30, 30)
        self.role_label.setAlignment(getattr(QtCore.Qt, 'AlignCenter'))
        self.role_label.setStyleSheet("""
            QLabel {border-radius:14px; color:white; font-weight:bold; font-size:12px;}
        """)
        if role == 'user':
            # 保持用户头像样式不变
            self.role_label.setStyleSheet("""QLabel {background-color:#3498db; border-radius:14px; color:white; font-weight:bold; font-size:12px;}""")
        else:
            # AI 头像使用项目图标（Conduct.png），若找不到则回退到绿色背景的文字标签
            try:
                # message_widget.py is in src/ui/bubbles -> go up two levels to reach src/icons
                icon_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'icons', 'Conduct.png'))
                if os.path.exists(icon_path):
                    pix = QtGui.QPixmap(icon_path)
                    if not pix.isNull():
                        # 适配尺寸并设置为标签图像
                        keep_aspect = getattr(QtCore.Qt, 'KeepAspectRatio')
                        smooth = getattr(QtCore.Qt, 'SmoothTransformation')
                        scaled = pix.scaled(28, 28, keep_aspect, smooth)
                        self.role_label.setPixmap(scaled)
                        self.role_label.setScaledContents(True)
                        # 透明背景，圆角由外层绘制实现
                        self.role_label.setStyleSheet("QLabel{background:transparent;}")
                    else:
                        self.role_label.setStyleSheet("""QLabel {background-color:#27ae60; border-radius:14px; color:white; font-weight:bold; font-size:12px;}""")
                else:
                    self.role_label.setStyleSheet("""QLabel {background-color:#27ae60; border-radius:14px; color:white; font-weight:bold; font-size:12px;}""")
            except Exception:
                self.role_label.setStyleSheet("""QLabel {background-color:#27ae60; border-radius:14px; color:white; font-weight:bold; font-size:12px;}""")

        # 内容部件使用 QTextBrowser 支持基础 HTML，Markdown 转换后展示
        self.content = QtWidgets.QTextBrowser()
        self.content.setOpenExternalLinks(True)
        self.content.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content.setHorizontalScrollBarPolicy(getattr(QtCore.Qt, 'ScrollBarAlwaysOff'))
        self.content.setVerticalScrollBarPolicy(getattr(QtCore.Qt, 'ScrollBarAlwaysOff'))
        self.content.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # 宽度策略：设置最大宽度和最小宽度
        self.content.setMaximumWidth(self.max_width)
        # 设置合适的最小宽度，避免过小
        self.content.setMinimumWidth(min(100, self.max_width // 2))
        # 启用文本换行
        self.content.setWordWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)
        # 为内容区加上圆角并确保背景只在气泡内
        base_style = (user_style if role == 'user' else ai_style)
        # 如果用户传入的样式不包含 border-radius 或 background，则补齐一份默认值
        if 'border-radius' not in base_style:
            base_style = base_style.rstrip('}') + ' border-radius:18px;}'
        if 'background' not in base_style and 'background-color' not in base_style:
            base_style = base_style.rstrip('}') + ' background-color:rgba(255,255,255,0.9);}'
        self.content.setStyleSheet(base_style + "\nQTextBrowser{border:0px solid transparent;}\n")
        # 初始设置内容 - 使用纯文本模式以便支持流式输出
        self.content.setPlainText("")
        self.raw_text = ""
        # --- 流式输出相关属性需在首次访问前初始化 ---
        self.is_streaming = False
        self.stream_buffer = ""
        self.stream_timer = QtCore.QTimer(self)
        self.stream_timer.timeout.connect(self._flush_stream_buffer)
        self.stream_timer.setInterval(50)  # 50ms刷新间隔，模拟打字效果

        # 如果当前不是流式模式，直接渲染完整 Markdown 内容
        # （AI 消息的流式模式稍后通过 start_streaming() 启动）
        # 对于AI消息，即使是空文本也应初始化为Markdown格式
        if not self.is_streaming or raw_text == "":
            self.set_markdown(raw_text)

        if role == 'user':
            layout.addWidget(self.content)
            layout.addWidget(self.role_label)
        else:
            layout.addWidget(self.role_label)
            layout.addWidget(self.content)
        # 侧边附加宽度参考（用于 sizeHint 中留白），但不强制固定总宽
        self._side_extra = self.role_label.width() + layout.spacing()

        self._adjust_height()
        # 监听文档内容变化，自动调整高度（保护性访问）
        doc = self.content.document()
        if doc is not None and hasattr(doc, 'contentsChanged'):
            doc.contentsChanged.connect(self._on_contents_changed)



    def set_markdown(self, text: str):
        """设置要显示的 Markdown 文本，带代码高亮。"""
        # 如果正在流式输出，则将文本添加到流缓冲区
        if self.is_streaming:
            self.stream_text(text)
            return
            
        if _markdown:
            try:
                # 使用完整的 Markdown 扩展路径并配置 codehilite，输出 HTML5
                html = _markdown.markdown(
                    text,
                    extensions=[
                        'markdown.extensions.fenced_code',
                        'markdown.extensions.tables',
                        'markdown.extensions.codehilite',
                        'markdown.extensions.extra',
                        'markdown.extensions.nl2br',
                        'markdown.extensions.sane_lists',
                    ],
                    extension_configs={
                        'markdown.extensions.codehilite': {'guess_lang': False}
                    },
                    output_format='html'
                )
            except Exception:
                html = self._fallback_html(text)
        else:
            html = self._fallback_html(text)

        # 如果包含代码围栏但未成功渲染为 <pre>，进行简易降级包装以避免水平滚动
        if '```' in text and '<pre' not in html:
            lines = text.split('\n')
            collecting = False
            buffer = []
            code_segments = []
            for line in lines:
                if line.startswith('```') and not collecting:
                    collecting = True
                    buffer = []
                    continue
                if line.startswith('```') and collecting:
                    collecting = False
                    code_segments.append('\n'.join(buffer))
                    buffer = []
                    continue
                if collecting:
                    buffer.append(line)
            # 如果解析到代码段但未渲染 <pre>，在末尾追加一个降级代码块，保证可见且可换行
            for seg in code_segments:
                escaped = seg.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html += f"<div><pre>{escaped}</pre></div>"

        # 注入基础样式 + codehilite 样式（简化版）
        style_block = (
            "<style>"
            "pre {background:#2d2d2d; color:#ccc; padding:8px 10px; border-radius:6px; font-size:12px; white-space:pre-wrap; word-break:break-word; overflow-wrap:anywhere; overflow:hidden;}"
            "code {font-family:Consolas, monospace; white-space: pre-wrap; word-break: break-word;}"
            ".codehilite pre {background:#2d2d2d; color:#ccc; padding:8px 10px; border-radius:6px; white-space:pre-wrap; word-break:break-word; overflow-wrap:anywhere;}"
            ".codehilite .hll {background-color:#444}"
            "p {white-space: pre-wrap; margin: 0 0 0.6em 0;}"  # 减小段落底部空白避免额外高度
            "div {white-space: pre-wrap;}"
            "ul, ol {margin: 0.5em 0; padding-left: 2em;}"
            "li {margin: 0.2em 0;}"
            "strong {font-weight: bold;}"
            "em {font-style: italic;}"
            "</style>"
        )
        wrapped = f'<div style="white-space:pre-wrap; word-wrap:break-word; background:transparent;">{style_block}{html}</div>'
        self.raw_text = text
        self._base_html = wrapped
        # 增强代码块（复制 / 折叠）
        self._enhanced_html = self._enhance_code_blocks(wrapped)
        self.content.setHtml(self._enhanced_html)
        self._adjust_height()

    def _fallback_html(self, text: str) -> str:
        # 简易转义并支持一小部分 Markdown 语法（粗体/斜体/行内代码）以做降级显示
        import re
        safe = (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        # 行内代码： `code` -> <code>code</code>
        safe = re.sub(r'`([^`]+?)`', r'<code>\1</code>', safe)
        # 粗体： **bold** 或 __bold__
        safe = re.sub(r'\*\*([^\*]+?)\*\*', r'<strong>\1</strong>', safe)
        safe = re.sub(r'__([^_]+?)__', r'<strong>\1</strong>', safe)
        # 斜体： *italic* 或 _italic_
        safe = re.sub(r'\*([^\*]+?)\*', r'<em>\1</em>', safe)
        safe = re.sub(r'_([^_]+?)_', r'<em>\1</em>', safe)
        # 换行
        safe = safe.replace('\n', '<br/>')
        return safe

    def _adjust_height(self):
        """根据文档内容计算高度"""
        doc = self.content.document()
        if doc is None:
            return
            
        # 使用实际可用宽度计算高度
        available_width = self.max_width - 10  # 留出边距
        doc.setTextWidth(available_width)
        
        # 获取文档的理想尺寸
        doc_layout = doc.documentLayout()
        if doc_layout is not None:
            ideal_size = doc_layout.documentSize()
            content_height = int(ideal_size.height())
        else:
            # 回退方案：使用默认方式计算高度
            sz = doc.size()
            content_height = int(sz.height())
        
        # 计算最终高度，包含适当的内边距
        final_height = content_height + 20  # 上下内边距
        
        # 设置最小高度确保可读性
        min_height = 45
        if final_height < min_height:
            final_height = min_height
            
        # 应用高度
        self.content.setFixedHeight(final_height)
        self.setMinimumHeight(final_height)
        
        # 更新布局
        self.updateGeometry()

    # ---------------- 代码块增强与交互 ----------------
    def _enhance_code_blocks(self, html: str) -> str:
        """扫描 <pre> 代码块并注入复制与折叠按钮包装。返回增强后的 HTML。"""
        import re, html as html_mod
        self._code_blocks.clear()
        # 匹配 <pre>...</pre>（允许内部含任何内容）
        pattern = re.compile(r'<pre>(.*?)</pre>', re.DOTALL)
        idx = 0
        def repl(m):
            nonlocal idx
            inner = m.group(1)
            # Plain 版本：去除多余标签（简单方式）
            plain = re.sub(r'<[^>]+>', '', inner)
            # 反转义 HTML 实体
            plain_unescaped = html_mod.unescape(plain)
            line_count = plain_unescaped.count('\n') + 1
            collapsed = line_count > self._collapse_line_threshold
            self._code_blocks.append({
                'html': inner,
                'plain': plain_unescaped,
                'lines': line_count,
                'collapsed': collapsed
            })
            tools_html = (
                f'<div class="code-tools">'
                f'<a href="copy://{idx}" class="copy-btn">复制</a>'
                f'<a href="toggle://{idx}" class="toggle-btn">{"展开" if collapsed else "折叠"}</a>'
                f'</div>'
            )
            content_div = (
                f'<div class="code-content{" collapsed" if collapsed else ""}"><pre>{inner}</pre></div>'
            )
            wrapper = f'<div class="code-block-wrapper" data-idx="{idx}">{tools_html}{content_div}</div>'
            idx += 1
            return wrapper
        enhanced = pattern.sub(repl, html)
        # 若未捕获任何 <pre> 但原始文本包含 fenced code，则构造单一代码块包装（降级模式）
        if len(self._code_blocks) == 0 and '```' in self.raw_text:
            # 提取 fenced 内容
            raw = self.raw_text
            start = raw.find('```')
            lang_line_end = raw.find('\n', start + 3)
            if lang_line_end == -1:
                lang_line_end = start
            end = raw.rfind('```')
            code_body = raw[lang_line_end + 1:end].strip() if end > lang_line_end else ''
            lines = code_body.count('\n') + 1 if code_body else 1
            collapsed = lines > self._collapse_line_threshold
            self._code_blocks.append({'html': code_body.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'),
                                      'plain': code_body,
                                      'lines': lines,
                                      'collapsed': collapsed})
            tools_html = (
                f'<div class="code-tools">'
                f'<a href="copy://0" class="copy-btn">复制</a>'
                f'<a href="toggle://0" class="toggle-btn">{"展开" if collapsed else "折叠"}</a>'
                f'</div>'
            )
            content_div = f'<div class="code-content{" collapsed" if collapsed else ""}"><pre>{self._code_blocks[0]["html"]}</pre></div>'
            wrapper = f'<div class="code-block-wrapper" data-idx="0">{tools_html}{content_div}</div>'
            enhanced += wrapper
        # 注入附加样式
        style_inject = (
            '<style>'
            '.code-block-wrapper{position:relative; margin:8px 0;}'
            '.code-tools{position:absolute; top:4px; right:8px; font-size:11px;}'
            '.code-tools a{color:#fff; background:rgba(0,0,0,0.35); padding:2px 6px; border-radius:4px; text-decoration:none; margin-left:4px;}'
            '.code-tools a:hover{background:rgba(0,0,0,0.55);}'
            '.code-content.collapsed{max-height:140px; overflow:hidden; position:relative;}'
            '.code-content.collapsed:after{content:""; position:absolute; left:0; right:0; bottom:0; height:32px; background:linear-gradient(to bottom, rgba(45,45,45,0), rgba(45,45,45,0.85));}'
            '</style>'
        )
        if '</style>' in enhanced:
            # 在原样式后附加（粗略方式）
            enhanced = enhanced.replace('</style>', '</style>' + style_inject, 1)
        else:
            enhanced = style_inject + enhanced
        # 连接交互信号
        self.content.setOpenLinks(False)
        try:
            self.content.anchorClicked.disconnect(self._on_anchor_clicked)
        except Exception:
            pass
        self.content.anchorClicked.connect(self._on_anchor_clicked)
        return enhanced

    def _on_anchor_clicked(self, url: QtCore.QUrl):  # type: ignore
        href = url.toString()
        if href.startswith('copy://'):
            idx_str = href.split('://', 1)[1]
            if idx_str.isdigit():
                self._copy_code_block(int(idx_str))
        elif href.startswith('toggle://'):
            idx_str = href.split('://', 1)[1]
            if idx_str.isdigit():
                self._toggle_code_block(int(idx_str))

    def _copy_code_block(self, idx: int):
        if 0 <= idx < len(self._code_blocks):
            block = self._code_blocks[idx]
            clipboard = QtWidgets.QApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(block['plain'])

    def _toggle_code_block(self, idx: int):
        if 0 <= idx < len(self._code_blocks):
            self._code_blocks[idx]['collapsed'] = not self._code_blocks[idx]['collapsed']
            # 重建增强 HTML
            rebuilt = self._rebuild_enhanced_html()
            self._enhanced_html = rebuilt
            self.content.setHtml(rebuilt)
            self._adjust_height()

    def _rebuild_enhanced_html(self) -> str:
        """根据当前 _code_blocks 折叠状态在 _base_html 基础上重建增强 HTML。"""
        import re
        pattern = re.compile(r'<pre>(.*?)</pre>', re.DOTALL)
        idx = 0
        def repl(m):
            nonlocal idx
            if idx >= len(self._code_blocks):
                return m.group(0)
            b = self._code_blocks[idx]
            inner = b['html']
            collapsed = b['collapsed']
            tools_html = (
                f'<div class="code-tools">'
                f'<a href="copy://{idx}" class="copy-btn">复制</a>'
                f'<a href="toggle://{idx}" class="toggle-btn">{"展开" if collapsed else "折叠"}</a>'
                f'</div>'
            )
            content_div = f'<div class="code-content{" collapsed" if collapsed else ""}"><pre>{inner}</pre></div>'
            wrapper = f'<div class="code-block-wrapper" data-idx="{idx}">{tools_html}{content_div}</div>'
            idx += 1
            return wrapper
        rebuilt = pattern.sub(repl, self._base_html)
        # 若无 <pre> 模式，采用降级包装重建
        if '```' in self.raw_text and '<pre' not in self._base_html and len(self._code_blocks) == 1:
            b = self._code_blocks[0]
            collapsed = b['collapsed']
            tools_html = (
                f'<div class="code-tools">'
                f'<a href="copy://0" class="copy-btn">复制</a>'
                f'<a href="toggle://0" class="toggle-btn">{"展开" if collapsed else "折叠"}</a>'
                f'</div>'
            )
            content_div = f'<div class="code-content{" collapsed" if collapsed else ""}"><pre>{b["html"]}</pre></div>'
            wrapper = f'<div class="code-block-wrapper" data-idx="0">{tools_html}{content_div}</div>'
            rebuilt = self._base_html + wrapper
        # 注入样式（若未存在）
        if 'code-block-wrapper' not in rebuilt:
            style_inject = (
                '<style>'
                '.code-block-wrapper{position:relative; margin:8px 0;}'
                '.code-tools{position:absolute; top:4px; right:8px; font-size:11px;}'
                '.code-tools a{color:#fff; background:rgba(0,0,0,0.35); padding:2px 6px; border-radius:4px; text-decoration:none; margin-left:4px;}'
                '.code-tools a:hover{background:rgba(0,0,0,0.55);}'
                '.code-content.collapsed{max-height:140px; overflow:hidden; position:relative;}'
                '.code-content.collapsed:after{content:""; position:absolute; left:0; right:0; bottom:0; height:32px; background:linear-gradient(to bottom, rgba(45,45,45,0), rgba(45,45,45,0.85));}'
                '</style>'
            )
            rebuilt = style_inject + rebuilt
        return rebuilt

    def _on_contents_changed(self):
        # 文本变化后刷新尺寸并通知父 QListWidgetItem（若已绑定）
        self._adjust_height()
        if hasattr(self, '_bound_item') and self._bound_item is not None:
            self._bound_item.setSizeHint(self.sizeHint() + QtCore.QSize(0, 6))

    def sizeHint(self):  # type: ignore
        """动态宽度 sizeHint"""
        doc = self.content.document()
        if doc is None:
            return QtCore.QSize(200, 50)
        
        # 计算内容宽度
        content_width = min(self.max_width, self.content.width())
        if content_width <= 0:
            content_width = self.max_width
        
        # 计算高度
        doc.setTextWidth(content_width - 20)
        doc_layout = doc.documentLayout()
        if doc_layout is not None:
            ideal_size = doc_layout.documentSize()
            content_height = int(ideal_size.height()) + 25
        else:
            # 回退方案
            sz = doc.size()
            content_height = int(sz.height()) + 25
        
        # 计算总宽度（包含角色标签）
        layout = self.layout()
        spacing = layout.spacing() if layout else 6
        side_extra = self.role_label.width() + spacing
        
        total_width = content_width + side_extra
        total_height = max(content_height, 45)
        
        return QtCore.QSize(total_width, total_height)

    def update_width(self, new_max_width: int):
        """更新最大宽度限制"""
        # 确保合理的宽度范围
        self.max_width = max(120, min(new_max_width, 800))
        self.content.setMaximumWidth(self.max_width)
        self.content.setMinimumWidth(min(100, self.max_width // 2))
        
        # 立即调整高度
        self._adjust_height()
        self.updateGeometry()
        
        # 如果绑定了列表项，更新其大小提示
        if hasattr(self, '_bound_item') and self._bound_item is not None:
            self._bound_item.setSizeHint(self.sizeHint())

    # ---------- 流式输出支持 ----------
    def start_streaming(self):
        """开始流式输出模式"""
        self.is_streaming = True
        self.stream_buffer = ""
        self.stream_timer.start()

    def stream_text(self, text_chunk: str):
        """接收流式文本块"""
        if self.is_streaming:
            self.stream_buffer += text_chunk

    def _flush_stream_buffer(self):
        """刷新流缓冲区到显示"""
        if self.stream_buffer:
            # 每次添加一小段文本以实现打字机效果
            text_to_add = self.stream_buffer
            self.stream_buffer = ""
            
            # 累积完整文本
            self.raw_text += text_to_add
            
            # 更新内容
            self.content.setPlainText(self.raw_text)
            
            # 滚动到底部
            cursor = self.content.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.content.setTextCursor(cursor)
            
            # 确保父级聊天历史区域也滚动到底部
            parent = self.parent()
            while parent:
                scroll_method = getattr(parent, 'scrollToBottom', None)
                if scroll_method and callable(scroll_method):
                    scroll_method()
                    break
                parent = parent.parent()
            
            # 节流高度刷新
            QtCore.QTimer.singleShot(30, self._adjust_height)

    def end_streaming(self):
        """流式输出结束，确保所有内容都已刷新。"""
        # 停止定时器并确保缓冲区中的任何剩余内容都被刷新
        self._flush_stream_buffer()
        self.stream_timer.stop()
        self.is_streaming = False
        # 确保流结束后，完整内容被作为 Markdown 渲染
        final_text = self.raw_text
        self.stream_buffer = ""  # 清空缓冲区
        self.set_markdown(final_text)
        self._adjust_height()

    def apply_theme(self, user_style: str, ai_style: str):
        """应用主题样式"""
        base_style = (user_style if self.role == 'user' else ai_style)
        # 如果用户传入的样式不包含 border-radius 或 background，则补齐一份默认值
        if 'border-radius' not in base_style:
            base_style = base_style.rstrip('}') + ' border-radius:18px;}'
        if 'background' not in base_style and 'background-color' not in base_style:
            base_style = base_style.rstrip('}') + ' background-color:rgba(255,255,255,0.9);}'
        self.content.setStyleSheet(base_style + "\nQTextBrowser{border:0px solid transparent;}\n")
        
        # 重新应用内容以确保样式正确更新
        if hasattr(self, 'raw_text') and self.raw_text:
            self.set_markdown(self.raw_text)
        # 更新 AI 头像（如果是 AI 消息且图标存在）
        if self.role == 'ai':
            try:
                icon_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'icons', 'Conduct.png'))
                if os.path.exists(icon_path):
                    pix = QtGui.QPixmap(icon_path)
                    if not pix.isNull():
                        keep_aspect = getattr(QtCore.Qt, 'KeepAspectRatio')
                        smooth = getattr(QtCore.Qt, 'SmoothTransformation')
                        scaled = pix.scaled(28, 28, keep_aspect, smooth)
                        self.role_label.setPixmap(scaled)
                        self.role_label.setStyleSheet("QLabel{background:transparent;}")
            except Exception:
                pass
