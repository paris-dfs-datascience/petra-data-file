import { useMemo, useState, type PropsWithChildren } from "react";

import { InteractionStatus } from "@azure/msal-browser";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";

import { signInWithMicrosoft } from "@/auth/client";


export function AuthGate({ children }: PropsWithChildren) {
  const isAuthenticated = useIsAuthenticated();
  const { accounts, inProgress } = useMsal();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const signedInLabel = useMemo(() => {
    const account = accounts[0];
    return account?.name || account?.username || null;
  }, [accounts]);

  const isWorking = inProgress !== InteractionStatus.None;

  const handleLogin = async () => {
    setErrorMessage(null);
    try {
      await signInWithMicrosoft();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Microsoft sign-in failed.");
    }
  };

  if (isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-8 sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[26rem] bg-aurora" />
      <div className="relative mx-auto flex min-h-[calc(100vh-4rem)] max-w-3xl items-center justify-center">
        <section className="glass-panel w-full overflow-hidden">
          <div className="px-6 py-8 lg:px-10">
            <p className="mb-3 inline-flex rounded-full bg-accentSoft px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-accent">
              Secure Access
            </p>
            <h1 className="max-w-2xl text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
              Petra Vision
            </h1>
            <p className="mt-4 text-sm leading-6 text-slate-600 sm:text-base">
              Sign in with your organization account to access the workspace, review rules, and upload documents.
            </p>

            <div className="mt-8 rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-panel">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-950">Access Required</p>
                  <p className="mt-1 text-sm text-slate-500">
                    Please continue with your organization account.
                  </p>
                  {signedInLabel ? (
                    <p className="mt-2 text-sm text-slate-500">Account detected: {signedInLabel}</p>
                  ) : null}
                </div>

                <button
                  className="cursor-pointer rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                  type="button"
                  onClick={() => {
                    void handleLogin();
                  }}
                  disabled={isWorking}
                >
                  {isWorking ? "Signing in..." : "Sign in with Microsoft"}
                </button>
              </div>

              {errorMessage ? (
                <p className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</p>
              ) : null}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
