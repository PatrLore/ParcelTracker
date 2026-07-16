# Mailboxes

IMAP mailboxes are managed from the frontend's `/mailboxes` page (add, edit,
remove, trigger a manual sync) - see `frontend/src/pages/MailAccountsPage.tsx`.
The "Email provider" picker fills in the IMAP host/port/SSL for common
providers (`frontend/src/constants/mailProviders.ts`); "Custom / other"
covers anything else.

Most providers connect with a normal password or app-specific password.
**Outlook.com/Hotmail/Live is the exception** - see below. Gmail also offers
an optional "Sign in with Google" alternative to an app password - see
further down.

## Why Outlook.com/Hotmail/Live needs a separate setup

Microsoft has retired plain-password ("Basic") IMAP authentication for
Outlook.com/Hotmail/Live accounts, including app passwords. This affects
every third-party mail client that connects over IMAP with a
username/password, not just Parcel Server. Only OAuth2 ("Modern
Authentication") is accepted now.

Because of that, mailboxes on this provider are connected through a
"Sign in with Microsoft" flow instead of a password field. Parcel Server
requests an OAuth2 access token from Microsoft and uses it for IMAP's
XOAUTH2 mechanism (`importer/imap_client.py`) instead of a plain
`LOGIN` - see `backend/app/services/oauth_microsoft.py`.

Gmail is **not** affected the same way: personal `@gmail.com` accounts still
support app passwords for IMAP as of this writing (the deprecation only hit
Google Workspace - business/education - accounts). Yahoo, iCloud, GMX and
WEB.DE are also unaffected.

## One-time setup: registering an Azure/Entra ID app

"Sign in with Microsoft" needs an app registration in Microsoft's identity
platform so it can ask Microsoft for permission on your behalf. This is a
one-time step done by whoever administers the Parcel Server instance (not
per mailbox) - it's free and takes a few minutes.

1. Go to <https://entra.microsoft.com> (or
   <https://portal.azure.com> → "Microsoft Entra ID") and sign in with any
   Microsoft account.
2. Navigate to **App registrations** → **New registration**.
3. Fill in:
   - **Name**: anything recognizable, e.g. "Parcel Server".
   - **Supported account types**: choose **"Personal Microsoft accounts
     only"** (this is what makes it work for Hotmail/Outlook.com/Live
     accounts specifically).
   - **Redirect URI**: leave empty. Parcel Server uses the OAuth2
     *device-code* flow, which needs no redirect URL - that's also why this
     works for a self-hosted server reachable at an arbitrary address
     without HTTPS.
4. Click **Register**. Copy the **Application (client) ID** shown on the
   overview page - you'll need it in step 6.
5. Under **Authentication**, scroll to **Advanced settings** and set
   **"Allow public client flows"** to **Yes**, then save. This lets the app
   use the device-code flow without a client secret.
6. Under **API permissions** → **Add a permission** → **APIs my
   organization uses** → search for **"Office 365 Exchange Online"** → pick
   **Delegated permissions** → check **`IMAP.AccessAsUser.All`**. Also make
   sure `offline_access` is present (it's added by default for most app
   registrations - if not, add it from **Microsoft Graph** → delegated
   permissions).
7. In `backend/config.yaml`, set:

   ```yaml
   microsoft_oauth:
     enabled: true
     client_id: "<the Application (client) ID from step 4>"
     tenant: "consumers"
   ```

8. Restart the backend so it picks up the new config.

## Connecting a Hotmail/Outlook.com/Live mailbox

1. Open `/mailboxes` → **Add mailbox**.
2. Pick **"Outlook / Hotmail / Live"** as the email provider.
3. Click **Sign in with Microsoft**. Parcel Server shows a short code and a
   link to `https://microsoft.com/devicelogin`.
4. Open that link (on any device - your phone works fine) and enter the
   code, then sign in with the Microsoft account you want to connect and
   approve the requested IMAP permission.
