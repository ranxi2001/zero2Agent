#!/usr/bin/env node

/**
 * 牛客网面经抓取脚本 — 原生 CDP WebSocket，复用已有 Chrome profile
 *
 * 用法：
 *   node scrape.mjs [选项]
 *
 * 工作方式：
 *   1. 关闭当前 Chrome（需用户确认）
 *   2. 用你原有的 Chrome profile 重新启动 + 启用调试端口
 *   3. 抓取完成后关闭 Chrome（你可以正常重新打开）
 *
 * 选项：
 *   --login           打开浏览器让你登录牛客，cookie 保存在 debug profile 中
 *   --pages <n>       抓取列表页数 (默认 1)
 *   --keyword <kw>    按关键词筛选标题 (如 "AI"、"大模型")
 *   --out <dir>       输出目录 (默认 ./nowcoder-output)
 *   --port <port>     Chrome 调试端口 (默认 9222)
 *   --no-headless     显示浏览器窗口（默认 headless，加此参数可看到抓取过程）
 *   --delay <ms>      请求间隔毫秒数 (默认 2000，避免反爬)
 *   --visible         同 --no-headless
 */

import { spawn, execSync } from "node:child_process";
import { mkdir, writeFile, symlink, cp, rm, access } from "node:fs/promises";
import { join } from "node:path";
import { homedir } from "node:os";
import { createInterface } from "node:readline";
import { existsSync } from "node:fs";

const USER_CHROME_DIR = join(
  homedir(),
  "Library",
  "Application Support",
  "Google",
  "Chrome"
);
const DEBUG_PROFILE_DIR = join(homedir(), ".chrome-debug-nowcoder");
const CHROME_PATH =
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

// ─── 参数解析 ───────────────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    login: false,
    pages: 1,
    keyword: "",
    search: "",
    out: join(process.cwd(), "nowcoder-output"),
    port: 9222,
    headless: true,
    delay: 2000,
  };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--login":
        opts.login = true;
        opts.headless = false;
        break;
      case "--pages":
        opts.pages = parseInt(args[++i], 10);
        break;
      case "--keyword":
        opts.keyword = args[++i];
        break;
      case "--search":
        opts.search = args[++i];
        break;
      case "--out":
        opts.out = args[++i];
        break;
      case "--port":
        opts.port = parseInt(args[++i], 10);
        break;
      case "--no-headless":
      case "--visible":
        opts.headless = false;
        break;
      case "--delay":
        opts.delay = parseInt(args[++i], 10);
        break;
    }
  }
  return opts;
}

// ─── CDP 封装 ────────────────────────────────────────────────────────────────────

class CDPSession {
  constructor(wsUrl) {
    this._wsUrl = wsUrl;
    this._ws = null;
    this._id = 0;
    this._callbacks = new Map();
    this._events = [];
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this._ws = new WebSocket(this._wsUrl);
      this._ws.addEventListener("open", () => resolve());
      this._ws.addEventListener("error", (e) => reject(e));
      this._ws.addEventListener("message", (evt) => {
        const msg = JSON.parse(
          typeof evt.data === "string" ? evt.data : evt.data.toString()
        );
        if (msg.id !== undefined && this._callbacks.has(msg.id)) {
          const { resolve, reject } = this._callbacks.get(msg.id);
          this._callbacks.delete(msg.id);
          if (msg.error) reject(new Error(JSON.stringify(msg.error)));
          else resolve(msg.result);
        } else if (msg.method) {
          this._events.push(msg);
        }
      });
    });
  }

  send(method, params = {}) {
    const id = ++this._id;
    return new Promise((resolve, reject) => {
      this._callbacks.set(id, { resolve, reject });
      this._ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async waitForEvent(name, timeout = 30000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      const idx = this._events.findIndex((e) => e.method === name);
      if (idx !== -1) return this._events.splice(idx, 1)[0];
      await sleep(100);
    }
    throw new Error(`Timeout waiting for event: ${name}`);
  }

  drainEvents(name) {
    const matched = this._events.filter((e) => e.method === name);
    this._events = this._events.filter((e) => e.method !== name);
    return matched;
  }

  close() {
    if (this._ws) this._ws.close();
  }
}

// ─── 工具函数 ────────────────────────────────────────────────────────────────────

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitForChrome(port, maxRetries = 40) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (res.ok) return await res.json();
    } catch {}
    await sleep(500);
  }
  throw new Error(
    `Chrome did not start on port ${port} after ${maxRetries * 500}ms`
  );
}

