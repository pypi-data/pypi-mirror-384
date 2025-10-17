"""页面模板相关工具"""
from __future__ import annotations

import html
import urllib.parse
from pathlib import Path


def create_html_file(
    file_path: str,
    title: str = "New Page",
    content: str = "",
    style: str = "ultra_modern",
    sections: list | dict | None = None,
) -> str:
    """创建HTML文件，支持多风格模板（统一引用 assets 目录）"""

    style_key = (style or "ultra_modern").lower().replace("-", "_")

    def hero_ultra() -> str:
        return f"""
    <header id=\"home\" class=\"hero hero-ultra section text-center\" data-bg-topic=\"hero premium gradient glassmorphism\" data-parallax=\"0.25\">
      <div class=\"hero-floating\" aria-hidden=\"true\">
        <div class=\"floating-shape shape-one\"></div>
        <div class=\"floating-shape shape-two\"></div>
      </div>
      <div class=\"container hero-inner\">
        <span class=\"badge badge-soft mb-3\">全新发布</span>
        <h1 class=\"display-5 mb-3\">{title}</h1>
        <p class=\"section-lead mx-auto\">一句话定义品牌价值主张：简洁而有力，体现高级感与专业度。</p>
        <div class=\"mt-4 d-flex justify-content-center gap-3\">
          <a href=\"#contact\" class=\"btn btn-primary btn-lg px-4\">立即咨询</a>
          <a href=\"#showcase\" class=\"btn btn-secondary btn-lg px-4\">查看案例</a>
        </div>
      </div>
      <div class=\"shape-bottom\" aria-hidden=\"true\">
        <svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 1440 320\"><path fill=\"#f8f9fa\" d=\"M0,128L48,117.3C96,107,192,85,288,112C384,139,480,213,576,229.3C672,245,768,203,864,165.3C960,128,1056,96,1152,85.3C1248,75,1344,85,1392,90.7L1440,96L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z\"></path></svg>
      </div>
    </header>
"""

    def body_ultra() -> str:
        return f"""
    <main>
      <section class=\"section section-sm\">
        <div class=\"container\">
          <div class=\"text-center text-muted mb-3\">受信任的合作伙伴</div>
          <div class=\"d-flex flex-wrap align-items-center justify-content-center gap-4 opacity-75 marquee-clients\">
            <div class=\"fw-bold\">ALPHA</div>
            <div class=\"fw-bold\">BETA</div>
            <div class=\"fw-bold\">GAMMA</div>
            <div class=\"fw-bold\">OMEGA</div>
            <div class=\"fw-bold\">NOVA</div>
          </div>
        </div>
      </section>

      <section class=\"section section-sm\">
        <div class=\"container\">
          <div class=\"row g-4 text-center\">
            <div class=\"col-md-3\"><div class=\"feature-card glass p-4 reveal\" data-tilt><div class=\"display-6 fw-bold counter\" data-target=\"120\">0</div><div class=\"text-muted mt-2\">成功项目</div></div></div>
            <div class=\"col-md-3\"><div class=\"feature-card glass p-4 reveal\" data-tilt><div class=\"display-6 fw-bold counter\" data-target=\"50\">0</div><div class=\"text-muted mt-2\">行业客户</div></div></div>
            <div class=\"col-md-3\"><div class=\"feature-card glass p-4 reveal\" data-tilt><div class=\"display-6 fw-bold counter\" data-target=\"98\">0</div><div class=\"text-muted mt-2\">满意度(%)</div></div></div>
            <div class=\"col-md-3\"><div class=\"feature-card glass p-4 reveal\" data-tilt><div class=\"display-6 fw-bold counter\" data-target=\"7\">0</div><div class=\"text-muted mt-2\">年行业经验</div></div></div>
          </div>
        </div>
      </section>

      <section id=\"services\" class=\"section\">
        <div class=\"container\">
          <h2 class=\"h3 text-center section-title\">我们打造一流体验</h2>
          <p class=\"section-lead text-center\">以品牌级视觉与工程化质控，交付可直接上线的商业作品。</p>
          <div class=\"row g-4 mt-2\">
            <div class=\"col-md-4\">
              <div class=\"feature-card reveal text-start\" data-tilt>
                <img data-topic=\"premium product hero\" alt=\"产品图\" class=\"mb-3 rounded shadow-sm\">
                <div class=\"feature-icon\" aria-hidden=\"true\">🚀</div>
                <h3 class=\"h5 mb-2\">高端设计系统</h3>
                <p class=\"mb-0 text-muted\">统一配色/字体/动效/圆角/阴影，保持品牌一致性。</p>
              </div>
            </div>
            <div class=\"col-md-4\">
              <div class=\"feature-card reveal text-start\" data-tilt>
                <img data-topic=\"lifestyle scene premium\" alt=\"场景图\" class=\"mb-3 rounded shadow-sm\">
                <div class=\"feature-icon\" aria-hidden=\"true\">🎯</div>
                <h3 class=\"h5 mb-2\">结果导向体验</h3>
                <p class=\"mb-0 text-muted\">移动优先、性能优化、可用性与可访问性全面考虑。</p>
              </div>
            </div>
            <div class=\"col-md-4\">
              <div class=\"feature-card reveal text-start\" data-tilt>
                <img data-topic=\"detail macro elegant\" alt=\"细节图\" class=\"mb-3 rounded shadow-sm\">
                <div class=\"feature-icon\" aria-hidden=\"true\">💎</div>
                <h3 class=\"h5 mb-2\">精致细节</h3>
                <p class=\"mb-0 text-muted\">玻璃态/渐变/光扫等细节，赋予质感与层次。</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id=\"showcase\" class=\"section section-sm\">
        <div class=\"container\">
          <h2 class=\"h3 text-center section-title\">精选案例</h2>
          <p class=\"section-lead text-center\">来自不同行业的视觉与体验实践。</p>
          <div id=\"product-grid\" class=\"row g-4 mt-2 product-grid\"></div>
        </div>
      </section>

      <section class=\"section section-sm\">
        <div class=\"container\">
          <div class=\"row g-4\">
            <div class=\"col-md-4\">
              <div class=\"feature-card glass reveal\" data-tilt>
                <div class=\"d-flex align-items-center gap-3 mb-3\">
                  <img class=\"rounded-circle\" width=\"48\" height=\"48\" alt=\"顾客\" data-topic=\"portrait minimal premium\">
                  <div class=\"fw-semibold\">Alex Chen</div>
                </div>
                <p class=\"mb-0 text-muted\">“设计质感与转化率提升明显，是一次非常愉快的合作。”</p>
              </div>
            </div>
            <div class=\"col-md-4\">
              <div class=\"feature-card glass reveal\" data-tilt>
                <div class=\"d-flex align-items-center gap-3 mb-3\">
                  <img class=\"rounded-circle\" width=\"48\" height=\"48\" alt=\"顾客\" data-topic=\"portrait minimal premium\">
                  <div class=\"fw-semibold\">Liang Wu</div>
                </div>
                <p class=\"mb-0 text-muted\">“移动端体验极佳，品牌形象焕然一新。”</p>
              </div>
            </div>
            <div class=\"col-md-4\">
              <div class=\"feature-card glass reveal\" data-tilt>
                <div class=\"d-flex align-items-center gap-3 mb-3\">
                  <img class=\"rounded-circle\" width=\"48\" height=\"48\" alt=\"顾客\" data-topic=\"portrait minimal premium\">
                  <div class=\"fw-semibold\">Yvonne Zhao</div>
                </div>
                <p class=\"mb-0 text-muted\">“细节到位，交互顺畅，交付质量超出预期。”</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id=\"pricing\" class=\"section\">
        <div class=\"container\">
          <h2 class=\"h3 text-center section-title\">灵活定价</h2>
          <p class=\"section-lead text-center\">按需选择，快速启动高质感网站项目。</p>
          <div class=\"row g-4 mt-2\">
            <div class=\"col-md-4\">
              <div class=\"feature-card glass text-start reveal\" data-tilt>
                <h3 class=\"h5 mb-1\">起步</h3>
                <div class=\"display-6 fw-bold mb-3\">¥ 9,999</div>
                <ul class=\"text-muted mb-4\">
                  <li>基础单页/落地页</li>
                  <li>品牌配色与排版</li>
                  <li>移动端适配</li>
                </ul>
                <a class=\"btn btn-primary w-100\" href=\"#contact\">咨询方案</a>
              </div>
            </div>
            <div class=\"col-md-4\">
              <div class=\"feature-card glass text-start reveal\" data-tilt>
                <h3 class=\"h5 mb-1\">专业</h3>
                <div class=\"display-6 fw-bold mb-3\">¥ 29,999</div>
                <ul class=\"text-muted mb-4\">
                  <li>多页面信息架构</li>
                  <li>图片智能注入与动效</li>
                  <li>明/暗主题切换</li>
                </ul>
                <a class=\"btn btn-primary w-100\" href=\"#contact\">咨询方案</a>
              </div>
            </div>
            <div class=\"col-md-4\">
              <div class=\"feature-card glass text-start reveal\" data-tilt>
                <h3 class=\"h5 mb-1\">旗舰</h3>
                <div class=\"display-6 fw-bold mb-3\">¥ 59,999</div>
                <ul class=\"text-muted mb-4\">
                  <li>定制视觉语言与插画</li>
                  <li>复杂交互与多端适配</li>
                  <li>性能优化与SEO结构化</li>
                </ul>
                <a class=\"btn btn-primary w-100\" href=\"#contact\">咨询方案</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class=\"section section-sm\">
        <div class=\"container\">
          <div class=\"p-5 cta text-center reveal\" data-parallax=\"-0.35\">
            <h2 class=\"h4 mb-2\">准备好升级你的品牌体验？</h2>
            <p class=\"mb-3\">我们将用设计与工程，让每一个像素都有价值。</p>
            <a class=\"btn btn-light btn-lg px-4\" href=\"#contact\">立即联系</a>
          </div>
        </div>
      </section>

      <section class=\"section section-sm\">
        <div class=\"container\">
          <h2 class=\"h3 text-center section-title\">常见问题</h2>
          <div class=\"mx-auto\" style=\"max-width:900px;\">
            <details class=\"feature-card mb-3\" data-tilt><summary class=\"fw-semibold\">项目周期一般多久？</summary><div class=\"mt-2 text-muted\">典型项目 2-4 周，复杂项目按需评估并排期。</div></details>
            <details class=\"feature-card mb-3\" data-tilt><summary class=\"fw-semibold\">是否支持品牌升级与重构？</summary><div class=\"mt-2 text-muted\">支持，提供配色、字体、组件体系与页面模板重塑。</div></details>
            <details class=\"feature-card mb-3\" data-tilt><summary class=\"fw-semibold\">如何保障交付质量？</summary><div class=\"mt-2 text-muted\">完善的设计系统、代码规范与多端测试，确保上线质量。</div></details>
          </div>
        </div>
      </section>

      <section id=\"contact\" class=\"section\">
        <div class=\"container\">
          <h2 class=\"h3 text-center section-title\">联系我们</h2>
          <p class=\"section-lead text-center\">留下您的需求，我们会尽快与您联系。</p>
          <form class=\"mx-auto mt-3 reveal form-floating-cards\" style=\"max-width:560px;\">
            <div class=\"mb-3\">
              <label class=\"form-label\">姓名</label>
              <input type=\"text\" class=\"form-control\" placeholder=\"请输入姓名\" aria-label=\"姓名\">
            </div>
            <div class=\"mb-3\">
              <label class=\"form-label\">邮箱</label>
              <input type=\"email\" class=\"form-control\" placeholder=\"name@example.com\" aria-label=\"邮箱\">
            </div>
            <div class=\"mb-3\">
              <label class=\"form-label\">留言</label>
              <textarea class=\"form-control\" rows=\"4\" placeholder=\"想聊点什么？\" aria-label=\"留言\"></textarea>
            </div>
            <button type=\"submit\" class=\"btn btn-primary w-100\">发送</button>
          </form>
        </div>
      </section>
    </main>

    <footer class=\"py-5 bg-dark text-white\">
      <div class=\"container\">
        <div class=\"row g-4\">
          <div class=\"col-md-4\">
            <div class=\"fw-bold mb-2\">{title}</div>
            <div class=\"text-muted\">以设计驱动增长，以工程保障质量。</div>
          </div>
          <div class=\"col-md-2\">
            <div class=\"fw-semibold mb-2\">产品</div>
            <ul class=\"list-unstyled text-muted\"><li>方案</li><li>案例</li><li>支持</li></ul>
          </div>
          <div class=\"col-md-2\">
            <div class=\"fw-semibold mb-2\">公司</div>
            <ul class=\"list-unstyled text-muted\"><li>关于</li><li>加入我们</li><li>联系</li></ul>
          </div>
          <div class=\"col-md-4\">
            <div class=\"fw-semibold mb-2\">订阅更新</div>
            <div class=\"d-flex gap-2\">
              <input class=\"form-control\" placeholder=\"输入邮箱\" aria-label=\"订阅邮箱\">
              <button class=\"btn btn-primary\">订阅</button>
            </div>
          </div>
        </div>
        <div class=\"text-center small mt-4 text-muted\">© {title}. 保留所有权利。</div>
      </div>
    </footer>
"""

    def hero_minimal() -> str:
        return f"""
    <header id=\"home\" class=\"hero hero-minimal section\" data-bg-topic=\"minimal luxury interior\">
      <div class=\"container hero-inner minimal-grid\">
        <div class=\"hero-minimal__content\">
          <span class=\"tagline\">{title}</span>
          <h1 class=\"display-4\">策略驱动的品牌体验设计</h1>
          <p class=\"section-lead\">以视觉、文字与交互的克制表达，呈现具有收藏价值的数字作品。</p>
          <div class=\"hero-minimal__cta\">
            <a href=\"#showcase\" class=\"btn btn-outline-light btn-lg\">浏览作品集</a>
            <a href=\"#contact\" class=\"btn btn-primary btn-lg\">预约咨询</a>
          </div>
        </div>
        <div class=\"hero-minimal__gallery\">
          <figure class=\"gallery-card\" data-topic=\"modern architecture warm light\"></figure>
          <figure class=\"gallery-card\" data-topic=\"editorial design minimal\"></figure>
          <figure class=\"gallery-card tall\" data-topic=\"art installation premium\"></figure>
        </div>
      </div>
    </header>
"""

    def body_minimal() -> str:
        return f"""
    <main>
      <section class=\"section section-alt\">
        <div class=\"container\">
          <div class=\"section-heading\">
            <span class=\"eyebrow\">合作品牌</span>
            <h2 class=\"h3\">与行业前沿品牌共同成长</h2>
          </div>
          <div class=\"brand-grid\">
            <span>ALPHA</span>
            <span>BARNES</span>
            <span>EMBER</span>
            <span>NEBULA</span>
            <span>FRAME</span>
            <span>STUDIO</span>
          </div>
        </div>
      </section>

      <section id=\"showcase\" class=\"section\">
        <div class=\"container\">
          <div class=\"section-heading d-flex justify-content-between align-items-center\">
            <div>
              <span class=\"eyebrow\">Selected Works</span>
              <h2 class=\"h3\">精选作品集</h2>
            </div>
            <a class=\"btn btn-outline-light btn-sm\" href=\"#\">下载作品集</a>
          </div>
          <div class=\"row g-4\">
            <article class=\"case-card reveal\">
              <div class=\"case-media\" data-bg-topic=\"luxury fashion website mockup\"></div>
              <div class=\"case-content\">
                <span class=\"eyebrow\">电商体验</span>
                <h3>Atelier Aurora</h3>
                <p class=\"text-muted\">为奢侈时尚品牌打造沉浸式购物体验，提升平均客单价 35%。</p>
              </div>
            </article>
            <article class=\"case-card reveal\">
              <div class=\"case-media\" data-bg-topic=\"digital product dashboard gradient\"></div>
              <div class=\"case-content\">
                <span class=\"eyebrow\">SaaS 平台</span>
                <h3>Nova Metrics</h3>
                <p class=\"text-muted\">打造全新数据可视化界面，信息更聚焦，决策效率提升 2 倍。</p>
              </div>
            </article>
            <article class=\"case-card reveal\">
              <div class=\"case-media\" data-bg-topic=\"editorial magazine layout photography\"></div>
              <div class=\"case-content\">
                <span class=\"eyebrow\">品牌官网</span>
                <h3>Studio Linear</h3>
                <p class=\"text-muted\">为创意工作室重塑线上形象，建立统一设计语言与内容矩阵。</p>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section class=\"section\">
        <div class=\"container\">
          <div class=\"section-heading\">
            <span class=\"eyebrow\">Capabilities</span>
            <h2 class=\"h3\">服务能力</h2>
          </div>
          <div class=\"row g-4\">
            <article class=\"service-card reveal\">
              <h3>品牌体验战略</h3>
              <p class=\"text-muted\">从品牌故事到视觉语言的系统构建，保持所有触点的一致性与辨识度。</p>
              <ul>
                <li>品牌识别系统</li>
                <li>体验旅程地图</li>
                <li>数字资产手册</li>
              </ul>
            </article>
            <article class=\"service-card reveal\">
              <h3>高保真视觉设计</h3>
              <p class=\"text-muted\">兼顾商业目标与审美品味，交付可直接上线的视觉稿与规范。</p>
              <ul>
                <li>高保真界面</li>
                <li>动效与交互动线</li>
                <li>组件库与设计系统</li>
              </ul>
            </article>
            <article class=\"service-card reveal\">
              <h3>体验工程实现</h3>
              <p class=\"text-muted\">工程团队协同，保证设计高复用与性能优化，上线即精品。</p>
              <ul>
                <li>响应式前端开发</li>
                <li>性能优化与SEO</li>
                <li>多端测试与迭代</li>
              </ul>
            </article>
          </div>
        </div>
      </section>
      
      <section class=\"section section-alt\">
        <div class=\"container\">
          <div class=\"row g-4 align-items-center\">
            <div class=\"col-lg-6\">
              <div class=\"testimonial-card reveal\">
                <p class=\"quotation\">“合作过程高效顺畅，设计稿上线几乎零返工，品牌形象全面升级。”</p>
                <div class=\"d-flex align-items-center gap-3 mt-3\">
                  <img class=\"rounded-circle\" width=\"48\" height=\"48\" data-topic=\"portrait minimal premium\" alt=\"客户头像\">
                  <div>
                    <div class=\"fw-semibold\">Evelyn Wang</div>
                    <div class=\"text-muted\">CMO · Aurora Studio</div>
                  </div>
                </div>
              </div>
            </div>
            <div class=\"col-lg-6\">
              <div class=\"numbers-card reveal\">
                <div><span class=\"display-5 fw-bold counter\" data-target=\"120\">0</span><span class=\"text-muted\">+ 完成项目</span></div>
                <div><span class=\"display-5 fw-bold counter\" data-target=\"98\">0</span><span class=\"text-muted\">% 客户满意度</span></div>
                <div><span class=\"display-5 fw-bold counter\" data-target=\"7\">0</span><span class=\"text-muted\">年行业经验</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class=\"section\">
        <div class=\"container\">
          <div class=\"section-heading\">
            <span class=\"eyebrow\">Service Plans</span>
            <h2 class=\"h3\">合作方案</h2>
          </div>
          <div class=\"row g-4\">
            <article class=\"pricing-card reveal\">
              <div class=\"pricing-card__header\">
                <span class=\"eyebrow\">Lite</span>
                <h3>起步方案</h3>
                <p class=\"display-6 fw-bold\">¥9,999</p>
              </div>
              <ul>
                <li>单页落地页设计</li>
                <li>品牌视觉与排版系统</li>
                <li>基础动效与滚动体验</li>
              </ul>
              <a class=\"btn btn-outline-light\" href=\"#contact\">预约沟通</a>
            </article>
            <article class=\"pricing-card reveal featured\">
              <div class=\"pricing-card__header\">
                <span class=\"eyebrow\">Signature</span>
                <h3>旗舰方案</h3>
                <p class=\"display-6 fw-bold\">¥29,999</p>
              </div>
              <ul>
                <li>多页面信息架构</li>
                <li>定制插画与交互动效</li>
                <li>明/暗主题切换与高端展示</li>
              </ul>
              <a class=\"btn btn-primary\" href=\"#contact\">立即咨询</a>
            </article>
            <article class=\"pricing-card reveal\">
              <div class=\"pricing-card__header\">
                <span class=\"eyebrow\">Enterprise</span>
                <h3>企业方案</h3>
                <p class=\"display-6 fw-bold\">¥59,999+</p>
              </div>
              <ul>
                <li>全链路品牌与产品体验</li>
                <li>复杂信息架构与系统设计</li>
                <li>性能优化、SEO 与 A/B 测试</li>
              </ul>
              <a class=\"btn btn-outline-light\" href=\"#contact\">定制方案</a>
            </article>
          </div>
        </div>
      </section>

      <section id=\"contact\" class=\"section section-alt\">
        <div class=\"container\">
          <div class=\"row g-4\">
            <div class=\"col-md-7\">
              <h2 class=\"h4 mb-3\">项目洽谈</h2>
              <form class=\"contact-form reveal\">
                <div class=\"field-pair\"><label>姓名</label><input type=\"text\" placeholder=\"您的名字\" required></div>
                <div class=\"field-pair\"><label>邮箱</label><input type=\"email\" placeholder=\"name@example.com\" required></div>
                <div class=\"field-pair\"><label>预算范围</label><select><option>¥10k-30k</option><option>¥30k-60k</option><option>¥60k+</option></select></div>
                <div class=\"field-pair\"><label>项目简介</label><textarea rows=\"4\" placeholder=\"请描述您的项目目标和期望体验\" required></textarea></div>
                <button class=\"btn btn-primary\" type=\"submit\">发送需求</button>
              </form>
            </div>
            <div class=\"col-md-5\">
              <div class=\"info-card reveal\">
                <h3>联系方式</h3>
                <p class=\"text-muted\">hello@example.com</p>
                <p class=\"text-muted\">+86 021 8888 6666</p>
                <div class=\"d-flex gap-2 mt-3\">
                  <a class=\"btn btn-outline-light btn-sm\" href=\"#\">Behance</a>
                  <a class=\"btn btn-outline-light btn-sm\" href=\"#\">Dribbble</a>
                  <a class=\"btn btn-outline-light btn-sm\" href=\"#\">LinkedIn</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class=\"footer-minimal\">
      <div class=\"container\">
        <div class=\"footer-brand\">
          <span>{title}</span>
          <p>Crafted with taste & clarity</p>
        </div>
        <div class=\"footer-meta\">
          <span>© {title}</span>
          <a href=\"mailto:hello@example.com\">hello@example.com</a>
        </div>
      </div>
    </footer>
"""

    def hero_creative() -> str:
        return f"""
    <header id=\"home\" class=\"hero hero-creative text-center\" data-bg-topic=\"futuristic gradient landscape\">
      <div class=\"hero-creative__orbit\" aria-hidden=\"true\">
        <div class=\"orbit-layer layer-one\"></div>
        <div class=\"orbit-layer layer-two\"></div>
        <div class=\"orbit-layer layer-three\"></div>
      </div>
      <div class=\"container\">
        <span class=\"badge badge-soft mb-3\">Immersive Experience Lab</span>
        <h1 class=\"display-4\">{title}</h1>
        <p class=\"section-lead mx-auto\">打造沉浸式数字体验，融合艺术美学、交互叙事与工程实现，让品牌被看见、被记住。</p>
        <div class=\"d-inline-flex gap-3 mt-4\">
          <a href=\"#showcase\" class=\"btn btn-primary btn-lg\">探索世界观</a>
          <a href=\"#services\" class=\"btn btn-outline-light btn-lg\">查看能力矩阵</a>
        </div>
      </div>
    </header>
"""

    def body_creative() -> str:
        return f"""
    <main>
      <section class=\"section\" id=\"mission\">
        <div class=\"container\">
          <div class=\"row g-4 align-items-center\">
            <div class=\"col-md-6\">
              <div class=\"mission-sphere\" data-bg-topic=\"abstract 3d gradient sphere\"></div>
            </div>
            <div class=\"col-md-6\">
              <span class=\"eyebrow\">设计使命</span>
              <h2 class=\"h3\">我们为先锋品牌构建沉浸式体验</h2>
              <p class=\"text-muted\">融合创意叙事、交互设计与工程能力，让用户在触达的每个瞬间感知品牌世界观。</p>
              <ul class=\"list-check\">
                <li>跨终端视觉与交互统一</li>
                <li>沉浸式故事体验</li>
                <li>工程落地与持续运营</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section class=\"section section-sm\" id=\"services\">
        <div class=\"container\">
          <span class=\"eyebrow\">能力矩阵</span>
          <h2 class=\"h3\">体验设计全链条服务</h2>
          <div class=\"row g-4\">
            <article class=\"ability-card reveal\" data-topic=\"3d abstract gradient\">
              <h3>世界观构建</h3>
              <p class=\"text-muted\">打造品牌叙事逻辑与视觉体系，让用户沉浸在统一的世界观中。</p>
            </article>
            <article class=\"ability-card reveal\" data-topic=\"ux design futuristic\">
              <h3>交互叙事设计</h3>
              <p class=\"text-muted\">结合交互节奏与微动画语言，构建具有情绪记忆的体验线索。</p>
            </article>
            <article class=\"ability-card reveal\" data-topic=\"creative code art\">
              <h3>创意代码实现</h3>
              <p class=\"text-muted\">通过 WebGL / Three.js 等技术，将创意视觉无缝落地。</p>
            </article>
          </div>
        </div>
      </section>

      <section class=\"section section-alt\" id=\"showcase\">
        <div class=\"container\">
          <span class=\"eyebrow\">Signature Projects</span>
          <h2 class=\"h3\">沉浸式体验案例</h2>
          <div class=\"row g-4\">
            <article class=\"orbit-card reveal\">
              <div class=\"orbit-card__visual\" data-bg-topic=\"metaverse hero visual\"></div>
              <h3>MetaSpace</h3>
              <p class=\"text-muted\">Web3 沉浸式社区官网，结合粒子动态与实时数据可视化。</p>
            </article>
            <article class=\"orbit-card reveal\">
              <div class=\"orbit-card__visual\" data-bg-topic=\"futuristic product launch\"></div>
              <h3>Nova Launch</h3>
              <p class=\"text-muted\">科技新品发布会互动官网，通过滚动驱动叙事呈现产品亮点。</p>
            </article>
            <article class=\"orbit-card reveal\">
              <div class=\"orbit-card__visual\" data-bg-topic=\"immersive art installation\"></div>
              <h3>Immersive Gallery</h3>
              <p class=\"text-muted\">艺术展览数字门票体验，整合3D展位地图与在线预约。</p>
            </article>
          </div>
        </div>
      </section>

      <section class=\"section\" id=\"labs\">
        <div class=\"container\">
          <div class=\"row g-4\">
            <div class=\"col-lg-8\">
              <div class=\"labs-capsule reveal\">
                <h3>Experience Lab</h3>
                <p class=\"text-muted\">探索生成式设计、沉浸式叙事与可持续体验的边界，持续迭代最佳实践。</p>
                <ul class=\"tag-list\">
                  <li>Generative Design</li>
                  <li>Immersive Storytelling</li>
                  <li>Creative Code</li>
                  <li>Multisensory</li>
                </ul>
              </div>
            </div>
            <div class=\"col-lg-4\">
              <div class=\"lab-stats reveal\">
                <div>
                  <span class=\"display-5 fw-bold counter\" data-target=\"42\">0</span>
                  <span class=\"text-muted\">Lab Experiments</span>
                </div>
                <div>
                  <span class=\"display-5 fw-bold counter\" data-target=\"12\">0</span>
                  <span class=\"text-muted\">Awards</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class=\"section section-alt\" id=\"contact\">
        <div class=\"container\">
          <div class=\"contact-capsule reveal\" data-parallax=\"-0.25\">
            <h2 class=\"h3\">合作邀约</h2>
            <p class=\"text-muted\">请留下品牌简介或项目愿景，我们将在 24 小时内联系您。</p>
            <form class=\"row g-3\">
              <div class=\"col-md-6\"><label class=\"form-label\">姓名 / Name</label><input type=\"text\" class=\"form-control\" placeholder=\"Your Name\" required></div>
              <div class=\"col-md-6\"><label class=\"form-label\">邮箱 / Email</label><input type=\"email\" class=\"form-control\" placeholder=\"name@example.com\" required></div>
              <div class=\"col-12\"><label class=\"form-label\">项目愿景 / Project Vision</label><textarea class=\"form-control\" rows=\"3\" placeholder=\"请描述项目背景与期待体验\" required></textarea></div>
              <div class=\"col-12\"><label class=\"form-label\">预算范围 / Budget</label><select class=\"form-select\"><option>¥50k-100k</option><option>¥100k-200k</option><option>¥200k+</option></select></div>
              <div class=\"col-12\"><button class=\"btn btn-primary w-100\" type=\"submit\">发送愿景</button></div>
            </form>
          </div>
        </div>
      </section>
    </main>

    <footer class=\"footer-creative\">
      <div class=\"container\">
        <div class=\"footer-creative__meta\">
          <span>{title}</span>
          <p>Immersive Experience Lab</p>
        </div>
        <div class=\"footer-creative__links\">
          <a href=\"#services\">能力矩阵</a>
          <a href=\"#showcase\">作品宇宙</a>
          <a href=\"#contact\">成为伙伴</a>
        </div>
      </div>
    </footer>
"""

    layouts = {
        "ultra_modern": lambda: hero_ultra() + body_ultra(),
        "minimal_elegant": lambda: hero_minimal() + body_minimal(),
        "creative_gradient": lambda: hero_creative() + body_creative(),
    }

    if isinstance(sections, dict):
        ordered = []
        for key, value in sections.items():
            ordered.append(value if value.strip().startswith("<section") else f"<section>{value}</section>")
        default_content = "\n".join(ordered)
    elif isinstance(sections, list):
        normalized = []
        for block in sections:
            if isinstance(block, str):
                normalized.append(block if block.strip().startswith("<section") else f"<section>{block}</section>")
        default_content = "\n".join(normalized) if normalized else layouts.get(style_key, layouts["ultra_modern"])()
    else:
        default_content = layouts.get(style_key, layouts["ultra_modern"])()

    html_template = f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{title}</title>
    <link rel=\"stylesheet\" href=\"assets/css/style.css\">
    <!-- 兜底响应式图片，防止样式文件未生成时体验过差 -->
    <style>
        img {{ max-width: 100%; height: auto; display: block; }}
    </style>
