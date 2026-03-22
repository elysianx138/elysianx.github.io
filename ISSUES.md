# Personal Blog — 问题反馈报告

> 报告时间：2026-03-22
> 项目：Personal Blog（Flask + SQLite）
> 报告人：开发团队
> 版本：v1.0

---

## 一、概述

本报告对 Personal Blog 项目进行全面审查，识别安全漏洞、功能缺陷及体验问题，按严重程度分级并给出修复建议。

---

## 二、安全问题（Critical / High）

### 【Critical-01】管理员路由权限校验缺失√

| 项目 | 内容 |
|------|------|
| 问题编号 | SEC-001 |
| 严重程度 | Critical |
| 影响范围 | 管理后台 `/admin` |
| 发现时间 | 2026-03-22 |

**问题描述：**

`app.py` 第 212-218 行，`admin` 路由仅使用 `@login_required` 装饰器，未对用户角色进行校验。这意味着任何已登录用户（包括 `role=visitor` 的普通访客）均可访问管理后台，执行公告发布与删除操作。

**影响评估：**

- 任何注册用户均可发布伪造公告
- 任何注册用户均可删除现有公告
- 攻击面覆盖所有登录用户

**根因分析：**

Flask-Login 的 `@login_required` 仅验证用户是否已认证（is_authenticated），不验证用户的角色（role）属性。

**修复建议：**

```python
from flask import abort

@app.route("/admin")
@login_required
def admin():
    if current_user.role != 'admin':
        abort(403)  # Forbidden
    conn = get_db_connection()
    ann = conn.execute("SELECT * FROM announcement").fetchall()
    conn.close()
    return render_template('admin.html', announcements=ann)
```

**修复优先级：** P0

---

### 【Critical-02】表单缺少 CSRF 保护√

| 项目 | 内容 |
|------|------|
| 问题编号 | SEC-002 |
| 严重程度 | Critical |
| 影响范围 | 所有 POST 表单 |
| 发现时间 | 2026-03-22 |

**问题描述：**

项目所有 POST 表单（登录、注册、发布文章、上传文件、发布公告、编辑资料）均未实现 CSRF（Cross-Site Request Forgery）令牌校验。

**影响评估：**

攻击者可在第三方网站诱导已登录用户向目标站点发起 POST 请求，执行未授权操作（如发布文章、删除公告）。

**修复建议：**

**方案 A：集成 Flask-WTF（推荐）**

```bash
pip install flask-wtf
```

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('Login')
```

模板中自动生成 CSRF token：

```html
<form method="POST">
    {{ form.hidden_tag() }}
    {{ form.csrf_token }}
    ...
</form>
```

**方案 B：手动实现 CSRF Token**

```python
import secrets
from functools import wraps
from flask import session, request, abort

@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get('csrf_token')
        if not token or token != request.form.get('csrf_token'):
            abort(403)

def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token
```

```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    ...
</form>
```

**修复优先级：** P0

---

### 【Critical-03】敏感配置硬编码√

| 项目 | 内容 |
|------|------|
| 问题编号 | SEC-003 |
| 严重程度 | Critical |
| 影响范围 | 全部 |
| 发现时间 | 2026-03-22 |

**问题描述：**

`app.py` 第 11 行将 `app.secret_key` 硬编码为明文字符串 `"MyBlog"`，第 102 行将管理员码 `ADMIN_CODE = 'MyBlog2026'` 写死在代码中。

**影响评估：**

- `secret_key` 用于签名 session cookie，弱密钥可被暴力破解
- 攻击者若获取源码即获得管理员注册权限
- 生产环境中密钥泄露可能导致用户会话被劫持

**修复建议：**

创建 `.env` 文件（已加入 `.gitignore`）：

```bash
SECRET_KEY=your-production-secret-key-here
ADMIN_CODE=your-admin-code-here
```

安装依赖：

```bash
pip install python-dotenv
```

修改 `app.py`：

```python
from dotenv import load_dotenv
import os

load_dotenv()

