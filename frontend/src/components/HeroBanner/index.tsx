import type { HeroBannerProps } from "./behaviors";


export function HeroBanner({ appName }: HeroBannerProps) {
  return (
    <section className="glass-panel overflow-hidden">
      <div className="px-6 py-8 lg:px-10">
        <div>
          <p className="mb-3 inline-flex rounded-full bg-accentSoft px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-accent">
            PDF Extraction Workspace
          </p>
          <h1 className="max-w-3xl text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
            {appName}
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
            Upload a PDF, inspect the extracted text page by page, and review text and visual analysis without
            persisting the document on the server.
          </p>
        </div>
      </div>
    </section>
  );
}
