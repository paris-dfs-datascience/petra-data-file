import { useMsal } from "@azure/msal-react";

import { azurePostLogoutRedirectUri } from "@/auth/config";
import { ExtractionResults } from "@/components/ExtractionResults";
import { EmptyState } from "@/components/EmptyState";
import { HeroBanner } from "@/components/HeroBanner";
import { PageRuleResults } from "@/components/PageRuleResults";
import { RulesSidebar } from "@/components/RulesSidebar";
import { SourcePreview } from "@/components/SourcePreview";
import { TabNavigation } from "@/components/TabNavigation";
import { UploadPanel } from "@/components/UploadPanel";
import { WorkspaceShell } from "@/components/WorkspaceShell";

import { useAppBehavior } from "./behaviors";


export function App() {
  const { accounts, instance } = useMsal();
  const {
    activeTab,
    analysis,
    appName,
    availableRules,
    beginUpload,
    documentId,
    handleRuleToggle,
    handleSelectAllRules,
    handleStopAnalysis,
    isBusy,
    loadRules,
    pages,
    result,
    rulesError,
    selectedRuleIds,
    sourceFilename,
    sourcePreviewUrl,
    status,
    setNextTab,
  } = useAppBehavior();

  const signedInAccount = instance.getActiveAccount() || accounts[0] || null;
  const signedInAs = signedInAccount?.name || signedInAccount?.username || null;

  const handleSignOut = async () => {
    await instance.logoutPopup({
      account: signedInAccount || undefined,
      postLogoutRedirectUri: azurePostLogoutRedirectUri,
    });
  };

  return (
    <WorkspaceShell
      hero={<HeroBanner appName={appName} signedInAs={signedInAs} onSignOut={handleSignOut} />}
      sidebar={
        <RulesSidebar
          rules={availableRules}
          selectedRuleIds={selectedRuleIds}
          onRuleToggle={handleRuleToggle}
          onSelectAll={handleSelectAllRules}
          onRefresh={loadRules}
          errorMessage={rulesError}
        />
      }
      main={
        <div className="space-y-6">
          <UploadPanel
            documentId={documentId}
            isBusy={isBusy}
            status={status}
            onFileSelected={beginUpload}
            onStopAnalysis={handleStopAnalysis}
          />

          <section className="section-panel overflow-hidden">
            <TabNavigation activeTab={activeTab} onTabChange={setNextTab} />

            <div className="p-5">
              {activeTab === "source" ? (
                <SourcePreview previewUrl={sourcePreviewUrl} sourceFilename={result?.source_filename || sourceFilename} />
              ) : null}

              {activeTab === "extracted" ? <ExtractionResults pages={pages} /> : null}

              {activeTab === "text-analysis" ? (
                analysis ? (
                  <PageRuleResults
                    analysisType="text"
                    emptyMessage="No text rules were selected for this run."
                    items={analysis.text_page_results || []}
                  />
                ) : (
                  <EmptyState title="No text analysis yet" description="Upload a PDF to see text/content rule results." />
                )
              ) : null}

              {activeTab === "visual-analysis" ? (
                analysis ? (
                  <PageRuleResults
                    analysisType="vision"
                    emptyMessage="No visual rules were selected for this run."
                    items={analysis.visual_page_results || []}
                  />
                ) : (
                  <EmptyState title="No visual analysis yet" description="Upload a PDF to inspect visual-rule status." />
                )
              ) : null}
            </div>
          </section>
        </div>
      }
    />
  );
}
