import { FormEvent, useEffect, useRef, useState } from 'react'
import {
  ArrowRight,
  BarChart3,
  Boxes,
  Check,
  ChevronDown,
  ClipboardCheck,
  Menu,
  SlidersHorizontal,
  Sparkles,
  X,
} from 'lucide-react'

const LOGIN_URL = 'https://ioe.idky.tech/accounts/login/'

type BookingStatus = 'idle' | 'sending' | 'success' | 'error'

function DigitalLandscape() {
  return (
    <div className="digital-landscape" aria-hidden="true">
      <div className="lattice lattice-left" />
      <div className="lattice lattice-right" />
      <svg className="contour-lines" viewBox="0 0 1440 760" preserveAspectRatio="none">
        <path d="M-20 614 C140 512 260 698 430 582 S740 430 930 584 S1240 690 1470 500" />
        <path d="M-30 636 C150 534 270 720 446 604 S752 452 946 606 S1255 712 1480 522" />
        <path d="M-40 658 C160 556 280 742 462 626 S764 474 962 628 S1270 734 1490 544" />
        <path d="M-50 680 C170 578 290 764 478 648 S776 496 978 650 S1285 756 1500 566" />
      </svg>
      <div className="data-rain data-rain-one" />
      <div className="data-rain data-rain-two" />
      <div className="seal-mark"><span>筹</span><span>策</span></div>
    </div>
  )
}

function ProductStage() {
  return (
    <div className="product-stage hero-fade-up" style={{ animationDelay: '360ms' }} aria-label="筹策工作台界面预览">
      <div className="product-window">
        <div className="window-bar">
          <span className="window-dots"><i /><i /><i /></span>
          <span>筹策 · 经营工作台</span>
          <span className="status-pill"><i /> 数据已更新</span>
        </div>
        <div className="product-body">
          <aside className="product-nav">
            <img src="/brand-mark.svg" alt="" />
            <span className="active">经营概览</span>
            <span>采购管理</span>
            <span>库存管理</span>
            <span>销售管理</span>
            <span>补货分析</span>
          </aside>
          <div className="product-canvas">
            <div className="canvas-head"><strong>工作台</strong><span>近 30 天⌄</span></div>
            <div className="metric-row">
              <div><small>待处理采购</small><b>12</b><em>待办</em></div>
              <div><small>今日单据</small><b>28</b><em>流转中</em></div>
              <div><small>库存预警</small><b>6</b><em>需关注</em></div>
            </div>
            <img src="/assets/shots/overview.webp" alt="筹策系统经营概览真实界面" />
          </div>
        </div>
      </div>
      <div className="mobile-panel" aria-hidden="true">
        <div><img src="/brand-mark.svg" alt="" /><span>筹策</span><Menu size={15} /></div>
        <strong>移动工作台</strong>
        <span>采购管理 <ArrowRight size={13} /></span>
        <span>库存管理 <ArrowRight size={13} /></span>
        <span>补货分析 <ArrowRight size={13} /></span>
        <small>今日待办 <b>9</b></small>
      </div>
    </div>
  )
}

function BookingDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [status, setStatus] = useState<BookingStatus>('idle')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!open) {
      setStatus('idle')
      setMessage('')
    }
  }, [open])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const values = new FormData(form)
    setStatus('sending')
    setMessage('')
    try {
      const response = await fetch('/api/bookings/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: String(values.get('phone') || '').trim(),
          category: String(values.get('category') || '').trim(),
          consent: values.get('consent') === 'on',
          website: String(values.get('website') || ''),
        }),
      })
      const result = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(result.message || '提交未成功，请稍后再试')
      form.reset()
      setStatus('success')
      setMessage('预约已收到，我们会与你联系。')
    } catch (error) {
      setStatus('error')
      setMessage(error instanceof Error ? error.message : '提交未成功，请稍后再试')
    }
  }

  if (!open) return null
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="booking-dialog" role="dialog" aria-modal="true" aria-labelledby="booking-title">
        <button className="dialog-close" type="button" onClick={onClose} aria-label="关闭预约窗口"><X /></button>
        <p className="dialog-kicker">预约产品讲解</p>
        <h2 id="booking-title">先聊业务，再谈系统。</h2>
        <p>留下经营品类和手机号，我们会结合你的实际流程沟通。</p>
        <form onSubmit={submit}>
          <label>手机号<input name="phone" type="tel" inputMode="numeric" autoComplete="tel" pattern="1[3-9][0-9]{9}" maxLength={11} placeholder="请输入 11 位手机号" required /></label>
          <label>经营品类<input name="category" type="text" maxLength={80} placeholder="例如：白酒批发" required /></label>
          <label className="consent"><input name="consent" type="checkbox" required /><span>同意仅将上述信息用于本次产品讲解联系</span></label>
          <label className="honeypot">网站<input name="website" type="text" tabIndex={-1} autoComplete="off" /></label>
          <button className="primary-button dialog-submit" type="submit" disabled={status === 'sending'}>{status === 'sending' ? '正在提交…' : '提交预约'} <ArrowRight /></button>
          {message && <p className={`form-message ${status}`} role="status">{status === 'success' && <Check />} {message}</p>}
        </form>
      </section>
    </div>
  )
}

