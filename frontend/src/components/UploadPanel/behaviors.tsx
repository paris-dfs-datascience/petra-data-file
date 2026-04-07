import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";

import type { WorkspaceStatus } from "@/types/api";


export interface UploadPanelProps {
  documentId: string | null;
  isBusy: boolean;
  status: WorkspaceStatus;
  onFileSelected: (file: File) => Promise<void>;
  onStopAnalysis: () => Promise<void>;
}

function isPdfFile(file: File | null | undefined): file is File {
  if (!file) {
    return false;
  }
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

export function useUploadPanelBehavior({ isBusy, onFileSelected }: Pick<UploadPanelProps, "isBusy" | "onFileSelected">) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleInputChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (isPdfFile(file)) {
      await onFileSelected(file);
    }
    event.target.value = "";
  };

  const handleDragEnter = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    if (!isBusy) {
      setIsDragActive(true);
    }
  };

  const handleDragLeave = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragActive(false);
  };

  const handleDragOver = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    if (!isBusy) {
      setIsDragActive(true);
    }
  };

  const handleDrop = async (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragActive(false);
    if (isBusy) {
      return;
    }
    const file = event.dataTransfer.files?.[0];
    if (isPdfFile(file)) {
      await onFileSelected(file);
    }
  };

  return {
    inputRef,
    isDragActive,
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
    handleInputChange,
  };
}
