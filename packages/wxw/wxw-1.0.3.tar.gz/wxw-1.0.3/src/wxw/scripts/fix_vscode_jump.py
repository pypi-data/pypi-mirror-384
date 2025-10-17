#!/usr/bin/env python3
import os
import sys
import json
import site
import subprocess
from pathlib import Path


def find_editable_paths():
    """
    找到所有 editable install 包的源码路径：
    1. pip list 输出中带路径的（新 pip Editable 安装）
    2. .egg-link 文件（旧 pip Editable 安装）
    """
    editable_paths = set()

    # 1️⃣ 先扫 pip list（快）
    try:
        result = subprocess.run("pip list", shell=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 3:
                possible_path = parts[-1]
                if possible_path.startswith("/") and Path(possible_path).exists():
                    editable_paths.add(Path(possible_path).resolve())
    except Exception as e:
        print(f"[⚠] 执行 pip list 失败: {e}")

    # 2️⃣ 再扫 .egg-link（旧 pip）
    search_dirs = set(site.getsitepackages() + [site.getusersitepackages()]) | set(
        sys.path
    )
    for sp in search_dirs:
        sp_path = Path(sp)
        if not sp_path.exists():
            continue
        for egg_link in sp_path.glob("*.egg-link"):
            try:
                target_path = Path(egg_link.read_text().strip()).resolve()
                if target_path.exists():
                    editable_paths.add(target_path)
            except Exception as e:
                print(f"[⚠] 读取 {egg_link} 失败: {e}")

    return list(editable_paths)


def update_vscode_settings(extra_paths):
    """
    将找到的路径写入当前工作区的 .vscode/settings.json
    """
    cwd = Path.cwd()
    vscode_dir = cwd / ".vscode"
    vscode_dir.mkdir(exist_ok=True)

    settings_file = vscode_dir / "settings.json"
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except:
            settings = {}
    else:
        settings = {}

    settings.setdefault("python.analysis.extraPaths", [])

    added_count = 0
    for path in extra_paths:
        path_str = str(path)
        if path_str not in settings["python.analysis.extraPaths"]:
            settings["python.analysis.extraPaths"].append(path_str)
            added_count += 1

    settings_file.write_text(json.dumps(settings, indent=4, ensure_ascii=False))
    print(f"[💾] 配置已写入 {settings_file}，新增 {added_count} 条路径。")


def main():
    print("[🔍] 正在扫描 editable install 包源码路径...\n")
    paths = find_editable_paths()

    if not paths:
        print("[ℹ] 未发现 editable install 包。")
        return

    print(f"[✅] 找到 {len(paths)} 个源码路径:")
    for p in paths:
        print("    -", p)

    update_vscode_settings(paths)

    print(
        "\n[🚀] 完成！请到 VSCode 执行 'Python: Restart Language Server' 之后重新尝试跳转。"
    )


if __name__ == "__main__":
    main()
