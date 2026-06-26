import json
from langchain_ollama import ChatOllama
from playwright.sync_api import sync_playwright

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0
)

task = input("Task: ")

prompt = f"""
You are a browser automation agent.

Convert the task into JSON.

Supported actions:

1. Open website

Example:
User: Open youtube

Output:
{{"action":"open","url":"https://youtube.com"}}

2. Search on website

Example:
User: Search ollama on youtube

Output:
{{"action":"search","website":"youtube","query":"ollama"}}

Task:
{task}

Return ONLY JSON.
"""

response = llm.invoke(prompt)

print(response.content)

data = json.loads(response.content)

print(data)

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    if data["action"] == "open":
        page.goto(data["url"])

    elif data["action"] == "search":

        if data["website"] == "youtube":

            page.goto("https://youtube.com")

            page.wait_for_timeout(3000)

            page.locator(
                "input[name='search_query']"
            ).fill(data["query"])

            page.keyboard.press("Enter")

    input("Press Enter to exit")

    browser.close()