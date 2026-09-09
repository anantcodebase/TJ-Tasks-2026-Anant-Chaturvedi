import type { MetadataRoute } from "next";
export default function sitemap(): MetadataRoute.Sitemap { const base=process.env.NEXT_PUBLIC_SITE_URL; if (!base) return []; return ["/","/features","/models","/pricing","/about","/chat"].map((url)=>({url:base+url,lastModified:new Date(),changeFrequency:url==="/"?"weekly":"monthly",priority:url==="/"?1:0.7})); }
