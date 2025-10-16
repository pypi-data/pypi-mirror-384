import threading
import selectors

try:
    import msvcrt
except ImportError:
    import sys, tty, termios


def Getch():
    def _GetchUnixNonBlocking():
        # 保存终端设置以便后续恢复
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            # 设置终端为原始模式
            tty.setcbreak(fd)

            selector = selectors.DefaultSelector()
            selector.register(sys.stdin, selectors.EVENT_READ)

            while True:
                events = selector.select(timeout=None)  # 阻塞直到有事件发生
                for key, mask in events:
                    if key.fileobj == sys.stdin:

                        ch = key.fileobj.read(1)  # 读取一个字符
                        if ch:
                            # 检查是否为ESC字符（\x1b），如果是则跳过接下来的读取以忽略特殊序列
                            if ch == '\x1b':
                                chs = ch
                                # 处理ESC序列，这里简单地读取并丢弃接下来的字符，实际应用中可能需要更复杂的逻辑
                                while True:
                                    next_ch = sys.stdin.read(1)
                                    chs += next_ch
                                    if next_ch == '[' or next_ch == "\x1b":  # 基本的ESC序列检测
                                        continue
                                    break  # 遇到非预期字符，跳出循环
                                return chs
                            else:
                                return ch  # 返回单字符输入
                        else:
                            # 没有读取到任何数据，继续等待
                            continue
        finally:
            # 恢复终端设置
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _GetchWindows():
        return msvcrt.getch()

    def _GetchUnix():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    try:
        impl = _GetchWindows()
    except NameError:
        impl = _GetchUnixNonBlocking()
    return impl


def get_key_thread(callback=None):
    try:
        def func():
            while True:
                sequence = Getch()
                callback(sequence)

        thread = threading.Thread(target=func)
    except Exception as e:
        with open('error.log', 'a') as f:
            f.write(f'error: \n{e}')
    return thread


def get_key_sequence():

    return Getch()


def is_current_process_in_foreground(window_name):
    import pygetwindow as gw
    # 检查传递的窗口名称是否与当前激活的窗口名称一致，用来检查当前程序是否是前台程序
    return gw.getActiveWindow() == window_name


if __name__ == '__main__':
    is_current_process_in_foreground()
    # while True:
    #     s = Getch()
    #     print('{:02x}'.format(ord(s)))
