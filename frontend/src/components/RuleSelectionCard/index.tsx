import { getCardClasses, getRuleTypeClasses, type RuleSelectionCardProps } from "./behaviors";


export function RuleSelectionCard({ checked, rule, onToggle }: RuleSelectionCardProps) {
  return (
    <label className={getCardClasses(checked)}>
      <div className="flex items-start gap-3">
        <div className="mt-0.5">
          <input checked={checked} className="peer sr-only" type="checkbox" onChange={() => onToggle(rule.id)} />
          <span className="flex h-5 w-5 items-center justify-center rounded-md border-2 border-slate-300 bg-white text-white transition peer-checked:border-teal-600 peer-checked:bg-teal-600 peer-focus-visible:ring-2 peer-focus-visible:ring-teal-500/30">
            <svg
              aria-hidden="true"
              className="h-3.5 w-3.5 opacity-0 transition peer-checked:opacity-100"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              viewBox="0 0 24 24"
            >
              <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900">{rule.name || rule.id}</h3>
            <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              {rule.severity || "rule"}
            </span>
            <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${getRuleTypeClasses(rule.analysis_type)}`}>
              {rule.analysis_type}
            </span>
          </div>

          <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-400">{rule.id}</p>
          <p className="mt-3 text-sm leading-6 text-slate-600">{rule.description || "No description available."}</p>
        </div>
      </div>
    </label>
  );
}
