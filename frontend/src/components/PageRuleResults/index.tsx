import { EmptyState } from "@/components/EmptyState";
import { RuleResultCard } from "@/components/RuleResultCard";

import { getPageResultsHeading, groupItemsByPage, type PageRuleResultsProps } from "./behaviors";


export function PageRuleResults({ analysisType, emptyMessage, items, documentId, sourceFilename }: PageRuleResultsProps) {
  if (!items.length) {
    return (
      <article className="rounded-[1.5rem] border border-slate-200 bg-white p-5 text-sm text-slate-500">
        {emptyMessage}
      </article>
    );
  }

  const groups = groupItemsByPage(items);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-950">{getPageResultsHeading(analysisType)}</h3>
        <span className="text-sm text-slate-500">{items.length} page-rule result(s)</span>
      </div>

      {groups.map((group) => (
        <section key={`${analysisType}-page-${group.page}`} className="rounded-[1.5rem] border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between gap-3 border-b border-slate-200 pb-4">
            <h4 className="text-base font-semibold text-slate-950">Page {group.page}</h4>
            <span className="text-sm text-slate-500">{group.items.length} rule result(s)</span>
          </div>

          <div className="mt-4 space-y-4">
            {group.items.map((item) => (
              <RuleResultCard
                key={`${analysisType}-${group.page}-${item.rule_id}`}
                item={item}
                documentId={documentId}
                sourceFilename={sourceFilename}
              />
            ))}
          </div>
        </section>
      ))}
    </section>
  );
}
