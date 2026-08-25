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
 *   --home            首页推荐流模式
 *   --topic <url|id>  话题流模式；支持 subject URL、完整 URL 或 type 值 (默认 818_1)
 *   --pages <n>       最大页数；首页模式下表示连续滚动批次 (默认 1)
 *   --since <date>    话题接口或搜索模式仅保留该日期及之后内容
 *   --until <date>    话题接口或搜索模式仅保留该日期及之前内容
 *   --keyword <kw>    按关键词筛选标题 (如 "AI"、"大模型")
 *   --search <query>  面经搜索模式（subType=818），按关键词翻页抓取
 *   --out <dir>       输出目录 (默认 .claude/skills/scrape-nowcoder/nowcoder-output)
 *   --port <port>     Chrome 调试端口 (默认 9222)
 *   --delay <ms>      请求间隔毫秒数 (默认 2000，避免反爬)
 */

import { spawn } from "node:child_process";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { homedir } from "node:os";
import { createInterface } from "node:readline";
import { existsSync } from "node:fs";

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  process.platform === "win32" && process.env.PROGRAMFILES
    ? join(process.env.PROGRAMFILES, "Google", "Chrome", "Application", "chrome.exe")
    : null,
  process.platform === "win32" && process.env["PROGRAMFILES(X86)"]
    ? join(process.env["PROGRAMFILES(X86)"], "Google", "Chrome", "Application", "chrome.exe")
    : null,
  process.platform === "win32" && process.env.LOCALAPPDATA
    ? join(process.env.LOCALAPPDATA, "Google", "Chrome", "Application", "chrome.exe")
    : null,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].filter(Boolean);
const CHROME_PATH = CHROME_CANDIDATES.find(existsSync);
const CHROME_USER_DIR = join(homedir(), ".chrome-nowcoder");
const SEARCH_INTERVIEW_SUBTYPE = "818";

// ─── 参数解析 ───────────────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    login: false,
    home: false,
    topic: "",
    pages: 1,
    since: "",
    until: "",
    keyword: "",
    search: "",
    out: join(import.meta.dirname, "nowcoder-output"),
    port: 9222,
    delay: 2000,
  };
  const nextValue = (index, option) => {
    const value = args[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`${option} 缺少参数值`);
    }
    return value;
  };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--login":
        opts.login = true;
        break;
      case "--home":
        opts.home = true;
        break;
      case "--topic":
        opts.topic = nextValue(i, args[i]);
        i++;
        break;
      case "--pages":
        opts.pages = Number(nextValue(i, args[i]));
        i++;
        break;
      case "--since":
        opts.since = nextValue(i, args[i]);
        i++;
        break;
      case "--until":
        opts.until = nextValue(i, args[i]);
        i++;
        break;
      case "--keyword":
        opts.keyword = nextValue(i, args[i]);
        i++;
        break;
      case "--search":
        opts.search = nextValue(i, args[i]);
        i++;
        break;
      case "--out":
        opts.out = nextValue(i, args[i]);
        i++;
        break;
      case "--port":
        opts.port = Number(nextValue(i, args[i]));
        i++;
        break;
      case "--delay":
        opts.delay = Number(nextValue(i, args[i]));
        i++;
        break;
      default:
        throw new Error(`未知参数: ${args[i]}`);
    }
  }
  if (!Number.isInteger(opts.pages) || opts.pages < 1) {
    throw new Error("--pages 必须是大于等于 1 的整数");
  }
  if (!Number.isInteger(opts.port) || opts.port < 1 || opts.port > 65535) {
    throw new Error("--port 必须是 1 到 65535 之间的整数");
  }
  if (!Number.isFinite(opts.delay) || opts.delay < 0) {
    throw new Error("--delay 必须是大于等于 0 的数字");
  }
  return opts;
}