function isChromeRunning() {
  try {
    const result = execSync("pgrep -x 'Google Chrome'", {
      encoding: "utf-8",
    });
    return result.trim().length > 0;
  } catch {
    return false;
  }
}

function quitChrome() {
  try {
    execSync(
      `osascript -e 'tell application "Google Chrome" to quit'`,
      { stdio: "ignore", timeout: 5000 }
    );
  } catch {
    execSync("pkill -x 'Google Chrome' 2>/dev/null || true", {
      stdio: "ignore",
    });
  }
}

async function prepareDebugProfile() {
  // Chrome 拒绝在默认 profile 路径上开启远程调试
  // 方案：创建独立目录 + symlink Default profile，保留登录态
  const lockFiles = ["SingletonLock", "SingletonSocket", "SingletonCookie"];
  for (const f of lockFiles) {
    const p = join(DEBUG_PROFILE_DIR, f);
    if (existsSync(p)) await rm(p, { force: true });
  }

  if (!existsSync(DEBUG_PROFILE_DIR)) {
    await mkdir(DEBUG_PROFILE_DIR, { recursive: true });
  }

  const defaultLink = join(DEBUG_PROFILE_DIR, "Default");
  if (!existsSync(defaultLink)) {
    await symlink(join(USER_CHROME_DIR, "Default"), defaultLink);
  }

  const localState = join(DEBUG_PROFILE_DIR, "Local State");
  if (!existsSync(localState)) {
    const src = join(USER_CHROME_DIR, "Local State");
    if (existsSync(src)) {
      await cp(src, localState);
    }
  }
}