app.secret_key = os.getenv('SECRET_KEY', 'dev-fallback-key')  # 生产必须设置
ADMIN_CODE = os.getenv('ADMIN_CODE', 'MyBlog2026')             # 注册时比对此值
```

**修复优先级：** P0

---

### 【Critical-04】questions.db 可能已提交至版本库

| 项目 | 内容 |
|------|------|
| 问题编号 | SEC-004 |
| 严重程度 | High |
| 影响范围 | 版本库 |
| 发现时间 | 2026-03-22 |

**问题描述：**

项目 `.gitignore` 中已包含 `*.db`，但若该文件在 `.gitignore` 创建之前被提交过，则仍保留在 Git 历史中，即使后续从工作目录删除也无效。

**影响评估：**

- 数据库文件含用户密码哈希值
- 历史 commit 中存有旧数据快照
- 攻击者可从 Git 历史中提取敏感信息

**修复建议：**

```bash
# 从 Git 历史中彻底移除数据库文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch questions.db" \
  --tag-name-filter cat -- --all

# 或使用 BFG Repo-Cleaner（更推荐）
java -jar bfg.jar --delete-files *.db
```

**修复优先级：** P1

---

## 三、体验问题（Medium / Low）

### 【Medium-01】文章详情页强制登录

| 项目 | 内容 |
|------|------|
| 问题编号 | UX-001 |
| 严重程度 | Medium |
| 影响范围 | `/article/<id>` |
| 发现时间 | 2026-03-22 |

**问题描述：**

`article_detail` 路由（第 186-197 行）使用了 `@login_required` 装饰器，导致未登录用户无法查看文章详情。

**用户体验影响：**

- 博客的核心价值是内容展示，强制登录阻断了内容传播
- 用户点进文章列表后无法阅读，只能注册登录
- 典型博客场景中，文章列表和详情页应对所有访客开放

**修复建议：**

移除 `@login_required`，仅在写文章/编辑操作时要求登录：

```python
@app.route("/article/<int:article_id>", methods=['GET'])
def article_detail(article_id):
    # 不需要 @login_required，文章对所有人可见
    conn = get_db_connection()
    det = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    conn.close()
    if det is None:
        return "文章不存在", 404
    return render_template('article_detail.html', detail=det)
```

**修复优先级：** P1

---

### 【Medium-02】用户主页缺失文章列表

| 项目 | 内容 |
|------|------|
| 问题编号 | UX-002 |
| 严重程度 | Medium |
| 影响范围 | `/profile/<username>` |
| 发现时间 | 2026-03-22 |

**问题描述：**

用户主页（`profile.html`）仅展示基本信息（用户名、邮箱、角色、个人简介），不显示该用户发布的文章列表。

**用户体验影响：**

- 无法通过个人主页了解用户的创作内容
- 读者无法追溯某位作者的全部文章
- 削弱了博客作者展示自身价值的途径

**修复建议：**

后端 `profile` 路由增加文章查询：

```python
@app.route('/profile/<username>', methods=['GET'])
@login_required
def profile(username):
    conn = get_db_connection()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if u is None:
        conn.close()
        return "用户不存在", 404
    user_articles = conn.execute(
        "SELECT * FROM articles WHERE author = ? ORDER BY date DESC",
        (username,)
    ).fetchall()
    conn.close()
    return render_template('profile.html', user=u, articles=user_articles)
