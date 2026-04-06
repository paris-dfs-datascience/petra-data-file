import type { RuleDefinition } from "@/types/api";


export interface RulesSidebarProps {
  rules: RuleDefinition[];
  selectedRuleIds: string[];
  onRuleToggle: (ruleId: string) => void;
  onSelectAll: () => void;
  onRefresh: () => Promise<void>;
  errorMessage?: string | null;
}

export function getSelectionLabel(selectedCount: number): string {
  return `${selectedCount} rule(s) selected`;
}

export function getSelectAllLabel(selectedCount: number, totalCount: number): string {
  return selectedCount === totalCount && totalCount > 0 ? "Clear All" : "Select All";
}
