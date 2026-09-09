import { ArrowRight, Crown, Crosshair, Feather, Wand2 } from "lucide-react";
import { Shell, Breadcrumbs } from "../../components/marketing/Shell";

const portfolioUrl = "https://anantcodebase.github.io/Anant-Chaturvedi-Portfolio/#home";
const profileImage = "https://anantcodebase.github.io/Anant-Chaturvedi-Portfolio/assets/profile.jpg";

export default function AboutPage() {
  return (
    <Shell>
      <div className="inner-page">
        <Breadcrumbs current="About" />
        <header className="inner-hero about-hero">
          <span className="section-label">// PROJECT NEXUS</span>
          <h1>A thinking partner should feel like a tool, not a billboard.</h1>
          <p>NEXUS is a visual system for working with AI: dark, technical, a little weird, and focused on getting you from question to useful output.</p>
        </header>

        <div className="about-grid">
          <div className="about-art glass-card">
            <img src="/nexus/demon-atmosphere.jpg" alt="Red moon and silhouette atmospheric artwork" />
            <div className="about-art-copy"><Crown size={15}/><span>KEEP THE HUMAN IN THE LOOP.</span></div>
          </div>
          <div className="about-copy">
            <div className="about-row"><Crosshair/><div><span className="section-label">DESIGN</span><h2>Technical without being sterile.</h2><p>Blueprint marks, glass, terminal type, and cinematic textures create a system with edges. The interface stays readable.</p></div></div>
            <div className="about-row"><Wand2/><div><span className="section-label">BEHAVIOR</span><h2>Useful motion, no circus.</h2><p>Transitions explain state. Hover states respond. Nothing is moving just to prove a library was installed.</p></div></div>
            <div className="about-row"><Feather/><div><span className="section-label">VOICE</span><h2>Human questions. Direct answers.</h2><p>The visual language is playful around the edges while the core product stays practical.</p></div></div>
            <a className="text-link" href={"/chat"}>ENTER THE CHAT <ArrowRight size={15}/></a>
          </div>
        </div>

        <section className="anant-about glass-card" aria-labelledby="anant-title">
          <div className="anant-about-media">
            <div className="anant-avatar-wrap"><img className="anant-avatar" src={profileImage} alt="Anant Chaturvedi, also known as XlaMus" /></div>
            <span className="section-label">PROFILE / XLAMUS</span>
          </div>
          <div className="anant-about-copy">
            <span className="section-label">// ANANT CHATURVEDI</span>
            <h2 id="anant-title">ANANT CHATURVEDI <span>aka XLAMUS</span></h2>
            <p>Anant Chaturvedi is a first-year Computer Science Engineering student focused on DSA, C++, fundamentals, and development. He is exploring AI/ML, NLP, web development, Node.js, and Kotlin, with Android development currently on the learning track.</p>
            <div className="anant-tags" aria-label="Portfolio skills">
              {['C++', 'DSA', 'Web Development', 'Node.js', 'AI/ML', 'NLP', 'TensorFlow', 'Kotlin'].map((tag) => <span key={tag}>{tag}</span>)}
            </div>
            <a className="text-link" href={portfolioUrl} target="_blank" rel="noopener noreferrer">VIEW PORTFOLIO <ArrowRight size={15}/></a>
          </div>
        </section>
      </div>
    </Shell>
  );
}
