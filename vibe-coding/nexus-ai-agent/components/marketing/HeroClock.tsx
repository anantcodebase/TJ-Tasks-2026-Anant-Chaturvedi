"use client";
import { useEffect, useState } from "react";
export function HeroClock(){
  const [stamp,setStamp]=useState("");
  useEffect(()=>{const tick=()=>setStamp(new Intl.DateTimeFormat("en-IN",{weekday:"long",month:"short",day:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit",hour12:false}).format(new Date()));tick();const id=window.setInterval(tick,1000);return()=>window.clearInterval(id)},[]);
  const displayTime = stamp ? stamp.slice(-5) : "--:--";
  const displayDate = stamp ? stamp.slice(0, stamp.lastIndexOf(", ")) : "LOCAL SYSTEM / LIVE";
  return <><span>{displayDate.toUpperCase()}</span><strong>{displayTime}</strong></>;
}
