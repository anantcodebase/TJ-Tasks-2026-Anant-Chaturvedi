"use client";

import { Lightbulb, ArrowRight, PenLine } from "lucide-react";
import Link from "next/link";
import { HeroClock } from "./HeroClock";
import { useNexusUI } from "../../lib/nexus-ui";

export function HomeHero() {
  const { model } = useNexusUI();
  const deep = model === "deep";
  const heroImage = deep ? "/assets/nexus-hero.webp" : "/nexus/demon-atmosphere.jpg";

  return <section className="hero-section">
    <div className="hero-copy">
      <div className="technical-chip"><span>v1.5</span><i/> OPEN MODEL RUNTIME</div>
      <div className="poster-heading">
        <span className="poster-small">CHAT / CREATE / THINK</span>
        <h1>NEXUS</h1>
        <div className="heading-sub"><span>CHAT</span><b>BEYOND LIMITS</b></div>
        <div className="measurement m1">1200 <span>PX</span></div><div className="measurement m2">/ 7.3°</div>
        <div className="crosshair c1">+</div><div className="crosshair c2">+</div>
      </div>
      <div className="model-identity-badge" aria-live="polite"><span className="model-identity-dot"/><span>ACTIVE MODEL</span><strong>{deep ? "NEXUS DEEP" : "NEXUS"}</strong></div>
      <p className="hero-tagline">Your all-in-one AI companion. Powered by open models. Built for creators, learners, and curious minds.</p>
      <div className="cta-row"><Link href="/chat" className="lime-button large">START CHATTING <ArrowRight size={16}/></Link><Link href="/features" className="ghost-button large">EXPLORE FEATURES</Link></div>
      <div className="social-proof"><div className="avatar-stack"><span>AI</span><span>NX</span><span>✦</span><span>07</span></div><span>10K+ creators, students & builders already using Nexus</span></div>
      <div className="doodle"><div className="cat">◠ᴗ◠</div><span>HUMAN QUESTIONS, AI POSSIBILITIES // NEXUS</span><PenLine size={13}/></div>
    </div>

    <div className={`hero-art ${deep ? "hero-art-deep" : "hero-art-nexus"}`}>
      <div className={`art-frame ${deep ? "deep" : "portrait"}`}><img src={heroImage} alt={deep ? "NEXUS Deep landscape model atmosphere" : "Dark anime-inspired red moon atmosphere"}/><div className="art-shade"/><div className="art-grain"/></div>
      <div className="vertical-jp">考え続ける</div>
      <div className="hud-box hb-1"><span>THINK</span><span>CHAT</span><span>CREATE</span><span>REPEAT</span></div>
      <div className="hud-box hb-2"><span>{deep ? "DEEP" : "SYNC"}</span><b>{deep ? "4.6" : "99.8"}</b><small>{deep ? "x" : "%"}</small></div>
      <div className="live-hud"><div><HeroClock/></div><p>SOMEWHERE ON THE INTERNET / IDEAS NEVER SLEEP</p></div>
      <div className="hero-sticker"><Lightbulb size={14}/><span>{deep ? "THINK DEEPER" : "KEEP THINKING"}</span></div>
    </div>
  </section>;
}
