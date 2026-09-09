"use client";

import { FormEvent, useEffect, useState, type CSSProperties } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { BarChart3, Box, ChevronDown, Command, Cpu, Globe2, Home, Menu, MessageSquare, Search, Settings2, X } from "lucide-react";
import { ACCENT_CONFIG, useNexusUI } from "../../lib/nexus-ui";
import type { AccentName } from "../../lib/types";

const links = [
  { href: "/", label: "HOME", icon: Home },
  { href: "/features", label: "FEATURES", icon: Box },
  { href: "/models", label: "MODELS", icon: Cpu },
  { href: "/pricing", label: "PRICING", icon: BarChart3 },
  { href: "/about", label: "ABOUT", icon: Globe2 },
];

function isActiveRoute(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

export function Shell({ children }: { children: React.ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [signInOpen, setSignInOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [time, setTime] = useState("");
  const pathname = usePathname();
  const { accent, setAccent } = useNexusUI();

  useEffect(() => {
    const tick = () => setTime(new Intl.DateTimeFormat("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(new Date()));
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    const handler = () => setSettingsOpen(true);
    document.addEventListener("nexus-settings", handler);
    return () => document.removeEventListener("nexus-settings", handler);
  }, []);

  const submitSearch = (event: FormEvent) => {
    event.preventDefault();
    const q = query.trim().toLowerCase();
    if (!q) return;
    const target = q.includes("model") ? "/models" : q.includes("price") ? "/pricing" : q.includes("feature") ? "/features" : q.includes("about") ? "/about" : q.includes("home") ? "/" : "/chat";
    window.location.href = target;
  };

  return (
    <main className="nexus-root nexus-grid nexus-noise">
      <div className="atmosphere atmosphere-red" aria-hidden="true" />
      <div className="atmosphere atmosphere-teal" aria-hidden="true" />
      <div className="blueprint blueprint-a" aria-hidden="true">+ 014 / 09</div>
      <div className="blueprint blueprint-b" aria-hidden="true">NX-UI-01 / 1:1</div>

      <aside className="side-rail" aria-label="Primary navigation">
        <div className="rail-top">
          <Link href="/" className="rail-avatar" aria-label="Nexus home"><span>N</span></Link>
          <div className="rail-vertical">GOOD IDEAS / BETTER CONVOS</div>
          <div className="barcode small-barcode" aria-hidden="true"><i/><i/><i/><i/><i/><i/><i/></div>
        </div>
        <nav className="rail-nav">
          {links.map(({ href, label, icon: Icon }) => {
            const active = isActiveRoute(pathname, href);
            return <Link key={href} href={href} title={label} aria-current={active ? "page" : undefined} className={`rail-button ${active ? "current" : ""}`}>
              <Icon size={17} strokeWidth={1.7} />
              <span>{label}</span>
            </Link>;
          })}
          {(() => {
            const active = isActiveRoute(pathname, "/chat");
            return <Link href="/chat" className={`rail-button ${active ? "current" : ""}`} title="Chat" aria-current={active ? "page" : undefined}><MessageSquare size={17} strokeWidth={1.7}/><span>CHAT</span></Link>;
          })()}
          <button className="rail-button" title="Settings" onClick={() => document.dispatchEvent(new CustomEvent("nexus-settings"))}><Settings2 size={17} strokeWidth={1.7}/><span>SET</span></button>
        </nav>
        <div className="rail-bottom">
          <Globe2 size={15} />
          <div className="rail-vertical">// NOT JUST A CHATBOT, A THINKING PARTNER.</div>
          <div className="rail-scroll">SCROLL DOWN <ChevronDown size={13}/></div>
        </div>
      </aside>

      <div className="page-frame">
        <header className="topbar">
          <Link href="/" className="brand"><span>NEXUS</span><small>♛</small></Link>
          <span className="brand-tag">// AI FOR REAL PEOPLE</span>

          <nav className="desktop-menu" aria-label="Section navigation">
            {links.map((item) => <Link key={item.href} href={item.href} aria-current={isActiveRoute(pathname, item.href) ? "page" : undefined} className={`toplink ${isActiveRoute(pathname, item.href) ? "current" : ""}`}>{item.label}</Link>)}
          </nav>

          <div className="top-actions">
            <button className="icon-button" onClick={() => setSearchOpen((v) => !v)} aria-label="Search"><Search size={16}/></button>
            <button className="signin" onClick={() => setSignInOpen(true)}>SIGN IN</button>
            <Link href="/chat" className="lime-button">GET STARTED <span>→</span></Link>
            <button className="icon-button mobile-menu-button" onClick={() => setMenuOpen(true)} aria-label="Open menu"><Menu size={17}/></button>
          </div>

          <AnimatePresence>
            {searchOpen && (
              <motion.form initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} onSubmit={submitSearch} className="search-pop">
                <Command size={15}/><input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search the Nexus…"/><button type="submit">ENTER</button>
              </motion.form>
            )}
          </AnimatePresence>
        </header>

        {children}

        <AnimatePresence>
          {settingsOpen && (
            <motion.div className="settings-pop glass-card" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}>
              <div className="settings-pop-head"><span>NX DESIGN SYSTEM</span><button onClick={() => setSettingsOpen(false)} aria-label="Close settings"><X size={14}/></button></div>
              <div className="settings-accent-row"><span className="settings-caption">ACCENT COLOR</span><strong>{ACCENT_CONFIG[accent].label.toUpperCase()}</strong></div>
              <div className="settings-swatches" role="group" aria-label="Accent color">
                {(Object.keys(ACCENT_CONFIG) as AccentName[]).map((name) => (
                  <button key={name} type="button" className={`accent-swatch ${accent === name ? "selected" : ""}`} onClick={() => setAccent(name)} aria-label={`Use ${ACCENT_CONFIG[name].label} accent`} aria-pressed={accent === name} style={{ "--swatch": ACCENT_CONFIG[name].hex } as CSSProperties}>
                    <span />
                  </button>
                ))}
              </div>
              <p>Accent changes stay controlled. The dark foundation and atmospheric imagery remain intact.</p>
            </motion.div>
          )}
        </AnimatePresence>

        <footer className="site-footer">
          <div>
            <div className="footer-brand">NEXUS // OPEN MODELS | REAL CONVERSATIONS | A BRIGHTER YOU</div>
            <div className="footer-muted">BUILT BY HUMANS, POWERED BY AI.</div>
          </div>
          <div className="title-block"><span>PROJECT: NEXUS AI LANDING PAGE</span><span>DRAWING NO: NX-UI-01</span><span>SCALE: 1:1</span></div>
          <div className="barcode footer-barcode" aria-hidden="true"><i/><i/><i/><i/><i/><i/><i/><i/><i/></div>
        </footer>
      </div>

      <div className="live-corner"><span className="status-dot"/> LOCAL / {time || "--:--:--"}</div>

      <AnimatePresence>
        {menuOpen && (
          <motion.div className="mobile-sheet" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div className="mobile-panel" initial={{ y: -20 }} animate={{ y: 0 }} exit={{ y: -20 }}>
              <div className="mobile-panel-head"><span>NX NAV</span><button onClick={() => setMenuOpen(false)} aria-label="Close menu"><X size={18}/></button></div>
              {links.map((item) => <Link key={item.href} href={item.href} onClick={() => setMenuOpen(false)} className={isActiveRoute(pathname, item.href) ? "mobile-current" : ""}>{item.label}<span>→</span></Link>)}
              <Link href="/chat" onClick={() => setMenuOpen(false)} className={isActiveRoute(pathname, "/chat") ? "mobile-current" : ""}>CHAT <span>→</span></Link>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <SignInModal open={signInOpen} onClose={() => setSignInOpen(false)} />
    </main>
  );
}

function SignInModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!open) return;
    setSubmitted(false);
  }, [open]);

  if (!open) return null;
  const valid = email.includes("@") && password.length >= 6;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!valid) return;
    window.localStorage.setItem("nexus-demo-session", JSON.stringify({ email, createdAt: Date.now() }));
    setSubmitted(true);
  };

  return <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
    <motion.div className="signin-modal glass-card" role="dialog" aria-modal="true" aria-labelledby="signin-title" initial={{ opacity: 0, y: 12, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} onMouseDown={(e) => e.stopPropagation()}>
      <div className="settings-pop-head"><span>// ACCESS NEXUS</span><button onClick={onClose} aria-label="Close sign in"><X size={14}/></button></div>
      {!submitted ? <form onSubmit={submit} className="signin-form">
        <div><span className="section-label">01 / IDENTITY</span><h2 id="signin-title">Sign in.</h2><p>Use an email and a six-character password to initialize a local NEXUS session.</p></div>
        <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required /></label>
        <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" minLength={6} required /></label>
        <button type="submit" className="lime-button" disabled={!valid}>INITIALIZE SESSION →</button>
        <span className="signin-hint">LOCAL DEMO SESSION / NO PASSWORD SENT TO A SERVER</span>
      </form> : <div className="signin-success"><span className="section-label">SESSION / READY</span><h2>Access granted.</h2><p>{email} is now stored as a local demo session on this device.</p><button className="lime-button" onClick={onClose}>CONTINUE →</button></div>}
    </motion.div>
  </div>;
}

export function Breadcrumbs({ current }: { current: string }) {
  return <div className="breadcrumbs"><Link href="/">HOME</Link><span>/</span><span>{current.toUpperCase()}</span></div>;
}
