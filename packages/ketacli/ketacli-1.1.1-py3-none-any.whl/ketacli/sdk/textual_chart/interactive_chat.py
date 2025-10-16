"""交互式聊天应用入口"""

from .app import run_interactive_chat

if __name__ == "__main__":
    try:
        run_interactive_chat()
    except Exception as e:
        print(f"交互式聊天应用启动失败: {e}")
        import traceback
        with open("interactive_chat_error.log", "w") as f:
            traceback.print_exc(file=f)
