#!/usr/bin/env node
/**
 * 从 `assets/logo.svg` 生成 Tauri 全平台图标到 `packages/desktop/tauri/icons/`。
 *
 * 调用 `tauri icon`(Tauri 2 CLI 内置)。该命令接受 SVG 输入,自动产出
 * Windows / macOS / iOS / Android / 通用 PNG 全套尺寸,覆盖到 tauri.conf.json
 * 旁的 `icons/` 目录。
 *
 * 用法
 * ----
 *     bun --filter=@template/desktop gen-icons
 *     # 或在 packages/desktop 目录下:
 *     bun run gen-icons
 *
 * 默认源 = 仓库根 `assets/logo.svg`,可用 --source 覆盖:
 *     bun run gen-icons -- --source ../../assets/logo1.svg
 */

import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DESKTOP_DIR = resolve(__dirname, "..");
const REPO_ROOT = resolve(DESKTOP_DIR, "..", "..");
const DEFAULT_SOURCE = resolve(REPO_ROOT, "assets", "logo.svg");

function parseArgs(argv) {
  let source = DEFAULT_SOURCE;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--source" || argv[i] === "-s") {
      source = resolve(argv[++i]);
    } else if (argv[i].startsWith("--source=")) {
      source = resolve(argv[i].slice("--source=".length));
    }
  }
  return { source };
}

function main() {
  const { source } = parseArgs(process.argv.slice(2));

  if (!existsSync(source)) {
    console.error(`[gen-icons] 源文件不存在:${source}`);
    process.exit(1);
  }

  // tauri icon 默认输出到 tauri.conf.json 旁的 icons/,即 packages/desktop/tauri/icons/
  // 在 packages/desktop 目录下跑,让 tauri CLI 自己定位 tauri.conf.json
  const sourceForCli = relative(DESKTOP_DIR, source);
  console.log(`[gen-icons] 源:${source}`);
  console.log(`[gen-icons] $ bun tauri icon ${sourceForCli}`);
  execFileSync("bun", ["tauri", "icon", sourceForCli], {
    cwd: DESKTOP_DIR,
    stdio: "inherit",
    shell: process.platform === "win32",
  });
  console.log("[gen-icons] OK  图标已写入 packages/desktop/tauri/icons/");
}

main();
