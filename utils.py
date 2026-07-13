import win32api
import win32con
import win32gui
import win32process
import subprocess
import time
import ctypes
from ctypes import wintypes
import psutil

# Ctypes structures for SendInput
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION)
    ]

INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002

VK_CODES = {
    'backspace': 0x08,
    'tab': 0x09,
    'clear': 0x0C,
    'enter': 0x0D,
    'shift': 0x10,
    'ctrl': 0x11,
    'alt': 0x12,
    'pause': 0x13,
    'caps_lock': 0x14,
    'escape': 0x1B,
    'space': 0x20,
    'page_up': 0x21,
    'page_down': 0x22,
    'end': 0x23,
    'home': 0x24,
    'left': 0x25,
    'up': 0x26,
    'right': 0x27,
    'down': 0x28,
    'select': 0x29,
    'print': 0x2A,
    'execute': 0x2B,
    'print_screen': 0x2C,
    'insert': 0x2D,
    'delete': 0x2E,
    'help': 0x2F,
    'f1': 0x70,
    'f2': 0x71,
    'f3': 0x72,
    'f4': 0x73,
    'f5': 0x74,
    'f6': 0x75,
    'f7': 0x76,
    'f8': 0x77,
    'f9': 0x78,
    'f10': 0x79,
    'f11': 0x7A,
    'f12': 0x7B,
}

def get_vk_code(key_name):
    key_name = key_name.lower().strip()
    if key_name in VK_CODES:
        return VK_CODES[key_name]
    if len(key_name) == 1:
        return ord(key_name.upper())
    raise ValueError(f"Unknown key name: {key_name}")

def type_text(text):
    """Types unicode text using SendInput."""
    for char in text:
        # Key down
        ki_down = KEYBDINPUT(wVk=0, wScan=ord(char), dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=None)
        inp_down = INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=ki_down))
        # Key up
        ki_up = KEYBDINPUT(wVk=0, wScan=ord(char), dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)
        inp_up = INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=ki_up))
        
        inputs = (INPUT * 2)(inp_down, inp_up)
        ctypes.windll.user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
        time.sleep(0.01)

def send_key_event(vk, down=True):
    """Sends a single virtual key press or release event."""
    flags = 0 if down else KEYEVENTF_KEYUP
    ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=None)
    inp = INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=ki))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    time.sleep(0.02)

def press_key(key_name):
    """Presses and releases a key by name. Handles combinations like 'ctrl+s' automatically."""
    key_name = key_name.lower().strip()
    if '+' in key_name:
        parts = key_name.split('+')
        press_hotkey(parts[:-1], parts[-1])
    else:
        vk = get_vk_code(key_name)
        send_key_event(vk, down=True)
        send_key_event(vk, down=False)

def press_hotkey(modifiers, key_name):
    """Presses modifiers, taps a key, and releases modifiers in reverse order."""
    mod_vks = [get_vk_code(m) for m in modifiers]
    key_vk = get_vk_code(key_name)
    
    for vk in mod_vks:
        send_key_event(vk, down=True)
    
    send_key_event(key_vk, down=True)
    send_key_event(key_vk, down=False)
    
    for vk in reversed(mod_vks):
        send_key_event(vk, down=False)

def list_windows():
    """Returns a list of tuples containing HWND and window title for all visible windows."""
    windows = []
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.strip():
                windows.append((hwnd, title.strip()))
        return True
    win32gui.EnumWindows(callback, None)
    return windows

def force_foreground(hwnd):
    """Tries multiple methods to force a window into the foreground."""
    try:
        # Check if already foreground
        if win32gui.GetForegroundWindow() == hwnd:
            return True
            
        # 1. Normal method
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            pass

        # 2. ALT key tap trick
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        time.sleep(0.05)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        return True
    except Exception as e1:
        # 3. Thread attachment method
        try:
            fore_hwnd = win32gui.GetForegroundWindow()
            fore_thread, _ = win32process.GetWindowThreadProcessId(fore_hwnd)
            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
            
            if fore_thread != target_thread:
                win32process.AttachThreadInput(fore_thread, target_thread, True)
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                win32process.AttachThreadInput(fore_thread, target_thread, False)
                return True
        except Exception as e2:
            pass
            
    return False

def focus_window(title_substring):
    """Finds a window by title substring and brings it to focus."""
    windows = list_windows()
    for hwnd, title in windows:
        if title_substring.lower() in title.lower():
            if force_foreground(hwnd):
                return f"Focused window: '{title}'"
            return f"Found window '{title}' but could not bring to foreground."
    return f"No window found matching '{title_substring}'."

def open_app(command):
    """Launches an application asynchronously using subprocess."""
    try:
        subprocess.Popen(command, shell=True)
        return f"Successfully started command: '{command}'"
    except Exception as e:
        return f"Failed to start command: '{command}'. Error: {str(e)}"

def get_active_window_title():
    """Returns the title of the currently active/foreground window."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            return win32gui.GetWindowText(hwnd)
    except Exception:
        pass
    return "Unknown"

def get_running_processes():
    """Returns a list of names of running processes."""
    processes = set()
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name']:
                processes.add(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return sorted(list(processes))

def write_to_notepad_direct(text):
    """Directly sends WM_SETTEXT to Notepad's rich edit control as a robust fallback."""
    windows = list_windows()
    notepad_hwnd = None
    for hwnd, title in windows:
        if "notepad" in title.lower() or "untitled" in title.lower():
            notepad_hwnd = hwnd
            break
            
    if not notepad_hwnd:
        return "Notepad window not found."
        
    edit_hwnd = None
    def child_callback(hwnd, extra):
        classname = win32gui.GetClassName(hwnd)
        if classname in ('RichEditD2DPT', 'Edit'):
            extra.append(hwnd)
            return False
        return True
        
    edit_hwnds = []
    win32gui.EnumChildWindows(notepad_hwnd, child_callback, edit_hwnds)
    if edit_hwnds:
        edit_hwnd = edit_hwnds[0]
        # Send WM_SETTEXT
        win32gui.SendMessage(edit_hwnd, win32con.WM_SETTEXT, 0, text)
        return "Directly set Notepad text via WM_SETTEXT."
    return "Notepad edit control not found."
