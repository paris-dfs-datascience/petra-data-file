import { EmptyState } from "@/components/EmptyState";

import type { SourcePreviewProps } from "./behaviors";


export function SourcePreview({ previewUrl, sourceFilename }: SourcePreviewProps) {
  if (!previewUrl) {
    return <EmptyState title="No PDF loaded" description="Upload a PDF to preview the original document here." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-3">
        <div>
          <p className="text-sm font-semibold text-slate-900">{sourceFilename || "Source PDF"}</p>
          <p className="text-xs text-slate-500">Local browser preview</p>
        </div>

        <a
          className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white"
          href={previewUrl}
          rel="noreferrer"
          target="_blank"
        >
          Open PDF
        </a>
      </div>

      <iframe className="h-[900px] w-full rounded-[1.5rem] border border-slate-200 bg-white" src={previewUrl} title="Source PDF Preview" />
    </div>
  );
}
