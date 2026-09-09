"use client";

import { NexusUIProvider } from "../../lib/nexus-ui";

export function NexusProvider({ children }: { children: React.ReactNode }) {
  return <NexusUIProvider>{children}</NexusUIProvider>;
}
