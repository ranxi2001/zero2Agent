---
layout: default
title: 从 0 开始 Vibe Coding：用 Codex 发布个人主页
description: 从下载 VS Code、认识项目文件夹和终端，到用 Codex 创建网站并部署到 GitHub Pages
eyebrow: Agent Practice / 01
---

# 从 0 开始 Vibe Coding：用 Codex 发布个人主页

这篇从真正的零开始：你不需要先学完一门编程语言，也不需要理解复杂框架。我们会先把开发环境搭起来，再让 Codex 帮你完成第一个能公开访问的作品。

最终你会得到：

- 一个放在自己电脑上的项目文件夹
- 一个包含 HTML、CSS 和 JavaScript 的个人主页
- 一段可以回看的 Git 修改历史
- 一个托管代码的 GitHub 仓库
- 一个任何人都能打开的 `https://你的用户名.github.io/` 网站

更重要的是，你会理解下面这条关系：

```text
VS Code 打开项目文件夹
        ↓
终端进入这个文件夹
        ↓
从这里启动 Codex
        ↓
Codex 读取和修改文件夹里的文件
        ↓
Git 记录修改历史
        ↓
GitHub 保存远端副本
        ↓
GitHub Pages 把网页发布到互联网
```

---

## 一、先认识这些工具

| 工具 | 在这篇教程里的作用 |
|------|--------------------|
| VS Code | 打开项目文件夹、查看文件、编辑代码和使用终端 |
| Codex | 理解你的需求，创建文件、修改代码并帮助排错 |
| Node.js | 提供 `node`、`npm` 和 `npx`，也用于安装 Codex CLI |
| Python | 运行简单脚本，也可以一条命令启动本地网页服务器 |
| Git | 在本地记录每次修改，支持回看和恢复 |
| GitHub | 在线保存 Git 仓库，方便分享和协作 |
| GitHub Pages | 免费托管仓库中的静态网页 |

注意：GitHub Pages 只能托管 HTML、CSS、JavaScript、图片等静态文件，不能在服务器上运行 Python 或 Node.js 后端。本项目安装 Python 和 Node.js，是为了学习本地开发工具链，不是把它们部署到 GitHub Pages。

---

## 二、下载并安装 VS Code