5. Back in Parcel Server, the dialog updates automatically once sign-in
   completes (it polls in the background - no need to refresh). Enter the
   mailbox's email address and adjust the folder/poll interval if needed,
   then **Save**.

No password is ever entered into Parcel Server for this provider - only the
resulting OAuth2 refresh token is stored (encrypted at rest, the same way
IMAP passwords are - see `app/core/crypto.py`), and it's redeemed for a
fresh access token before every sync.

### If sign-in expires or is revoked

Microsoft OAuth2 refresh tokens can be revoked (e.g. after a password
change, or extended inactivity). If a sync starts failing with a
"Microsoft sign-in has expired or was revoked" error, use the **Reconnect
Microsoft sign-in** action in the mailbox list - it repeats the same
device-code flow and replaces the stored token without recreating the
mailbox.

## Optional: "Sign in with Google" for Gmail

Unlike Outlook.com/Hotmail, a Gmail app password still works fine for IMAP -
there's no requirement to switch. "Sign in with Google" is offered as an
**alternative**, useful if you'd rather not generate an app password, or if
2-Step Verification isn't enabled on the account (a prerequisite for app
passwords, but not for this OAuth2 flow). Pick **"Gmail (Google Mail) -
Sign in with Google"** as the provider instead of the app-password entry to
use it.

Structurally this works exactly like the Microsoft flow above (a
device-code sign-in, no password ever entered into Parcel Server, a
"Reconnect Google sign-in" action if the token is later revoked) - see
`backend/app/services/oauth_google.py`. The one-time setup differs though,
since it goes through Google Cloud rather than Azure/Entra ID:

### One-time setup: registering a Google Cloud OAuth client

1. Go to <https://console.cloud.google.com/> and create a new project (or
   pick an existing one) - top left, next to the Google Cloud logo.
2. Go to **APIs & Services** → **OAuth consent screen**.
   - **User type**: **External** (this is what allows any Gmail account,
     not just ones inside a Google Workspace organization, to sign in).
   - Fill in the required app name/support email fields - anything
     recognizable, e.g. "Parcel Server".
   - Under **Scopes**, add `https://mail.google.com/` (full Gmail/IMAP
     access - there's no narrower IMAP-only scope).
   - Under **Test users**, add the Gmail address(es) you'll actually
     connect to Parcel Server.
   - **Leave the app in "Testing" publishing status.** Requesting
     `https://mail.google.com/` for a "Published"/production app requires
     Google's app verification process (a multi-week review, meant for
     public-facing apps) - staying in Testing with your own account(s)
     listed as test users skips that entirely and is the right choice for
     a self-hosted, personal-use server.
3. Go to **APIs & Services** → **Credentials** → **Create Credentials** →
   **OAuth client ID**.
   - **Application type**: **TVs and Limited Input devices**. This is the
     client type that supports the device-code flow Parcel Server uses.
   - Give it a name (e.g. "Parcel Server") and create it.
4. Copy the **Client ID** and **Client secret** shown - unlike Microsoft's
   flow, Google's device-code token exchange requires a client secret even
   for this "limited input device" client type.
5. In `backend/config.yaml`, set:

   ```yaml
   google_oauth:
     enabled: true
     client_id: "<the Client ID from step 4>"
     client_secret: "<the Client secret from step 4>"
   ```

6. Restart the backend so it picks up the new config.

Test users' refresh tokens keep working indefinitely in Testing mode -
there's no need to ever "publish" the app for personal use.

## Provider reference

| Provider | Auth | Notes |
| --- | --- | --- |
| Gmail (personal) | App password, or Sign in with Google | <https://myaccount.google.com/apppasswords> |
| Outlook / Hotmail / Live | Sign in with Microsoft | see above |
| Yahoo Mail | App password | Yahoo Account Security |
| iCloud Mail | App-specific password | Apple ID account page |
| GMX | Password (enable IMAP first) | GMX Mail settings |
| WEB.DE | Password (enable IMAP first) | WEB.DE Mail settings |
| Custom / other | Password or app password | Any IMAP4rev1 server |
