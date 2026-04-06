import { cn } from "@/utils/cn";

import type { WorkspaceStatus } from "@/types/api";


export interface StatusPillProps {
  status: WorkspaceStatus;
}

export function getStatusClasses(tone: WorkspaceStatus["tone"]): string {
  return cn(
    "inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium",
    tone === "error" && "bg-rose-100 text-rose-700",
    tone === "success" && "bg-emerald-100 text-emerald-700",
    tone === "working" && "bg-amber-100 text-amber-700",
    tone === "neutral" && "bg-slate-100 text-slate-600",
  );
}
