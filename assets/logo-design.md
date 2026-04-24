# Logo 设计记录

> **这是模板占位文档**。克隆这个模板到新项目后,用你自己的 logo 替换 `assets/logo.svg`,
> 然后填写本文。参考完整例子:<https://github.com/cliffordll/chariot/blob/main/assets/logo-design.md>

---

## 1. 核心概念

<!-- 你的项目是什么?logo 要传达什么语义? -->

## 2. 元素拆解

<!-- 形状 / 文字 / 几何细节 -->

## 3. 配色

| 角色 | 颜色 | 象征 |
|---|---|---|
| 主色 | `#TODO` | |
| 强调色 | `#TODO` | |

## 4. 使用指南

- 主 logo:[`assets/logo.svg`](logo.svg)(**当前是占位版**,记得替换)
- Web favicon:[`packages/app/public/favicon.svg`](../packages/app/public/favicon.svg)(也是占位版)
- 桌面图标:`packages/desktop/tauri/icons/` —— **模板默认不带,克隆后跑下面脚本生成**

## 5. 重新生成 icons 的命令

换了 `assets/logo.svg` 之后,从仓库根:

```bash
bun --filter=@template/desktop gen-icons
```

或在 `packages/desktop/` 下:

```bash
bun run gen-icons
```

脚本(`packages/desktop/scripts/gen-icons.mjs`)封装 `bun tauri icon`,以
`assets/logo.svg` 为输入,产出 Windows / macOS / iOS / Android 全套尺寸,
写入 `packages/desktop/tauri/icons/`。

需要换源 logo:

```bash
bun run gen-icons -- --source ../../assets/your-logo.svg
```

Web favicon 没有自动脚本,直接替换 `packages/app/public/favicon.svg` 即可
(现代浏览器接受 SVG;如需老旧浏览器的 ico/png,自行用工具转)。

完整背景见 [`docs/guides/tauri-icons.md`](../docs/guides/tauri-icons.md)。
