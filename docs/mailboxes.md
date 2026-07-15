# Mailboxes

IMAP mailboxes are managed from the frontend's `/mailboxes` page (add, edit,
remove, trigger a manual sync) - see `frontend/src/pages/MailAccountsPage.tsx`.
The "Email provider" picker fills in the IMAP host/port/SSL for common
providers (`frontend/src/constants/mailProviders.ts`); "Custom / other"
covers anything else.

Most providers connect with a normal password or app-specific password.
**Outlook.com/Hotmail/Live is the exception** - see below.

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

## Provider reference

| Provider | Auth | Notes |
| --- | --- | --- |
| Gmail (personal) | App password | <https://myaccount.google.com/apppasswords> |
| Outlook / Hotmail / Live | Sign in with Microsoft | see above |
| Yahoo Mail | App password | Yahoo Account Security |
| iCloud Mail | App-specific password | Apple ID account page |
| GMX | Password (enable IMAP first) | GMX Mail settings |
| WEB.DE | Password (enable IMAP first) | WEB.DE Mail settings |
| Custom / other | Password or app password | Any IMAP4rev1 server |
