import type { WorkspaceShellProps } from "./behaviors";


export function WorkspaceShell({ hero, sidebar, main }: WorkspaceShellProps) {
  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-8 sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[26rem] bg-aurora" />
      <div className="relative mx-auto flex w-full max-w-7xl flex-col gap-6">
        {hero}
        <div className="grid gap-6 lg:grid-cols-[370px_minmax(0,1fr)]">
          <aside>{sidebar}</aside>
          <section>{main}</section>
        </div>
      </div>
    </main>
  );
}
