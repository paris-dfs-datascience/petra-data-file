import type { WorkspaceTabKey } from "@/types/api";


export interface TabDefinition {
  key: WorkspaceTabKey;
  label: string;
}

export interface TabNavigationProps {
  activeTab: WorkspaceTabKey;
  onTabChange: (tab: WorkspaceTabKey) => void;
}

export const tabDefinitions: TabDefinition[] = [
  { key: "source", label: "Original PDF" },
  { key: "extracted", label: "Extracted Text" },
  { key: "text-analysis", label: "Text Analysis Result" },
  { key: "visual-analysis", label: "Visual Analysis Result" },
];