</head>
<body>
    {content if content else default_content}

    <script src=\"assets/js/main.js\"></script>
</body>
</html>"""

    def is_full_document(s: str) -> bool:
        low = (s or "").lower()
        return "<html" in low or "<!doctype" in low

    def strip_nested_docs(s: str) -> str:
        low = s.lower()
        start = low.find("<!doctype html", 1)
        while start != -1:
            end = low.find("</html>", start)
            if end == -1:
                break
            s = s[:start] + s[end + len("</html>") :]
            low = s.lower()
            start = low.find("<!doctype html", 1)
        return s

    def ensure_assets_links(s: str) -> str:
        has_css = "assets/css/style.css" in s
        has_js = "assets/js/main.js" in s
        if "</head>" in s and not has_css:
            s = s.replace("</head>", "    <link rel=\"stylesheet\" href=\"assets/css/style.css\">\n</head>")
        if "</body>" in s and not has_js:
            s = s.replace("</body>", "    <script src=\"assets/js/main.js\"></script>\n</body>")
        return s

    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        out = html_template
        if content and is_full_document(content):
            doc = strip_nested_docs(content)
            doc = ensure_assets_links(doc)
            out = doc
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(out)
        return f"HTML文件创建成功: {file_path}"
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"创建HTML文件失败: {str(exc)}")


def create_menu_page(file_path: str, project_name: str | None = None) -> str:
    """创建餐厅/咖啡店的“菜单”页面"""
    brand = (project_name or "Coffee & Menu").strip()
    title = f"{brand} · 菜单 Menu"
    html_doc = f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <link rel=\"stylesheet\" href=\"assets/css/style.css\" />
</head>
<body>
  <header class=\"hero hero-ultra section text-center\" data-bg-topic=\"cozy coffee shop interior, warm light, depth of field\" id=\"home\">
    <div class=\"container hero-inner\">
      <span class=\"badge badge-soft mb-3\">菜单 MENU</span>
      <h1 class=\"display-5 mb-2\">{brand}</h1>
      <p class=\"section-lead mx-auto\">精品咖啡与精致甜点的完美搭配</p>
    </div>
  </header>

  <main>
    <nav class=\"section section-sm\" aria-label=\"菜单分类导航\">
      <div class=\"container\">
        <ul class=\"nav nav-pills justify-content-center gap-2\">
          <li class=\"nav-item\"><a class=\"nav-link active\" href=\"#coffee\">咖啡 Coffee</a></li>
          <li class=\"nav-item\"><a class=\"nav-link\" href=\"#tea\">茶饮 Tea</a></li>
          <li class=\"nav-item\"><a class=\"nav-link\" href=\"#desserts\">甜点 Desserts</a></li>
          <li class=\"nav-item\"><a class=\"nav-link\" href=\"#signature\">招牌 Specials</a></li>
        </ul>
      </div>
    </nav>

    <section class=\"section\" id=\"coffee\">
      <div class=\"container\">
        <h2 class=\"h3 text-center mb-4\">手工咖啡 Coffee</h2>
        <div class=\"row g-4\">
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"latte art, coffee cup, warm light\" alt=\"精品拿铁\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">招牌拿铁</h3>
              <span class=\"price\">¥ 36</span>
            </div>
            <p class=\"text-muted mt-2\">醇厚意式浓缩搭配自制牛奶泡沫，入口绵密。</p>
          </article>
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"pour over coffee, minimal setup\" alt=\"手冲咖啡\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">单品手冲</h3>
              <span class=\"price\">¥ 42</span>
            </div>
            <p class=\"text-muted mt-2\">精选小农庄豆种，手工萃取层次丰富的水果酸甜。</p>
          </article>
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"cold brew coffee glass\" alt=\"冷萃咖啡\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">冷萃特调</h3>
              <span class=\"price\">¥ 38</span>
            </div>
            <p class=\"text-muted mt-2\">16 小时低温萃取，风味清爽，尾韵甘甜。</p>
          </article>
        </div>
      </div>
    </section>

    <section class=\"section section-alt\" id=\"tea\">
      <div class=\"container\">
        <h2 class=\"h3 text-center mb-4\">臻选茶饮 Tea</h2>
        <div class=\"row g-4\">
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"matcha latte with latte art\" alt=\"抹茶拿铁\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">宇治抹茶拿铁</h3>
              <span class=\"price\">¥ 38</span>
            </div>
            <p class=\"text-muted mt-2\">选用一番摘宇治抹茶，奶香与茶香层层绽放。</p>
          </article>
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"fruit tea highball glass\" alt=\"鲜果茶\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">初夏鲜果茶</h3>
              <span class=\"price\">¥ 34</span>
            </div>
            <p class=\"text-muted mt-2\">四季鲜果冷泡乌龙，酸甜清爽，层次丰富。</p>
          </article>
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"earl grey tea setup warm light\" alt=\"伯爵茶\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">伯爵奶香</h3>
              <span class=\"price\">¥ 32</span>
            </div>
            <p class=\"text-muted mt-2\">经典佛手柑香气，搭配丝滑奶沫，馥郁优雅。</p>
          </article>
        </div>
      </div>
    </section>

    <section class=\"section\" id=\"desserts\">
      <div class=\"container\">
        <h2 class=\"h3 text-center mb-4\">法式甜点 Desserts</h2>
        <div class=\"row g-4\">
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"tiramisu close up\" alt=\"提拉米苏\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">经典提拉米苏</h3>
              <span class=\"price\">¥ 42</span>
            </div>
            <p class=\"text-muted mt-2\">马斯卡彭与手指饼干的完美比例，口感细腻柔滑。</p>
          </article>
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"lemon tart minimal\" alt=\"柠檬塔\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">柠檬奶油塔</h3>
              <span class=\"price\">¥ 38</span>
            </div>
            <p class=\"text-muted mt-2\">酸甜平衡的柠檬凝乳，搭配酥脆塔皮。</p>
          </article>
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"croissant bakery setup\" alt=\"可颂\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">黄油可颂</h3>
              <span class=\"price\">¥ 28</span>
            </div>
            <p class=\"text-muted mt-2\">百层黄油折叠，外酥内软，香气浓郁。</p>
          </article>
        </div>
      </div>
    </section>

    <section class=\"section section-alt\" id=\"signature\">
      <div class=\"container\">
        <h2 class=\"h3 text-center mb-4\">招牌组合 Specials</h2>
        <div class=\"row g-4\">
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"coffee beans with packaging\" alt=\"咖啡礼盒\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">精品豆礼盒</h3>
              <span class=\"price\">¥ 158</span>
            </div>
            <p class=\"text-muted mt-2\">季节限定咖啡豆搭配手冲器具，馈赠自用皆宜。</p>
          </article>
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"coffee and dessert pairing\" alt=\"咖啡甜点双人套餐\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">双人下午茶</h3>
              <span class=\"price\">¥ 128</span>
            </div>
            <p class=\"text-muted mt-2\">两杯咖啡搭配两款甜点，分享美味时光。</p>
          </article>
          <article class=\"menu-card reveal col-md-4\">
            <img data-topic=\"coffee beans roasting\" alt=\"烘焙体验\" class=\"img-fluid rounded shadow-sm\">
            <div class=\"d-flex justify-content-between align-items-center mt-3\">
              <h3 class=\"h5 mb-0\">烘焙体验课</h3>
              <span class=\"price\">¥ 198</span>
            </div>
            <p class=\"text-muted mt-2\">手把手体验烘焙流程，带走专属烘焙豆。</p>
          </article>
        </div>
      </div>
    </section>
  </main>

  <footer class=\"footer-minimal\"><div class=\"container\"><div class=\"footer-brand\"><span>{brand}</span><p>See you in our cafe</p></div><div class=\"footer-meta\"><span>© {brand}</span><a href=\"mailto:hello@example.com\">hello@example.com</a></div></div></footer>
  <script src=\"assets/js/main.js\"></script>
</body>
</html>"""
    return create_html_file(file_path=file_path, title=title, content=html_doc, style="minimal_elegant")


THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "transport": ("公交", "巴士", "bus", "交通", "出行", "地铁", "shuttle", "线路", "换乘", "班车"),
    "cafe": ("咖啡", "coffee", "烘焙", "甜点", "饮品", "餐饮", "latte", "menu", "brew"),
}

THEME_ALIASES: dict[str, str] = {
    "public-transport": "transport",
    "transportation": "transport",
    "mobility": "transport",
    "bus": "transport",
    "shuttle": "transport",
    "restaurant": "cafe",
    "food": "cafe",
    "coffee": "cafe",
    "cafe": "cafe",
}

THEME_LIBRARY: dict[str, dict] = {
    "transport": {
        "hero": {
            "tagline": "{brand}",
            "title": "连接亦城出行的每一站",
            "lead": "我们聚合亦城科技中心周边公交线路、站点与换乘数据，提供实时、准确的出行指引。",
            "bg_topic": "smart city bus transit hub at dusk",
            "gallery_topics": [
                "modern city bus stop at golden hour",
                "commuters boarding bus aerial view",
                "urban transit data dashboard in use"
            ],
        },
        "vision": {
            "eyebrow": "我们的使命",
            "title": "让城市出行信息更透明",
            "description": "围绕公交线路的实时数据、站点体验与周边服务，我们构建面向园区、企业与居民的智慧出行服务。",
            "bullets": [
                "多源数据实时汇聚，分钟级更新线路与站点状态",
                "按站点、线路和企业场景提供可视化决策与报表",
                "与运营方协同优化站点设施与换乘体验"
            ],
            "media_topic": "transportation analytics teamwork",
        },
        "metrics": [
            {"value": "180+", "label": "覆盖站点"},
            {"value": "65", "label": "整合线路"},
            {"value": "5min", "label": "数据刷新"},
            {"value": "25+", "label": "合作园区"},
        ],
        "team": [
            {
                "name": "张雪",
                "role": "数据运营负责人",
                "desc": "负责公交线路数据采集、质量监测与指标体系搭建。",
                "topic": "female data analyst working on city transport dashboard",
            },
            {
                "name": "李晨",
                "role": "城市交通研究员",
                "desc": "分析亦城园区出行需求，与运营方共创站点优化方案。",
                "topic": "urban mobility planner reviewing maps",
            },
            {
                "name": "王可",
                "role": "产品体验负责人",
                "desc": "设计出行助手、站点详情与班车服务的用户体验。",
                "topic": "product designer showcasing transit app interface",
            },
            {
                "name": "周阳",
                "role": "技术平台架构师",
                "desc": "构建数据平台、实时监控与多端 API 服务能力。",
                "topic": "software architect in control room",
            },
        ],
        "services": [
            {
                "title": "线路数据中心",
                "desc": "整合亦城 5 公里范围公交线路、站点与换乘关系。",
                "bullets": [
                    "实时线路状态与班次频率监测",
                    "站点配套、步行换乘与周边服务标签",
                    "异常事件、绕行信息即时推送",
                ],
                "topic": "city bus map interface on tablet",
            },
            {
                "title": "智能出行助手",
                "desc": "让园区员工与居民快速获取最优出行方案。",
                "bullets": [
                    "早晚高峰拥堵预测与出发提醒",
                    "收藏常用站点与线路，跨端同步",
                    "个性化换乘方案与步行时间估算",
                ],
                "topic": "commuter using mobile transit app",
            },
            {
                "title": "企业班车与定制化服务",
                "desc": "为园区企业提供接驳方案与数据分析。",
                "bullets": [
                    "企业定制班车线路规划与动态调整",
                    "乘车签到、满载率与满意度数据仪表板",
                    "与物业、运营方联动的服务回路",
                ],
                "topic": "corporate shuttle planning meeting",
            },
        ],
        "partners": {
            "eyebrow": "合作生态",
            "title": "携手打造智慧出行网络",
            "items": [
                "BDA Transit",
                "Metro Link",
                "SmartCity Lab",
                "亦庄产业联盟",
                "LYF Shuttle",
                "Urban Data Lab",
            ],
        },
        "culture": {
            "values_title": "我们的价值观",
            "values": [
                "以数据驱动公共交通体验升级",
                "保持透明、开放的跨部门协作",
                "以用户出行感受为第一优先",
            ],
            "method_title": "我们的工作方法",
            "methods": [
                "日常线路巡检与数据校验机制",
                "园区走访与乘客调研同步推进",
                "滚动迭代的产品反馈与发布节奏",
            ],
        },
        "cta": {
            "title": "想要定制园区或企业班车方案？",
            "lead": "无论是新增线路、优化乘车体验还是数据接口合作，欢迎与我们联系。",
            "button_text": "提出合作需求",
            "button_href": "#contact",
        },
        "contact": {
            "address": "北京市经济技术开发区 亦城科技中心",
            "hours": "工作日 09:00 - 18:00",
            "email": "contact@yicheng-bus.com",
            "phone": "+86 010 8888 2025",
            "social": [
                {"label": "小程序", "href": "#"},
                {"label": "企业微信", "href": "#"},
                {"label": "公众号", "href": "#"},
            ],
            "map_topic": "smart bus stop map illustration",
        },
        "footer_subtitle": "让出行更简单、更可信。",
    },
    "cafe": {
        "hero": {
            "tagline": "{brand}",
            "title": "用一杯咖啡连接亦城人的灵感时刻",
            "lead": "我们扎根亦城科技中心，每天精选烘焙，为周边社区带来香气、灵感与交谈。",
            "bg_topic": "artisan coffee shop interior morning light",
            "gallery_topics": [
                "fresh roasted coffee beans in roastery",
                "barista pouring latte art close up",
                "coffee shop community event evening",
            ],
        },
        "vision": {
            "eyebrow": "品牌愿景",
            "title": "把精品咖啡带到工作与生活的每一个瞬间",
            "description": "我们对风味的研究、空间体验的营造与社区活动的组织，共同构成亦城人的咖啡日常。",
            "bullets": [
                "坚持 48 小时内烘焙，锁住豆种原产地风味",
                "把咖啡学院课程开放给每一位好奇者",
                "与园区社区联动，打造共享的第三空间",
            ],
            "media_topic": "coffee cupping workshop enthusiasts",
        },
        "metrics": [
            {"value": "12年", "label": "品牌历程"},
            {"value": "18", "label": "手冲配方"},
            {"value": "120+", "label": "日均服务顾客"},
            {"value": "5", "label": "联营城市"},
        ],
        "team": [
            {
                "name": "林暮",
                "role": "首席烘焙师",
                "desc": "负责豆种甄选、烘焙曲线设计与杯测标准。",
                "topic": "coffee roaster inspecting beans",
            },
            {
                "name": "宋以",
                "role": "体验主理人",
                "desc": "打造门店陈列、音乐与香气的感官动线。",
                "topic": "coffee shop manager arranging space",
            },
            {
                "name": "陈路",
                "role": "咖啡学院教练",
                "desc": "带领咖啡入门、拉花与杯测课程，培养社区咖啡师。",
                "topic": "barista teaching latte art class",
            },
            {
                "name": "高礼",
                "role": "营运经理",
                "desc": "统筹供应链、会员体系与联名合作。",
                "topic": "operations manager reviewing cafe dashboard",
            },
        ],
        "services": [
            {
                "title": "精品咖啡研发实验室",
                "desc": "持续探索单品手冲、拼配意式与冷萃新品。",
                "bullets": [
                    "全程记录豆种、烘焙与萃取参数",
                    "与产区合作，共建季节性风味",
                    "发布杯测报告与风味指南",
                ],
                "topic": "coffee lab with tasting notes",
            },
            {
                "title": "空间体验与活动策划",
                "desc": "为园区与社区打造可聚会、可办公的第三空间。",
                "bullets": [
                    "定期举办音乐、小型展览与分享会",
                    "提供会客、路演与培训定制布置",
                    "与本地品牌共创限定周边",
                ],
                "topic": "coffee shop community event",
            },
            {
                "title": "企业咖啡解决方案",
                "desc": "为企业提供驻场咖啡吧、咖啡培训与福利礼盒。",
                "bullets": [
                    "企业驻点咖啡师与移动咖啡车",
                    "员工咖啡入门与精品品鉴课堂",
                    "节日礼盒与专属烘焙纪念豆",
                ],
                "topic": "corporate coffee catering setup",
            },
        ],
        "partners": {
            "eyebrow": "合作伙伴",
            "title": "与我们一起端出好咖啡",
            "items": [
                "Origin Farm",
                "Brew Lab",
                "Slow Bar",
                "亦城社区联盟",
                "Creative Hub",
                "City Roast",
            ],
        },
        "culture": {
            "values_title": "我们的坚持",
            "values": [
                "尊重咖啡产区与农作伙伴",
                "把风味讲给每一位顾客听",
                "让咖啡空间成为社区链接",
            ],
            "method_title": "我们的方式",
            "methods": [
                "每日开放杯测，邀请顾客参与评测",
                "记录每一批烘焙数据并透明公示",
                "与社区联合发起公益与环保活动",
            ],
        },
        "cta": {
            "title": "预约烘焙课程或企业咖啡方案",
            "lead": "欢迎企业福利合作、烘焙课堂与活动场地预约。",
            "button_text": "联系咖啡顾问",
            "button_href": "#contact",
        },
        "contact": {
            "address": "北京市经济技术开发区 荣华南路 咖啡共享空间",
            "hours": "每日 08:00 - 21:00",
            "email": "hello@yicheng-coffee.com",
            "phone": "+86 010 6688 2020",
            "social": [
                {"label": "微博", "href": "#"},
                {"label": "小红书", "href": "#"},
                {"label": "Instagram", "href": "#"},
            ],
            "map_topic": "coffee shop map illustration",
        },
        "footer_subtitle": "好咖啡与好故事在此相遇。",
    },
    "default": {
        "hero": {
            "tagline": "{brand}",
            "title": "与 {brand} 一起创造值得信赖的体验",
            "lead": "我们帮助团队把愿景落地为可持续增长的数字与空间体验。",
            "bg_topic": "modern creative studio interior",
            "gallery_topics": [
                "design team collaborating on strategy",
                "customer journey mapping workshop",
                "developers shipping product features",
            ],
        },
        "vision": {
            "eyebrow": "愿景",
            "title": "以策略、体验与技术驱动业务成长",
            "description": "我们聚焦品牌叙事、体验设计与工程落地，帮助组织在复杂环境中保持增长力。",
            "bullets": [
                "深入理解用户旅程与业务需求",
                "以设计系统保障体验一致性",
                "以数据驱动快速迭代与优化",
            ],
            "media_topic": "team reviewing product roadmaps",
        },
        "metrics": [
            {"value": "120+", "label": "完成项目"},
            {"value": "50+", "label": "服务行业"},
            {"value": "98%", "label": "客户满意度"},
            {"value": "7年", "label": "交付经验"},
        ],
        "team": [
            {
                "name": "Evelyn Zhang",
                "role": "体验策略合伙人",
                "desc": "擅长品牌叙事与体验创新，帮助客户构建可持续的体验体系。",
                "topic": "female strategist leading workshop",
            },
            {
                "name": "Leo Chen",
                "role": "产品设计总监",
                "desc": "负责设计系统、跨平台体验与可视化呈现。",
                "topic": "ux designer presenting interface",
            },
            {
                "name": "Mia Wu",
                "role": "产品策略负责人",
                "desc": "搭建需求洞察与数据分析机制，确保产品迭代与业务目标一致。",
                "topic": "product manager analyzing data",
            },
            {
                "name": "Jason Li",
                "role": "技术负责人",
                "desc": "带领工程团队以高质量代码与自动化流程保障交付。",
                "topic": "software lead reviewing code",
            },
        ],
        "services": [
            {
                "title": "策略洞察",
                "desc": "帮助品牌厘清定位、价值主张与用户旅程。",
                "bullets": [
                    "市场与用户调研",
                    "品牌与体验定位",
                    "增长机会识别",
                ],
                "topic": "strategy workshop with sticky notes",
            },
            {
                "title": "体验设计",
                "desc": "从概念到落地，打造兼具美感与可用性的体验。",
                "bullets": [
                    "跨平台界面设计",
                    "设计系统与组件库",
                    "可用性测试与验证",
                ],
                "topic": "designers collaborating on interface",
            },
            {
                "title": "技术工程",
                "desc": "以现代工程实践保障体验的稳定与性能。",
                "bullets": [
                    "前端工程与性能优化",
                    "自动化测试与交付",
                    "数据驱动的运维与监控",
                ],
                "topic": "developers deploying product",
            },
        ],
        "partners": {
            "eyebrow": "合作伙伴",
            "title": "与不同规模的团队携手",
            "items": [
                "ALPHA",
                "NOVA",
                "FRAME",
                "UNITY",
                "ORBIT",
                "SPECTRA",
            ],
        },
        "culture": {
            "values_title": "我们的价值观",
            "values": [
                "以用户与业务结果为最终衡量",
                "保持诚实与透明的沟通",
                "持续学习并拥抱新技术",
            ],
            "method_title": "我们的工作方式",
            "methods": [
                "跨学科团队共创",
                "以数据与实验驱动决策",
                "短周期迭代与可持续交付",
            ],
        },
        "cta": {
            "title": "准备好与我们合作了吗？",
            "lead": "告诉我们你的挑战与目标，我们会为你组建合适的项目团队。",
            "button_text": "与我们交流",
            "button_href": "#contact",
        },
        "contact": {
            "address": "上海市徐汇区 漕溪北路 333 号",
            "hours": "工作日 10:00 - 19:00",
            "email": "hello@example.com",
            "phone": "+86 021 8888 6666",
            "social": [
                {"label": "LinkedIn", "href": "#"},
                {"label": "Behance", "href": "#"},
                {"label": "WeChat", "href": "#"},
            ],
            "map_topic": "city map illustration",
        },
        "footer_subtitle": "以体验驱动业务增长。",
    },
}


