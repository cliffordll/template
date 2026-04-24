"""Template 管理工具 —— 从本模板派生一个新项目。

用法
----

```bash
python scripts/template.py new <name>              # 就地改写当前仓库
python scripts/template.py new <name> --dir <path>  # 生成到新目录
```

<name> 支持 kebab(`my-new-app`) / snake(`my_new_app`)两种输入;脚本内部自己
派生 TitleCase / UPPER_SNAKE / 变体,按各文件的惯例挑合适的那个替换:

| 场景 | 用的变体 |
|---|---|
| Python 包名 / module 路径 / 标识符 | snake_case(合法 Python 标识符) |
| npm workspace 名 / exe 名 / `.xxx` 运行时目录 | kebab-case |
| 类名 / 文档首字母大写 | TitleCase |
| 环境变量前缀 | UPPER_SNAKE |

执行
----

1. 派生 4 个大小写变体
2. 若 `--dir` 非空:先 rsync 式复制当前目录到 `--dir`(跳过 .git / .venv /
   node_modules 等不该复制的东西),之后在副本里操作
3. 在目标目录:
   a. 按文件扩展名白名单,sed 替换 text 文件里的 template / Template / TEMPLATE
      —— word boundary 匹配,避免误改英文散文里的 "template" 一词(本模板里
      已经用 "模板" / "scaffold" 这些词替代,让 sed 更安全)
   b. 把 Python 包目录 `template/` 重命名为 `<snake>/`
   c. 把 `build/template.spec` / `build/template-server.spec` 也重命名
   d. 删掉本脚本(新项目不需要再开子项目了);如需保留:传 `--keep-script`
4. Git reset:rm -rf .git 后重新 `git init`(不继承 template 的历史)

注意
----

- 模板里所有 "template" 标识符都假设是可以被替换的;不想被替换的地方请在模板
  源文件里用中文 "模板" 这种非标识符写法。
- 重命名后 venv / node_modules / target 都作废,重新 `uv sync && bun install`。
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ---------- 大小写变体推导 ----------


def _normalize_input(name: str) -> str:
    """接受 kebab 或 snake,统一转 snake_case。"""
    name = name.strip().lower()
    if not name:
        raise ValueError("项目名不能空")
    name = name.replace("-", "_")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
        raise ValueError(f"项目名 {name!r} 不是合法 Python 标识符 —— 必须字母开头,仅含 a-z/0-9/_/-")
    if name in _PY_KEYWORDS:
        raise ValueError(f"项目名 {name!r} 是 Python 保留字")
    return name


_PY_KEYWORDS: set[str] = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
    "match",
    "case",
}


def _derive_cases(snake: str) -> dict[str, str]:
    """派生 snake/kebab/title/upper 四种写法。"""
    parts = snake.split("_")
    return {
        "snake": snake,
        "kebab": "-".join(parts),
        "title": "".join(p.capitalize() for p in parts),
        "upper": "_".join(p.upper() for p in parts),
    }


# ---------- 文件扫描 ----------

# 会做文本替换的扩展名白名单
_TEXT_EXTS: set[str] = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".mjs",
    ".cjs",
    ".rs",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
    ".sql",
    ".html",
    ".css",
    ".md",
    ".spec",
    ".lock",
    ".sh",
    ".bat",
    ".cmd",
    ".ps1",
}
# 还会处理的特定无扩展名文件
_SPECIAL_NAMES: set[str] = {
    ".gitignore",
    ".python-version",
    ".ruff.toml",
    "Dockerfile",
}
# 永不进入 / 永不修改的目录
_SKIP_DIRS: set[str] = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".pyright_cache",
    "dist",
    "target",
    "gen",
}


def _iter_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        # 跳过 skip dirs 里的东西
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        # 白名单:扩展名命中 或 特定文件名命中
        if p.suffix.lower() in _TEXT_EXTS or p.name in _SPECIAL_NAMES:
            result.append(p)
    return result


# ---------- 文本替换 ----------


def _replace_in_file(path: Path, cases: dict[str, str]) -> bool:
    """对单个文件做 template/Template/TEMPLATE → 新名字变体替换。返回是否改动。"""
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # 二进制文件或编码异常,跳过
        return False

    # 顺序重要:先替 UPPER(最具体),再 Title,再 lower。避免 "Template" 被 lower
    # 规则吞掉。
    patterns: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"\bTEMPLATE\b"), cases["upper"]),
        (re.compile(r"\bTemplate\b"), cases["title"]),
        # 小写有 kebab 和 snake 两种形态。按上下文挑:
        # - npm workspace 名 @template/foo / template-desktop / ~/.template/ → kebab
        # - Python imports `from template.` `import template` / module path → snake
        #   但 kebab "template-xxx" 里嵌的 "template" 也应该被 kebab 替换
        # 做法:先 kebab(匹配 template-xxx / @template/ / template/ 在字符串上下文),
        # 再 snake(匹配 template. / import template / ...)
    ]
    new = original
    for pat, repl in patterns:
        new = pat.sub(repl, new)

    # lowercase 替换 —— 按"紧邻分隔符"决定 kebab 或 snake
    # 规则:"template" 后跟 `-` 或 `/`,或在 `@template/` 前缀,按 kebab
    #       "template" 后跟 `.` 或 `_` 或单独出现,按 snake
    def _pick(match: re.Match[str]) -> str:
        ch_before = new[match.start() - 1] if match.start() > 0 else ""
        ch_after = new[match.end()] if match.end() < len(new) else ""
        # kebab 上下文:前后带 `-` / `/` / `@` 这种
        if ch_after in ("-", "/") or ch_before == "@" or ch_before == "-":
            return cases["kebab"]
        # 其它默认 snake(Python 标识符场景)
        return cases["snake"]

    new = re.sub(r"\btemplate\b", _pick, new)

    if new != original:
        path.write_text(new, encoding="utf-8")
        return True
    return False


# ---------- 目录 / 文件重命名 ----------


def _rename_paths(root: Path, cases: dict[str, str]) -> list[tuple[Path, Path]]:
    """重命名路径里含 template 的目录 / 文件。返回 (old, new) 列表。"""
    moves: list[tuple[Path, Path]] = []
    # 多轮扫描,优先处理深层路径(深层先 rename,浅层再 rename,避免路径漂移)
    # 先收集,深度排序,再执行
    candidates: list[Path] = []
    for p in root.rglob("*"):
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        if "template" in p.name.lower() or "Template" in p.name or "TEMPLATE" in p.name:
            candidates.append(p)

    # 深度降序 —— 先 rename 深层
    candidates.sort(key=lambda p: len(p.parts), reverse=True)

    for old in candidates:
        if not old.exists():
            continue  # 已被深层 rename 连带搬走
        # 挑合适的 case
        new_name = old.name
        # UPPER → snake/kebab 的变体选择:按上下文比较难,这里统一按小写出现
        # 形式来决定 —— 目录名里通常不出现 TEMPLATE / Template
        new_name = new_name.replace("TEMPLATE", cases["upper"])
        new_name = new_name.replace("Template", cases["title"])
        # 小写:含 `-` 用 kebab,否则 snake
        if "-" in new_name:
            new_name = new_name.replace("template", cases["kebab"])
        else:
            new_name = new_name.replace("template", cases["snake"])
        new = old.with_name(new_name)
        if new == old:
            continue
        old.rename(new)
        moves.append((old, new))
    return moves


# ---------- 复制(--dir 模式) ----------


def _copy_tree(src: Path, dst: Path) -> None:
    """复制 src → dst,跳过 _SKIP_DIRS + 明显的二进制 / 临时产物。"""
    if dst.exists():
        if any(dst.iterdir()):
            raise FileExistsError(f"目标 {dst} 非空,拒绝覆盖")
    else:
        dst.mkdir(parents=True)

    def _ignore(_src: str, names: list[str]) -> list[str]:
        return [n for n in names if n in _SKIP_DIRS or n.endswith(".tsbuildinfo")]

    shutil.copytree(src, dst, ignore=_ignore, dirs_exist_ok=True)


# ---------- Git 重置 ----------


def _reset_git(root: Path) -> None:
    git_dir = root / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
    subprocess.run(["git", "init"], cwd=root, check=True)


# ---------- 主入口 ----------


def cmd_new(name: str, target_dir: Path | None, keep_script: bool) -> None:
    snake = _normalize_input(name)
    cases = _derive_cases(snake)
    print(f"[template] deriving cases: {cases}")

    here = Path(__file__).resolve().parent.parent

    if target_dir is not None:
        target = target_dir.resolve()
        print(f"[template] copying {here} → {target}")
        _copy_tree(here, target)
    else:
        target = here
        print(f"[template] working in-place at {target}")

    # 1. 文本替换
    print("[template] rewriting text files …")
    files = _iter_files(target)
    changed = 0
    for f in files:
        if _replace_in_file(f, cases):
            changed += 1
    print(f"[template] rewrote {changed} / {len(files)} files")

    # 2. 删除 template-only 元文件(顺序很重要 —— 必须在 path rename 之前,
    # 否则这些含 "template" 的文件名会被 rename 走)
    if not keep_script:
        self_in_target = target / "scripts" / "template.py"
        if self_in_target.exists():
            self_in_target.unlink()
            print("[template] removed scripts/template.py (template-only tool)")
    template_md = target / "TEMPLATE.md"
    if template_md.exists():
        template_md.unlink()
        print("[template] removed TEMPLATE.md (template-only doc)")

    # 3. 路径重命名
    print("[template] renaming paths …")
    moves = _rename_paths(target, cases)
    for old, new in moves:
        print(f"  {old.relative_to(target)}  →  {new.relative_to(target)}")

    # 4. Git reset
    _reset_git(target)
    print(f"[template] fresh git repo initialized at {target}")

    print("\n[template] DONE. Next:")
    print(f"  cd {target}")
    print("  uv sync && bun install")
    print("  # 换 logo: edit assets/logo.svg, 跑 assets/logo-design.md §5 的脚本")
    print("  # 起开发: uv run python -m {snake}.server".format(snake=cases["snake"]))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="template",
        description="Template 管理工具(派生新项目)。",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="从本模板派生新项目")
    p_new.add_argument("name", help="新项目名,支持 snake_case 或 kebab-case")
    p_new.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="生成到指定目录(默认就地改写当前仓库)",
    )
    p_new.add_argument(
        "--keep-script",
        action="store_true",
        help="保留 scripts/template.py(默认删掉)",
    )

    args = parser.parse_args()

    if args.cmd == "new":
        try:
            cmd_new(args.name, args.dir, args.keep_script)
        except Exception as e:
            print(f"[template] ERROR: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
