import asyncio
import json
import os
import queue
import threading
import tkinter as tk

import customtkinter as ctk

from api.api import QueryModel
from constant.SystemToolPrompt import get_system_prompt
from tools.Tool import get_tools
from tools.shell import ShellExecutor
from util.fileCacheUtil import CacheUtils
from util.toolContext import toolContext


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class DesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Hong Code")
        self.geometry("1040x720")
        self.minsize(860, 600)
        self.configure(fg_color="#f3f0e8")

        self.event_queue = queue.Queue()
        self.context = []
        self.tools = get_tools()
        self.query_model = None
        self.tool_ctx = toolContext(
            executor=ShellExecutor(),
            file_cache_util=CacheUtils(100)
        )
        self.is_waiting = False

        self._build_ui()
        self._init_model()
        self.after(80, self._drain_events)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="#153f3a", corner_radius=0, height=92)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        mark = ctk.CTkFrame(header, width=54, height=54, fg_color="#e3b04b", corner_radius=8)
        mark.grid(row=0, column=0, padx=(28, 16), pady=18)
        mark.grid_propagate(False)

        mark_label = ctk.CTkLabel(
            mark,
            text="H",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color="#153f3a",
        )
        mark_label.place(relx=0.5, rely=0.5, anchor="center")

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w", pady=16)

        title = ctk.CTkLabel(
            title_box,
            text="Hong Code",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color="#fff9ea",
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="本地桌面助手 · 支持 Bash 与文件读取工具",
            font=ctk.CTkFont(size=13),
            text_color="#cfe2d5",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.status_label = ctk.CTkLabel(
            header,
            text="准备就绪",
            font=ctk.CTkFont(size=13),
            text_color="#fff9ea",
        )
        self.status_label.grid(row=0, column=2, padx=28)

        body = ctk.CTkFrame(self, fg_color="#f3f0e8", corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.chat = ctk.CTkScrollableFrame(body, fg_color="#f8f5ee", corner_radius=0)
        self.chat.grid(row=0, column=0, sticky="nsew", padx=28, pady=(24, 12))
        self.chat.grid_columnconfigure(0, weight=1)

        self._add_message(
            "assistant",
            "你好，我是 Hong Code。把你的问题写在下面，我会在这个桌面窗口里回复。",
        )

        composer = ctk.CTkFrame(self, fg_color="#f3f0e8", corner_radius=0)
        composer.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 24))
        composer.grid_columnconfigure(0, weight=1)

        self.input_box = ctk.CTkTextbox(
            composer,
            height=92,
            corner_radius=8,
            border_width=1,
            border_color="#d3c9b5",
            fg_color="#fffdf8",
            text_color="#1d2521",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15),
            wrap="word",
        )
        self.input_box.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.input_box.bind("<Control-Return>", self._send_message)

        self.send_button = ctk.CTkButton(
            composer,
            width=132,
            height=92,
            corner_radius=8,
            fg_color="#2f6f61",
            hover_color="#25584d",
            text="发送\nCtrl+Enter",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._send_message,
        )
        self.send_button.grid(row=0, column=1, sticky="e")

    def _init_model(self):
        try:
            self.query_model = QueryModel(get_system_prompt())
        except KeyError as exc:
            self._set_status("缺少环境变量")
            self._add_message("error", f"缺少环境变量：{exc}。请先设置 BASE_URL 和 API_KEY。")
        except Exception as exc:
            self._set_status("初始化失败")
            self._add_message("error", f"模型客户端初始化失败：{exc}")

    def _send_message(self, event=None):
        if self.is_waiting:
            return "break"

        content = self.input_box.get("1.0", "end").strip()
        if not content:
            return "break"

        if self.query_model is None:
            self._add_message("error", "模型客户端还没有初始化成功。")
            return "break"

        self.input_box.delete("1.0", "end")
        self._add_message("user", content)
        self._set_busy(True)

        worker = threading.Thread(target=self._run_query, args=(content,), daemon=True)
        worker.start()
        return "break"

    def _run_query(self, content):
        try:
            asyncio.run(
                self.query_model.query(
                    tools=self.tools,
                    code=content,
                    context=self.context,
                    tool_context=self.tool_ctx,
                    on_event=self._publish_event,
                )
            )
            self.event_queue.put({"type": "done"})
        except Exception as exc:
            self.event_queue.put({"type": "error", "text": str(exc)})

    def _publish_event(self, event):
        self.event_queue.put(event)

    def _drain_events(self):
        while True:
            try:
                event = self.event_queue.get_nowait()
            except queue.Empty:
                break

            event_type = event.get("type")
            if event_type == "text":
                self._add_message("assistant", event.get("text", ""))
            elif event_type == "tool_use":
                tool_input = json.dumps(event.get("input", {}), ensure_ascii=False, indent=2)
                self._add_message("tool", f"调用工具：{event.get('name')}\n{tool_input}")
            elif event_type == "error":
                self._add_message("error", event.get("text", "未知错误"))
                self._set_busy(False)
            elif event_type == "done":
                self._set_busy(False)

        self.after(80, self._drain_events)

    def _add_message(self, role, text):
        row = len(self.chat.winfo_children())

        palette = {
            "user": ("#dcefe4", "#16352f", "你"),
            "assistant": ("#fffdf8", "#1e2521", "AI"),
            "tool": ("#ecdfc5", "#3b2a12", "工具"),
            "error": ("#f8d7d2", "#5f1f18", "错误"),
        }
        bg, fg, label = palette.get(role, palette["assistant"])

        outer = ctk.CTkFrame(self.chat, fg_color="transparent")
        outer.grid(row=row, column=0, sticky="ew", pady=8)
        outer.grid_columnconfigure(0, weight=1)

        align = "e" if role == "user" else "w"
        bubble = ctk.CTkFrame(outer, fg_color=bg, corner_radius=8)
        bubble.grid(row=0, column=0, sticky=align, padx=(120, 0) if role == "user" else (0, 120))
        bubble.grid_columnconfigure(0, weight=1)

        name = ctk.CTkLabel(
            bubble,
            text=label,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=fg,
        )
        name.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 2))

        body = ctk.CTkLabel(
            bubble,
            text=text,
            justify="left",
            wraplength=680,
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15),
            text_color=fg,
        )
        body.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

        self.after(10, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        self.chat._parent_canvas.yview_moveto(1.0)

    def _set_busy(self, busy):
        self.is_waiting = busy
        self.send_button.configure(state="disabled" if busy else "normal")
        self._set_status("思考中..." if busy else "准备就绪")

    def _set_status(self, text):
        self.status_label.configure(text=text)


if __name__ == "__main__":
    app = DesktopApp()
    app.mainloop()
