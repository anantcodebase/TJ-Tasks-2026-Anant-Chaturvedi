import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export function FeatureCard({ accent, title, text, image, href = "/features" }: { accent: string; title: string; text: string; image: string; href?: string }) {
  return <Link href={href} className={`feature-card ${accent}`}>
    <div className="feature-top"><span>{accent === "lime" ? "01" : accent === "cyan" ? "02" : accent === "purple" ? "03" : "04"}</span><ArrowUpRight size={16}/></div>
    <div className="feature-image"><img src={image} alt=""/></div>
    <div className="feature-copy"><h3>{title}</h3><p>{text}</p></div>
    <div className="feature-line" />
  </Link>;
}
