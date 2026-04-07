import type { PageExtraction } from "@/types/api";


export interface ExtractionPageCardProps {
  page: PageExtraction;
}

export function getTableLabel(tableCount: number): string {
  return `${tableCount} detected table${tableCount === 1 ? "" : "s"} on this page.`;
}
