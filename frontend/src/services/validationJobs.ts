import { apiGet, apiPost, apiPostForm } from "@/services/apiClient";
import type { RuleDefinition, ValidationJobResponse } from "@/types/api";


export async function createValidationJob(
  file: File,
  selectedRules: RuleDefinition[],
): Promise<ValidationJobResponse> {
  const formData = new FormData();
  formData.append("pdf", file);
  formData.append("rules_json", JSON.stringify({ rules: selectedRules }));
  return apiPostForm<ValidationJobResponse>("/validations/jobs", formData);
}

export async function getValidationJob(jobId: string): Promise<ValidationJobResponse> {
  return apiGet<ValidationJobResponse>(`/validations/jobs/${jobId}`);
}

export async function cancelValidationJob(jobId: string): Promise<ValidationJobResponse> {
  return apiPost<ValidationJobResponse>(`/validations/jobs/${jobId}/cancel`);
}
