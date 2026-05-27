#!/usr/bin/env node

/**
 * 牛客网面经抓取脚本 — 原生 CDP WebSocket
 *
 * 用法：
 *   node scrape.mjs [选项]
 *
 * 工作方式：
 *   使用独立的 Chrome 实例（~/.chrome-nowcoder），不影响日常 Chrome。
 *   首次使用需 --login 登录牛客，之后 cookie 永久保存在独立 profile 中。
 *   脚本自动检测：已有调试实例就直接连接，没有就启动新的。
 *
 * 选项：
 *   --login           打开浏览器让你登录牛客，cookie 保存在独立 profile 中
 *   --pages <n>       抓取列表页数 (默认 1)
 *   --keyword <kw>    按关键词筛选标题 (如 "AI"、"大模型")
 *   --search <query>  搜索模式，按关键词在搜索页抓取
 *   --out <dir>       输出目录 (默认 .claude/skills/scrape-nowcoder/nowcoder-output)
 *   --port <port>     Chrome 调试端口 (默认 9222)
 *   --delay <ms>      请求间隔毫秒数 (默认 2000，避免反爬)
 */

import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { homedir } from "node:os";
import { createInterface } from "node:readline";
import { existsSync } from "node:fs";

const CHROME_PATH =
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const CHROME_USER_DIR = join(homedir(), ".chrome-nowcoder");

// ─── 参数解析 ───────────────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    login: false,
    pages: 1,
    keyword: "",
    search: "",
    out: join(import.meta.dirname, "nowcoder-output"),
    port: 9222,
    delay: 2000,
  };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--login":
        opts.login = true;
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

async function isCdpReachable(port) {
  try {
    const res = await fetch(`http://127.0.0.1:${port}/json/version`);
    return res.ok;
  } catch { return false; }
}

