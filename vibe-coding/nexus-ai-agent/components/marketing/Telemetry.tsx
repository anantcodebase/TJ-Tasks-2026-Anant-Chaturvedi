import { Activity, Bolt, Box, MessageCircle, Users } from "lucide-react";

const metrics = [
  ["10K+", "Active Users", Users], ["50K+", "Messages Today", MessageCircle], ["3", "AI Models", Box], ["99.8%", "Uptime", Activity], ["< 2s", "Avg. Response Time", Bolt],
] as const;

export function Telemetry() {
  return <section className="telemetry glass-card" aria-label="Product telemetry">
    {metrics.map(([value, label, Icon]) => <div className="telemetry-item" key={label}><Icon size={15}/><div><strong>{value}</strong><span>{label}</span></div></div>)}
    <div className="telemetry-photo"><img src="/nexus/forest-atmosphere.jpg" alt="Dark atmospheric forest"/><div><strong>BETTER TOOLS, A BRIGHTER YOU</strong><span>NX / SIGNAL RIBBON</span></div><div className="barcode"><i/><i/><i/><i/><i/><i/></div></div>
  </section>;
}
