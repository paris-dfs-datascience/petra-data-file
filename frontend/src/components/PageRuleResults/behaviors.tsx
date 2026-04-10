import type { PageRuleAssessment } from "@/types/api";


export interface PageRuleResultsProps {
  analysisType: "text" | "vision";
  items: PageRuleAssessment[];
  emptyMessage: string;
  documentId: string | null;
  sourceFilename: string | null;
}

export function groupItemsByPage(items: PageRuleAssessment[]): Array<{ page: number; items: PageRuleAssessment[] }> {
  const groups = new Map<number, PageRuleAssessment[]>();

  for (const item of items) {
    const current = groups.get(item.page) || [];
    current.push(item);
    groups.set(item.page, current);
  }

  return Array.from(groups.entries())
    .sort((left, right) => left[0] - right[0])
    .map(([page, pageItems]) => ({ page, items: pageItems }));
}

export function getPageResultsHeading(analysisType: PageRuleResultsProps["analysisType"]): string {
  return analysisType === "vision" ? "Visual Rule Assessments By Page" : "Text Rule Assessments By Page";
}
