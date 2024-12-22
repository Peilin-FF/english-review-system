import os
import random
from datetime import datetime, timedelta
import streamlit as st
import sqlite3
import pandas as pd
import time
from database import WordDatabase

# 设置页面配置
st.set_page_config(
    page_title="英语单词复习系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #45a049;
        transform: scale(1.05);
    }
    .word-button {
        font-size: 18px !important;
        margin: 5px !important;
        min-height: 60px !important;
    }
    .trash-word {
        background-color: #ff4444 !important;
    }
    .trash-word:hover {
        background-color: #cc0000 !important;
    }
    .review-progress {
        font-size: 20px;
        font-weight: bold;
        color: #4CAF50;
    }
    h1 {
        color: #2E7D32;
        text-align: center;
        padding: 20px;
        background: #E8F5E9;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .review-reminder {
        padding: 10px;
        background-color: #FFF3E0;
        border-left: 5px solid #FF9800;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 初始化数据库
    db = WordDatabase()
    
    # 页面标题
    st.title("🌘 记忆系统")
    
    # 初始化session state
    if 'review_words' not in st.session_state:
        st.session_state.review_words = []
    if 'reviewed_words' not in st.session_state:
        st.session_state.reviewed_words = set()
    if 'new_word' not in st.session_state:
        st.session_state.new_word = ""
    if 'selected_box_id' not in st.session_state:
        st.session_state.selected_box_id = None
    
    # 创建三列布局
    left_col, middle_col, right_col = st.columns([2,3,2])
    
    with left_col:
        # 创建新盒子的部分
        with st.expander("📦 创建新的记忆盒子", expanded=False):
            box_name = st.text_input("盒子名称")
            article_title = st.text_input("文章标题（可选）")
            
            if st.button("创建新的盒子", key="create_box"):
                if box_name:
                    box_id = db.create_box(box_name, article_title)
                    if box_id:
                        st.success(f"✨ 成功创建盒子: {box_name}")
                        st.session_state.selected_box_id = box_id
                else:
                    st.warning("⚠️ 请输入盒子名称")
    
    with middle_col:
        # 选择盒子
        st.header("💡 选择记忆盒子")
        boxes = db.get_all_boxes()
        if not boxes.empty:
            # 创建ID到显示名称的映射
            box_display_names = {
                row['id']: f"{row['name']} (📝 {db.get_box_word_count(row['id'])} 个单词)"
                for _, row in boxes.iterrows()
            }
            
            # 如果没有选中的盒子ID，默认选择第一个
            if st.session_state.selected_box_id is None:
                st.session_state.selected_box_id = boxes.iloc[0]['id']
            
            # 获取所有盒子ID的列表
            box_ids = list(box_display_names.keys())
            
            # 找到当前选中盒子ID的索引
            current_index = box_ids.index(st.session_state.selected_box_id)
            
            # 使用盒子ID作为实际值，显示名称作为标签
            selected_box_id = st.selectbox(
                "选择要使用的盒子",
                options=box_ids,
                format_func=lambda x: box_display_names[x],
                index=current_index,
                key="box_selector"
            )
            
            # 更新选中的盒子ID
            st.session_state.selected_box_id = selected_box_id
            current_box_id = selected_box_id

            # 添加新单词的部分
            with st.expander("✍️ 添加新单词", expanded=True):
                def on_change():
                    if st.session_state.new_word:
                        if db.add_word(current_box_id, st.session_state.new_word):
                            st.success(f"✅ 成功添加单词: {st.session_state.new_word}")
                            st.session_state.review_words = []
                            st.session_state.reviewed_words = set()
                        st.session_state.new_word = ""

                new_word = st.text_input(
                    "输入新单词（按回车添加）",
                    key="new_word",
                    on_change=on_change,
                    value=st.session_state.new_word
                )

            # 复习部分
            st.subheader("🔄 单词复习")
            col1, col2 = st.columns([1, 4])
            with col1:
                start_review = st.button("开始复习")
            with col2:
                if st.session_state.review_words:
                    if st.button("🔀 重新打乱顺序"):
                        random.shuffle(st.session_state.review_words)
                        st.session_state.reviewed_words = set()

            if start_review or (st.session_state.review_words and len(st.session_state.review_words) > len(st.session_state.reviewed_words)):
                if not st.session_state.review_words or start_review:
                    # 如果是点击开始复习，增加计数器
                    include_error_words = False
                    if start_review:
                        if db.increment_review_counter():
                            include_error_words = True
                    
                    # 获取单词列表
                    words = db.get_words_from_box(current_box_id, include_error_words)
                    if words:
                        random.shuffle(words)
                        st.session_state.review_words = words
                        st.session_state.reviewed_words = set()
                
                if st.session_state.review_words:
                    total_words = len(st.session_state.review_words)
                    reviewed_count = len(st.session_state.reviewed_words)
                    
                    # 显示进度
                    st.markdown(f"""
                        <div class="review-progress">
                            进度: {reviewed_count}/{total_words}
                        </div>
                    """, unsafe_allow_html=True)
                    st.progress(reviewed_count / total_words)

                    # 使用网格布局显示单词
                    for i, (word_id, word, review_count, trash_count) in enumerate(st.session_state.review_words):
                        if word_id in st.session_state.reviewed_words:
                            st.button(
                                f"✓ {word} (复习: {review_count}, 错误: {trash_count})", 
                                key=f"reviewed_{word_id}", 
                                disabled=True
                            )
                        else:
                            col1, col2, col3 = st.columns([4, 1, 1])
                            with col1:
                                if st.button(f"{word} (复习: {review_count}, 错误: {trash_count})", key=word_id):
                                    db.update_review_count(word_id)
                                    st.session_state.reviewed_words.add(word_id)
                                    st.rerun()
                            with col2:
                                if st.button("❌", key=f"trash_{word_id}", help="记录为错误"):
                                    db.move_to_trash(word_id)
                                    st.session_state.reviewed_words.add(word_id)
                                    st.rerun()
                            with col3:
                                if st.button("🗑️", key=f"delete_{word_id}", help="从数据库中删除此单词"):
                                    if st.session_state.get('confirm_delete') == word_id:
                                        db.delete_word(word_id)
                                        st.session_state.review_words = []
                                        st.session_state.reviewed_words = set()
                                        st.rerun()
                                    else:
                                        st.session_state.confirm_delete = word_id
                                        st.warning(f"再次点击删除按钮确认删除单词 '{word}'")
                            st.markdown("---")

                    if len(st.session_state.reviewed_words) == total_words:
                        st.success("🎉 恭喜！你已完成所有单词的复习！")
                        if st.button("🔄 重新开始"):
                            st.session_state.review_words = []
                            st.session_state.reviewed_words = set()
                            st.rerun()
                else:
                    st.info("📝 这个盒子还没有添加任何单词")
        else:
            st.info("📦 还没有创建任何单词盒子，请先创建一个盒子")
    
    with right_col:
        # 错误队列
        st.header("❌ 错误队列")
        trash_stats = db.get_trash_stats()
        if not trash_stats.empty:
            st.info(f"队列中有 {len(trash_stats)} 个单词")
            st.write("每10次点击开始复习时，最早加入的5个单词会进入复习列表")
            st.write("成功记忆5次的单词会自动移出错误队列")
            for _, row in trash_stats.iterrows():
                with st.expander(f"📖 {row['word']} (错误: {row['trash_count']}, 成功: {row['success_count']}/5)", expanded=True):
                    st.write(f"来自: {row['box_name']}")
                    st.write(f"总复习次数: {row['review_count']}")
                    error_rate = row['trash_count'] / (row['review_count'] + 1) * 100
                    st.write(f"错误率: {error_rate:.1f}%")
                    st.write(f"加入时间: {pd.to_datetime(row['trash_date']).strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.info("🎉 太棒了！错误队列是空的")

if __name__ == "__main__":
    main() 