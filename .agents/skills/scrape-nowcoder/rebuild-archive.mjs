#!/usr/bin/env node

import { readdir, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

const archiveDir = resolve(
  process.argv[2]
    || join(import.meta.dirname, "nowcoder-agent-excellent-full")
);
const generatedFiles = new Set(["index.md", "all-in-one.md"]);

function extractPost(filename, content) {
  const title = content.match(/^#\s+(.+)$/m)?.[1]?.trim();
  const source = content.match(
    /^(?:>\s*)?(?:\*\*)?来源(?:\*\*)?[：:]\s*(https:\/\/www\.nowcoder\.com\/\S+)\s*$/m
  )?.[1];
  const published = content.match(
    /^(?:>\s*)?发布日期[：:]\s*(\d{4}-\d{2}-\d{2})\s*$/m
  )?.[1];
  const filenameDate = filename.match(/^(\d{4}-\d{2}-\d{2})-/)?.[1];

  if (!title) throw new Error(`${filename}: 缺少一级标题`);
  if (!source) throw new Error(`${filename}: 缺少牛客来源 URL`);

  return {
    filename,
    title,
    source,
    date: published || filenameDate || "未知",
    content: content.replace(/[ \t]+$/gm, "").trim(),
  };
}

function escapeTableText(value) {
  return value.replaceAll("|", "\\|").replaceAll("\n", " ");
}

function encodeMarkdownPath(filename) {
  return encodeURI(filename).replaceAll("(", "%28").replaceAll(")", "%29");
}

function shanghaiDate() {
  const parts = new Intl.DateTimeFormat("en", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

const filenames = (await readdir(archiveDir))
  .filter((name) => name.endsWith(".md") && !generatedFiles.has(name));
const posts = await Promise.all(
  filenames.map(async (filename) => {
    const content = await readFile(join(archiveDir, filename), "utf8");
    return extractPost(filename, content);
  })
);

posts.sort((left, right) => {
  if (left.date === "未知" && right.date !== "未知") return 1;
  if (right.date === "未知" && left.date !== "未知") return -1;
  if (left.date !== right.date) return right.date.localeCompare(left.date);
  return left.filename.localeCompare(right.filename, "zh-CN");
});

const sourceOwners = new Map();
for (const post of posts) {
  if (sourceOwners.has(post.source)) {
    throw new Error(
      `来源 URL 重复: ${post.filename} 与 ${sourceOwners.get(post.source)}`
    );
  }
  sourceOwners.set(post.source, post.filename);
}

const datedPosts = posts.filter((post) => post.date !== "未知");
const unknownCount = posts.length - datedPosts.length;
const dateRange = datedPosts.length > 0
  ? `${datedPosts.at(-1).date} 至 ${datedPosts[0].date}`
  : "未知";
const indexLines = [
  "# Agent 面经精选原文档案",
  "",
  `> 更新日期：${shanghaiDate()}`,
  `> 收录：${posts.length} 篇`,
  `> 日期范围：${dateRange}${unknownCount ? `；另有 ${unknownCount} 篇未标明发布日期` : ""}`,
  "",
  "本目录长期保留 Agent、LLM 与 AI 应用岗位的一手面试记录。新增内容保留整轮面试链路，包括开场流程、Agent 与传统技术题、项目追问、原作者记录的回答反馈、算法和反问；不补答案。账号、学校、作者所在地、具体个人结果、评论和相关推荐等噪声已移除。2026-08-12 之前的历史存量按原归档版本保留。",
  "",
  "| 日期 | 标题 | 本地原文 | 牛客来源 |",
  "|------|------|----------|----------|",
];
for (const post of posts) {
  indexLines.push(
    `| ${post.date} | ${escapeTableText(post.title)} | [打开](${encodeMarkdownPath(post.filename)}) | [原帖](${post.source}) |`
  );
}

const allInOneLines = [
  "# Agent 面经精选原文合集",
  "",
  `> 更新日期：${shanghaiDate()} | 收录：${posts.length} 篇`,
  "> 本文件由单篇归档自动生成；单篇文件及其牛客来源 URL 是维护入口。",
  "",
  ...posts.flatMap((post, index) => [
    ...(index === 0 ? [] : ["", "---", ""]),
    post.content,
  ]),
];

await writeFile(join(archiveDir, "index.md"), `${indexLines.join("\n")}\n`, "utf8");
await writeFile(
  join(archiveDir, "all-in-one.md"),
  `${allInOneLines.join("\n")}\n`,
  "utf8"
);

console.log(`归档索引已重建：${posts.length} 篇，${dateRange}，未知日期 ${unknownCount} 篇`);
