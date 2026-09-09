import Link from "next/link";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { Shell } from "../components/marketing/Shell";
import { HomeHero } from "../components/marketing/HomeHero";
import { CompanionSelector } from "../components/marketing/CompanionSelector";
import { Telemetry } from "../components/marketing/Telemetry";
import { FeatureCard } from "../components/marketing/FeatureCard";
import { Terminal } from "../components/marketing/Terminal";
import { NexusWidgetSurface } from "../components/agent/NexusWidgetSurface";

const featureCards = [
  { accent: "lime", title: "Ask Anything", text: "Get clear, helpful answers on any topic.", image: "/nexus/demon-atmosphere.jpg" },
  { accent: "cyan", title: "Code & Build", text: "Debug, generate, and learn with AI.", image: "/assets/nexus-wave.webp" },
  { accent: "purple", title: "Learn Faster", text: "Summarize, explain, and explore concepts.", image: "/nexus/forest-atmosphere.jpg" },
  { accent: "pink", title: "Be More Productive", text: "Plan, write, and get things done.", image: "/assets/nexus-hero.webp" },
];

export default function Home() {
  return <Shell>
    <HomeHero />

    <section className="between-grid">
      <CompanionSelector />
      <div className="operator-note glass-card"><span className="section-label">01 / OPERATING PRINCIPLE</span><h2>Give the interface a thought. It gives you room to think.</h2><p>NEXUS is built around short paths: ask, inspect, create, repeat. The visual system stays out of your way until it needs your attention.</p><Link href="/about" className="text-link">WHY NEXUS? <ArrowUpRight size={15}/></Link></div>
    </section>

    <Telemetry />
    <NexusWidgetSurface />

    <section id="features" className="features-section"><div className="section-heading"><div><span className="section-label">// WHAT CAN YOU DO</span><h2>Tools that feel like extensions of your hands.</h2></div><span className="heading-note">BUILT FOR CURIOUS MINDS<br/>NOT FOR CLICKING AROUND</span></div>
      <div className="feature-grid">{featureCards.map((card) => <FeatureCard key={card.title} {...card}/>)}</div>
    </section>

    <section className="terminal-section"><div className="section-heading"><div><span className="section-label">// LIVE INTERFACE</span><h2>Talk to the machine.</h2></div><span className="heading-note">LOCAL-FIRST / LOW FRICTION</span></div><Terminal /></section>

    <section className="closing-grid">
      <div className="closing-copy"><span className="section-label">// READY WHEN YOU ARE</span><h2>Questions have no loading screen.</h2><p>Open the chat, choose a model, and start from wherever your brain happens to be.</p><Link href="/chat" className="lime-button large">OPEN NEXUS <ArrowRight size={16}/></Link></div>
      <div className="closing-visual"><img src="/nexus/forest-atmosphere.jpg" alt="Teal forest atmosphere with moon and birds"/><div className="closing-overlay"/><div className="closing-stamp">NX / 2026<br/><b>SIGNAL IS LIVE</b></div></div>
    </section>
  </Shell>;
}
