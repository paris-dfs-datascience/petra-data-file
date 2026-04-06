import { apiGet } from "@/services/apiClient";
import type { RuleDefinition, RulesResponse } from "@/types/api";


export async function fetchRules(): Promise<RuleDefinition[]> {
  const response = await apiGet<RulesResponse>("/rules");
  return response.rules || [];
}
