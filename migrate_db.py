import sqlite3
import pandas as pd
from datetime import datetime

def migrate_database():
    """迁移并整理数据库"""
    print("开始数据库迁移...")
    
    # 连接数据库
    conn = sqlite3.connect('words.db')
    c = conn.cursor()
    
    try:
        # 1. 备份现有数据
        print("备份现有数据...")
        boxes_df = pd.read_sql_query("SELECT * FROM boxes", conn)
        words_df = pd.read_sql_query("SELECT * FROM words", conn)
        
        # 2. 删除现有表
        print("删除旧表...")
        c.execute("DROP TABLE IF EXISTS words")
        c.execute("DROP TABLE IF EXISTS boxes")
        
        # 3. 创建新表结构
        print("创建新表结构...")
        c.execute('''
            CREATE TABLE boxes
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT NOT NULL,
             article_title TEXT,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        ''')
        
        c.execute('''
            CREATE TABLE words
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             word TEXT NOT NULL,
             box_id INTEGER,
             review_count INTEGER DEFAULT 0,
             added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
             FOREIGN KEY (box_id) REFERENCES boxes (id),
             UNIQUE(word, box_id))
        ''')
        
        # 4. 恢复盒子数据
        print("恢复盒子数据...")
        for _, row in boxes_df.iterrows():
            c.execute(
                "INSERT INTO boxes (id, name, article_title, created_at) VALUES (?, ?, ?, ?)",
                (row['id'], row['name'], row.get('article_title', ''), row.get('created_at', datetime.now()))
            )
        
        # 5. 恢复单词数据，去除重复
        print("恢复单词数据，并去除重复...")
        # 按box_id和word分组，保留最早的记录
        words_df = words_df.sort_values('added_date').groupby(['box_id', 'word']).first().reset_index()
        
        for _, row in words_df.iterrows():
            try:
                c.execute(
                    "INSERT INTO words (word, box_id, review_count, added_date) VALUES (?, ?, ?, ?)",
                    (row['word'], row['box_id'], row.get('review_count', 0), row.get('added_date', datetime.now()))
                )
            except sqlite3.IntegrityError:
                print(f"跳过重复单词: {row['word']} (盒子ID: {row['box_id']})")
        
        # 6. 提交更改
        conn.commit()
        print("数据库迁移完成！")
        
        # 7. 显示统计信息
        c.execute("SELECT COUNT(*) FROM boxes")
        boxes_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM words")
        words_count = c.fetchone()[0]
        print(f"\n统计信息:")
        print(f"- 盒子数量: {boxes_count}")
        print(f"- 单词总数: {words_count}")
        
    except Exception as e:
        print(f"迁移过程中出错: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # 在执行迁移前先备份数据库
    import shutil
    from datetime import datetime
    
    # 创建备份
    backup_file = f'words_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    try:
        shutil.copy2('words.db', backup_file)
        print(f"数据库已备份至: {backup_file}")
        
        # 执行迁移
        migrate_database()
    except Exception as e:
        print(f"备份过程中出错: {str(e)}") 