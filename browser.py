from playwright.sync_api import sync_playwright
import time
import os

class Browser:
    def __init__(self):
        self.playwright = sync_playwright().start()
        # Launch browser with headless=False so the user can see the automation happening
        self.browser = self.playwright.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )
        self.context = self.browser.new_context(no_viewport=True)
        self.page = self.context.new_page()

    def open_url(self, url):
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        try:
            self.page.goto(url, wait_until="load", timeout=30000)
            # Give a small buffer for dynamic elements/hydration
            self.page.wait_for_timeout(2000)
            return f"Successfully opened {url}"
        except Exception as e:
            return f"Failed to open {url}. Error: {str(e)}"

    def click_element(self, agent_id):
        try:
            selector = f'[data-agent-id="{agent_id}"]'
            # Wait for it to be present
            self.page.wait_for_selector(selector, timeout=5000)
            self.page.click(selector)
            # Wait for post-click transitions
            self.page.wait_for_timeout(1500)
            return f"Successfully clicked element with ID {agent_id}"
        except Exception as e:
            return f"Failed to click element {agent_id}. Error: {str(e)}"

    def type_element(self, agent_id, text):
        try:
            selector = f'[data-agent-id="{agent_id}"]'
            self.page.wait_for_selector(selector, timeout=5000)
            self.page.fill(selector, "")
            self.page.type(selector, text, delay=50)
            # Wait a bit
            self.page.wait_for_timeout(500)
            return f"Successfully typed '{text}' into element {agent_id}"
        except Exception as e:
            return f"Failed to type into element {agent_id}. Error: {str(e)}"

    def press_key(self, key):
        try:
            self.page.keyboard.press(key)
            self.page.wait_for_timeout(1000)
            return f"Successfully pressed key: '{key}'"
        except Exception as e:
            return f"Failed to press key '{key}'. Error: {str(e)}"

    def go_back(self):
        try:
            self.page.go_back()
            self.page.wait_for_timeout(1500)
            return "Successfully went back to previous page"
        except Exception as e:
            return f"Failed to go back. Error: {str(e)}"

    def wait(self, seconds):
        try:
            self.page.wait_for_timeout(seconds * 1000)
            return f"Waited for {seconds} seconds"
        except Exception as e:
            return f"Failed waiting. Error: {str(e)}"

    def get_url(self):
        return self.page.url

    def get_title(self):
        return self.page.title()

    def extract_interactive_elements(self):
        """Injects a JavaScript snippet to tag visible interactive elements and retrieve them."""
        js_script = """
        (() => {
            const interactiveElements = [];
            let idCounter = 0;

            // Clean up any old data-agent-id tags
            document.querySelectorAll('[data-agent-id]').forEach(el => el.removeAttribute('data-agent-id'));

            function isElementVisible(el) {
                if (el.offsetWidth === 0 && el.offsetHeight === 0) return false;
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                return true;
            }

            const tags = ['button', 'a', 'input', 'textarea', 'select'];
            const roles = ['button', 'link', 'checkbox', 'radio', 'combobox', 'tab', 'menuitem', 'option'];

            document.querySelectorAll('*').forEach(el => {
                const tagName = el.tagName.toLowerCase();
                const role = el.getAttribute('role') || '';
                const hasClick = el.hasAttribute('onclick') || (el.onclick !== null);
                
                const isInteractive = tags.includes(tagName) || roles.includes(role) || hasClick;
                
                if (isInteractive && isElementVisible(el)) {
                    idCounter++;
                    el.setAttribute('data-agent-id', idCounter.toString());
                    
                    let text = el.innerText || el.textContent || '';
                    text = text.replace(/\\s+/g, ' ').trim();
                    if (text.length > 80) {
                        text = text.substring(0, 77) + '...';
                    }
                    
                    let placeholder = el.getAttribute('placeholder') || '';
                    let type = el.getAttribute('type') || '';
                    let name = el.getAttribute('name') || '';
                    let value = el.value || '';
                    if (typeof value !== 'string') value = '';
                    value = value.trim().substring(0, 50);

                    interactiveElements.push({
                        id: idCounter.toString(),
                        tag: tagName,
                        type: type,
                        text: text,
                        placeholder: placeholder,
                        name: name,
                        value: value,
                        role: role
                    });
                }
            });

            return interactiveElements;
        })()
        """
        try:
            return self.page.evaluate(js_script)
        except Exception as e:
            print(f"Error evaluating interactive elements: {e}")
            return []

    def close(self):
        try:
            self.context.close()
            self.browser.close()
            self.playwright.stop()
        except Exception:
            pass