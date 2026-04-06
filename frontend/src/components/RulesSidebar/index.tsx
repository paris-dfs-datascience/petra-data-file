import { RuleSelectionCard } from "@/components/RuleSelectionCard";

import { getSelectAllLabel, getSelectionLabel, type RulesSidebarProps } from "./behaviors";


export function RulesSidebar({
  errorMessage,
  onRefresh,
  onRuleToggle,
  onSelectAll,
  rules,
  selectedRuleIds,
}: RulesSidebarProps) {
  const selectedCount = selectedRuleIds.length;

  return (
    <article className="section-panel p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Validation Rules</h2>
          <p className="mt-1 text-sm text-slate-500">Enable the rules you want to include in the analysis.</p>
        </div>

        <button
          className="rounded-full border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
          type="button"
          onClick={() => {
            void onRefresh();
          }}
        >
          Refresh
        </button>
      </div>

      <div className="mt-5 flex items-center justify-between rounded-[1.25rem] bg-slate-50 px-4 py-3">
        <p className="text-sm text-slate-500">
          <span className="font-semibold text-slate-900">{getSelectionLabel(selectedCount)}</span>
        </p>
        <button
          className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500"
          type="button"
          onClick={onSelectAll}
        >
          {getSelectAllLabel(selectedCount, rules.length)}
        </button>
      </div>

      <div className="pretty-scrollbar mt-5 max-h-[calc(100vh-20rem)] space-y-3 overflow-y-auto pr-1">
        {errorMessage ? <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</p> : null}

        {!rules.length && !errorMessage ? (
          <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500">No rules available.</p>
        ) : null}

        {rules.map((rule) => (
          <RuleSelectionCard
            key={rule.id}
            checked={selectedRuleIds.includes(rule.id)}
            rule={rule}
            onToggle={onRuleToggle}
          />
        ))}
      </div>
    </article>
  );
}
