"use client";

import { Check, X } from "lucide-react";
import { useNexusUI } from "../../lib/nexus-ui";

export function CompanionSelector() {
  const { model, setModel } = useNexusUI();
  const items = [
    { id: "nexus" as const, name: "NEXUS", meta: "Balanced · General", img: "/nexus/demon-atmosphere.jpg", pos: "center 55%", label: "↑ NEXUS" },
    { id: "deep" as const, name: "NEXUS (Deep)", meta: "Deeper · Analytical", img: "/assets/nexus-hero.webp", pos: "right center", label: "● NEXUS DEEP" },
  ];
  return (
    <section className="companion-card glass-card">
      <div className="card-kicker"><span>CHOOSE YOUR COMPANION</span><div className="companion-card-actions"><span className="companion-status">ACTIVE: {model === "deep" ? "NEXUS DEEP" : "NEXUS"}</span><button type="button" aria-label="Companion panel status"><X size={13}/></button></div></div>
      <div className="companion-grid">
        {items.map((item) => {
          const active = model === item.id;
          return <button key={item.name} onClick={() => setModel(item.id)} className={`companion ${active ? "active" : ""}`} aria-pressed={active}>
            <div className={`companion-image ${item.id === "deep" ? "landscape" : "portrait"}`}><img src={item.img} alt="" style={{ objectPosition: item.pos }}/><span className="image-scan"/></div>
            <div className="companion-info"><strong>{active ? item.label : `○ ${item.name}`}</strong><span>{item.meta}</span></div>
            {active && <Check size={14} className="companion-check" />}
          </button>;
        })}
      </div>
      <div className="speech-bubble"><div className="mascot">◒</div><span>“Same curiosity, Different perspectives.” <b>→</b></span></div>
    </section>
  );
}
