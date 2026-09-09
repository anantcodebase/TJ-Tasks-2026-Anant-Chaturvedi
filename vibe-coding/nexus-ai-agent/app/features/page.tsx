import Link from "next/link";
import { ArrowRight, Brain, Code2, FileText, Gauge, Sparkles } from "lucide-react";
import { Shell, Breadcrumbs } from "../../components/marketing/Shell";

const features = [
  ["ASK ANYTHING", "Search less. Reason more.", "NEXUS keeps the conversation in one place so you can move from a half-formed question to a usable answer without resetting context.", Brain],
  ["CODE & BUILD", "From bug to breakpoint.", "Use it for debugging, code explanations, scaffolding, refactors and learning the why behind the code.", Code2],
  ["LEARN FASTER", "Turn dense into clear.", "Drop in a concept, notes, or a problem. Ask for a simpler explanation, a deeper one, or a step-by-step route through it.", FileText],
  ["WORK WITH SIGNAL", "Useful output, less noise.", "NEXUS is designed around concise actions, clear states, and a terminal-style interaction layer that keeps work moving.", Gauge],
];

export default function FeaturesPage() {
  return <Shell><div className="inner-page"><Breadcrumbs current="Features"/><header className="inner-hero"><span className="section-label">// PRODUCT CAPABILITIES</span><h1>What NEXUS can actually do.</h1><p>One interface for conversation, creation, analysis, and the boring little tasks that usually break your focus.</p></header><div className="feature-list">{features.map(([kicker, title, body, Icon]) => { const C = Icon as typeof Sparkles; return <article key={kicker} className="big-feature glass-card"><div className="big-feature-icon"><C size={19}/></div><div><span className="section-label">{kicker as string}</span><h2>{title as string}</h2><p>{body as string}</p><Link href="/chat" className="text-link">TRY IT <ArrowRight size={15}/></Link></div></article>})}</div></div></Shell>;
}
