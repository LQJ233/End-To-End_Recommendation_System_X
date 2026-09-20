import pymysql

from local_env import mysql_config


MYSQL_CONFIG = mysql_config()


def get_watermark(pipeline_name: str) -> int:
    connection = pymysql.connect(**MYSQL_CONFIG)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT `last_value` FROM pipeline_watermark WHERE pipeline_name = %s",
                (pipeline_name,),
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0
    finally:
        connection.close()


def set_watermark(pipeline_name: str, value: int) -> None:
    connection = pymysql.connect(**MYSQL_CONFIG)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO pipeline_watermark (pipeline_name, `last_value`)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    `last_value` = GREATEST(`last_value`, VALUES(`last_value`))
                """,
                (pipeline_name, int(value)),
            )
        connection.commit()
    finally:
        connection.close()
