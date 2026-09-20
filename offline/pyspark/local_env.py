"""本地凭据加载器。

读取顺序（后者覆盖前者）：

1. 代码内的非敏感默认值（host / port / database 等）
2. 环境变量
3. 项目根目录的 ``.env.local``

``.env.local`` 不纳入版本管理（见仓库根目录 ``.gitignore``），
仓库里只提供 ``.env.local.example`` 作为模板。
"""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env.local"

_loaded = False


def _load_env_file() -> None:
    """把 .env.local 里的 KEY=VALUE 注入 os.environ（不覆盖已存在的变量）。"""
    global _loaded
    if _loaded:
        return
    _loaded = True
    if not ENV_FILE.exists():
        return
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def get_env(name: str, default: str = "") -> str:
    _load_env_file()
    return os.environ.get(name, default)


def get_int(name: str, default: int) -> int:
    value = get_env(name, "")
    if not value:
        return default
    return int(value)


def mysql_config() -> dict:
    """MySQL 连接配置（供离线脚本与模型注册使用）。"""
    return {
        "host": get_env("MYSQL_HOST", "127.0.0.1"),
        "port": get_int("MYSQL_PORT", 3306),
        "user": get_env("MYSQL_USER"),
        "password": get_env("MYSQL_PASSWORD"),
        "database": get_env("MYSQL_DATABASE", "ecommerce"),
        "charset": "utf8mb4",
    }
