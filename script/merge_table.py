import sqlite3


def merge_table(source_db, target_db, table_names):
    """
    :param source_db: 被复制表的数据库
    :param target_db: 要插入表的数据库
    :param table_names: 要合并的表,列表
    :return:
    """
    for table_name in table_names:
        # 连接到MicroMsg.db并读取数据
        conn_micro = sqlite3.connect(source_db)
        cursor_micro = conn_micro.cursor()

        # 假设你要复制的表名是"your_table_name"
        query = f"SELECT * FROM {table_name}"
        cursor_micro.execute(query)
        rows = cursor_micro.fetchall()

        # 获取表的列信息
        cursor_micro.execute(f"PRAGMA table_info({table_name})")
        columns = [(info[1], info[2]) for info in cursor_micro.fetchall()]

        # 连接到MSG.db
        conn_msg = sqlite3.connect(target_db)
        cursor_msg = conn_msg.cursor()

        # 检查表是否存在，如果不存在则创建它
        table_exists = False
        for table_info in cursor_msg.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"):
            table_exists = True

        if not table_exists:
            create_table_query = f"CREATE TABLE {table_name} ("
            for column_name, column_type in columns:
                create_table_query += f"{column_name} {column_type}, "
            create_table_query = create_table_query[:-2] + ")"  # 移除最后的逗号和空格
            cursor_msg.execute(create_table_query)

        # 插入数据到MSG.db的表中
        insert_query = f"INSERT INTO {table_name} (" + ", ".join([col[0] for col in columns]) + ") VALUES (" + ", ".join(
            ["?" for _ in columns]) + ")"
        cursor_msg.executemany(insert_query, rows)
        print(f"{source_db}库{table_name}数据已成功插入到{target_db}库中")

        # 提交更改并关闭连接
        conn_msg.commit()
        conn_micro.close()
        conn_msg.close()


if __name__ == '__main__':
    merge_table('MicroMsg.db', 'MSG.db', 'Contact')