```

前端 `profile.html` 增加文章列表区块。

**修复优先级：** P1

---

### 【Medium-03】文章无法编辑与删除

| 项目 | 内容 |
|------|------|
| 问题编号 | UX-003 |
| 严重程度 | Medium |
| 影响范围 | 文章模块 |
| 发现时间 | 2026-03-22 |

**问题描述：**

当前仅实现了文章发布（`/add`），没有编辑和删除接口。用户无法修改已发布的文章内容，也无法删除自己的文章。

**用户体验影响：**

- 文章内容有误无法更正
- 用户发布后无法管理自己的内容
- 管理员无法删除违规文章

**修复建议：**

新增两个路由：

```python
@app.route("/article/<int:article_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    conn = get_db_connection()
    article = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    if request.method == 'POST':
        conn.execute("UPDATE articles SET title=?, body=? WHERE id=?",
                     (request.form['title'], request.form['body'], article_id))
        conn.commit()
        conn.close()
        return redirect(url_for('article_detail', article_id=article_id))
    conn.close()
    return render_template('edit_article.html', article=article)

@app.route("/article/<int:article_id>/delete", methods=['POST'])
@login_required
def delete_article(article_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()
    flash("文章已删除", "success")
    return redirect(url_for('article_list'))
```

**修复优先级：** P2

---

### 【Medium-04】列表页缺少分页

| 项目 | 内容 |
|------|------|
| 问题编号 | UX-004 |
| 严重程度 | Medium |
| 影响范围 | `/articles_list`、`/files_list` |
| 发现时间 | 2026-03-22 |

**问题描述：**

`articles_list` 和 `files_list` 路由直接返回全量数据，无分页处理。当数据规模增长（如文章超过 100 篇）时，页面加载缓慢，用户体验差。

**修复建议：**

在 SQL 查询中加入 `LIMIT` 和 `OFFSET`，URL 传参控制页码：

```python
@app.route("/articles_list")
def article_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    articles = conn.execute(
        "SELECT * FROM articles ORDER BY date DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    ).fetchall()
    conn.close()

    return render_template('articles_list.html',
                           articles=articles,
                           page=page,
                           total_pages=(total + per_page - 1) // per_page)
```

**修复优先级：** P2

---

### 【Low-01】文章列表页引用不存在的 tag 字段

| 项目 | 内容 |
|------|------|
| 问题编号 | BUG-001 |
| 严重程度 | Low |
| 影响范围 | `/articles_list` |
| 发现时间 | 2026-03-22 |

**问题描述：**

`articles_list.html` 第 20 行引用 `{{ article.tag }}`，但 `articles` 表中不存在 `tag` 列，会导致 Jinja2 渲染时报错。

**修复建议：**

前端模板删除对 `article.tag` 的引用（已在本次审查中修复）。

---

## 四、问题汇总

### 按严重程度

| 编号 | 问题 | 严重程度 | 优先级 |
|------|------|----------|--------|
| SEC-001 | 管理员路由无角色校验 | Critical | P0 |
| SEC-002 | 表单无 CSRF 保护 | Critical | P0 |
| SEC-003 | 敏感配置硬编码 | Critical | P0 |
| SEC-004 | 数据库文件可能入版本库 | High | P1 |
| UX-001 | 文章详情强制登录 | Medium | P1 |
| UX-002 | 用户主页无文章列表 | Medium | P1 |
| UX-003 | 文章无法编辑/删除 | Medium | P2 |
| UX-004 | 列表页无分页 | Medium | P2 |
| BUG-001 | 引用不存在的 tag 字段 | Low | 已修复 |

### 按修复优先级

| 优先级 | 问题编号 | 预计工时 |
|--------|----------|----------|
| P0 | SEC-001, SEC-002, SEC-003 | 2-3 小时 |
| P1 | SEC-004, UX-001, UX-002 | 2-3 小时 |
| P2 | UX-003, UX-004 | 3-4 小时 |
| Low | BUG-001 | 已修复 |

---

## 五、附录

### A. 环境信息

- Python 版本：3.8+
- Flask 版本：最新稳定版
- 数据库：SQLite 3
- 操作系统：跨平台

### B. 相关文件

| 文件 | 位置 | 说明 |
|------|------|------|
| 应用入口 | `app.py` | 所有路由和业务逻辑 |
| 数据库初始化 | `init_db.py` | 表结构定义 |
| 用户认证 | Flask-Login | `@login_required` 装饰器 |
| Markdown 渲染 | marked.js | 前端 CDN 引入 |

### C. 建议的后续工作

1. 完成 P0 安全问题修复后进行代码审查
2. 集成 Flask-WTF，统一表单处理
3. 引入环境配置管理，建立 dev/staging/production 配置分离
4. 考虑引入数据库迁移工具（如 Flask-Migrate）
5. 建立单元测试和集成测试覆盖
