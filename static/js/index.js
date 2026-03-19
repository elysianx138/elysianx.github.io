// 首页交互逻辑

// 文件上传点击触发
function triggerUpload() {
    document.getElementById('fileInput').click();
}

// 文件选择处理
document.getElementById('fileInput').addEventListener('change', function(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFileUpload(files);
    }
});

// 拖拽上传
const uploadCard = document.querySelector('.upload-card');

uploadCard.addEventListener('dragover', function(e) {
    e.preventDefault();
    this.style.borderColor = '#c9a962';
    this.style.background = 'rgba(201, 169, 98, 0.05)';
});

uploadCard.addEventListener('dragleave', function(e) {
    e.preventDefault();
    this.style.borderColor = 'rgba(201, 169, 98, 0.15)';
    this.style.background = 'transparent';
});

uploadCard.addEventListener('drop', function(e) {
    e.preventDefault();
    this.style.borderColor = 'rgba(201, 169, 98, 0.15)';
    this.style.background = 'transparent';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files);
    }
});

// 处理文件上传（暂时打印，后续对接后端）
function handleFileUpload(files) {
    console.log('准备上传文件:', files.length, '个');
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        console.log('文件:', file.name, '大小:', formatFileSize(file.size));
    }
    
    // TODO: 这里后续对接后端 API
    alert(`已选择 ${files.length} 个文件，请到后端添加上传接口！`);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 文章卡片点击（暂时，后续对接详情页）
document.querySelectorAll('.article-card').forEach(card => {
    card.addEventListener('click', function() {
        const title = this.querySelector('.article-title').textContent;
        console.log('点击文章:', title);
        // TODO: 跳转到文章详情页
        alert('文章详情页开发中...');
    });
});

// 用户卡片点击
document.querySelectorAll('.user-card').forEach(card => {
    card.addEventListener('click', function() {
        const name = this.querySelector('.user-name').textContent;
        console.log('点击用户:', name);
        // TODO: 跳转到用户详情页
        alert('用户详情页开发中...');
    });
});

// 导航栏滚动效果
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(10, 10, 10, 0.95)';
    } else {
        navbar.style.background = 'rgba(10, 10, 10, 0.9)';
    }
});

console.log('MyBlog 首页加载完成');