function resolveFeedMode(opts) {
  const explicitModes = [opts.home, Boolean(opts.topic), Boolean(opts.search)]
    .filter(Boolean).length;
  if (explicitModes > 1) {
    throw new Error("--home、--topic 和 --search 只能选择一种模式");
  }
  if (opts.search) {
    return {
      mode: "search",
      label: `面经搜索:subType=${SEARCH_INTERVIEW_SUBTYPE}, query=\"${opts.search}\"`,
    };
  }
  if (opts.home) {
    return { mode: "home", label: "首页推荐流", url: "https://www.nowcoder.com/" };
  }

  const topic = opts.topic || "818_1";
  if (/^https?:\/\//i.test(topic)) {
    const url = new URL(topic);
    if (url.hostname !== "nowcoder.com" && !url.hostname.endsWith(".nowcoder.com")) {
      throw new Error(`--topic 只接受牛客网 URL，当前为 ${url.hostname}`);
    }
    const type = url.searchParams.get("type") || "";
    const match = type.match(/^(\d+)_(\d+)$/);
    const subjectMatch = url.pathname.match(/^\/creation\/subject\/([a-zA-Z0-9]+)\/?$/);
    return {
      mode: "topic",
      label: subjectMatch
        ? `话题专题:subject=${subjectMatch[1]}`
        : `话题流:${url.href}`,
      url: url.href,
      topicApi: match ? { tabId: match[1], categoryType: match[2] } : null,
      subjectScroll: subjectMatch ? { uuid: subjectMatch[1] } : null,
    };
  }
  const match = topic.match(/^(\d+)_(\d+)$/);
  return {
    mode: "topic",
    label: `话题流:type=${topic}`,
    url: `https://www.nowcoder.com/?type=${encodeURIComponent(topic)}`,
    topicApi: match ? { tabId: match[1], categoryType: match[2] } : null,
  };
}

function parseDateOption(value, option) {
  if (!value) return 0;
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) {
    throw new Error(`${option} 格式应为 YYYY-MM-DD，当前为 ${value}`);
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth[month - 1]) {
    throw new Error(`${option} 不是有效日期，当前为 ${value}`);
  }
  const timestamp = Date.parse(`${value}T00:00:00+08:00`);
  if (!Number.isFinite(timestamp)) throw new Error(`无法解析 ${option} ${value}`);
  return timestamp;
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
  if (!CHROME_PATH) {
    throw new Error(`Chrome not found. Checked: ${CHROME_CANDIDATES.join(", ")}`);
  }
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

async function extractListArticles(cdp) {
  return (await evaluate(
    cdp,
    `(() => {
      const items = [];
      const seen = new Set();

      // 首页和话题流的标题不是链接，正文预览才是链接；从链接反查卡片标题。
      const links = document.querySelectorAll(
        'a[href*="/feed/main/detail/"], a[href*="/discuss/"]'
      );

      links.forEach(linkEl => {
        const href = linkEl.href.split('?')[0];
        if (!href || seen.has(href)) return;
        if (!href.includes('/feed/') && !href.includes('/discuss/')) return;
        seen.add(href);

        const card = linkEl.closest('[class*="tw-px-5"][class*="tw-relative"]')
          || linkEl.closest('article, li')
          || linkEl.parentElement?.parentElement;
        const titleEl = card?.querySelector(
          '.tw-font-bold, h1, h2, h3, [class*="title"]'
        );
        const linkText = linkEl.textContent.trim().replace(/\s+/g, ' ');
        let title = titleEl?.textContent.trim().replace(/\s+/g, ' ') || linkText;
        if (!title || title.length < 4) return;
        if (title.length > 150) title = title.slice(0, 147) + '...';

        let author = '';
        let preview = linkText.slice(0, 500);
        if (card) {
          const authorEl = card.querySelector(
            '[class*="user-nickname"], [class*="author"] [class*="name"], [class*="nick"]'
          );
          if (authorEl) author = authorEl.textContent.trim();
          const previewEl = card.querySelector('.feed-text');
          if (previewEl) preview = previewEl.textContent.trim().replace(/\s+/g, ' ').slice(0, 500);
        }

        items.push({ title, url: href, author, preview });
      });

      return items;
    })()`
  )) || [];
}

async function getFeedState(cdp) {
  return evaluate(
    cdp,
    `(() => ({
      height: document.documentElement.scrollHeight,
      top: document.documentElement.scrollTop,
      links: document.querySelectorAll('a[href*="/feed/main/detail/"], a[href*="/discuss/"]').length
    }))()`
  );
}

