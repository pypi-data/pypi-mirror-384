"""简单JavaScript功能工具"""
from __future__ import annotations

from pathlib import Path


def create_simple_js_file(file_path: str) -> str:
    """创建简单的JavaScript文件，只包含基础功能"""

    js_content = """// 简单JavaScript功能

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成');

    // 平滑滚动
    setupSmoothScrolling();

    // 简单的表单验证
    setupFormValidation();

    // 返回顶部按钮
    setupBackToTop();
});

// 平滑滚动到锚点
function setupSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

// 简单表单验证
function setupFormValidation() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#dc3545';

                    // 移除错误样式（3秒后）
                    setTimeout(() => {
                        field.style.borderColor = '';
                    }, 3000);
                } else {
                    field.style.borderColor = '';
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('请填写所有必填字段');
            }
        });
    });
}

// 返回顶部功能
function setupBackToTop() {
    // 创建返回顶部按钮
    const backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '↑';
    backToTopBtn.className = 'back-to-top';
    backToTopBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 25px;
        background-color: #007bff;
        color: white;
        border: none;
        font-size: 20px;
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.3s;
        z-index: 1000;
    `;

    document.body.appendChild(backToTopBtn);

    // 滚动时显示/隐藏按钮
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.opacity = '1';
        } else {
            backToTopBtn.style.opacity = '0';
        }
    });

    // 点击返回顶部
    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// 简单的切换功能
function toggleElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        if (element.style.display === 'none') {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    }
}

// 简单的模态框功能
function showModal(message) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;

    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        max-width: 400px;
        text-align: center;
    `;

    modalContent.innerHTML = `
        <p>${message}</p>
        <button onclick="this.closest('.modal').remove()" style="
            background-color: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            margin-top: 10px;
            cursor: pointer;
        ">确定</button>
    `;

    modal.className = 'modal';
    modal.appendChild(modalContent);
    document.body.appendChild(modal);

    // 点击背景关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        return f"简单JavaScript文件创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建JavaScript文件失败: {str(exc)}")


def create_minimal_js_file(file_path: str) -> str:
    """创建极简JavaScript文件"""

    js_content = """// 极简JavaScript功能

// 平滑滚动
document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// 简单表单验证
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const required = form.querySelectorAll('[required]');
        for (let field of required) {
            if (!field.value.trim()) {
                e.preventDefault();
                alert('请填写所有必填字段');
                field.focus();
                return;
            }
        }
    });
});"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        return f"极简JavaScript文件创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建JavaScript文件失败: {str(exc)}")


def create_interactive_js_file(file_path: str) -> str:
    """创建交互式JavaScript文件"""

    js_content = """// 交互式JavaScript功能

document.addEventListener('DOMContentLoaded', function() {
    // 菜单切换
    setupMobileMenu();

    // 图片懒加载
    setupLazyLoading();

    // 简单动画
    setupScrollAnimations();

    // 表单增强
    setupEnhancedForms();
});

// 移动端菜单切换
function setupMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('nav');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
}

// 图片懒加载
function setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// 滚动动画
function setupScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');

    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
            }
        });
    });

    animatedElements.forEach(el => animationObserver.observe(el));
}

// 表单增强
function setupEnhancedForms() {
    // 实时验证
    const inputs = document.querySelectorAll('input, textarea');

    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });

        input.addEventListener('input', function() {
            clearFieldError(this);
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const type = field.type;

    // 清除之前的错误
    clearFieldError(field);

    // 必填字段验证
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, '此字段为必填项');
        return false;
    }

    // 邮箱验证
    if (type === 'email' && value) {
        const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
        if (!emailRegex.test(value)) {
            showFieldError(field, '请输入有效的邮箱地址');
            return false;
        }
    }

    // 电话验证
    if (type === 'tel' && value) {
        const phoneRegex = /^[\\d\\s\\-\\+\\(\\)]+$/;
        if (!phoneRegex.test(value)) {
            showFieldError(field, '请输入有效的电话号码');
            return false;
        }
    }

    return true;
}

function showFieldError(field, message) {
    field.classList.add('error');

    // 创建错误消息
    const errorElement = document.createElement('span');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    errorElement.style.cssText = `
        color: #dc3545;
        font-size: 0.875rem;
        display: block;
        margin-top: 4px;
    `;

    field.parentNode.appendChild(errorElement);
}

function clearFieldError(field) {
    field.classList.remove('error');
    const errorMessage = field.parentNode.querySelector('.error-message');
    if (errorMessage) {
        errorMessage.remove();
    }
}

// 简单的图片轮播
function createSimpleSlider(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const images = container.querySelectorAll('img');
    if (images.length <= 1) return;

    let currentIndex = 0;

    // 隐藏所有图片
    images.forEach((img, index) => {
        img.style.display = index === 0 ? 'block' : 'none';
    });

    // 创建控制按钮
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '‹';
    prevBtn.style.cssText = `
        position: absolute;
        left: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(0,0,0,0.5);
        color: white;
        border: none;
        padding: 10px;
        cursor: pointer;
    `;

    const nextBtn = document.createElement('button');
    nextBtn.textContent = '›';
    nextBtn.style.cssText = `
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(0,0,0,0.5);
        color: white;
        border: none;
        padding: 10px;
        cursor: pointer;
    `;

    container.style.position = 'relative';
    container.appendChild(prevBtn);
    container.appendChild(nextBtn);

    function showImage(index) {
        images.forEach((img, i) => {
            img.style.display = i === index ? 'block' : 'none';
        });
    }

    prevBtn.addEventListener('click', () => {
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        showImage(currentIndex);
    });

    nextBtn.addEventListener('click', () => {
        currentIndex = (currentIndex + 1) % images.length;
        showImage(currentIndex);
    });

    // 自动轮播
    setInterval(() => {
        currentIndex = (currentIndex + 1) % images.length;
        showImage(currentIndex);
    }, 5000);
}"""

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        return f"交互式JavaScript文件创建成功: {file_path}"
    except Exception as exc:
        raise RuntimeError(f"创建JavaScript文件失败: {str(exc)}")


__all__ = [
    "create_simple_js_file",
    "create_minimal_js_file",
    "create_interactive_js_file"
]