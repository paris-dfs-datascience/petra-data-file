export interface HeroBannerProps {
  appName: string;
  authEnabled: boolean;
  signedInAs: string | null;
  onSignOut: () => void | Promise<void>;
}