async function scrapeListPage(cdp, pageNum, seenUrls, url) {
  if (pageNum === 1) {
    await navigate(cdp, url);
    await sleep(3000);
  }

  const articles = [];
  let staleRounds = 0;

  // 首页和非标准话题 URL 使用无限滚动流。每个 --pages 批次
  // 最多触发 8 次懒加载，并在连续两轮没有新链接时提前停止。
  for (let i = 0; i < 8 && staleRounds < 2; i++) {
    const before = await getFeedState(cdp);
    const beforeCount = articles.length;
    const visible = await extractListArticles(cdp);
    for (const article of visible) {
      if (seenUrls.has(article.url)) continue;
      seenUrls.add(article.url);
      articles.push(article);
    }

    await evaluate(
      cdp,
      `window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' })`
    );
    await sleep(2000);

    const loaded = await extractListArticles(cdp);
    for (const article of loaded) {
      if (seenUrls.has(article.url)) continue;
      seenUrls.add(article.url);
      articles.push(article);
    }
    const after = await getFeedState(cdp);
    const grew = after.height > before.height || articles.length > beforeCount;
    staleRounds = grew ? 0 : staleRounds + 1;
  }

  return articles;
}

async function waitForFeedGrowth(cdp, before, timeoutMs = 12000) {
  const deadline = Date.now() + timeoutMs;
  let current = before;
  while (Date.now() < deadline) {
    await sleep(400);
    current = await getFeedState(cdp);
    if (current.links > before.links || current.height > before.height) {
      return true;
    }
  }
  return false;
}

async function scrapeSubjectBatch(cdp, feed, pageNum, seenUrls) {
  if (pageNum === 1) {
    await navigate(cdp, feed.url);
    await sleep(3000);
  } else {
    const before = await getFeedState(cdp);
    await evaluate(
      cdp,
      `window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' })`
    );
    await waitForFeedGrowth(cdp, before);
  }

  const visible = await extractListArticles(cdp);
  const articles = [];
  for (const article of visible) {
    if (seenUrls.has(article.url)) continue;
    seenUrls.add(article.url);
    articles.push(article);
  }
  return articles;
}

async function scrapeTopicPage(cdp, feed, pageNum) {
  if (pageNum === 1) {
    await navigate(cdp, feed.url);
    await sleep(2000);
  }

  const params = new URLSearchParams({
    pageNo: String(pageNum),
    categoryType: feed.topicApi.categoryType,
    tabId: feed.topicApi.tabId,
  });
  const endpoint = `https://gw-c.nowcoder.com/api/sparta/home/tab/content?${params}`;
  const payload = await evaluate(
    cdp,
    `fetch(${JSON.stringify(endpoint)}, { credentials: "include" }).then(r => r.json())`
  );
  if (!payload?.success || !payload.data) {
    throw new Error(`话题页接口失败: ${payload?.msg || "unknown error"}`);
  }

  const articles = (payload.data.records || []).map((record) => {
    const body = record.momentData || record.contentData || {};
    const content = String(body.newContent || body.content || "").trim();
    const fallbackTitle = content.split(/\r?\n/).find(Boolean) || `面经-${record.contentId}`;
    const title = String(body.newTitle || body.title || fallbackTitle)
      .replace(/\s+/g, " ")
      .slice(0, 150);
    const url = record.contentType === 74 && body.uuid
      ? `https://www.nowcoder.com/feed/main/detail/${body.uuid}`
      : `https://www.nowcoder.com/discuss/${record.contentId}`;
    return {
      title,
      url,
      author: record.userBrief?.nickname || "",
      preview: content.replace(/\s+/g, " ").slice(0, 500),
      publishedAt: Number(body.createdAt || body.createTime || body.showTime || 0),
    };
  });

  return {
    articles,
    totalPage: Number(payload.data.totalPage || pageNum),
  };
}

// ─── 搜索页抓取 ──────────────────────────────────────────────────────────────────

async function getSearchPageState(cdp) {
  return (await evaluate(
    cdp,
    `(() => {
      const resultRoot = document.querySelector('.subject-all-list');
      const urls = resultRoot ? Array.from(resultRoot.querySelectorAll(
        'a[href*="/feed/main/detail/"], a[href*="/discuss/"]'
      )).map((link) => (link.href || "").split("?")[0]).filter(Boolean) : [];
      const loading = resultRoot
        ? Array.from(resultRoot.querySelectorAll('.loading, [class*="loading"]'))
            .some((node) => node.offsetParent !== null)
        : true;
      return {
        rootPresent: Boolean(resultRoot),
        activePage: document.querySelector("ul.pager li.active")?.textContent.trim() || "",
        fingerprint: Array.from(new Set(urls)).join("\\n"),
        loading
      };
    })()`
  )) || { rootPresent: false, activePage: "", fingerprint: "", loading: true };
}

