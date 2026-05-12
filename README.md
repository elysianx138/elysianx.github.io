[![GitHub](https://img.shields.io/badge/GitHub-MyBlog-brightgreen?style=flat)](https://github.com/elysianx138/personal_blog)
[![Flask](https://img.shields.io/badge/Flask-2.3+-blue?style=flat)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat)](https://www.python.org/)
[![language](https://img.shields.io/badge/language-English-green?style=flat)](#)

> 🚀MyBlog
> That's an excellent project to practice for green hands

A personal blog system built with Flask. This project is for learning purposes - I started with basic Flask and gradually added more features while organizing the code using Blueprints for better maintainability.

**if you like the project,please star⭐**

## 🤔What's Inside

- User registration and login
- Write and publish articles
- File upload and management
- Real-time chat room
- Admin dashboard
- Article tagging and categories
- Dark/light theme switching
- Reading count tracking
- Article annotations (for open articles)

## 🔧Tech Stack

- **Backend**: Flask, Python 3.10
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login

## 📂Project Structure

```
MyBlog/
├── app.py                 # Main entry point
├── extensions.py          # Flask extensions setup
├── init_db.py            # Database initialization
│
├── routes/                # Blueprint modules
│   ├── user.py          # Login, register, profile
│   ├── articles.py      # Article CRUD
│   ├── files.py         # File handling
│   ├── chat.py          # Chat room
│   ├── admin.py         # Admin dashboard
│   ├── api.py           # API endpoints
│   └── main.py          # Home page
│
├── models/               # Database models
├── utils/                # Helper functions
├── static/               # CSS, JS, images
└── templates/           # HTML templates
```

## ⚙️How to Run

```bash
# Clone the repo
git clone https://github.com/elysianx138/elysianx.github.io.git
cd personal_blog

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
pip install flask flask-login python-dotenv

# Run
python app.py
```

Visit `http://localhost:5000`

## 👀Preview
![](<img/屏幕截图 2026-05-12 200909.png>)
![alt text](<img/屏幕截图 2026-05-12 201026.png>)
![alt text](<img/屏幕截图 2026-05-12 201102.png>)

## 💻My Web
You can also visit https://elysianxgithubio-production-8080.up.railway.app

## ❓What I Learned

Building this project helped me understand:
- Flask Blueprints and project structure
- Database operations with SQLite
- User authentication
- Basic frontend (HTML/CSS/JS)
- Environment variable configuration
- RESTful API concepts (still learning)

## 📚Notes

This is a learning project. The code might not follow all best practices, but it works and shows my progression from basic Flask to more organized architecture.

## 🗨Contact

- GitHub: https://github.com/elysianx138/elysianx.github.io.git

## 📫Social media
**if you want to talk more with me,welcome to add my Gmail adn social media❤**

Gmail: elysianx138@gmail.com

Ins:https://instagram.com/elysianx138

YouTube:https://youtube.com/elysianx

X:https://x.com/@johnchenmOwn

## License
- MIT License. See [MIT LICENSE]()