function launchChrome(port, headless) {
  const args = [
    `--remote-debugging-port=${port}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    `--user-data-dir=${DEBUG_PROFILE_DIR}`,
    "--profile-directory=Default",
  ];
  if (headless) args.push("--headless=new");

  const child = spawn(CHROME_PATH, args, {
    stdio: "ignore",
    detached: true,
  });
  child.unref();
  return child;
}

function askUser(question) {
  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

// ─── 页面操作 ────────────────────────────────────────────────────────────────────

async function navigate(cdp, url) {
  cdp.drainEvents("Page.loadEventFired");
  await cdp.send("Page.navigate", { url });
  await cdp.waitForEvent("Page.loadEventFired", 30000);
  await sleep(2000);
}

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  if (result.exceptionDetails) {
    throw new Error(
      `Eval error: ${JSON.stringify(result.exceptionDetails.text || result.exceptionDetails)}`
    );
  }
  return result.result.value;
}

async function scrollToBottom(cdp, maxScrolls = 10) {
  for (let i = 0; i < maxScrolls; i++) {
    const atBottom = await evaluate(
      cdp,
      `(() => {
        window.scrollBy(0, window.innerHeight);
        return document.documentElement.scrollTop + window.innerHeight >= document.documentElement.scrollHeight - 100;
      })()`
    );
    await sleep(1000);
    if (atBottom) break;
  }
}

// ─── 登录模式 ────────────────────────────────────────────────────────────────────

async function loginMode(opts) {
  console.log("[login] 登录模式 — 打开浏览器，自动检测登录状态");
  console.log(`[login] Profile 保存位置: ${DEBUG_PROFILE_DIR}`);
  console.log();

  if (isChromeRunning()) {
    console.log("[login] 需要先关闭当前 Chrome...");
    const answer = await askUser("[login] 确认关闭 Chrome？(y/n) ");
    if (answer.toLowerCase() !== "y") {
      console.log("[login] 已取消。");
      process.exit(0);
    }
    quitChrome();
    await sleep(2000);
  }

  await prepareDebugProfile();
  const chrome = launchChrome(opts.port, false);

  try {
    const versionInfo = await waitForChrome(opts.port);
    console.log(`[login] Chrome 已启动: ${versionInfo.Browser}`);

    const targets = await (await fetch(`http://127.0.0.1:${opts.port}/json`)).json();
    let pageTarget = targets.find((t) => t.type === "page");
    if (!pageTarget) {
      pageTarget = await (
        await fetch(`http://127.0.0.1:${opts.port}/json/new?about:blank`, { method: "PUT" })
      ).json();
    }

    const cdp = new CDPSession(pageTarget.webSocketDebuggerUrl);
    await cdp.connect();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");

    // 导航到登录页
    await navigate(cdp, "https://www.nowcoder.com/login");
    console.log("[login] ════════════════════════════════════════════════");
    console.log("[login]  浏览器已打开牛客登录页，请扫码/账密登录");
    console.log("[login]  正在自动检测登录状态...");
    console.log("[login] ════════════════════════════════════════════════");

    // 轮询检测登录成功（最长等 120 秒）
    const maxWait = 120000;
    const pollInterval = 2000;
    const start = Date.now();
    let loggedIn = false;

    while (Date.now() - start < maxWait) {
      await sleep(pollInterval);
      try {
        const result = await evaluate(
          cdp,
          `(() => {
            // 登录成功后通常会跳转离开 /login 页面
            if (!location.href.includes('/login')) return true;
            // 或者页面上出现了用户头像
            if (document.querySelector('[class*="avatar"]')) return true;
            // 或者 cookie 中出现登录标识
            if (document.cookie.includes('t=') || document.cookie.includes('token')) return true;
            return false;
          })()`
        );
        if (result) {
          loggedIn = true;
          break;
        }
      } catch {
        // CDP 可能因页面跳转暂时断开，忽略
      }
      const elapsed = Math.round((Date.now() - start) / 1000);
      process.stdout.write(`\r[login] 等待登录中... ${elapsed}s`);
    }
    console.log();

    if (loggedIn) {
      // 等一下让 cookie 完全写入
      await sleep(2000);
      console.log("[login] ✅ 检测到登录成功！Cookie 已保存。");
      console.log("[login] 后续运行 scrape.mjs 将自动使用此登录态。");
    } else {
      console.log("[login] ⚠️  等待超时，未检测到登录。");
      console.log("[login] 请重试: node scrape.mjs --login");
    }

    cdp.close();
  } finally {
    chrome.kill();
    console.log("[login] Chrome 已关闭。");
  }
}

// ─── 列表页抓取 ──────────────────────────────────────────────────────────────────

async function scrapeListPage(cdp, pageNum) {
  const url = "https://www.nowcoder.com/?type=818_1";
  await navigate(cdp, url);
  await sleep(2000);

  // SPA 可能默认显示"推荐"，需要点击"面经"tab
  await evaluate(
    cdp,
    `(() => {
      const tabs = document.querySelectorAll('a, span, div, li');
      for (const tab of tabs) {
        if (tab.textContent.trim() === '面经' && tab.offsetHeight > 0) {
          tab.click();
          return true;
        }
      }
      return false;
    })()`
  );
  await sleep(4000);

  // 多次滚动加载，等待懒加载内容
  for (let round = 0; round < 3; round++) {
    await scrollToBottom(cdp, 5);
    await sleep(2000);
  }

  const articles = await evaluate(
    cdp,
    `(() => {
      const items = [];
      const seen = new Set();

      const links = document.querySelectorAll('a[href*="/discuss/"]');
      links.forEach(a => {
        const href = a.href.split('?')[0];
        if (seen.has(href)) return;

        let title = a.textContent.trim();
        if (!title || title.length < 4) return;
        // 过滤非文章链接
        if (['查看更多', '查看全部', '登录', '注册', '真题和解析', '查看详情'].some(x => title.includes(x))) return;

        // 清理标题：去除热度数字后缀（如 "标题 ... 标题 1.1W"）
        const dupeMatch = title.match(/^(\\d+\\s+)?(.+?)\\s+\\.{3}\\s+.+$/);
        if (dupeMatch) {
          title = dupeMatch[2].trim();
        }
        // 去除尾部数字(阅读量)
        title = title.replace(/\\s+[\\d.]+[WwKk万]?\\s*$/, '').trim();

        if (title.length > 150 || title.length < 4) return;

        // 面经贴过滤：标题必须含面试相关关键词
        const interviewKeywords = ['面', '面经', '面试', '一面', '二面', '三面', 'HR面', '笔试', 'OC', 'offer'];
        const isInterview = interviewKeywords.some(kw => title.includes(kw));
        if (!isInterview) return;

        seen.add(href);

        const card = a.closest('[class*="feed"], [class*="discuss"], [class*="post"], [class*="card"], [class*="item"]') || a.parentElement?.parentElement;
        let author = '';
        let preview = '';
        if (card) {
          const authorEl = card.querySelector('[class*="name"], [class*="author"], [class*="nick"]');
          if (authorEl && authorEl !== a) author = authorEl.textContent.trim();
          const previewEl = card.querySelector('[class*="content"], [class*="desc"], [class*="text"], [class*="summary"]');
          if (previewEl && previewEl !== a) preview = previewEl.textContent.trim().slice(0, 300);
        }

        items.push({ title, url: href, author, preview });
      });

      return items;
    })()`
  );

  return articles || [];
}

