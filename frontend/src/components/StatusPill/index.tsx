import { getStatusClasses, type StatusPillProps } from "./behaviors";


export function StatusPill({ status }: StatusPillProps) {
  return (
    <span className={getStatusClasses(status.tone)}>
      {status.isLoading ? (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : null}
      <span>{status.label}</span>
    </span>
  );
}
