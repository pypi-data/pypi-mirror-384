"""JavaScript 脚本生成工具"""
from __future__ import annotations

from pathlib import Path


def create_js_file(file_path: str, content: str = ""):
    """创建JavaScript文件；自动创建父级目录"""
    js_template = f"""// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {{
  // Smooth scroll 由 CSS scroll-behavior 支持，这里补充导航折叠与激活态处理
  const navLinks = Array.from(document.querySelectorAll('.navbar a.nav-link[href^="#"]'));
  if (navLinks.length) {{
    navLinks.forEach(link => {{
      link.addEventListener('click', () => {{
        const navbarCollapse = document.querySelector('.navbar .navbar-collapse');
        if (navbarCollapse && navbarCollapse.classList.contains('show')) {{
          const toggler = document.querySelector('.navbar .navbar-toggler');
          toggler && toggler.click();
        }}
      }});
    }});
  }}

  // 简易 ScrollSpy
  const sections = Array.from(document.querySelectorAll('section[id]'));
  const onScroll = () => {{
    let activeId = null;
    const scrollY = window.scrollY + 120; // 预留导航高度
    sections.forEach(sec => {{
      const rect = sec.getBoundingClientRect();
      const top = window.scrollY + rect.top;
      if (scrollY >= top) activeId = sec.id;
    }});
    if (activeId && navLinks.length) {{
      navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + activeId));
    }}

    // 玻璃态导航滚动态
    const nav = document.querySelector('.navbar-glass');
    if (nav) {{
      nav.classList.toggle('scrolled', window.scrollY > 10);
    }}
  }};
  window.addEventListener('scroll', onScroll, {{ passive: true }});
  onScroll();

  // Reveal 动画
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {{
    const io = new IntersectionObserver(entries => {{
      entries.forEach(e => {{ if (e.isIntersecting) e.target.classList.add('revealed'); }});
    }}, {{ threshold: 0.1 }});
    reveals.forEach(el => io.observe(el));
  }} else {{
    reveals.forEach(el => el.classList.add('revealed'));
  }}

  // 主题切换（明/暗）
  const applyTheme = (theme) => {{
    const html = document.documentElement;
    if (theme === 'dark') html.setAttribute('data-theme', 'dark');
    else html.removeAttribute('data-theme');
  }};
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {{
    applyTheme(savedTheme);
  }} else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
    applyTheme('dark');
  }}
  const toggleBtn = document.querySelector('[data-action="toggle-theme"]');
  toggleBtn && toggleBtn.addEventListener('click', () => {{
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const next = isDark ? 'light' : 'dark';
    localStorage.setItem('theme', next);
    applyTheme(next);
  }});

  // 统计数字动画
  const counters = document.querySelectorAll('.counter[data-target]');
  const animateCounter = (el) => {{
    const target = parseFloat(el.getAttribute('data-target')) || 0;
    const duration = 1200;
    const startTime = performance.now();
    const startVal = 0;
    const step = (now) => {{
      const p = Math.min(1, (now - startTime) / duration);
      const eased = p < 0.5 ? 2*p*p : -1 + (4 - 2*p)*p; // easeInOutQuad
      const val = Math.floor(startVal + (target - startVal) * eased);
      el.textContent = val.toString();
      if (p < 1) requestAnimationFrame(step);
    }};
    requestAnimationFrame(step);
  }};
  if ('IntersectionObserver' in window) {{
    const co = new IntersectionObserver(entries => {{
      entries.forEach(e => {{ if (e.isIntersecting) {{ animateCounter(e.target); co.unobserve(e.target); }} }});
    }}, {{ threshold: 0.4 }});
    counters.forEach(el => co.observe(el));
  }} else {{
    counters.forEach(el => animateCounter(el));
  }}

  // AI 图片占位兜底（即使未执行 inject_images，也能避免破图）
  const placeholderSVG = (text = 'Image') => {{
    const svg = "<?xml version='1.0' encoding='UTF-8'?>" +
      "<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600'>" +
      "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>" +
      "<stop offset='0%' stop-color='rgba(13,110,253,0.15)'/>" +
      "<stop offset='100%' stop-color='rgba(102,16,242,0.15)'/></linearGradient></defs>" +
      "<rect width='100%' height='100%' fill='url(#g)'/>" +
      "<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='#99a2b3' font-size='24' font-family='-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial'>" +
      text +
      "</text></svg>";
    return "data:image/svg+xml;utf8," + encodeURIComponent(svg);
  }};

  const phImg = placeholderSVG('Image');
  document.querySelectorAll('img[data-topic]').forEach(img => {{
    if (!img.getAttribute('src')) img.setAttribute('src', phImg);
    img.onerror = () => {{ img.setAttribute('src', phImg); }};
  }});
  document.querySelectorAll('[data-bg-topic]').forEach(el => {{
    const cs = window.getComputedStyle(el);
    const hasBg = cs.backgroundImage && cs.backgroundImage !== 'none';
    if (!hasBg) {{
      el.style.backgroundImage = 'linear-gradient(135deg, rgba(13,110,253,.15) 0%, rgba(102,16,242,.15) 100%)';
      el.style.backgroundSize = 'cover';
      el.style.backgroundPosition = 'center';
      if (!el.style.minHeight) el.style.minHeight = '220px';
    }}
  }});

  // 视差滚动（基于 data-parallax）
  const parallaxNodes = Array.from(document.querySelectorAll('[data-parallax]'));
  if (parallaxNodes.length) {{
    const updateParallax = () => {{
      const scrollY = window.scrollY || window.pageYOffset;
      parallaxNodes.forEach(node => {{
        const speed = parseFloat(node.getAttribute('data-parallax')) || 0.18;
        const rect = node.getBoundingClientRect();
        const offset = (scrollY + rect.top) * speed * -1;
        node.style.setProperty('--parallax-offset', `${{offset.toFixed(2)}}px`);
      }});
    }};
    updateParallax();
    window.addEventListener('scroll', () => requestAnimationFrame(updateParallax), {{ passive: true }});
    window.addEventListener('resize', () => requestAnimationFrame(updateParallax));
  }}

  // 轻量 3D 倾斜效果（data-tilt）
  const tiltNodes = Array.from(document.querySelectorAll('[data-tilt]'));
  tiltNodes.forEach(node => {{
    const strength = parseFloat(node.getAttribute('data-tilt-strength')) || 10;
    const damp = parseFloat(node.getAttribute('data-tilt-damping')) || 0.12;
    let currentX = 0;
    let currentY = 0;
    let frame;

    const animate = () => {{
      node.style.setProperty('--tilt-rotate-x', `${{currentY.toFixed(3)}}deg`);
      node.style.setProperty('--tilt-rotate-y', `${{currentX.toFixed(3)}}deg`);
      frame = requestAnimationFrame(animate);
    }};

    const handlePointerMove = (event) => {{
      const rect = node.getBoundingClientRect();
      const relX = (event.clientX - rect.left) / rect.width;
      const relY = (event.clientY - rect.top) / rect.height;
      const targetX = (relX - 0.5) * strength;
      const targetY = (0.5 - relY) * strength;
      currentX = currentX + (targetX - currentX) * damp;
      currentY = currentY + (targetY - currentY) * damp;
    }};

    const resetTilt = () => {{
      currentX = 0;
      currentY = 0;
    }};

    node.addEventListener('pointerenter', () => {{
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(animate);
    }});
    node.addEventListener('pointermove', handlePointerMove);
    node.addEventListener('pointerleave', () => {{
      resetTilt();
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(animate);
      setTimeout(() => cancelAnimationFrame(frame), 180);
    }});
    node.addEventListener('pointerup', resetTilt);
  }});

  // 噪点背景（data-canvas="noise"）
  const noiseCanvas = document.querySelector('[data-canvas="noise"]');
  if (noiseCanvas) {{
    const ctx = noiseCanvas.getContext('2d');
    const renderNoise = () => {{
      const {{ width, height }} = noiseCanvas.parentElement.getBoundingClientRect();
      noiseCanvas.width = Math.max(320, Math.round(width));
      noiseCanvas.height = Math.max(320, Math.round(height));
      const imageData = ctx.createImageData(noiseCanvas.width, noiseCanvas.height);
      const buffer = imageData.data;
      for (let i = 0; i < buffer.length; i += 4) {{
        const value = Math.random() * 255;
        buffer[i] = value;
        buffer[i + 1] = value;
        buffer[i + 2] = value;
        buffer[i + 3] = Math.random() * 50 + 30;
      }}
      ctx.putImageData(imageData, 0, 0);
    }};
    renderNoise();
    window.addEventListener('resize', () => requestAnimationFrame(renderNoise));
  }}

  {content if content else '// 在这里添加你的JavaScript代码'}
}});

// 工具函数
function $(selector) {{ return document.querySelector(selector); }}
function $$(selector) {{ return document.querySelectorAll(selector); }}
"""

    try:
        # 确保父目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(js_template)
        return f"JavaScript文件创建成功: {file_path}"
    except Exception as e:
        raise RuntimeError(f"创建JavaScript文件失败: {str(e)}")



__all__ = ["create_js_file"]
