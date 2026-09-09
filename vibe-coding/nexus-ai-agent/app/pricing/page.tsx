import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import { Shell, Breadcrumbs } from "../../components/marketing/Shell";

const plans = [
  { name: "LOCAL", price: "FREE", text: "Run the core Nexus experience locally.", items: ["Chat interface", "Open model support", "Terminal mode", "Theme controls"] },
  { name: "PLUS", price: "₹499", text: "For people who want more room to work.", items: ["Longer sessions", "Priority model access", "Advanced workflows", "Expanded analytics" ] },
  { name: "STUDIO", price: "₹999", text: "For serious builders and creators.", items: ["Team-ready workspace", "Model switching", "Higher limits", "Project tooling"] },
];
export default function PricingPage() { return <Shell><div className="inner-page"><Breadcrumbs current="Pricing"/><header className="inner-hero"><span className="section-label">// NO HIDDEN BUTTONS</span><h1>Pricing that reads like pricing.</h1><p>These are UI-ready tiers. Connect your billing provider before publishing any commercial figures.</p></header><div className="pricing-grid">{plans.map((p, i) => <article className={`price-card glass-card ${i === 1 ? "recommended" : ""}`} key={p.name}>{i === 1 && <span className="recommended-tag">MOST POPULAR</span>}<span className="section-label">{p.name}</span><h2>{p.price}</h2><p>{p.text}</p><div className="price-list">{p.items.map((item) => <div key={item}><Check size={13}/><span>{item}</span></div>)}</div><Link href="/chat" className={i === 1 ? "lime-button" : "ghost-button"}>START <ArrowRight size={15}/></Link></article>)}</div></div></Shell> }
