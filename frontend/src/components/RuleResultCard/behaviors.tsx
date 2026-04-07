import { cn } from "@/utils/cn";

import type { AnalysisType } from "@/types/api";


export interface RuleResultLike {
  analysis_type: AnalysisType;
  citations: Array<{ page: number; evidence: string }>;
  execution_status: string;
  findings: string[];
  matched_pages?: number[];
  notes: string[];
  reasoning: string;
  rule_id: string;
  rule_name: string;
  summary: string;
  verdict: string;
}

export interface RuleResultCardProps {
  item: RuleResultLike;
}

export function getVerdictClasses(verdict: string): string {
  return cn(
    "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide",
    verdict === "pass" && "bg-emerald-100 text-emerald-700",
    verdict === "fail" && "bg-rose-100 text-rose-700",
    verdict === "not_applicable" && "bg-slate-200 text-slate-700",
    !["pass", "fail", "not_applicable"].includes(verdict) && "bg-amber-100 text-amber-700",
  );
}

export function getAnalysisTypeClasses(type: AnalysisType): string {
  return type === "vision"
    ? "rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-violet-700"
    : "rounded-full bg-cyan-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-cyan-700";
}