async function scrapeSearchPage(cdp, query, pageNum) {
  if (pageNum === 1) {
    // 固定在面经分类内搜索，避免混入题库、课程等全站结果。
    const params = new URLSearchParams({
      query,
      type: "all",
      searchType: "顶部导航栏",
      subType: SEARCH_INTERVIEW_SUBTYPE,
    });
    const url = `https://www.nowcoder.com/search/all?${params.toString()}`;
    await navigate(cdp, url);
    const deadline = Date.now() + 10000;
    let stableFingerprint = "";
    let stableRounds = 0;
    while (Date.now() < deadline) {
      const state = await getSearchPageState(cdp);
      if (state.rootPresent && !state.loading) {
        const fingerprint = state.fingerprint || "__empty__";
        if (fingerprint === stableFingerprint) {
          stableRounds += 1;
        } else {
          stableFingerprint = fingerprint;
          stableRounds = 0;
        }
        if (stableRounds >= 2) break;
      }
      await sleep(250);
    }
    if (stableRounds < 2) {
      throw new Error("搜索第一页在 10 秒内未稳定加载，请检查登录态或网络");
    }
  } else {
    // 后续页：点击分页按钮
    const previousState = await getSearchPageState(cdp);
    const clicked = await evaluate(
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
        var active = Number(document.querySelector("ul.pager li.active")?.textContent.trim() || 0);
        if (active + 1 !== ${pageNum}) return false;
        for (var j = 0; j < items.length; j++) {
          var text = items[j].textContent.trim();
          var classes = items[j].className || "";
          var title = items[j].getAttribute("title") || "";
          if (text === "下一页" || title.includes("下一页") || /(^|\\s)next(\\s|$)/i.test(classes)) {
            if (/disabled/i.test(classes)) return false;
            items[j].click();
            return true;
          }
        }
        return false;
      })()`
    );
    if (!clicked) return null;

    const deadline = Date.now() + 10000;
    let loaded = false;
    let changedFingerprint = "";
    let stableRounds = 0;
    while (Date.now() < deadline) {
      const state = await getSearchPageState(cdp);
      const changed = state.fingerprint
        && state.fingerprint !== previousState.fingerprint;
      if (state.activePage === String(pageNum) && !state.loading && changed) {
        if (state.fingerprint === changedFingerprint) {
          stableRounds += 1;
        } else {
          changedFingerprint = state.fingerprint;
          stableRounds = 0;
        }
        if (stableRounds >= 2) {
          loaded = true;
          break;
        }
      } else {
        changedFingerprint = "";
        stableRounds = 0;
      }
      await sleep(250);
    }
    if (!loaded) return null;
  }

  const articles = await evaluate(
    cdp,
    `(() => {
      var items = [];
      var seen = {};
      var resultRoot = document.querySelector('.subject-all-list');
      var links = (resultRoot || document).querySelectorAll("a");

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

        var row = a;
        while (row.parentElement && row.parentElement !== resultRoot) {
          row = row.parentElement;
        }
        if (!resultRoot || row.parentElement !== resultRoot) row = null;
        var publishedTime = '';
        if (row) {
          var timeNodes = row.querySelectorAll(
            'time, [class*="publish-time"], [class*="create-time"], [class*="post-time"], [class*="date"], [class*="time"]'
          );
          for (var t = 0; t < timeNodes.length; t++) {
            var node = timeNodes[t];
            var candidates = [
              node.getAttribute('datetime'),
              node.getAttribute('title'),
              node.getAttribute('data-time'),
              node.getAttribute('data-timestamp'),
              node.textContent
            ];
            for (var c = 0; c < candidates.length; c++) {
              var value = (candidates[c] || '').trim();
              if (/20\\d{2}[年\\-\\/.]\\d{1,2}[月\\-\\/.]\\d{1,2}|(?:今天|昨天|前天|刚刚)|\\d+\\s*(?:分钟|小时)前|\\d{1,2}[月\\-\\/.]\\d{1,2}/.test(value)) {
                publishedTime = value;
                break;
              }
            }
            if (publishedTime) break;
          }
        }

        seen[href] = true;
        items.push({ title: title, url: href, author: "", preview: "", publishedTime: publishedTime });
      }

      return items;
    })()`
  );

  const capturedAt = Date.now();
  return (articles || []).map((article) => {
    const publishedDate = extractDate(article.publishedTime, capturedAt);
    return {
      ...article,
      publishedAt: publishedDate === "unknown"
        ? 0
        : parseDateOption(publishedDate, "搜索列表发布日期"),
    };
  });
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

async function loadExistingArticles(outputDir) {
  const articlesByUrl = new Map();
  for (const filename of await readdir(outputDir)) {
    if (!filename.endsWith(".md") || ["index.md", "all-in-one.md", "manual-audit.md"].includes(filename)) {
      continue;
    }

    const markdown = await readFile(join(outputDir, filename), "utf-8");
    const source = markdown.match(/^\*\*来源\*\*：\s*(https?:\/\/\S+)\s*$/m)?.[1];
    const normalizedSource = normalizeArticleUrl(source);
    if (normalizedSource && !articlesByUrl.has(normalizedSource)) {
      articlesByUrl.set(normalizedSource, { filename, markdown });
    }
  }
  return articlesByUrl;
}

async function loadGlobalExistingArticles(outputDir) {
  const directories = [resolve(outputDir)];
  const skillEntries = await readdir(import.meta.dirname, { withFileTypes: true });
  for (const entry of skillEntries) {
    if (!entry.isDirectory()) continue;
    if (entry.name !== "nowcoder-agent-excellent-full" && !entry.name.startsWith("nowcoder-output")) continue;
    const directory = resolve(import.meta.dirname, entry.name);
    if (!directories.includes(directory)) directories.push(directory);
  }

  const articlesByUrl = new Map();
  for (const directory of directories) {
    if (!existsSync(directory)) continue;
    for (const [url, article] of await loadExistingArticles(directory)) {
      if (!articlesByUrl.has(url)) {
        articlesByUrl.set(url, { ...article, directory });
      }
    }
  }
  return articlesByUrl;
}

function normalizeArticleUrl(value) {
  if (!value) return "";
  try {
    const url = new URL(value.trim());
    url.search = "";
    url.hash = "";
    url.pathname = url.pathname.replace(/\/+$/, "");
    return url.toString();
  } catch {
    return value.trim().split(/[?#]/, 1)[0].replace(/\/+$/, "");
  }
}

function sanitizeFilename(name) {
  return name
    .replace(/[\/\\:*?"<>|\n\r]/g, "")
    .replace(/\s+/g, "-")
    .slice(0, 50);
}

function extractDate(timeStr, capturedAt = 0) {
  if (!timeStr) return "unknown";
  const m = timeStr.match(/(\d{4})[年\-\/.](\d{1,2})[月\-\/.](\d{1,2})/);
  if (m) return `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}`;
  const m2 = timeStr.match(/(\d{1,2})[月\-\/.](\d{1,2})/);
  if (m2) {
    const year = new Date().getFullYear();
    return `${year}-${m2[1].padStart(2, "0")}-${m2[2].padStart(2, "0")}`;
  }
  if (capturedAt > 0) {
    if (/前天/.test(timeStr)) return timestampToDate(capturedAt - 2 * 24 * 60 * 60 * 1000);
    if (/昨天/.test(timeStr)) return timestampToDate(capturedAt - 24 * 60 * 60 * 1000);
    const hourMatch = timeStr.match(/(\d+)\s*小时前/);
    if (hourMatch) return timestampToDate(capturedAt - Number(hourMatch[1]) * 60 * 60 * 1000);
    const minuteMatch = timeStr.match(/(\d+)\s*分钟前/);
    if (minuteMatch) return timestampToDate(capturedAt - Number(minuteMatch[1]) * 60 * 1000);
    if (/今天|刚刚/.test(timeStr)) return timestampToDate(capturedAt);
  }
  return "unknown";
}

function extractExistingDate(existing) {
  const filenameDate = existing.filename.match(/^(\d{4}-\d{2}-\d{2})-/)?.[1];
  if (filenameDate) return filenameDate;
  const metaLine = existing.markdown.match(/^>\s*(.+)$/m)?.[1] || "";
  return extractDate(metaLine);
}

function isDateInRange(date, sinceTimestamp, untilExclusiveTimestamp) {
  if (!sinceTimestamp && !untilExclusiveTimestamp) return true;
  if (!date || date === "unknown") return false;
  const timestamp = parseDateOption(date, "文章发布日期");
  if (sinceTimestamp > 0 && timestamp < sinceTimestamp) return false;
  if (untilExclusiveTimestamp > 0 && timestamp >= untilExclusiveTimestamp) return false;
  return true;
}

function timestampToDate(timestamp) {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(timestamp));
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

// ─── 主流程 ──────────────────────────────────────────────────────────────────────

async function main() {
  const opts = parseArgs();
  const feed = resolveFeedMode(opts);
  const requestedSinceTimestamp = parseDateOption(opts.since, "--since");
  const requestedUntilTimestamp = parseDateOption(opts.until, "--until");
  if (requestedSinceTimestamp && requestedUntilTimestamp && requestedSinceTimestamp > requestedUntilTimestamp) {
    throw new Error("--since 不能晚于 --until");
  }
  const supportsDateFilter = Boolean(feed.topicApi) || feed.mode === "search";
  const sinceTimestamp = supportsDateFilter ? requestedSinceTimestamp : 0;
  const untilExclusiveTimestamp = supportsDateFilter && requestedUntilTimestamp
    ? requestedUntilTimestamp + 24 * 60 * 60 * 1000
    : 0;
  const sinceSummary = sinceTimestamp
    ? opts.since
    : requestedSinceTimestamp
      ? `${opts.since}（未应用）`
      : "无";

  // 登录模式
  if (opts.login) {
    await loginMode(opts);
    return;
  }

  console.log(`[scrape] 牛客面经抓取 — CDP 方案`);
  console.log(`[scrape] 配置: mode=${feed.label}, pages=${opts.pages}, keyword="${opts.keyword}", since="${opts.since}", until="${opts.until}", delay=${opts.delay}ms`);
  if ((requestedSinceTimestamp || requestedUntilTimestamp) && !supportsDateFilter) {
    console.log("[scrape] 提示: --since/--until 仅对标准话题接口和搜索模式生效，本次忽略");
  }
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
    const listMode = feed.mode === "search" ? "搜索" : feed.label;
    console.log(`[scrape] === 抓取面经列表（${listMode}） ===`);
    let allArticles = [];
    const listSeenUrls = new Set();
    let oldOnlyPageStreak = 0;
    let pagesScanned = 0;
    let listCandidateCount = 0;
    let listOutOfRangeCount = 0;

    for (let p = 1; p <= opts.pages; p++) {
      const unit = feed.mode === "search" || feed.topicApi ? "页" : "滚动页";
      console.log(`[scrape] 第 ${p}/${opts.pages} ${unit}...`);
      let articles;
      let lastPage = false;
      if (feed.mode === "search") {
        articles = await scrapeSearchPage(cdp, opts.search, p);
      } else if (feed.topicApi) {
        const page = await scrapeTopicPage(cdp, feed, p);
        articles = page.articles;
        lastPage = p >= page.totalPage;
      } else if (feed.subjectScroll) {
        articles = await scrapeSubjectBatch(cdp, feed, p, listSeenUrls);
      } else {
        articles = await scrapeListPage(cdp, p, listSeenUrls, feed.url);
      }
      if (articles === null) {
        console.log(`[scrape]   → 搜索结果没有第 ${p} 页，提前停止`);
        break;
      }
      pagesScanned += 1;
      const datedSummary = feed.mode === "search"
        ? `，列表日期可解析 ${articles.filter((article) => article.publishedAt > 0).length} 篇`
        : "";
      console.log(`[scrape]   → ${articles.length} 篇${datedSummary}`);
      const usesInfiniteScroll = feed.mode === "home"
        || (feed.mode === "topic" && !feed.topicApi);
      const newArticles = usesInfiniteScroll
        ? articles
        : articles.filter((article) => {
            if (listSeenUrls.has(article.url)) return false;
            listSeenUrls.add(article.url);
            return true;
          });
      const oldOnlyPage = sinceTimestamp > 0
        && feed.topicApi
        && newArticles.length > 0
        && newArticles.every(
          (article) => article.publishedAt > 0 && article.publishedAt < sinceTimestamp
        );
      oldOnlyPageStreak = oldOnlyPage ? oldOnlyPageStreak + 1 : 0;
      const pageArticles = newArticles.filter((article) => {
        if (!article.publishedAt) return true;
        if (sinceTimestamp > 0 && article.publishedAt < sinceTimestamp) return false;
        if (untilExclusiveTimestamp > 0 && article.publishedAt >= untilExclusiveTimestamp) return false;
        return true;
      });
      listCandidateCount += newArticles.length;
      listOutOfRangeCount += newArticles.length - pageArticles.length;
      allArticles.push(...pageArticles);
      if (oldOnlyPageStreak >= 2) {
        console.log(`[scrape]   → 连续两页内容均早于 ${opts.since}，提前停止`);
        break;
      }
      if (lastPage) {
        console.log("[scrape]   → 已到话题最后一页");
        break;
      }
      if (newArticles.length === 0) {
        console.log("[scrape]   → 本页无新增结果，提前停止");
        break;
      }
      if (oldOnlyPage) {
        console.log(`[scrape]   → 本页内容均早于 ${opts.since}，继续探测下一页`);
      }
      if (p < opts.pages) await sleep(opts.delay);
    }

    // 去重
    const seen = new Set();
    allArticles = allArticles.filter((a) => {
      a.url = normalizeArticleUrl(a.url);
      if (!a.url) return false;
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
    const existingArticles = await loadGlobalExistingArticles(opts.out);
    if (existingArticles.size > 0) {
      console.log(`[scrape] 历史数据区已有 ${existingArticles.size} 个唯一来源 URL，将直接复用相同链接\n`);
    }

    // 逐篇抓详情
    console.log("[scrape] === 抓取文章详情 ===");
    const resultMarkdowns = [];
    const resultArticles = [];
    const resultSeenUrls = new Set();
    let reusedCount = 0;
    let outOfRangeCount = 0;
    let unknownDateCount = 0;
    let detailFailedCount = 0;
    let canonicalDuplicateCount = 0;
    const addResult = (resultArticle, markdown) => {
      if (resultSeenUrls.has(resultArticle.url)) return false;
      resultSeenUrls.add(resultArticle.url);
      resultArticles.push(resultArticle);
      resultMarkdowns.push(markdown);
      return true;
    };
    for (let i = 0; i < allArticles.length; i++) {
      const article = allArticles[i];
      console.log(
        `[scrape] [${i + 1}/${allArticles.length}] ${article.title}`
      );
      const existing = existingArticles.get(article.url);
      if (existing) {
        const verifyExistingDetail = feed.mode === "search"
          && Boolean(sinceTimestamp || untilExclusiveTimestamp);
        const existingDate = article.publishedAt
          ? timestampToDate(article.publishedAt)
          : extractExistingDate(existing);
        if (!verifyExistingDetail
          && (existingDate !== "unknown" || (!sinceTimestamp && !untilExclusiveTimestamp))) {
          if (!isDateInRange(existingDate, sinceTimestamp, untilExclusiveTimestamp)) {
            outOfRangeCount += 1;
            console.log(`[scrape]   跳过：发布日期 ${existingDate} 不在目标区间`);
            continue;
          }
          addResult({
            ...article,
            publishedDate: existingDate,
            reused: true,
            localSourcePath: join(existing.directory, existing.filename),
          }, existing.markdown);
          reusedCount += 1;
          console.log(`[scrape]   ♻️ 已存在同一来源，复用 ${join(existing.directory, existing.filename)}`);
          continue;
        }
        console.log("[scrape]   搜索日期模式重新打开详情，补验历史文件发布日期");
      }

      try {
        const capturedAt = Date.now();
        const detail = await scrapeArticleDetail(cdp, article.url);
        const publishedDate = feed.mode !== "search" && article.publishedAt
          ? timestampToDate(article.publishedAt)
          : extractDate(detail.time, capturedAt);
        if (publishedDate === "unknown") {
          unknownDateCount += 1;
          if (sinceTimestamp || untilExclusiveTimestamp) {
            console.log(`[scrape]   跳过：无法从详情时间“${detail.time || "(空)"}”解析发布日期`);
            if (i < allArticles.length - 1) await sleep(opts.delay);
            continue;
          }
          console.log(`[scrape]   提示：发布日期无法解析，按 unknown 保存`);
        }
        if (!isDateInRange(publishedDate, sinceTimestamp, untilExclusiveTimestamp)) {
          outOfRangeCount += 1;
          console.log(`[scrape]   跳过：发布日期 ${publishedDate} 不在目标区间`);
          if (i < allArticles.length - 1) await sleep(opts.delay);
          continue;
        }
        const canonicalUrl = normalizeArticleUrl(detail.url) || article.url;
        if (resultSeenUrls.has(canonicalUrl)) {
          canonicalDuplicateCount += 1;
          console.log(`[scrape]   跳过：重定向后的来源 URL 已处理 ${canonicalUrl}`);
          if (i < allArticles.length - 1) await sleep(opts.delay);
          continue;
        }

        if (existing) {
          addResult({
            ...article,
            url: canonicalUrl,
            title: detail.title || article.title,
            author: detail.author || article.author,
            publishedDate,
            reused: true,
            localSourcePath: join(existing.directory, existing.filename),
          }, existing.markdown);
          reusedCount += 1;
          console.log(`[scrape]   ♻️ 日期补验通过，复用 ${join(existing.directory, existing.filename)}`);
          if (i < allArticles.length - 1) await sleep(opts.delay);
          continue;
        }

        const normalizedDetail = {
          ...detail,
          url: canonicalUrl,
        };
        const markdown = toMarkdown(normalizedDetail);

        const datePrefix = publishedDate;
        let filename = `${datePrefix}-${sanitizeFilename(detail.title)}.md`;
        if (existsSync(join(opts.out, filename))) {
          const id = article.url.split("/").filter(Boolean).pop().slice(0, 8);
          filename = `${datePrefix}-${sanitizeFilename(detail.title)}-${id}.md`;
        }
        await writeFile(join(opts.out, filename), markdown, "utf-8");
        const savedArticle = {
          filename,
          markdown,
          directory: resolve(opts.out),
        };
        existingArticles.set(article.url, savedArticle);
        existingArticles.set(canonicalUrl, savedArticle);
        addResult({
          ...article,
          url: canonicalUrl,
          title: detail.title || article.title,
          author: detail.author || article.author,
          publishedDate,
          reused: false,
          localSourcePath: join(resolve(opts.out), filename),
        }, markdown);
        console.log(`[scrape]   ✅ ${detail.content.length} 字`);
      } catch (err) {
        console.error(`[scrape]   ❌ ${err.message}`);
        detailFailedCount += 1;
        console.log("[scrape]   跳过：详情失败，未写入 manifest 或合集");
      }

      if (i < allArticles.length - 1) await sleep(opts.delay);
    }

    // 搜索列表没有可靠日期，必须等逐篇详情过滤完成后再生成索引。
    const indexLines = [
      "# 牛客面经抓取结果\n",
      `抓取时间：${new Date().toLocaleString("zh-CN")}\n`,
      `模式：${feed.label} | 筛选：${opts.keyword || "无"} | 起始日期：${sinceSummary} | 结束日期：${opts.until || "无"} | 页数：${opts.pages}\n`,
      "| # | 日期 | 标题 | 作者 |",
      "|---|------|------|------|",
    ];
    resultArticles.forEach((article, index) => {
      indexLines.push(
        `| ${index + 1} | ${article.publishedDate || ""} | [${article.title}](${article.url}) | ${article.author || ""} |`
      );
    });
    await writeFile(join(opts.out, "index.md"), indexLines.join("\n"), "utf-8");

    const manifest = {
      generatedAt: new Date().toISOString(),
      mode: feed.label,
      query: opts.search || "",
      since: opts.since || null,
      until: opts.until || null,
      requestedPages: opts.pages,
      scannedPages: pagesScanned,
      stats: {
        listCandidates: listCandidateCount,
        listOutOfRange: listOutOfRangeCount,
        detailCandidates: allArticles.length,
        accepted: resultArticles.length,
        reused: reusedCount,
        outOfRange: outOfRangeCount,
        unknownDate: unknownDateCount,
        detailFailed: detailFailedCount,
        canonicalDuplicates: canonicalDuplicateCount,
      },
      articles: resultArticles.map((article) => ({
        title: article.title,
        author: article.author || "",
        publishedDate: article.publishedDate,
        url: article.url,
        reused: Boolean(article.reused),
        localSourcePath: article.localSourcePath || "",
      })),
    };
    await writeFile(
      join(opts.out, "manifest.json"),
      `${JSON.stringify(manifest, null, 2)}\n`,
      "utf-8"
    );

    // 合并文件
    await writeFile(
      join(opts.out, "all-in-one.md"),
      resultMarkdowns.join("\n\n---\n\n"),
      "utf-8"
    );

    console.log(`\n[scrape] ════════════════════════════════════════`);
    console.log(`[scrape] ✅ 完成！共 ${resultMarkdowns.length} 篇面经（复用 ${reusedCount} 篇）`);
    console.log(`[scrape] 排除: 列表区间外 ${listOutOfRangeCount}，详情区间外 ${outOfRangeCount}，日期未知 ${unknownDateCount}，详情失败 ${detailFailedCount}，规范 URL 重复 ${canonicalDuplicateCount}`);
    console.log(`[scrape] 📂 ${opts.out}`);
    console.log(`[scrape]    index.md       — 目录`);
    console.log(`[scrape]    manifest.json  — 本轮逐篇来源清单`);
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
