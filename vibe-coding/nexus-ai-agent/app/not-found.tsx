import Link from "next/link";
import { ArrowLeft, RadioTower } from "lucide-react";
import { Shell } from "../components/marketing/Shell";
export default function NotFound() { return <Shell><div className="notfound"><div className="notfound-code"><RadioTower size={18}/> ERROR 404</div><h1>SIGNAL LOST.</h1><p>THE PAGE YOU'RE LOOKING FOR DOESN'T EXIST IN THIS NEXUS.</p><div className="signal"><span/><span/><span/><span/><span/><span/></div><Link href="/" className="lime-button large"><ArrowLeft size={15}/> RETURN HOME</Link></div></Shell> }
