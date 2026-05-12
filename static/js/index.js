// MyBlog 首页 - 前后端完全分离
async function initIndex() {
    try {
        var res = await fetch('/api/index');
        var data = await res.json();
        
        if (data.success) {
            renderUser(data.current_user);
            renderArticles(data.articles);
            renderStats(data.stats);
            renderAnnouncements(data.announcements);
        }
    } catch (err) {
        console.error('加载首页数据失败:', err);
    }
}

function renderUser(username) {
    var titleEl = document.getElementById('pageTitle');
    var authEl = document.getElementById('authSection');
    var profileEl = document.getElementById('profileLink');
    
    if (titleEl) {
        titleEl.textContent = username ? username + '，欢迎回来' : '欢迎来到 MyBlog';
    }
    
    if (authEl) {
        authEl.style.display = username ? 'none' : 'block';
    }
    
    if (profileEl) {
        if (username) {
            profileEl.style.display = 'flex';
            profileEl.href = '/profile/' + username;
        } else {
            profileEl.style.display = 'none';
        }
    }
}

function renderArticles(articles) {
    var container = document.getElementById('articleList');
    if (!container) return;
    
    if (!articles || articles.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>暂无文章</p><a href="/add" style="color:var(--accent); font-size:13px;">写第一篇</a></div>';
        return;
    }
    
    var html = articles.map(function(article) {
        var reading = article.reading || 0;
        var tags = '';
        if (article.tag) {
            var tagList = article.tag.split(',');
            tags = tagList.map(function(t) {
                return '<span style="display:inline-block; padding:2px 10px; margin-right:8px; font-size:12px; background:var(--accent-light); color:var(--accent); border-radius:12px;">' + t.trim() + '</span>';
            }).join('');
        }
        
        return '<div class="article-card" onclick="location.href=\'/article/' + article.id + '\'">' +
            '<div class="article-thumb">' +
                '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' +
            '</div>' +
            '<div class="article-body">' +
                '<div class="article-top">' +
                    '<span class="article-date">' + (article.date || '') + '</span>' +
                    '<span class="article-reading" style="color:var(--text-muted); font-size:12px;">' + reading + ' 阅读</span>' +
                '</div>' +
                '<h3 class="article-title">' + (article.title || '') + '</h3>' +
                (tags ? '<div style="margin-top:10px;">' + tags + '</div>' : '') +
                '<div class="article-footer">' +
                    '<span class="article-author">' + (article.author || '') + '</span>' +
                    '<span class="article-link">阅读全文</span>' +
                '</div>' +
            '</div>' +
        '</div>';
    }).join('');
    
    container.innerHTML = html;
}

function renderStats(stats) {
    if (!stats) return;
    
    var articlesEl = document.getElementById('statArticles');
    var usersEl = document.getElementById('statUsers');
    var filesEl = document.getElementById('statFiles');
    
    if (articlesEl) articlesEl.textContent = stats.articles || 0;
    if (usersEl) usersEl.textContent = stats.users || 0;
    if (filesEl) filesEl.textContent = stats.files || 0;
}

function renderAnnouncements(announcements) {
    var widget = document.getElementById('announcementWidget');
    var body = document.getElementById('announcementBody');
    
    if (!announcements || announcements.length === 0) {
        if (widget) widget.style.display = 'none';
        return;
    }
    
    if (widget && body) {
        widget.style.display = 'block';
        body.innerHTML = announcements.map(function(a) {
            return '<div class="announcement-item">' +
                '<div class="ann-title">' + (a.title || '') + '</div>' +
                '<div class="md-body ann-body">' + (a.body || '') + '</div>' +
                '<div class="ann-date">' + (a.date || '') + '</div>' +
            '</div>';
        }).join('');
    }
}

document.addEventListener('DOMContentLoaded', initIndex);