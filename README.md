# 英语单词复习系统

这是一个基于 Python 和 Streamlit 开发的英语单词复习系统，它使用艾宾浩斯遗忘曲线来帮助你更有效地记忆英语单词。系统支持创建多个单词盒子，每个盒子可以对应不同的阅读文章。

## 功能特点

### 基本功能
- 创建多个单词盒子，每个盒子对应不同的阅读文章
- 显示每个盒子中的单词数量
- 添加新单词到选定的盒子
- 随机顺序展示盒子中的单词
- 记录每个单词的复习次数和错误次数
- 简单直观的用户界面

### 错误队列功能
- 点击❌将难记的单词加入错误队列
- 错误队列可以存储无限多的单词
- 每10次点击"开始复习"时，最早加入错误队列的5个单词会自动加入复习列表
- 当一个单词被成功记忆5次后，会自动从错误队列中移除
- 显示每个单词的错误率和成功记忆进度

### 数据统计
- 记录每个单词的复习次数
- 统计错误次数和错误率
- 显示单词加入错误队列的时间
- 追踪成功记忆的进度

## 技术栈

- Python 3.12
- Streamlit 1.29.0
- SQLite3
- Pandas 2.1.4

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/english-review-system.git
cd english-review-system
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行程序：
```bash
streamlit run english_review_local.py
```

## 使用说明

### 创建单词盒子
1. 点击左侧的"📦 创建新的记忆盒子"
2. 输入盒子名称（例如："Article 1"）
3. 可选输入文章标题
4. 点击"创建新盒子"按钮

### 添加单词
1. 从下拉菜单选择要使用的盒子
2. 在输入框中输入新单词
3. 按回车键添加单词

### 复习单词
1. 选择要复习的盒子
2. 点击"开始复习"按钮
3. 单词会以随机顺序显示
4. 如果记得这个单词，直接点击单词
5. 如果不记得，点击❌将其加入错误队列
6. 如果需要删除单词，点击🗑️

### 错误队列
- 右侧面板显示错误队列中的所有单词
- 显示每个单词的错误次数和成功记忆进度
- 每10次开始复习时，系统会自动添加5个错误队列中的单词
- 成功记忆5次的单词会自动移出错误队列

## 项目结构

```
english-review-system/
├── README.md              # 项目说明文档
├── requirements.txt       # 项目依赖
├── english_review_local.py # 主程序
├── database.py           # 数据库操作类
└── words.db             # SQLite数据库文件
```

## 贡献指南

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 开源协议

本项目采用 MIT 协议开源。