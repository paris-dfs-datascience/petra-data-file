import { cn } from "@/utils/cn";

import type { RuleDefinition } from "@/types/api";


export interface RuleSelectionCardProps {
  checked: boolean;
  rule: RuleDefinition;
  onToggle: (ruleId: string) => void;
}

export function getRuleTypeClasses(type: RuleDefinition["analysis_type"]): string {
  return type === "vision"
    ? "bg-violet-100 text-violet-700"
    : "bg-cyan-100 text-cyan-700";
}

export function getCardClasses(checked: boolean): string {
  return cn(
    "block w-full cursor-pointer rounded-[1.4rem] border p-4 transition",
    checked ? "border-teal-300 bg-teal-50/70" : "border-slate-200 bg-slate-50",
  );
}
