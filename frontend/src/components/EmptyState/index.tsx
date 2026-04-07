import type { EmptyStateProps } from "./behaviors";


export function EmptyState({ description, title }: EmptyStateProps) {
  return (
    <article className="rounded-[1.75rem] border border-slate-200 bg-white p-10 text-center">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
    </article>
  );
}
