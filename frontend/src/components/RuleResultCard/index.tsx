import { getAnalysisTypeClasses, getVerdictClasses, type RuleResultCardProps } from "./behaviors";


export function RuleResultCard({ item }: RuleResultCardProps) {
  return (
    <article className="rounded-[1.5rem] border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center gap-3">
        <h4 className="text-base font-semibold text-slate-950">{item.rule_name || item.rule_id}</h4>
        <span className={getAnalysisTypeClasses(item.analysis_type)}>{item.analysis_type}</span>
        <span className={getVerdictClasses(item.verdict)}>{item.verdict}</span>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
          {item.execution_status}
        </span>
        {item.matched_pages ? (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
            {item.matched_pages.length} page match{item.matched_pages.length === 1 ? "" : "es"}
          </span>
        ) : null}
      </div>

      <p className="mt-4 text-sm font-medium text-slate-900">{item.summary}</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">{item.reasoning}</p>

      {item.findings.length ? (
        <div className="mt-4">
          <h5 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Findings</h5>
          <ul className="mt-3 space-y-2">
            {item.findings.map((finding, index) => (
              <li key={`${item.rule_id}-finding-${index}`} className="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">
                {finding}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {item.citations.length ? (
        <div className="mt-4">
          <h5 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Citations</h5>
          <ul className="mt-3 space-y-2">
            {item.citations.map((citation, index) => (
              <li key={`${item.rule_id}-citation-${index}`} className="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">
                Page {citation.page}: {citation.evidence}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {item.notes.length ? (
        <div className="mt-4">
          <h5 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Notes</h5>
          <ul className="mt-3 space-y-2">
            {item.notes.map((note, index) => (
              <li key={`${item.rule_id}-note-${index}`} className="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">
                {note}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </article>
  );
}