1. 打开 [VS Code 官方下载页](https://code.visualstudio.com/download)。
2. 选择你的操作系统并完成安装。
3. 启动 VS Code。

安装后先认识三个区域：

```text
左侧活动栏       中间编辑区                下方终端
Explorer        打开的文件                命令运行位置
查看项目文件     阅读和修改内容             启动 Codex、Python、Git
```

VS Code 本身不是项目。**当你用 VS Code 打开一个文件夹时，这个文件夹才是当前项目的边界。**

不要直接把桌面、下载目录或整个用户目录当成项目打开。一个项目应该有自己的独立文件夹，例如：

```text
Desktop/
└── my-homepage/       ← 这一个文件夹就是项目
    ├── index.html
    ├── style.css
    └── script.js
```

---

## 三、创建并打开第一个项目文件夹

先在桌面创建一个名为 `my-homepage` 的空文件夹，然后在 VS Code 中选择：

```text
File → Open Folder → 选择 my-homepage
```

打开后，左侧 Explorer 顶部应该显示 `MY-HOMEPAGE`。这表示 VS Code 当前工作的根目录就是这个文件夹。

现在选择：

```text
Terminal → New Terminal
```

也可以使用快捷键：

```text
Ctrl + `
```

终端会出现在 VS Code 下方。Windows PowerShell 中输入：

```powershell
Get-Location
```

macOS 或 Linux 输入：

```bash
pwd
```

输出路径的最后一段应该是 `my-homepage`。这一步非常重要：**终端当前目录决定了接下来命令作用在哪个项目上。**

再输入：

```powershell
Get-ChildItem
```

macOS 或 Linux 使用：

```bash
ls
```

因为项目还是空的，所以现在不会看到网页文件。

终端里最常用的几个路径概念：

| 写法 | 含义 |
|------|------|
| `cd 文件夹名` | 进入一个子文件夹 |
| `cd ..` | 回到上一级文件夹 |
| `.` | 当前文件夹 |
| `code .` | 用 VS Code 打开当前文件夹 |

这里的 `.` 不是省略号，而是“当前目录”。以后你也可以先在终端进入某个项目，再运行 `code .` 打开它。如果系统无法识别 `code` 命令，继续使用 VS Code 的 `File → Open Folder` 即可。

### 项目、文件夹和仓库是什么关系

| 名称 | 含义 |
|------|------|
| 文件 | 一份具体内容，例如 `index.html` |
| 文件夹 | 把一个项目的所有文件放在一起 |
| VS Code Workspace | VS Code 当前打开和操作的文件夹 |
| Git 仓库 | 增加了 `.git` 历史记录的项目文件夹 |
| GitHub 仓库 | Git 仓库放在互联网服务器上的远端副本 |

对这个项目来说，它们指向的是同一份作品，只是所处阶段不同。

---

## 四、安装 Node.js、Python 和 Git

### 安装 Node.js

打开 [Node.js 官网](https://nodejs.org/)，安装当前 LTS 版本。安装完成后关闭并重新打开 VS Code 终端，然后运行：

```bash
node --version
npm --version
```

两个命令都显示版本号，说明 Node.js 和 npm 已经可以使用。

### 安装 Python

打开 [Python 官方下载页](https://www.python.org/downloads/)，安装当前稳定版本。Windows 安装器如果出现“Add Python to PATH”，请勾选。

安装完成后运行：

```bash
python --version
```

部分 Windows 环境需要使用：

```powershell
py --version
```

### 安装 Git

打开 [Git 官方下载页](https://git-scm.com/downloads)，安装适合你系统的版本，然后运行：

```bash
git --version
```

如果任何命令提示“无法识别”或“command not found”，先关闭并重新打开 VS Code；仍然失败时，再检查安装器是否把程序加入了 PATH。

---

## 五、安装并登录 Codex

[Codex CLI 官方文档](https://learn.chatgpt.com/docs/codex/cli)提供终端优先的本地开发方式。在 VS Code 的集成终端中运行：

```bash
npm install -g @openai/codex@latest
```

安装后检查：

```bash
codex --version
```

然后登录：

```bash
codex login
```

按照浏览器中的提示完成 ChatGPT 登录。登录完成后回到 VS Code 终端。

### 从项目目录启动 Codex

再次确认终端当前位于 `my-homepage`：

```powershell
Get-Location
```

然后启动：

```bash
codex
```

Codex 会把当前目录作为工作目录，读取这里的文件，并在你允许时修改它们。因此不要在用户主目录、桌面根目录或包含私人文件的文件夹中启动 Codex。

### `codex --yolo` 是什么

你可能会看到下面这种启动方式：

```bash
codex --yolo
```

`--yolo` 是 `--dangerously-bypass-approvals-and-sandbox` 的别名。根据 [Codex 官方命令说明](https://learn.chatgpt.com/docs/developer-commands#global-flags)，它会关闭命令审批和沙箱限制，让 Codex 直接执行所有命令。

这不是普通的“少点几次确认”，而是取消两道安全边界。官方只建议在外部已经做好隔离的环境中使用，例如一次性虚拟机、受控容器或专门的 Dev Container。

```text
个人电脑上的普通文件夹：使用 codex
受控的一次性容器或虚拟机：确认隔离后才考虑 codex --yolo
```

对于第一次练习，请使用 `codex`。等后续学会 Dev Container、Git 恢复和权限边界后，再尝试 `--yolo`。

---

## 六、让 Codex 创建个人主页

进入 Codex 后，先把目标、范围和验收标准一次说清楚：

```text
请在当前空项目中创建一个个人主页。

要求：
1. 只使用原生 HTML、CSS 和 JavaScript，不使用 React、Vue 或构建工具。
2. 创建 index.html、style.css、script.js 和 .gitignore。
3. 页面包含姓名、个人简介、技能、项目经历和联系方式。
4. 适配手机和桌面，链接可以用键盘访问，颜色对比清晰。
5. 不使用外部图片；先用纯色、排版和简单图标完成。
6. 完成后告诉我创建了哪些文件，以及如何在本地预览。
```

Codex 完成后，左侧 Explorer 应该出现：

```text
my-homepage/
├── index.html       页面结构和文字
├── style.css        颜色、字体、间距和响应式布局
├── script.js        少量页面交互
└── .gitignore       不需要提交到 Git 的文件规则
```

不要只看 Codex 的文字回复。逐个打开文件，确认它确实创建了内容。

### 第一次迭代不要追求复杂

第一版只需要做到：

- 页面能打开
- 文字是你自己的信息
- 手机和电脑都能阅读
- 没有明显错位
- 联系方式链接有效

动画、博客、评论、后台管理都先不做。Vibe Coding 的第一课不是“功能越多越好”，而是让一个小目标完整上线。

---

## 七、用 Python 或 Node.js 本地预览

网页文件虽然可以双击打开，但使用本地服务器更接近真实网站环境。

### 方案 A：Python

在 VS Code 终端中运行：

```bash
python -m http.server 8000
```

Windows 如果只有 `py` 命令：

```powershell
py -m http.server 8000
```

浏览器打开：

```text
http://localhost:8000
```

### 方案 B：Node.js

也可以运行：

```bash
npx serve .
```

第一次运行时，npm 可能询问是否下载 `serve`，确认后会显示本地地址。

两个方案选一个即可。停止服务器时，在终端按 `Ctrl + C`。

### 验收页面

至少检查：

- 浏览器没有显示 404
- 页面标题、姓名和简介正确
- 所有链接都能打开
- 缩窄浏览器窗口后文字仍然可读
- 页面没有横向滚动条
- 刷新后样式和交互仍然存在

发现问题时，把现象具体告诉 Codex：

```text
手机宽度下“项目经历”超出屏幕。请先定位 CSS 原因，只修改相关样式，
不要重写整个页面。修改后说明如何验证。
```

---

## 八、用 Git 记录第一版

先配置提交身份，这通常只需要做一次：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

邮箱只用于标记提交作者，不等于 GitHub 登录密码。希望隐藏真实邮箱时，可以使用 GitHub 提供的 noreply 邮箱。

在 `my-homepage` 项目终端中运行：

```bash
git init
git branch -M main
git status
```

提交前先查看将要记录的内容：

```bash
git add .
git diff --cached
```

确认没有 `.env`、密码、Token 或私人文件后提交：

```bash
git commit -m "feat: create personal homepage"
git log --oneline
```

现在项目文件夹已经变成 Git 仓库。Git 保存的是文件变化历史，不会自动上传到互联网。

---

## 九、认识 GitHub 并推送代码

Git 和 GitHub 不是同一个东西：

```text
Git      = 电脑上的版本记录工具
GitHub   = 保存和协作 Git 仓库的网站
```

登录 [GitHub](https://github.com/)，创建一个 Public 仓库。个人主页建议将仓库命名为：

```text
你的GitHub用户名.github.io
```

例如用户名是 `xiaoming`，仓库名就是：

```text
xiaoming.github.io
```

创建远端仓库时不要勾选自动生成 README、`.gitignore` 或 License，避免和本地第一次推送产生冲突。

GitHub 会显示仓库地址。回到 VS Code 终端运行：

```bash
git remote add origin https://github.com/你的用户名/你的用户名.github.io.git
git remote -v
git push -u origin main
```

首次推送时通常会打开浏览器完成 GitHub 授权。不要在终端里输入 GitHub 账户密码；按 Git Credential Manager 或浏览器登录流程完成授权。

推送完成后刷新 GitHub 仓库页面，应该能看到 `index.html`、`style.css` 和 `script.js`。

---

## 十、用 GitHub Pages 发布网站

对于名为 `用户名.github.io` 的公开仓库，GitHub 通常会自动识别 Pages。你的地址是：

```text
https://你的用户名.github.io/
```

如果没有自动发布：

1. 打开仓库的 `Settings`。
2. 进入 `Pages`。
3. 在 Build and deployment 中选择从分支部署。
4. 选择 `main` 分支和仓库根目录。
5. 保存并等待部署完成。

可以参考 [GitHub Pages 官方文档](https://docs.github.com/pages/getting-started-with-github-pages/creating-a-github-pages-site)。

网站上线后，每次更新都走同一个循环：

```bash
git status
git add .
git diff --cached
git commit -m "feat: update homepage"
git push
```

GitHub Pages 收到新的 `main` 分支后会重新部署。页面没有立刻变化时，等待几分钟并强制刷新浏览器缓存。

---

## 十一、完成后的知识地图

到这里，你已经实际走过一遍现代 AI Coding 的最小闭环：

| 你做的动作 | 背后的概念 |
|------------|------------|
| VS Code 打开 `my-homepage` | 项目以文件夹为边界 |
| 在集成终端启动 Codex | 命令继承终端当前目录 |
| Codex 创建 HTML/CSS/JS | Agent 把自然语言需求转成文件修改 |
| Python 或 Node 启动服务器 | Runtime 在本地执行命令和程序 |
| `git commit` | 保存一个可恢复的版本快照 |
| `git push` | 把本地提交同步到 GitHub |
| GitHub Pages 部署 | 把静态文件发布为公开网站 |

下一步不是立刻学习更多框架，而是继续迭代这个项目：替换成真实经历、增加一个项目、修复一个移动端问题，并坚持每次修改都先预览、再提交、再推送。

---

## 常见问题

### 终端不在项目目录

先运行 `Get-Location` 或 `pwd`。如果路径不对，最简单的处理是关闭终端，在已经打开项目文件夹的 VS Code 中重新选择 `Terminal → New Terminal`。

### `codex` 无法识别

重新打开 VS Code 后运行 `npm --version`。npm 正常但 Codex 不存在时，再执行：

```bash
npm install -g @openai/codex@latest
```

### 本地正常，GitHub Pages 404

检查仓库是否为 Public、首页文件是否准确命名为小写 `index.html`、Pages 是否选择了 `main` 分支和根目录。

### Codex 改坏了页面

先看变化：

```bash
git diff
```

不要在不理解影响时执行破坏性 Git 命令。把 diff 和问题交给 Codex 分析，或回到最近一次明确保存的提交后再继续。

---

下一篇：[AI Coding 面试：解题流程与交付策略](../02-ai-coding-interview/index.html)
