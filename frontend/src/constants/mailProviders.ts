export interface MailProviderPreset {
  id: string;
  label: string;
  imapHost: string;
  imapPort: number;
  useSsl: boolean;
  /** Shown as a hint when selected - most major providers require an
   * app-specific password for IMAP rather than the normal account
   * password once two-factor authentication is enabled. */
  appPasswordHint?: string;
  appPasswordUrl?: string;
  /** "oauth_microsoft"/"oauth_google" providers show a "Sign in with ..."
   * device-code flow instead of a password field. Mandatory for
   * "oauth_microsoft" (Microsoft retired plain-password IMAP login for
   * these accounts); just an alternative to an app password for
   * "oauth_google". See docs/mailboxes.md. */
  authType?: "password" | "oauth_microsoft" | "oauth_google";
}

export const CUSTOM_PROVIDER_ID = "custom";

export const MAIL_PROVIDER_PRESETS: MailProviderPreset[] = [
  { id: CUSTOM_PROVIDER_ID, label: "Custom / other", imapHost: "", imapPort: 993, useSsl: true },
  {
    id: "gmail",
    label: "Gmail (Google Mail) - App password",
    imapHost: "imap.gmail.com",
    imapPort: 993,
    useSsl: true,
    appPasswordHint: "Requires a Google App Password, not your normal login password.",
    appPasswordUrl: "https://myaccount.google.com/apppasswords",
  },
  {
    id: "gmail_oauth",
    label: "Gmail (Google Mail) - Sign in with Google",
    imapHost: "imap.gmail.com",
    imapPort: 993,
    useSsl: true,
    authType: "oauth_google",
  },
  {
    id: "outlook",
    label: "Outlook / Hotmail / Live",
    imapHost: "outlook.office365.com",
    imapPort: 993,
    useSsl: true,
    authType: "oauth_microsoft",
    appPasswordHint:
      "Microsoft retired plain-password IMAP access for these accounts - sign in with your " +
      "Microsoft account instead, below.",
  },
  {
    id: "yahoo",
    label: "Yahoo Mail",
    imapHost: "imap.mail.yahoo.com",
    imapPort: 993,
    useSsl: true,
    appPasswordHint: "Requires a Yahoo App Password, generated in Yahoo Account Security.",
    appPasswordUrl: "https://login.yahoo.com/myaccount/security",
  },
  {
    id: "icloud",
    label: "iCloud Mail",
    imapHost: "imap.mail.me.com",
    imapPort: 993,
    useSsl: true,
    appPasswordHint: "Requires an app-specific password from your Apple ID account page.",
    appPasswordUrl: "https://appleid.apple.com/account/manage",
  },
  {
    id: "gmx",
    label: "GMX",
    imapHost: "imap.gmx.net",
    imapPort: 993,
    useSsl: true,
    appPasswordHint: "Make sure IMAP access is enabled under GMX Mail settings first.",
  },
  {
    id: "web.de",
    label: "WEB.DE",
    imapHost: "imap.web.de",
    imapPort: 993,
    useSsl: true,
    appPasswordHint: "Make sure IMAP access is enabled under WEB.DE Mail settings first.",
  },
];
