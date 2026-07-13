import os
import subprocess
import time
import shutil
from PIL import ImageGrab
from browser import Browser
import utils

class Executor:
    def __init__(self):
        self._browser = None

    @property
    def browser(self):
        """Lazy initialization of browser to save memory/speed if not using web features."""
        if self._browser is None:
            self._browser = Browser()
        return self._browser

    def has_active_browser(self):
        return self._browser is not None

    def get_browser_state(self):
        """Returns the current state of the browser if active, otherwise returns inactive."""
        if not self.has_active_browser():
            return {"active": False}
        try:
            url = self.browser.get_url()
            title = self.browser.get_title()
            elements = self.browser.extract_interactive_elements()
            return {
                "active": True,
                "url": url,
                "title": title,
                "elements": elements
            }
        except Exception as e:
            return {"active": False, "error": str(e)}

    def get_desktop_state(self):
        """Returns the current active window and running interesting processes."""
        try:
            active_win = utils.get_active_window_title()
            processes = utils.get_running_processes()
            return {
                "active_window": active_win,
                "processes": processes
            }
        except Exception as e:
            return {
                "active_window": "Unknown",
                "processes": [],
                "error": str(e)
            }

    def capture_screenshot(self, path="static/screenshot.png"):
        """Captures a screenshot of the active browser page or the Windows desktop."""
        try:
            # Ensure folder exists
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            if self.has_active_browser():
                # Take viewport screenshot
                self.browser.page.screenshot(path=path)
                return "browser"
            else:
                # Take desktop screen grab using Pillow
                im = ImageGrab.grab()
                im.save(path)
                return "desktop"
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return "failed"

    def execute(self, step):
        """Dispatches action execution and automatically captures a screenshot afterwards."""
        action = step["action"]
        result = self._execute_internal(action, step)
        
        # Take screenshot
        self.capture_screenshot()
        return result

    def _execute_internal(self, action, step):
        # 1. Web actions
        if action == "web_open":
            return self.browser.open_url(step["url"])
            
        elif action == "web_click":
            return self.browser.click_element(step["element_id"])
            
        elif action == "web_type":
            return self.browser.type_element(step["element_id"], step["text"])
            
        elif action == "web_press_key":
            return self.browser.press_key(step["key"])
            
        elif action == "web_go_back":
            return self.browser.go_back()
            
        elif action == "web_wait":
            return self.browser.wait(float(step["seconds"]))
            
        # 2. Desktop actions
        elif action == "desktop_open_app":
            return utils.open_app(step["command"])
            
        elif action == "desktop_type":
            active_win = utils.get_active_window_title()
            # If target window is Notepad, type and send direct message
            if "notepad" in active_win.lower() or "untitled" in active_win.lower():
                utils.type_text(step["text"])
                msg = utils.write_to_notepad_direct(step["text"])
                return f"Simulated typing into Notepad. {msg}"
            else:
                utils.type_text(step["text"])
                return f"Simulated keyboard typing of text: '{step['text']}'"
            
        elif action == "desktop_press_key":
            utils.press_key(step["key"])
            return f"Simulated keypress: '{step['key']}'"
            
        elif action == "desktop_hotkey":
            keys = step["keys"]
            if len(keys) > 1:
                utils.press_hotkey(keys[:-1], keys[-1])
            else:
                utils.press_key(keys[0])
            return f"Simulated hotkey combination: {keys}"
            
        elif action == "desktop_wait":
            wait_time = float(step["seconds"])
            time.sleep(wait_time)
            return f"Waited on desktop for {wait_time} seconds"
            
        # 3. File System & OS Shell actions
        elif action == "run_shell":
            try:
                result = subprocess.run(
                    step["command"],
                    shell=True,
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                return output.strip()
            except Exception as e:
                return f"Failed to run shell command. Error: {str(e)}"
                
        elif action == "read_file":
            try:
                filepath = step["filepath"]
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                return f"Read {len(content)} characters from file '{filepath}'. File contents:\n{content}"
            except Exception as e:
                return f"Failed to read file. Error: {str(e)}"
                
        elif action == "write_file":
            try:
                filepath = step["filepath"]
                content = step["content"]
                parent_dir = os.path.dirname(os.path.abspath(filepath))
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully wrote content to file '{filepath}'"
            except Exception as e:
                return f"Failed to write file. Error: {str(e)}"

        elif action == "file_action":
            op = step["operation"]
            try:
                if op == "copy":
                    src = step["source"]
                    dst = step["destination"]
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                    return f"Successfully copied '{src}' to '{dst}'"
                elif op == "move":
                    src = step["source"]
                    dst = step["destination"]
                    shutil.move(src, dst)
                    return f"Successfully moved '{src}' to '{dst}'"
                elif op == "delete":
                    path = step["path"]
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    return f"Successfully deleted '{path}'"
                elif op == "list":
                    path = step["path"]
                    items = os.listdir(path)
                    return f"Directory listing of '{path}':\n" + "\n".join(items)
                elif op == "create_directory":
                    path = step["path"]
                    os.makedirs(path, exist_ok=True)
                    return f"Successfully created directory '{path}'"
            except Exception as e:
                return f"Failed file explorer operation '{op}'. Error: {str(e)}"
                
        elif action == "finish":
            return f"Task execution finished: {step['message']}"
            
        return f"Unhandled action type: '{action}'"

    def close(self):
        if self.has_active_browser():
            self.browser.close()