def _guess_theme(brand: str, ctx: dict, nav_items: list[dict], site_hint: str) -> str:
    candidates = []
    if site_hint:
        candidates.append(site_hint)
    for key in ("theme", "site_type", "project_type"):
        value = ctx.get(key)
        if isinstance(value, str):
            candidates.append(value.lower())

    for candidate in candidates:
        alias = THEME_ALIASES.get(candidate, candidate)
        if alias in THEME_LIBRARY:
            return alias

    text_parts = [brand]
    for key in ("project_description", "project_summary", "description", "mission", "keywords"):
        value = ctx.get(key)
        if isinstance(value, str):
            text_parts.append(value)
    for item in nav_items:
        text_parts.append(str(item.get("name", "")))
        text_parts.append(str(item.get("href", "")))

    text = " ".join(text_parts).lower()
    for theme_key, keywords in THEME_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return theme_key

    return "default"


def create_about_page(
    file_path: str,
    project_name: str | None = None,
    context: dict | None = None,
    theme: str | None = None,
) -> str:
    """创建行业感知的“关于我们”页面"""

    brand = (project_name or "Modern Brand").strip()
    ctx = context.copy() if isinstance(context, dict) else {}
    nav_items_raw = ctx.get("nav_items") if isinstance(ctx.get("nav_items"), list) else []
    nav_items: list[dict] = [item for item in nav_items_raw if isinstance(item, dict)]

    site_hint = (theme or ctx.get("theme") or ctx.get("site_type") or "").lower()
    theme_key = _guess_theme(brand, ctx, nav_items, site_hint)
    theme_key = THEME_ALIASES.get(theme_key, theme_key)
    config = THEME_LIBRARY.get(theme_key, THEME_LIBRARY["default"])

    city = ctx.get("city") or ctx.get("region") or ctx.get("area") or ""

    def fmt(value: str | None) -> str:
        if not value:
            return ""
        replacements = {
            "brand": brand,
            "project": brand,
            "city": city or brand,
            "area": city,
        }
        try:
            return value.format(**replacements)
        except Exception:
            return value

    def escape(text: str | None) -> str:
        return html.escape(text or "")

    hero_cfg = config.get("hero", {})
    hero_tagline = fmt(hero_cfg.get("tagline"))
    hero_title = fmt(hero_cfg.get("title")) or f"{brand} · 关于我们"
    hero_lead = fmt(hero_cfg.get("lead"))
    hero_bg_topic = hero_cfg.get("bg_topic", "modern gradient background")
    hero_placeholder = (
        f"https://placehold.co/1200x800/EEE/31343C?text="
        f"{urllib.parse.quote_plus(hero_bg_topic[:40])}"
    )
    hero_remote = (
        f"https://image.pollinations.ai/prompt/{urllib.parse.quote_plus(hero_bg_topic)}"
        "?width=1200&height=800"
    )
    hero_style = (
        f"background-image:url('{hero_placeholder}');"
        "background-size:cover;background-position:center;background-repeat:no-repeat;"
    )
    gallery_topics = hero_cfg.get("gallery_topics", [])

    gallery_html = ""
    for idx, topic in enumerate(gallery_topics):
        card_class = "gallery-card tall" if idx == len(gallery_topics) - 1 and len(gallery_topics) > 2 else "gallery-card"
        gallery_html += (
            f"        <figure class=\"{card_class}\" data-topic=\"{escape(topic)}\"></figure>\n"
        )

    hero_tagline_html = (
        f"        <span class=\"tagline\">{escape(hero_tagline)}</span>\n" if hero_tagline else ""
    )

    hero_html = f"""
  <header class=\"hero hero-minimal section\" data-bg-topic=\"{escape(hero_bg_topic)}\" id=\"home\" style=\"{hero_style}\" data-ai-image=\"bg\" data-remote-bg=\"{hero_remote}\">
    <div class=\"container hero-inner minimal-grid\">
      <div class=\"hero-minimal__content\">
{hero_tagline_html}        <h1 class=\"display-4\">{escape(hero_title)}</h1>
        <p class=\"section-lead\">{escape(hero_lead)}</p>
      </div>
      <div class=\"hero-minimal__gallery\">\n{gallery_html}      </div>
    </div>
  </header>
"""

    metrics_cfg = config.get("metrics", [])
    metrics_html = ""
    if metrics_cfg:
        metric_cards = []
        for metric in metrics_cfg:
            metric_cards.append(
                "        <div class=\"col-md-3\">\n"
                "          <div class=\"feature-card glass p-4 reveal\" data-tilt>\n"
                f"            <div class=\"display-6 fw-bold\">{escape(fmt(metric.get('value')))}</div>\n"
                f"            <div class=\"text-muted mt-2\">{escape(fmt(metric.get('label')))}</div>\n"
                "          </div>\n        </div>\n"
            )
        metrics_html = (
            "  <section class=\"section section-sm\">\n"
            "    <div class=\"container\">\n"
            "      <div class=\"row g-4 text-center\">\n"
            + "".join(metric_cards)
            + "      </div>\n    </div>\n  </section>\n"
        )

    vision_cfg = config.get("vision", {})
    vision_bullets = vision_cfg.get("bullets", [])
    vision_list_html = "".join(
        f"                <li>{escape(fmt(item))}</li>\n" for item in vision_bullets if item
    )
    vision_section_html = ""
    if vision_cfg:
        vision_section_html = f"""
  <section class=\"section\" id=\"vision\">
    <div class=\"container\">
      <div class=\"row g-5 align-items-center\">
        <div class=\"col-lg-6\">
          <div class=\"vision-capsule reveal\">
            <span class=\"eyebrow\">{escape(fmt(vision_cfg.get('eyebrow')) or '愿景')}</span>
            <h2 class=\"h3\">{escape(fmt(vision_cfg.get('title')) or '与团队共同迈向下一程')}</h2>
            <p class=\"text-muted\">{escape(fmt(vision_cfg.get('description')))}</p>
            <ul class=\"list-check\">\n{vision_list_html}            </ul>
          </div>
        </div>
        <div class=\"col-lg-6\">
          <div class=\"vision-media reveal\" data-bg-topic=\"{escape(vision_cfg.get('media_topic', 'team collaboration workshop'))}\"></div>
        </div>
      </div>
    </div>
  </section>
"""

    team_cfg = config.get("team", [])
    team_cards_html = ""
    for member in team_cfg:
        team_cards_html += f"""
          <article class=\"team-card reveal col-md-3\">
            <img data-topic=\"{escape(member.get('topic', 'team portrait'))}\" alt=\"{escape(fmt(member.get('role')) or '团队成员')}\" class=\"img-fluid rounded shadow-sm\">
            <h3 class=\"h6 mt-3\">{escape(fmt(member.get('name')) or 'Team Member')}</h3>
            <p class=\"text-muted\">{escape(fmt(member.get('desc')))}</p>
          </article>\n"""
    team_section_html = ""
    if team_cards_html:
        team_section_html = (
            "  <section class=\"section section-alt\" id=\"team\">\n"
            "    <div class=\"container\">\n"
            "      <span class=\"eyebrow\">团队</span>\n"
            "      <h2 class=\"h3\">核心团队</h2>\n"
            "      <div class=\"row g-4\">\n"
            + team_cards_html
            + "      </div>\n    </div>\n  </section>\n"
        )

    services_cfg = config.get("services", [])
    service_cards_html = ""
    for service in services_cfg:
        bullets = service.get("bullets", [])
        bullet_html = "".join(
            f"              <li>{escape(fmt(bullet))}</li>\n" for bullet in bullets if bullet
        )
        service_cards_html += f"""
          <article class=\"service-card reveal col-md-4\">
            <h3>{escape(fmt(service.get('title')))}</h3>
            <p class=\"text-muted\">{escape(fmt(service.get('desc')))}</p>
            <ul>\n{bullet_html}            </ul>
          </article>\n"""
    services_section_html = ""
    if service_cards_html:
        services_section_html = (
            "  <section class=\"section\" id=\"services\">\n"
            "    <div class=\"container\">\n"
            "      <span class=\"eyebrow\">我们提供</span>\n"
            "      <h2 class=\"h3\">服务与能力</h2>\n"
            "      <div class=\"row g-4\">\n"
            + service_cards_html
            + "      </div>\n    </div>\n  </section>\n"
        )

    partners_cfg = config.get("partners", {})
    partner_items = partners_cfg.get("items", [])
    partners_html = ""
    if partner_items:
        partner_spans = "".join(f"          <span>{escape(fmt(item))}</span>\n" for item in partner_items)
        partners_html = f"""
  <section class=\"section section-alt\" id=\"partners\">
    <div class=\"container\">
      <span class=\"eyebrow\">{escape(fmt(partners_cfg.get('eyebrow')) or '合作伙伴')}</span>
      <h2 class=\"h3\">{escape(fmt(partners_cfg.get('title')) or '与我们同行的伙伴')}</h2>
      <div class=\"partner-grid\">\n{partner_spans}      </div>
    </div>
  </section>
"""

    culture_cfg = config.get("culture", {})
    values_html = "".join(
        f"                <li>{escape(fmt(item))}</li>\n" for item in culture_cfg.get("values", []) if item
    )
    methods_html = "".join(
        f"                <li>{escape(fmt(item))}</li>\n" for item in culture_cfg.get("methods", []) if item
    )
    culture_section_html = ""
    if values_html or methods_html:
        culture_section_html = f"""
  <section class=\"section\" id=\"culture\">
    <div class=\"container\">
      <div class=\"row g-4\">
        <div class=\"col-md-6\">
          <div class=\"culture-card reveal\">
            <h3>{escape(fmt(culture_cfg.get('values_title')) or '我们的价值观')}</h3>
            <ul>\n{values_html}            </ul>
          </div>
        </div>
        <div class=\"col-md-6\">
          <div class=\"culture-card reveal\">
            <h3>{escape(fmt(culture_cfg.get('method_title')) or '我们的工作方式')}</h3>
            <ul>\n{methods_html}            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>
"""

    cta_cfg = config.get("cta", {})
    cta_html = f"""
  <section class=\"section\" id=\"cta\">
    <div class=\"container\">
      <div class=\"cta-card reveal\" data-parallax=\"-0.25\">
        <h2 class=\"h3\">{escape(fmt(cta_cfg.get('title')) or '期待与你合作')}</h2>
        <p class=\"text-muted\">{escape(fmt(cta_cfg.get('lead')))}</p>
        <a class=\"btn btn-primary btn-lg\" href=\"{escape(cta_cfg.get('button_href') or '#contact')}\">{escape(fmt(cta_cfg.get('button_text')) or '联系团队')}</a>
      </div>
    </div>
  </section>
"""

    contact_cfg = config.get("contact", {}).copy()
    contact_override = ctx.get("contact") if isinstance(ctx.get("contact"), dict) else {}
    contact_cfg.update(contact_override)
    for key in ("address", "email", "phone", "hours"):
        override_value = ctx.get(key)
        if isinstance(override_value, str):
            contact_cfg[key] = override_value
    contact_cfg.setdefault("email", "hello@example.com")
    contact_cfg.setdefault("phone", "+86 021 8888 6666")
    contact_cfg.setdefault("address", f"{city or '中国'}")
    contact_cfg.setdefault("hours", "工作日 09:00 - 18:00")
    contact_cfg.setdefault("social", config.get("contact", {}).get("social", []))
    contact_cfg.setdefault("map_topic", "city map illustration")

    social_html = "".join(
        f"                <a class=\"btn btn-outline-light btn-sm\" href=\"{escape(fmt(s.get('href')) or '#')}\">{escape(fmt(s.get('label')))}</a>\n"
        for s in contact_cfg.get("social", [])
        if isinstance(s, dict)
    )

    contact_section_html = f"""
  <section class=\"section section-alt\" id=\"contact\">
    <div class=\"container\">
      <div class=\"row g-4\">
        <div class=\"col-md-6\">
          <div class=\"contact-card reveal\">
            <h3>{escape(fmt(contact_cfg.get('title')) or '到访我们')}</h3>
            <p class=\"text-muted\">{escape(fmt(contact_cfg.get('address')))}</p>
            <p class=\"text-muted\">{escape(fmt(contact_cfg.get('hours')))}</p>
            <div class=\"contact-map\" data-bg-topic=\"{escape(contact_cfg.get('map_topic'))}\"></div>
          </div>
        </div>
        <div class=\"col-md-6\">
          <div class=\"contact-card reveal\">
            <h3>{escape(fmt(contact_cfg.get('subtitle')) or '联系我们')}</h3>
            <p class=\"text-muted\">{escape(fmt(contact_cfg.get('email')))}</p>
            <p class=\"text-muted\">{escape(fmt(contact_cfg.get('phone')))}</p>
            <div class=\"d-flex flex-wrap gap-2 mt-3\">
{social_html}            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
"""

    footer_subtitle = escape(fmt(config.get("footer_subtitle")) or "与我们一起创造更多价值。")

    sections_html = "".join(
        part
        for part in (
            metrics_html,
            vision_section_html,
            team_section_html,
            services_section_html,
            partners_html,
            culture_section_html,
        )
        if part
    )

    title = f"{brand} · 关于我们"
    html_doc = f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{escape(title)}</title>
  <link rel=\"stylesheet\" href=\"assets/css/style.css\" />
