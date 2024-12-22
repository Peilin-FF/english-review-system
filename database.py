import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

class WordDatabase:
    def __init__(self, db_path='words.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """初始化数据库表"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # 创建盒子表
        c.execute('''
            CREATE TABLE IF NOT EXISTS boxes
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT NOT NULL,
             article_title TEXT,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        ''')
        
        # 创建单词表
        c.execute('''
            CREATE TABLE IF NOT EXISTS words
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             word TEXT NOT NULL,
             box_id INTEGER,
             review_count INTEGER DEFAULT 0,
             trash_count INTEGER DEFAULT 0,
             trash_date TIMESTAMP,
             success_count INTEGER DEFAULT 0,  -- 成功记忆次数
             added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
             last_review TIMESTAMP,
             next_review TIMESTAMP,
             FOREIGN KEY (box_id) REFERENCES boxes (id),
             UNIQUE(word, box_id))
        ''')
        
        # 创建复习计数表
        c.execute('''
            CREATE TABLE IF NOT EXISTS review_counter
            (id INTEGER PRIMARY KEY,
             count INTEGER DEFAULT 0)
        ''')
        
        # 检查并添加缺失的列
        c.execute("PRAGMA table_info(words)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'trash_count' not in columns:
            c.execute("ALTER TABLE words ADD COLUMN trash_count INTEGER DEFAULT 0")
        if 'trash_date' not in columns:
            c.execute("ALTER TABLE words ADD COLUMN trash_date TIMESTAMP")
        if 'success_count' not in columns:
            c.execute("ALTER TABLE words ADD COLUMN success_count INTEGER DEFAULT 0")
        if 'last_review' not in columns:
            c.execute("ALTER TABLE words ADD COLUMN last_review TIMESTAMP")
        if 'next_review' not in columns:
            c.execute("ALTER TABLE words ADD COLUMN next_review TIMESTAMP")
        if 'review_count' not in columns:
            c.execute("ALTER TABLE words ADD COLUMN review_count INTEGER DEFAULT 0")
        
        # 初始化复习计数器
        c.execute("INSERT OR IGNORE INTO review_counter (id, count) VALUES (1, 0)")
        
        conn.commit()
        conn.close()
    
    def create_box(self, box_name, article_title=""):
        """创建新的单词盒子"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO boxes (name, article_title) VALUES (?, ?)",
                (box_name, article_title)
            )
            box_id = c.lastrowid
            conn.commit()
            return box_id
        except Exception as e:
            st.error(f"创建盒子时出错: {str(e)}")
            return None
        finally:
            conn.close()
    
    def get_all_boxes(self):
        """获取所有单词盒子"""
        conn = self.get_connection()
        try:
            boxes = pd.read_sql_query("SELECT * FROM boxes", conn)
            return boxes
        except Exception as e:
            st.error(f"获取盒子列表时出错: {str(e)}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_box_word_count(self, box_id):
        """获取盒子中的单词数量（包括垃圾桶中的单词）"""
        conn = self.get_connection()
        try:
            count = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM words WHERE box_id = ?",
                conn,
                params=[box_id]
            ).iloc[0]['count']
            return count
        except Exception as e:
            st.error(f"获取单词数量时出错: {str(e)}")
            return 0
        finally:
            conn.close()
    
    def word_exists(self, box_id, word):
        """检查单词是否已存在于盒子中"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute(
                "SELECT COUNT(*) FROM words WHERE box_id = ? AND word = ?",
                (box_id, word)
            )
            exists = c.fetchone()[0] > 0
            return exists
        finally:
            conn.close()
    
    def add_word(self, box_id, word):
        """添加新单词到指定的盒子"""
        if self.word_exists(box_id, word):
            st.warning(f"单词 '{word}' 已存在于此盒子中")
            return False
        
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute(
                "INSERT INTO words (word, box_id, added_date) VALUES (?, ?, ?)",
                (word, box_id, datetime.now())
            )
            conn.commit()
            return True
        except Exception as e:
            st.error(f"添加单词时出错: {str(e)}")
            return False
        finally:
            conn.close()
    
    def increment_review_counter(self):
        """增加复习计数器，每10次返回True"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("UPDATE review_counter SET count = (count + 1) % 10 WHERE id = 1")
            c.execute("SELECT count FROM review_counter WHERE id = 1")
            count = c.fetchone()[0]
            conn.commit()
            return count == 0  # 当计数为0时（即第10次）返回True
        except Exception as e:
            st.error(f"更新复习计数器时出错: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_words_from_box(self, box_id, include_error_words=False):
        """获取指定盒子中的所有单词和需要复习的错误队列单词"""
        conn = self.get_connection()
        try:
            words_list = []
            
            # 如果需要包含错误队列单词
            if include_error_words:
                error_words = pd.read_sql_query(
                    """SELECT id, word, review_count, trash_count 
                       FROM words 
                       WHERE trash_date IS NOT NULL
                       AND success_count < 5
                       ORDER BY trash_date ASC 
                       LIMIT 5""",
                    conn
                )
                # 将错误队列单词添加到列表
                for _, row in error_words.iterrows():
                    words_list.append((row['id'], row['word'], row['review_count'], row['trash_count']))
                if len(error_words) > 0:
                    st.info(f"已添加 {len(error_words)} 个错误队列单词到复习列表")
            
            # 获取当前盒子的单词
            box_words = pd.read_sql_query(
                """SELECT id, word, review_count, trash_count 
                   FROM words 
                   WHERE box_id = ? 
                   AND (trash_date IS NULL OR success_count >= 5)
                   ORDER BY added_date""",
                conn,
                params=[box_id]
            )
            
            # 将盒子单词添加到列表
            for _, row in box_words.iterrows():
                words_list.append((row['id'], row['word'], row['review_count'], row['trash_count']))
            
            return words_list
        except Exception as e:
            st.error(f"获取单词列表时出错: {str(e)}")
            return []
        finally:
            conn.close()
    
    def delete_word(self, word_id):
        """从数据库中删除单词"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("DELETE FROM words WHERE id = ?", (word_id,))
            
            if c.rowcount == 0:
                st.error("删除单词失败：找不到指定的单词")
            else:
                st.success("单词已成功删除")
            
            conn.commit()
        except Exception as e:
            st.error(f"删除单词时出错: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_trash_stats(self):
        """获取错误队列中的所有单词"""
        conn = self.get_connection()
        try:
            words = pd.read_sql_query(
                """SELECT w.id, w.word, w.box_id, w.review_count, w.trash_count,
                         w.success_count, b.name as box_name, w.trash_date
                   FROM words w
                   JOIN boxes b ON w.box_id = b.id
                   WHERE w.trash_date IS NOT NULL
                   AND w.success_count < 5
                   ORDER BY w.trash_date ASC""",
                conn
            )
            return words
        except Exception as e:
            st.error(f"获取错误队列时出错: {str(e)}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def update_review_count(self, word_id):
        """更新单词的复习次数和成功记忆次数"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # 获取当前单词信息
            c.execute("""
                SELECT review_count, success_count, trash_date 
                FROM words 
                WHERE id = ?
            """, (word_id,))
            result = c.fetchone()
            if result is None:
                st.error("找不到指定的单词")
                return
            
            current_count, success_count, trash_date = result
            next_review = self.calculate_next_review(current_count + 1)
            
            # 如果是错误队列中的单词，增加成功记忆次数
            new_success_count = success_count
            if trash_date is not None:
                new_success_count = success_count + 1
                if new_success_count >= 5:
                    # 成功记忆5次，从错误队列中移除
                    st.success("🎉 该单词已成功记忆5次，从错误队列中移除！")
            
            # 更新单词信息
            c.execute(
                """UPDATE words 
                   SET review_count = review_count + 1,
                       success_count = ?,
                       last_review = ?,
                       next_review = ?,
                       trash_date = CASE WHEN ? >= 5 THEN NULL ELSE trash_date END
                   WHERE id = ?""",
                (new_success_count, datetime.now(), next_review, new_success_count, word_id)
            )
            
            if c.rowcount == 0:
                st.error("更新复习次数失败：找不到指定的单词")
            
            conn.commit()
        except Exception as e:
            st.error(f"更新复习次数时出错: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    @staticmethod
    def calculate_next_review(review_count):
        """根据艾宾浩斯遗忘曲线计算下次复习时间"""
        intervals = [
            timedelta(minutes=5),    # 5分钟后
            timedelta(hours=1),      # 1小时后
            timedelta(hours=6),      # 6小时后
            timedelta(days=1),       # 1天后
            timedelta(days=3),       # 3天后
            timedelta(days=7),       # 1周后
            timedelta(days=14),      # 2周后
            timedelta(days=30),      # 1月后
        ]
        interval = intervals[min(review_count, len(intervals)-1)]
        return datetime.now() + interval 
    
    def move_to_trash(self, word_id):
        """将单词加入错误队列"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            now = datetime.now()
            
            # 更新单词状态
            c.execute(
                """UPDATE words 
                   SET trash_count = trash_count + 1,
                       trash_date = ?,
                       success_count = 0
                   WHERE id = ?""",
                (now, word_id)
            )
            
            if c.rowcount == 0:
                st.error("更新错误队列失败：找不到指定的单词")
                return
            
            conn.commit()
            st.success("已加入错误队列")
            
        except Exception as e:
            st.error(f"更新错误队列时出错: {str(e)}")
            conn.rollback()
        finally:
            conn.close()