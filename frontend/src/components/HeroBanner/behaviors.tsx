export interface HeroBannerProps {
  appName: string;
  signedInAs: string | null;
  onSignOut: () => void | Promise<void>;
}