const services = [
  { icon: Boxes, title: '进销存系统', text: '采购、库存、销售和对账放进同一套工作台，让单据与业务状态随时对得上。', link: 'product.html#ledger' },
  { icon: BarChart3, title: '补货分析', text: '结合销量、库存与在途给出可解释建议，采购人员确认后再形成单据。', link: 'product.html#how' },
  { icon: SlidersHorizontal, title: '业务流程定制', text: '围绕箱规、起订量、账期与岗位权限，把企业规则落实进系统。', link: '#delivery' },
]

const cases = [
  { image: '/assets/shots/wholesale.webp', label: '批发开单', note: '订单、商品与客户信息同步流转' },
  { image: '/assets/shots/po.webp', label: '采购审核', note: '从建议到采购单保留审核依据' },
  { image: '/assets/shots/b2b.webp', label: 'To B 概览', note: '业务状态在同一工作台集中查看' },
]

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [bookingOpen, setBookingOpen] = useState(false)
  const pageRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const root = pageRef.current
    if (!root || matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed')
          observer.unobserve(entry.target)
        }
      })
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' })
    root.querySelectorAll('.reveal, .reveal-scale').forEach((node) => observer.observe(node))
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={pageRef}>
      <a className="skip-link" href="#main">跳到正文</a>
      <header className="site-header">
        <nav className="nav-shell" aria-label="主导航">
          <a className="brand" href="#top" aria-label="筹策首页"><img src="/brand-mark.svg" alt="" /><span>筹策</span></a>
          <button className="menu-button" type="button" onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen} aria-label="打开导航">{menuOpen ? <X /> : <Menu />}</button>
          <div className={`nav-links ${menuOpen ? 'open' : ''}`}>
            <a href="#services" onClick={() => setMenuOpen(false)}>产品能力 <ChevronDown /></a>
            <a href="#delivery" onClick={() => setMenuOpen(false)}>解决方案 <ChevronDown /></a>
            <a href="#case" onClick={() => setMenuOpen(false)}>德鉴案例</a>
            <a href="#about" onClick={() => setMenuOpen(false)}>关于我们</a>
          </div>
          <div className="nav-actions">
            <a className="login-button" href={LOGIN_URL}>登录系统</a>
            <button className="primary-button compact" type="button" onClick={() => setBookingOpen(true)}>预约产品讲解</button>
          </div>
        </nav>
      </header>

      <main id="main">
        <section className="hero" id="top">
          <div className="hero-photo" />
          <DigitalLandscape />
          <div className="hero-grid">
            <div className="hero-copy">
              <p className="eyebrow hero-fade-up"><i /> 为经销企业而做</p>
              <h1 className="hero-fade-up" style={{ animationDelay: '100ms' }}>经销企业的<br /><em>业务系统与数字化交付</em></h1>
              <p className="hero-lead hero-fade-up" style={{ animationDelay: '220ms' }}>把采购、库存、销售与补货判断，放进同一套工作台。</p>
              <div className="hero-actions hero-fade-up" style={{ animationDelay: '300ms' }}>
                <a className="primary-button" href={LOGIN_URL}>登录系统 <ArrowRight /></a>
                <button className="outline-button" type="button" onClick={() => setBookingOpen(true)}>预约产品讲解 <ArrowRight /></button>
              </div>
              <p className="hero-proof hero-fade-up" style={{ animationDelay: '420ms' }}><span><Check /></span> 贵州德鉴酒业 · 已交付使用</p>
            </div>
            <ProductStage />
          </div>
          <div className="cloud-transition" aria-hidden="true" />
        </section>

        <section className="services paper-section" id="services">
          <div className="section-inner">
            <div className="section-heading reveal"><p className="section-index">01 / 产品能力</p><h2>一套工作台，接住日常经营。</h2><p>从真实业务与岗位分工出发，让系统贴合企业每天的工作。</p></div>
            <div className="service-grid">
              {services.map((service, index) => {
                const Icon = service.icon
                return <a className="service-item reveal" href={service.link} key={service.title} style={{ transitionDelay: `${index * 90}ms` }}>
                  <span className="service-icon"><Icon /></span>
                  <span><b>{service.title}</b><small>{service.text}</small></span>
                  <ArrowRight className="service-arrow" />
                </a>
              })}
            </div>
          </div>
        </section>

        <section className="delivery paper-section" id="delivery">
          <div className="delivery-pattern" aria-hidden="true" />
          <div className="section-inner delivery-grid">
            <div className="delivery-copy reveal">
              <p className="section-index">02 / 交付方式</p>
              <h2>先看业务怎么走，<br />再让系统怎么跑。</h2>
              <p>梳理单据、岗位和仓库流程，把关键规则写进系统；上线后也能随业务继续调整。</p>
              <button className="ink-link" type="button" onClick={() => setBookingOpen(true)}>聊聊你的业务需求 <ArrowRight /></button>
            </div>
            <div className="delivery-steps reveal">
              <article><span>壹</span><div><strong>看现场</strong><p>了解商品、仓库、岗位与单据流转。</p></div></article>
              <article><span>贰</span><div><strong>定规则</strong><p>说清审批、箱规、账期与补货口径。</p></div></article>
              <article><span>叁</span><div><strong>交付使用</strong><p>迁移数据、培训团队，陪伴平稳上线。</p></div></article>
            </div>
          </div>
        </section>

        <section className="case paper-section" id="case">
          <div className="section-inner">
            <div className="case-heading reveal">
              <div><p className="section-index">03 / 德鉴案例</p><h2>来自真实业务，也回到真实业务。</h2></div>
              <p>基于贵州德鉴酒业的商品、仓库和采购流程，交付进销存与补货分析系统。</p>
            </div>
            <div className="case-grid">
              {cases.map((item, index) => <a className="case-card reveal-scale" href={item.image} target="_blank" rel="noreferrer" key={item.label} style={{ animationDelay: `${index * 100}ms` }}>
                <img src={item.image} alt={`筹策系统${item.label}界面`} loading="lazy" />
                <span><b>{item.label}</b><small>{item.note}</small></span>
                <ArrowRight />
              </a>)}
            </div>
          </div>
        </section>

        <section className="about" id="about">
          <div className="section-inner about-inner reveal">
            <div className="about-mark"><Sparkles /></div>
            <p className="section-index">04 / 开始合作</p>
            <h2>传统行业的经验，<br /><em>值得被更好的系统接住。</em></h2>
            <p>告诉我们你的经营品类和当前流程，先把问题聊清楚，再决定系统怎么做。</p>
            <button className="primary-button" type="button" onClick={() => setBookingOpen(true)}>预约产品讲解 <ArrowRight /></button>
          </div>
        </section>
      </main>

      <footer>
        <div className="footer-inner">
          <a className="brand" href="#top"><img src="/brand-mark.svg" alt="" /><span>筹策</span></a>
          <p>业务系统 · 流程定制 · 补货分析</p>
          <div><a href={LOGIN_URL}>登录系统</a><button type="button" onClick={() => setBookingOpen(true)}>预约讲解</button></div>
        </div>
        <div className="footer-bottom"><span>© 2026 筹策</span><span>为经销企业而做</span></div>
      </footer>

      <BookingDialog open={bookingOpen} onClose={() => setBookingOpen(false)} />
    </div>
  )
}
