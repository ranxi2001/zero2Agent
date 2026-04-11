---
layout: default
title: 构建你的 OpenClaw
description: Fork pi-mono，换成你自己的 LLM 和工具，用 PM2 部署，通过 Slack/飞书对话
eyebrow: OpenClaw / 08
---

# 构建你的 OpenClaw

这一节是动手实践。目标是把 pi-mono 改成属于你自己的 Agent，部署起来，通过 Slack 或飞书跟它对话。

完成之后，你就有了一个真正运行在你自己机器上的 Coding Agent，可以叫它 `[你的名字]Claw`。

---

## 第一步：Fork 并克隆 pi-mono

```bash
# Fork 仓库（在 GitHub 上操作）
# 然后克隆你自己的 fork
git clone https://github.com/[你的用户名]/pi-mono
cd pi-mono
```

为什么 fork 而不是直接 clone？

fork 之后，你可以自由修改、提交到自己的仓库，同时还能从上游拉取更新。你的 Agent 是你自己的代码，不是别人的。

---

## 第二步：配置 LLM

pi-mono 使用 OpenAI 兼容协议，只需要设置环境变量：

```bash
# Kimi (Moonshot)
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL="https://api.moonshot.cn/v1"
export OPENAI_MODEL="moonshot-v1-32k"

# 智谱 GLM
export OPENAI_API_KEY="your-key.your-secret"
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
export OPENAI_MODEL="glm-4"

# DeepSeek
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export OPENAI_MODEL="deepseek-chat"
```

建议把这些写进 `.env` 文件（加进 `.gitignore`），用 `python-dotenv` 加载：

```python
# 在入口文件顶部
from dotenv import load_dotenv
load_dotenv()
```

---

## 第三步：修改系统 Prompt

`SYSTEM_PROMPT.md` 是你 Agent 的“人格”。把它改成你想要的行为：

```markdown
你是 [你的名字]Claw，一个专注于 Python 和 TypeScript 的 Coding Agent。

你的工作方式：
- 修改代码前先读取并理解现有实现
- 遇到不确定的需求，直接问用户，不要猜测
- 每次修改后运行相关测试
- 用中文和用户对话，代码注释用英文

你的限制：
- 不修改 .env 文件
- 不执行 git push（需要用户确认后再推）
```

系统 Prompt 的质量直接决定 Agent 的可靠性。多花时间在这里。

---

## 第四步：精简工具集

根据你的使用场景，决定保留哪些工具：

```python
# agent/tools/__init__.py — 根据需要增删
from .file_ops import ReadFile, WriteFile, EditFile, ListDir
from .shell import Bash
from .search_ops import Grep, Find
# from .web import SearchWeb  ← 如果不需要联网搜索，注释掉

ALL_TOOLS = [ReadFile(), WriteFile(), EditFile(), ListDir(), Bash(), Grep(), Find()]
```

**原则：你用不到的工具，删掉。工具越少，Agent 行为越可预测。**

---

## 第五步：本地测试

```bash
# 安装依赖
uv sync

# 命令行交互模式
uv run python -m agent.main

# 你应该能看到：
# > 你好，我是 [你的名字]Claw。有什么可以帮你？
# You: 帮我看看 src/main.py 有没有问题
```

在部署之前，在命令行把几个典型任务跑通：

- 读文件并分析
- 修改代码并解释改了什么
- 执行 shell 命令并处理输出

---

## 第六步：PM2 后台部署

PM2 是 Node.js 生态的进程管理器，支持 Python 脚本，是 Agent 后台部署的标准工具。

```bash
# 安装 PM2
npm install -g pm2

# 启动 Agent（HTTP 服务模式）
pm2 start "uv run python -m agent.server" --name "myclaw"

# 查看状态
pm2 status

# 查看日志
pm2 logs myclaw

# 开机自启
pm2 startup
pm2 save
```

`agent/server.py` 是一个简单的 HTTP 服务，接收消息，调用 Agent，返回结果：

```python
# agent/server.py
from flask import Flask, request, jsonify
from agent.main import process_message

app = Flask(__name__)

@app.route("/message", methods=["POST"])
def handle_message():
    data = request.json
    user_id = data.get("user_id", "default")
    text = data["text"]
    response = process_message(user_id=user_id, text=text)
    return jsonify({"text": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

## 第七步：接入 Slack 或飞书

### Slack 集成

```python
# integrations/slack_bot.py
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import requests

slack_app = App(token=os.environ["SLACK_BOT_TOKEN"],
                signing_secret=os.environ["SLACK_SIGNING_SECRET"])

@slack_app.event("app_mention")
def handle_mention(event, say):
    user_id = event["user"]
    text = event["text"].replace(f"<@{slack_app.client.auth_test()['user_id']}>", "").strip()

    # 转发给 Agent 服务
    resp = requests.post("http://localhost:5000/message",
                         json={"user_id": user_id, "text": text})
    say(resp.json()["text"])
```

### 飞书集成

```python
# integrations/feishu_bot.py
import hmac, hashlib, json
from flask import Flask, request

app = Flask(__name__)

@app.route("/feishu/webhook", methods=["POST"])
def handle_feishu():
    data = request.json

    # 飞书 URL 验证
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    # 处理消息
    if data.get("header", {}).get("event_type") == "im.message.receive_v1":
        msg = data["event"]["message"]
        user_id = data["event"]["sender"]["sender_id"]["user_id"]
        text = json.loads(msg["content"])["text"]

        resp = requests.post("http://localhost:5000/message",
                             json={"user_id": user_id, "text": text})

        # 回复消息（需要调飞书发送 API）
        send_feishu_message(user_id, resp.json()["text"])

    return jsonify({"code": 0})
```

---

## 你的 Agent 叫什么

OpenClaw 的命名约定：`[你的名字]Claw`。

比如：
- **AliceClaw** — Alice 的 Coding Agent
- **BobClaw** — Bob 的 Coding Agent

这不只是命名游戏。给你的 Agent 一个名字，意味着它是你自己的东西，不是某个框架的实例。你对它的行为负责，你也最了解它。

```python
# SYSTEM_PROMPT.md 第一行
你是 AliceClaw，Alice 的个人 Coding Agent。
```

---

## 完整的部署检查清单

```
□ fork + clone pi-mono
□ 配置 .env（API key + base URL + model）
□ 修改 SYSTEM_PROMPT.md
□ 精简工具集（删掉用不到的）
□ 本地命令行测试（至少 5 个典型任务）
□ 启动 agent/server.py，测试 HTTP 接口
□ pm2 start，验证后台运行
□ 接入 Slack 或飞书，测试端到端对话
□ pm2 save + pm2 startup（配置开机自启）
```

---

下一篇：[面试与实习准备](../09-interview/index.html)