</head>
<body>
{hero_html}  <main>
{sections_html}{cta_html}{contact_section_html}  </main>

  <footer class=\"footer-minimal\">
    <div class=\"container\">
      <div class=\"footer-brand\">
        <span>{escape(brand)}</span>
        <p>{footer_subtitle}</p>
      </div>
      <div class=\"footer-meta\">
        <span>© {escape(brand)}</span>
        <a href=\"mailto:{escape(fmt(contact_cfg.get('email')))}\">{escape(fmt(contact_cfg.get('email')))}</a>
      </div>
    </div>
  </footer>
  <script src=\"assets/js/main.js\"></script>
</body>
</html>"""

    return create_html_file(
        file_path=file_path,
        title=title,
        content=html_doc,
        style="minimal_elegant",
    )


def create_contact_page(file_path: str, project_name: str | None = None) -> str:
    """创建“联系我们”页面"""
    brand = (project_name or "Modern Brand").strip()
    title = f"{brand} · 联系我们"
    html_doc = f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <link rel=\"stylesheet\" href=\"assets/css/style.css\" />
</head>
<body>
  <header class=\"hero hero-ultra section text-center\" data-bg-topic=\"customer support modern office\" id=\"home\">
    <div class=\"container hero-inner\">
      <span class=\"badge badge-soft mb-3\">Contact</span>
      <h1 class=\"display-5 mb-2\">与 {brand} 取得联系</h1>
      <p class=\"section-lead mx-auto\">我们在这里倾听需求、提供支持，帮助你启动或升级项目。</p>
    </div>
  </header>

  <main>
    <section class=\"section\">
      <div class=\"container\">
        <div class=\"row g-4\">
          <div class=\"col-md-5\">
            <div class=\"contact-info-card reveal\">
              <h2 class=\"h4 mb-3\">联系渠道</h2>
              <ul class=\"list-unstyled text-muted\">
                <li class=\"mb-2\"><strong>邮箱</strong>：hello@example.com</li>
                <li class=\"mb-2\"><strong>商务合作</strong>：business@example.com</li>
                <li class=\"mb-2\"><strong>电话</strong>：+86 021 8888 6666</li>
                <li class=\"mb-2\"><strong>地址</strong>：上海市徐汇区 漕溪北路 333 号 8F</li>
              </ul>
              <div class=\"d-flex gap-2 mt-3\">
                <a class=\"btn btn-outline-light btn-sm\" href=\"#\">LinkedIn</a>
                <a class=\"btn btn-outline-light btn-sm\" href=\"#\">Behance</a>
                <a class=\"btn btn-outline-light btn-sm\" href=\"#\">WeChat</a>
              </div>
            </div>
          </div>
          <div class=\"col-md-7\">
            <h2 class=\"h4 mb-3\">发送消息</h2>
            <form class=\"contact-form reveal\">
              <div class=\"field-pair\"><label>姓名</label><input type=\"text\" placeholder=\"您的名字\" required></div>
              <div class=\"field-pair\"><label>邮箱</label><input type=\"email\" placeholder=\"name@example.com\" required></div>
              <div class=\"field-pair\"><label>电话</label><input type=\"tel\" placeholder=\"您的联系电话\"></div>
              <div class=\"field-pair\"><label>留言</label><textarea rows=\"4\" placeholder=\"请描述您的需求或预约时间\" required></textarea></div>
              <button class=\"btn btn-primary\" type=\"submit\">提交</button>
            </form>
          </div>
        </div>
      </div>
    </section>

    <section class=\"section section-alt\">
      <div class=\"container\">
        <div class=\"row g-4\">
          <div class=\"col-md-4\">
            <div class=\"feature-card glass p-3 reveal\">
              <strong>营业时间</strong>
              <ul class=\"text-muted mb-0\" style=\"list-style:none; padding-left:0;\">
                <li>周一至周五：09:30 - 18:30</li>
                <li>周六（预约制）：10:00 - 16:00</li>
              </ul>
            </div>
          </div>
          <div class=\"col-md-4\">
            <div class=\"feature-card glass p-3 reveal\">
              <strong>项目合作</strong>
              <p class=\"text-muted mb-1\">欢迎邮件简要介绍品牌现状、目标和时间节点。</p>
              <p class=\"text-muted mb-0\">我们将在 24 小时内回复。</p>
            </div>
          </div>
          <div class=\"col-md-4\">
            <div class=\"feature-card glass p-3 reveal\" data-bg-topic=\"city map marker illustration\" style=\"height:200px; border-radius: var(--radius-lg);\" aria-label=\"地图占位\"></div>
          </div>
        </div>
      </div>
    </section>
  </main>

  <footer class=\"footer-minimal\"><div class=\"container\"><div class=\"footer-brand\"><span>{brand}</span><p>期待与你合作</p></div><div class=\"footer-meta\"><span>© {brand}</span><a href=\"mailto:hello@example.com\">hello@example.com</a></div></div></footer>
  <script src=\"assets/js/main.js\"></script>
</body>
</html>"""
    return create_html_file(file_path=file_path, title=title, content=html_doc, style="ultra_modern")


__all__ = [
    "create_html_file",
    "create_menu_page",
    "create_about_page",
    "create_contact_page",
]