async function launchChrome(port) {
  if (!existsSync(CHROME_PATH)) throw new Error(`Chrome not found at ${CHROME_PATH}`);
  if (!existsSync(CHROME_USER_DIR)) await mkdir(CHROME_USER_DIR, { recursive: true });
  const child = spawn(CHROME_PATH, [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${CHROME_USER_DIR}`,
  ], { detached: true, stdio: 'ignore' });
  child.unref();
  for (let i = 0; i < 30; i++) {
    await sleep(500);
    if (await isCdpReachable(port)) return;
  }
  throw new Error(`Chrome 启动失败：端口 ${port} 在 15 秒内未就绪`);
}

async function ensureCdp(port) {
  if (await isCdpReachable(port)) return;
  await launchChrome(port);
}

async function findPage(port, urlPattern) {
  await ensureCdp(port);
  const resp = await fetch(`http://127.0.0.1:${port}/json`);
  const pages = await resp.json();
  return pages.find(p => p.type === 'page' && p.url.includes(urlPattern));
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
  console.log("[login] 请确保 Chrome 已以调试端口启动并已登录牛客。");
  console.log("[login] 如未启动，脚本会自动启动独立 Chrome（~/.chrome-nowcoder）。");
  console.log();

  await ensureCdp(opts.port);
  const page = await findPage(opts.port, "nowcoder");
  if (page) {
    console.log("[login] ✅ 已找到牛客页面，登录态有效。可直接抓取。");
  } else {
    // 打开牛客首页让用户登录
    const newTab = await (await fetch(`http://127.0.0.1:${opts.port}/json/new?https://www.nowcoder.com/login`, { method: "PUT" })).json();
    console.log("[login] 已打开牛客登录页，请在浏览器中登录。");
    console.log("[login] 登录完成后按 Enter 继续...");
    await askUser("");
    console.log("[login] ✅ 完成。");
  }
}

// ─── 列表页抓取 ──────────────────────────────────────────────────────────────────

async function scrapeListPage(cdp, pageNum) {
  const url = "https://www.nowcoder.com/?type=818_1";
  await navigate(cdp, url);
  await sleep(3000);

  // 滚动加载更多内容
  await scrollToBottom(cdp, 8);
  await sleep(2000);

  const articles = await evaluate(
    cdp,
    `(() => {
      const items = [];
      const seen = new Set();

      // 标题元素：Tailwind 的 tw-font-bold 或 tw-overflow-hidden 标题 div
      // 它们的父级 a 标签包含文章链接
      const titleEls = document.querySelectorAll('.tw-font-bold, [class*="tw-overflow-hidden"][class*="hover:tw-text"]');

      titleEls.forEach(el => {
        const title = el.textContent.trim();
        if (!title || title.length < 4 || title.length > 150) return;

        // 找到包含链接的父级 a
        const linkEl = el.closest('a') || el.parentElement?.closest('a');
        let href = '';
        if (linkEl) {
          href = linkEl.href.split('?')[0];
        } else {
          // 尝试从同级找 feed-text 链接
          const card = el.closest('[class*="feed"]') || el.parentElement?.parentElement?.parentElement;
          const feedLink = card?.querySelector('a[href*="/feed/main/detail/"], a[href*="/discuss/"]');
          if (feedLink) href = feedLink.href.split('?')[0];
        }
        if (!href || seen.has(href)) return;
        if (!href.includes('/feed/') && !href.includes('/discuss/')) return;
        seen.add(href);

        // 找作者和预览
        const card = el.closest('[class*="feed"]') || el.parentElement?.parentElement?.parentElement?.parentElement;
        let author = '';
        let preview = '';
        if (card) {
          const authorEl = card.querySelector('[class*="name"], [class*="nick"]');
          if (authorEl) author = authorEl.textContent.trim();
          const previewEl = card.querySelector('.feed-text, [class*="text-gray"]');
          if (previewEl && previewEl !== el) preview = previewEl.textContent.trim().slice(0, 300);
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
  if (pageNum === 1) {
    // 第一页：直接导航到搜索 URL
    const url = `https://www.nowcoder.com/search/all?query=${encodeURIComponent(query)}&type=all&searchType=${encodeURIComponent("顶部导航栏")}`;
    await navigate(cdp, url);
    await sleep(3000);
  } else {
    // 后续页：点击分页按钮
    await evaluate(
      cdp,
      `(() => {
        var pager = document.querySelector("ul.pager");
        if (!pager) return false;
        var items = pager.querySelectorAll("li");
        for (var i = 0; i < items.length; i++) {
          if (items[i].textContent.trim() === "${pageNum}") {
            items[i].click();
            return true;
          }
        }
        return false;
      })()`
    );
    await sleep(3000);
  }

  const articles = await evaluate(
    cdp,
    `(() => {
      var items = [];
      var seen = {};
      var links = document.querySelectorAll("a");

      for (var i = 0; i < links.length; i++) {
        var a = links[i];
        var href = (a.href || "").split("?")[0];
        if (!href.includes("/feed/main/detail/") && !href.includes("/discuss/")) continue;
        if (seen[href]) continue;

        var title = (a.textContent || "").trim();
        if (!title || title.length < 4) continue;
        if (title.includes("查看更多") || title.includes("查看全部")) continue;

        title = title.replace(/\\s+[\\d.]+[WwKk万]?\\s*$/, "").trim();
        if (title.length > 150 || title.length < 4) continue;

        // 搜索结果中进一步过滤：必须包含面试相关词
        var interviewKeywords = ["面经", "面试", "一面", "二面", "三面", "HR面", "实习", "秋招", "春招", "暑期", "校招", "笔试"];
        var isInterview = false;
        for (var k = 0; k < interviewKeywords.length; k++) {
          if (title.includes(interviewKeywords[k])) { isInterview = true; break; }
        }
        if (!isInterview) continue;

        seen[href] = true;
        items.push({ title: title, url: href, author: "", preview: "" });
      }

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

function extractDate(timeStr) {
  if (!timeStr) return "unknown";
  const m = timeStr.match(/(\d{4})[年\-\/.](\d{1,2})[月\-\/.](\d{1,2})/);
  if (m) return `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}`;
  const m2 = timeStr.match(/(\d{1,2})[月\-\/.](\d{1,2})/);
  if (m2) {
    const year = new Date().getFullYear();
    return `${year}-${m2[1].padStart(2, "0")}-${m2[2].padStart(2, "0")}`;
  }
  return "unknown";
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

  // 连接 Chrome 调试端口（已运行就直连，否则启动独立实例）
  await ensureCdp(opts.port);
  let cdp = null;

  try {
    // 获取 page target（优先用已有的 nowcoder tab，否则新建）
    const targetsRes = await fetch(`http://127.0.0.1:${opts.port}/json`);
    const targets = await targetsRes.json();
    let pageTarget = targets.find((t) => t.type === "page" && t.url.includes("nowcoder"));
    if (!pageTarget) pageTarget = targets.find((t) => t.type === "page");
    if (!pageTarget) {
      const newTabRes = await fetch(`http://127.0.0.1:${opts.port}/json/new?about:blank`, { method: "PUT" });
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

        const datePrefix = extractDate(detail.time);
        const filename = `${datePrefix}-${sanitizeFilename(detail.title)}.md`;
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
    console.log(`[scrape]    YYYY-MM-DD-xx.md — 单篇（按发布日期命名）`);
    console.log(`[scrape] ════════════════════════════════════════\n`);
  } finally {
    if (cdp) cdp.close();
  }
}

main().catch((err) => {
  console.error(`[scrape] 致命错误: ${err.message}`);
  process.exit(1);
});
