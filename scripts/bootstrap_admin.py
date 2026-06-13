"""Create or reset the bootstrap admin user.

Usage:
    python scripts/bootstrap_admin.py --username admin --password Admin@12345
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bcrypt
import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithm.common.config_loader import get_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="Admin@12345")
    parser.add_argument("--user-id", default="u_admin")
    args = parser.parse_args()

    pwd_hash = bcrypt.hashpw(args.password.encode("utf-8"), bcrypt.gensalt(10)).decode("utf-8")

    cfg = get_config()["mysql"]
    conn = pymysql.connect(host=cfg["host"], port=int(cfg["port"]),
                           user=cfg["username"], password=cfg["password"],
                           database=cfg["database"], charset="utf8mb4",
                           cursorclass=pymysql.cursors.DictCursor, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM biz_user WHERE username=%s", (args.username,))
            existing = cur.fetchone()
            if existing:
                cur.execute("UPDATE biz_user SET password_hash=%s, status=1 WHERE username=%s",
                            (pwd_hash, args.username))
            else:
                cur.execute(
                    "INSERT INTO biz_user (user_id, username, password_hash, nickname, gender, user_type, status) "
                    "VALUES (%s,%s,%s,%s,0,1,1)",
                    (args.user_id, args.username, pwd_hash, "系统管理员")
                )
            cur.execute("INSERT IGNORE INTO biz_user_role (user_id, role_code) VALUES (%s, 'USER')", (args.user_id,))
            cur.execute("INSERT IGNORE INTO biz_user_role (user_id, role_code) VALUES (%s, 'ADMIN')", (args.user_id,))
        print(f"admin bootstrapped: username={args.username} userId={args.user_id}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