// ─── 搜索页抓取 ──────────────────────────────────────────────────────────────────

async function scrapeSearchPage(cdp, query, pageNum) {
  const url = `https://www.nowcoder.com/search?type=discuss&query=${encodeURIComponent(query)}&page=${pageNum}&order=time`;
  await navigate(cdp, url);
  await sleep(3000);

  // 滚动加载
  await scrollToBottom(cdp, 3);
  await sleep(2000);

  const articles = await evaluate(
    cdp,
    `(() => {
      const items = [];
      const seen = new Set();

      const links = document.querySelectorAll('a[href*="/discuss/"]');
      links.forEach(a => {
        const href = a.href.split('?')[0];
        if (seen.has(href)) return;

        let title = a.textContent.trim();
        if (!title || title.length < 4) return;
        if (['查看更多', '查看全部', '登录', '注册'].some(x => title.includes(x))) return;

        title = title.replace(/\\s+[\\d.]+[WwKk万]?\\s*$/, '').trim();
        if (title.length > 150 || title.length < 4) return;

        // 搜索结果中进一步过滤：必须包含面试相关词
        const interviewKeywords = ['面经', '面试', '一面', '二面', '三面', 'HR面', '实习'];
        const isInterview = interviewKeywords.some(kw => title.includes(kw));
        if (!isInterview) return;

        seen.add(href);

        const card = a.closest('[class*="search"], [class*="result"], [class*="item"], [class*="card"]') || a.parentElement?.parentElement;
        let author = '';
        if (card) {
          const authorEl = card.querySelector('[class*="name"], [class*="author"], [class*="nick"]');
          if (authorEl && authorEl !== a) author = authorEl.textContent.trim();
        }

        items.push({ title, url: href, author, preview: '' });
      });

      return items;
    })()`
  );

  return articles || [];
}

// ─── 详情页抓取 ──────────────────────────────────────────────────────────────────

async function scrapeArticleDetail(cdp, url) {
  await navigate(cdp, url);
  await sleep(2000);

  // 点击展开按钮
  await evaluate(
    cdp,
    `(() => {
      const allEls = document.querySelectorAll('span, button, a, div');
      for (const el of allEls) {
        const text = el.textContent.trim();
        if ((text === '查看更多' || text === '展开全文' || text === '展开') && el.offsetHeight > 0) {
          el.click();
          return true;
        }
      }
      return false;
    })()`
  );
  await sleep(1500);

  await scrollToBottom(cdp, 5);

  const detail = await evaluate(
    cdp,
    `(() => {
      const titleEl = document.querySelector(
        'h1, [class*="detail"] [class*="title"], [class*="discuss-title"]'
      );
      const title = titleEl ? titleEl.textContent.trim() : document.title.split(' - ')[0];

      const authorEl = document.querySelector(
        '[class*="author"] [class*="name"], [class*="nickname"], [class*="user-name"]'
      );
      const author = authorEl ? authorEl.textContent.trim() : '';

      const timeEl = document.querySelector(
        '[class*="time"], [class*="date"], time'
      );
      const time = timeEl ? timeEl.textContent.trim() : '';

      let content = '';
      const selectors = [
        '.nc-post-content',
        '[class*="post-content"]',
        '[class*="detail-content"]',
        '[class*="discuss-main"] [class*="content"]',
        '[class*="rich-text"]',
        '[class*="markdown-body"]',
        'article',
      ];
      for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.innerText.trim().length > 50) {
          content = el.innerText.trim();
          break;
        }
      }
      if (!content) {
        const fallbacks = ['main', '[class*="detail"]', '#__next'];
        for (const sel of fallbacks) {
          const el = document.querySelector(sel);
          if (el && el.innerText.trim().length > 100) {
            content = el.innerText.trim();
            break;
          }
        }
      }

      const tags = [...document.querySelectorAll('[class*="tag"] span, [class*="tag"] a')]
        .map(t => t.textContent.trim().replace(/^#/, ''))
        .filter(t => t.length > 0 && t.length < 30);

      return { title, author, time, content, tags, url: location.href };
    })()`
  );

  return detail;
}

// ─── Markdown 格式化 ─────────────────────────────────────────────────────────────

function toMarkdown(article) {
  const lines = [];
  lines.push(`# ${article.title}\n`);
  if (article.author || article.time) {
    const meta = [article.author, article.time].filter(Boolean).join(" | ");
    lines.push(`> ${meta}\n`);
  }
  if (article.tags && article.tags.length > 0) {
    lines.push(`**标签**：${article.tags.join("、")}\n`);
  }
  lines.push(`**来源**：${article.url}\n`);
  lines.push("---\n");
  lines.push(article.content || "(内容为空)");
  lines.push("");
  return lines.join("\n");
}

function sanitizeFilename(name) {
  return name
    .replace(/[\/\\:*?"<>|\n\r]/g, "")
    .replace(/\s+/g, "-")
    .slice(0, 50);
}

// ─── 主流程 ──────────────────────────────────────────────────────────────────────

async function main() {
  const opts = parseArgs();

  // 登录模式
  if (opts.login) {
    await loginMode(opts);
    return;
  }

  console.log(`[scrape] 牛客面经抓取 — CDP 方案`);
  const mode = opts.search ? `搜索:"${opts.search}"` : `面经tab`;
  console.log(`[scrape] 配置: mode=${mode}, pages=${opts.pages}, keyword="${opts.keyword}", delay=${opts.delay}ms`);
  console.log(`[scrape] 输出目录: ${opts.out}`);
  console.log();

  // 检查并关闭现有 Chrome（因为同一 profile 不能多开）
  if (isChromeRunning()) {
    console.log("[scrape] 检测到 Chrome 正在运行");
    const answer = await askUser("[scrape] 需要关闭 Chrome 以复用你的登录状态，确认？(y/n) ");
    if (answer.toLowerCase() !== "y") {
      console.log("[scrape] 已取消。");
      process.exit(0);
    }
    console.log("[scrape] 正在关闭 Chrome...");
    quitChrome();
    await sleep(2000);
  }

  // 准备调试用 profile（symlink 用户真实 profile，绕过 Chrome 安全限制）
  console.log("[scrape] 准备调试 profile...");
  await prepareDebugProfile();

  // 启动 Chrome
  console.log(`[scrape] 启动 Chrome (headless=${opts.headless})...`);
  const chrome = launchChrome(opts.port, opts.headless);
  let cdp = null;

  try {
    const versionInfo = await waitForChrome(opts.port);
    console.log(`[scrape] Chrome 已就绪: ${versionInfo.Browser}`);

    // 获取或创建 page target
    let pageTarget;
    const targetsRes = await fetch(`http://127.0.0.1:${opts.port}/json`);
    const targets = await targetsRes.json();
    pageTarget = targets.find((t) => t.type === "page");

    if (!pageTarget) {
      // Chrome 148+ 要求 PUT 方法创建新 tab
      const newTabRes = await fetch(`http://127.0.0.1:${opts.port}/json/new?about:blank`, {
        method: "PUT",
      });
      pageTarget = await newTabRes.json();
    }

    // CDP 连接
    cdp = new CDPSession(pageTarget.webSocketDebuggerUrl);
    await cdp.connect();
    console.log("[scrape] CDP 连接成功\n");

    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");

    // 抓列表
    const listMode = opts.search ? "搜索" : "面经tab";
    console.log(`[scrape] === 抓取面经列表（${listMode}） ===`);
    let allArticles = [];

    for (let p = 1; p <= opts.pages; p++) {
      console.log(`[scrape] 第 ${p}/${opts.pages} 页...`);
      const articles = opts.search
        ? await scrapeSearchPage(cdp, opts.search, p)
        : await scrapeListPage(cdp, p);
      console.log(`[scrape]   → ${articles.length} 篇`);
      allArticles.push(...articles);
      if (p < opts.pages) await sleep(opts.delay);
    }

    // 去重
    const seen = new Set();
    allArticles = allArticles.filter((a) => {
      if (seen.has(a.url)) return false;
      seen.add(a.url);
      return true;
    });

    // 关键词筛选
    if (opts.keyword) {
      const kw = opts.keyword.toLowerCase();
      allArticles = allArticles.filter(
        (a) =>
          a.title.toLowerCase().includes(kw) ||
          a.preview.toLowerCase().includes(kw)
      );
      console.log(
        `[scrape] 关键词 "${opts.keyword}" 筛选后: ${allArticles.length} 篇`
      );
    }

    console.log(`[scrape] 去重后共 ${allArticles.length} 篇\n`);

    // 输出目录
    await mkdir(opts.out, { recursive: true });

    // 索引文件
    const indexLines = [
      "# 牛客面经抓取结果\n",
      `抓取时间：${new Date().toLocaleString("zh-CN")}\n`,
      `筛选：${opts.keyword || "无"} | 页数：${opts.pages}\n`,
      "| # | 标题 | 作者 |",
      "|---|------|------|",
    ];
    allArticles.forEach((a, i) => {
      indexLines.push(`| ${i + 1} | [${a.title}](${a.url}) | ${a.author} |`);
    });
    await writeFile(join(opts.out, "index.md"), indexLines.join("\n"), "utf-8");

    // 逐篇抓详情
    console.log("[scrape] === 抓取文章详情 ===");
    const results = [];
    for (let i = 0; i < allArticles.length; i++) {
      const article = allArticles[i];
      console.log(
        `[scrape] [${i + 1}/${allArticles.length}] ${article.title}`
      );
      try {
        const detail = await scrapeArticleDetail(cdp, article.url);
        results.push(detail);

        const filename = `${String(i + 1).padStart(2, "0")}-${sanitizeFilename(detail.title)}.md`;
        await writeFile(join(opts.out, filename), toMarkdown(detail), "utf-8");
        console.log(`[scrape]   ✅ ${detail.content.length} 字`);
      } catch (err) {
        console.error(`[scrape]   ❌ ${err.message}`);
        results.push({
          ...article,
          content: `(抓取失败: ${err.message})`,
          tags: [],
        });
      }

      if (i < allArticles.length - 1) await sleep(opts.delay);
    }

    // 合并文件
    const allMd = results.map((r, i) =>
      toMarkdown({ ...r, title: r.title || allArticles[i].title })
    );
    await writeFile(
      join(opts.out, "all-in-one.md"),
      allMd.join("\n\n---\n\n"),
      "utf-8"
    );

    console.log(`\n[scrape] ════════════════════════════════════════`);
    console.log(`[scrape] ✅ 完成！共 ${results.length} 篇面经`);
    console.log(`[scrape] 📂 ${opts.out}`);
    console.log(`[scrape]    index.md       — 目录`);
    console.log(`[scrape]    all-in-one.md  — 合并版`);
    console.log(`[scrape]    01-xx.md ...   — 单篇`);
    console.log(`[scrape] ════════════════════════════════════════\n`);
  } finally {
    if (cdp) cdp.close();
    chrome.kill();
    console.log("[scrape] Chrome 已关闭，你可以正常重新打开浏览器。");
  }
}

main().catch((err) => {
  console.error(`[scrape] 致命错误: ${err.message}`);
  process.exit(1);
});
