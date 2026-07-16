import AddIcon from "@mui/icons-material/Add";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import LoginIcon from "@mui/icons-material/Login";
import SyncIcon from "@mui/icons-material/Sync";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  Link,
  MenuItem,
  Paper,
  Select,
  type SelectChangeEvent,
  Snackbar,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { type FormEvent, useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { CUSTOM_PROVIDER_ID, MAIL_PROVIDER_PRESETS } from "../constants/mailProviders";
import type {
  MailAccount,
  MailAccountAuthType,
  MailAccountInput,
  MailAccountSyncResult,
  OAuthDeviceFlowStart,
  OAuthDeviceFlowStatus,
} from "../types";

const EMPTY_FORM: MailAccountInput = {
  email_address: "",
  imap_host: "",
  imap_port: 993,
  imap_username: "",
  password: "",
  use_ssl: true,
  folder: "INBOX",
  use_idle: false,
  poll_interval_seconds: 300,
};

type OAuthSignInStatus = "idle" | "starting" | "waiting" | "complete" | "error";

/** "microsoft" or "google" - matches the ``/mail-accounts/oauth/<name>/...``
 * endpoint path segment on the backend, so it doubles as the URL fragment. */
type OAuthProviderName = "microsoft" | "google";

const OAUTH_PROVIDER_LABEL: Record<OAuthProviderName, string> = {
  microsoft: "Microsoft",
  google: "Google",
};

function oauthProviderFromAuthType(
  authType: MailAccountAuthType | undefined,
): OAuthProviderName | null {
  if (authType === "oauth_microsoft") return "microsoft";
  if (authType === "oauth_google") return "google";
  return null;
}

function errorDetail(err: unknown): string | undefined {
  const detail = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
  return typeof detail === "string" ? detail : undefined;
}

function OAuthDeviceCodePanel({
  provider,
  status,
  flow,
  error,
  onStart,
}: {
  provider: OAuthProviderName;
  status: OAuthSignInStatus;
  flow: OAuthDeviceFlowStart | null;
  error: string | null;
  onStart: () => void;
}) {
  const providerLabel = OAUTH_PROVIDER_LABEL[provider];

  if (status === "idle") {
    return (
      <Button variant="outlined" startIcon={<LoginIcon />} onClick={onStart} fullWidth>
        Sign in with {providerLabel}
      </Button>
    );
  }

  if (status === "starting") {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (status === "error") {
    return (
      <Stack spacing={1.5}>
        <Alert severity="error">{error ?? `${providerLabel} sign-in failed.`}</Alert>
        <Button variant="outlined" onClick={onStart}>
          Try again
        </Button>
      </Stack>
    );
  }

  if (status === "complete") {
    return <Alert severity="success">Signed in with {providerLabel}.</Alert>;
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 1.5,
        textAlign: "center",
      }}
    >
      <Typography variant="body2">
        Go to{" "}
        <Link href={flow?.verification_uri} target="_blank" rel="noopener noreferrer">
          {flow?.verification_uri}
        </Link>{" "}
        and enter this code:
      </Typography>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
          px: 2,
          py: 1,
          bgcolor: "action.hover",
          borderRadius: 1,
          fontFamily: "monospace",
          fontSize: "1.25rem",
          letterSpacing: 2,
        }}
      >
        {flow?.user_code}
        <Tooltip title="Copy code">
          <IconButton
            size="small"
            onClick={() => flow && navigator.clipboard.writeText(flow.user_code)}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <CircularProgress size={16} />
        <Typography variant="body2" color="text.secondary">
          Waiting for you to finish signing in…
        </Typography>
      </Box>
    </Box>
  );
}

export function MailAccountsPage() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const [accounts, setAccounts] = useState<MailAccount[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<MailAccountInput>(EMPTY_FORM);
  const [providerId, setProviderId] = useState<string>(CUSTOM_PROVIDER_ID);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<MailAccount | null>(null);
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [reconnectTarget, setReconnectTarget] = useState<MailAccount | null>(null);

  const [oauthStatus, setOauthStatus] = useState<OAuthSignInStatus>("idle");
  const [oauthFlow, setOauthFlow] = useState<OAuthDeviceFlowStart | null>(null);
  const [oauthError, setOauthError] = useState<string | null>(null);

  function loadAccounts() {
    apiClient
      .get<MailAccount[]>("/mail-accounts")
      .then((response) => setAccounts(response.data))
      .catch(() => setError("Could not load mailboxes."));
  }

  useEffect(loadAccounts, []);

  function resetOAuthSignIn() {
    setOauthStatus("idle");
    setOauthFlow(null);
    setOauthError(null);
  }

  async function startOAuthSignIn(provider: OAuthProviderName) {
    setOauthError(null);
    setOauthStatus("starting");
    try {
      const { data } = await apiClient.post<OAuthDeviceFlowStart>(
        `/mail-accounts/oauth/${provider}/start`,
      );
      setOauthFlow(data);
      setOauthStatus("waiting");
    } catch (err) {
      setOauthStatus("error");
      setOauthError(errorDetail(err) ?? `Could not start ${OAUTH_PROVIDER_LABEL[provider]} sign-in.`);
    }
  }

  const createOAuthProvider = oauthProviderFromAuthType(
    MAIL_PROVIDER_PRESETS.find((p) => p.id === providerId)?.authType,
  );
  const reconnectProvider = oauthProviderFromAuthType(reconnectTarget?.auth_type);
  // Whichever OAuth panel is currently visible (add-dialog or reconnect-dialog).
  const activeOAuthProvider = reconnectTarget ? reconnectProvider : createOAuthProvider;

  // Polls the device-code flow while "waiting". A completed create-flow just
  // flips to "complete" so the dialog can reveal the rest of the form; a
  // completed reconnect-flow finishes the job itself (no extra fields to
  // collect) and closes its dialog.
  useEffect(() => {
    if (oauthStatus !== "waiting" || !oauthFlow || !activeOAuthProvider) return undefined;

    const flowId = oauthFlow.flow_id;
    const provider = activeOAuthProvider;
    const id = window.setInterval(async () => {
      try {
        const { data } = await apiClient.get<OAuthDeviceFlowStatus>(
          `/mail-accounts/oauth/${provider}/poll/${flowId}`,
        );
        if (data.status !== "complete") return;

        if (reconnectTarget) {
          await apiClient.post(`/mail-accounts/${reconnectTarget.id}/oauth/${provider}/reconnect`, {
            flow_id: flowId,
          });
          setNotice(`Reconnected ${reconnectTarget.email_address}.`);
          setReconnectTarget(null);
          resetOAuthSignIn();
          loadAccounts();
        } else {
          setOauthStatus("complete");
        }
      } catch (err) {
        setOauthStatus("error");
        setOauthError(errorDetail(err) ?? `${OAUTH_PROVIDER_LABEL[provider]} sign-in failed.`);
      }
    }, oauthFlow.interval * 1000);

    return () => window.clearInterval(id);
  }, [oauthStatus, oauthFlow?.flow_id, reconnectTarget, activeOAuthProvider]);

  function openAddDialog() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setProviderId(CUSTOM_PROVIDER_ID);
    setFormError(null);
    resetOAuthSignIn();
    setDialogOpen(true);
  }

  function openEditDialog(account: MailAccount) {
    setEditingId(account.id);
    setForm({
      email_address: account.email_address,
      imap_host: account.imap_host,
      imap_port: account.imap_port,
      imap_username: account.imap_username,
      password: "",
      use_ssl: account.use_ssl,
      folder: account.folder,
      use_idle: account.use_idle,
      poll_interval_seconds: account.poll_interval_seconds,
    });
    setProviderId(CUSTOM_PROVIDER_ID);
    setFormError(null);
    resetOAuthSignIn();
    setDialogOpen(true);
  }

  function closeDialog() {
    setDialogOpen(false);
    resetOAuthSignIn();
  }

  function openReconnectDialog(account: MailAccount) {
    setReconnectTarget(account);
    resetOAuthSignIn();
  }

  function closeReconnectDialog() {
    setReconnectTarget(null);
    resetOAuthSignIn();
  }

  function handleProviderChange(event: SelectChangeEvent) {
    const id = event.target.value;
    setProviderId(id);
    resetOAuthSignIn();
    const preset = MAIL_PROVIDER_PRESETS.find((p) => p.id === id);
    if (preset && preset.id !== CUSTOM_PROVIDER_ID) {
      setForm({
        ...form,
        imap_host: preset.imapHost,
        imap_port: preset.imapPort,
        use_ssl: preset.useSsl,
      });
    }
  }

  const selectedPreset = MAIL_PROVIDER_PRESETS.find((p) => p.id === providerId);
  const isOAuthCreate = editingId === null && createOAuthProvider !== null;
  const editingAccount = editingId === null ? null : (accounts?.find((a) => a.id === editingId) ?? null);
  const editOAuthProvider = oauthProviderFromAuthType(editingAccount?.auth_type);
  const isOAuthEdit = editOAuthProvider !== null;

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    if (isOAuthCreate && (!oauthFlow || oauthStatus !== "complete")) {
      setFormError(`Finish signing in with ${OAUTH_PROVIDER_LABEL[createOAuthProvider!]} first.`);
      return;
    }

    setIsSaving(true);
    try {
      if (isOAuthCreate && oauthFlow) {
        await apiClient.post(`/mail-accounts/oauth/${createOAuthProvider}/finalize`, {
          flow_id: oauthFlow.flow_id,
          email_address: form.email_address,
          folder: form.folder,
          use_idle: form.use_idle,
          poll_interval_seconds: form.poll_interval_seconds,
        });
        setNotice("Mailbox added.");
      } else if (editingId === null) {
        await apiClient.post("/mail-accounts", form);
        setNotice("Mailbox added.");
      } else {
        const { password, ...rest } = form;
        const payload = password ? { ...rest, password } : rest;
        await apiClient.patch(`/mail-accounts/${editingId}`, payload);
        setNotice("Mailbox updated.");
      }
      closeDialog();
      loadAccounts();
    } catch {
      setFormError("Could not save the mailbox. Check the details and try again.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await apiClient.delete(`/mail-accounts/${deleteTarget.id}`);
      setNotice("Mailbox removed.");
      setDeleteTarget(null);
      loadAccounts();
    } catch {
      setError("Could not remove the mailbox.");
      setDeleteTarget(null);
    }
  }

  async function handleSync(account: MailAccount) {
    setSyncingId(account.id);
    try {
      const { data } = await apiClient.post<MailAccountSyncResult>(
        `/mail-accounts/${account.id}/sync`,
      );
      setNotice(
        `Synced ${account.email_address}: ${data.fetched_emails} email(s), ` +
          `${data.matched_orders} order(s) matched, ${data.created_shipments} shipment(s) created.`,
      );
      loadAccounts();
    } catch (err) {
      setError(
        errorDetail(err) ??
          `Could not sync ${account.email_address} - check the mailbox is reachable.`,
      );
    } finally {
      setSyncingId(null);
    }
  }

  if (error && !accounts) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!accounts) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          flexDirection: { xs: "column", sm: "row" },
          alignItems: { xs: "stretch", sm: "flex-start" },
          justifyContent: "space-between",
          gap: 2,
          mb: 3,
        }}
      >
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }} gutterBottom>
            Mailboxes
          </Typography>
          <Typography variant="body1" color="text.secondary">
            IMAP mailboxes polled for shipping confirmations.
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openAddDialog}>
          Add mailbox
        </Button>
      </Box>

      {accounts.length === 0 && (
        <Paper
          elevation={0}
          sx={{ border: 1, borderColor: "divider", p: 4, textAlign: "center", color: "text.secondary" }}
        >
          No mailboxes yet. Add one to start importing shipping confirmations.
        </Paper>
      )}

      {accounts.length > 0 && isMobile && (
        <Stack spacing={2}>
          {accounts.map((account) => {
            const rowOAuthProvider = oauthProviderFromAuthType(account.auth_type);
            return (
              <Card key={account.id} elevation={0} sx={{ border: 1, borderColor: "divider" }}>
                <CardContent>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      gap: 1,
                    }}
                  >
                    <Typography sx={{ fontWeight: 600, wordBreak: "break-all" }}>
                      {account.email_address}
                    </Typography>
                    <Chip
                      label={account.is_active ? "Active" : "Inactive"}
                      color={account.is_active ? "success" : "default"}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ wordBreak: "break-all" }}>
                    {account.imap_host}:{account.imap_port}
                  </Typography>

                  <Stack direction="row" spacing={1} sx={{ mt: 1.5, flexWrap: "wrap", rowGap: 1 }}>
                    <Chip
                      label={rowOAuthProvider ? OAUTH_PROVIDER_LABEL[rowOAuthProvider] : "Password"}
                      size="small"
                      variant="outlined"
                    />
                    <Chip label={account.folder} size="small" variant="outlined" />
                    <Chip
                      label={`every ${account.poll_interval_seconds}s`}
                      size="small"
                      variant="outlined"
                    />
                  </Stack>

                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Last synced:{" "}
                    {account.last_synced_at
                      ? new Date(account.last_synced_at).toLocaleString()
                      : "Never"}
                  </Typography>

                  <Divider sx={{ my: 1.5 }} />

                  <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
                    <Tooltip title="Sync now">
                      <span>
                        <IconButton
                          onClick={() => handleSync(account)}
                          disabled={syncingId === account.id}
                        >
                          {syncingId === account.id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <SyncIcon fontSize="small" />
                          )}
                        </IconButton>
                      </span>
                    </Tooltip>
                    {rowOAuthProvider && (
                      <Tooltip title={`Reconnect ${OAUTH_PROVIDER_LABEL[rowOAuthProvider]} sign-in`}>
                        <IconButton onClick={() => openReconnectDialog(account)}>
                          <LoginIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Edit">
                      <IconButton onClick={() => openEditDialog(account)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Remove">
                      <IconButton onClick={() => setDeleteTarget(account)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}

      {accounts.length > 0 && !isMobile && (
        <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: "divider" }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Email address</TableCell>
                <TableCell>IMAP host</TableCell>
                <TableCell>Sign-in</TableCell>
                <TableCell>Folder</TableCell>
                <TableCell>Poll interval</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last synced</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {accounts.map((account) => {
                const rowOAuthProvider = oauthProviderFromAuthType(account.auth_type);
                return (
                  <TableRow key={account.id} hover>
                    <TableCell>{account.email_address}</TableCell>
                    <TableCell>
                      {account.imap_host}:{account.imap_port}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={rowOAuthProvider ? OAUTH_PROVIDER_LABEL[rowOAuthProvider] : "Password"}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{account.folder}</TableCell>
                    <TableCell>{account.poll_interval_seconds}s</TableCell>
                    <TableCell>
                      <Chip
                        label={account.is_active ? "Active" : "Inactive"}
                        color={account.is_active ? "success" : "default"}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {account.last_synced_at
                        ? new Date(account.last_synced_at).toLocaleString()
                        : "Never"}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Sync now">
                        <span>
                          <IconButton
                            size="small"
                            onClick={() => handleSync(account)}
                            disabled={syncingId === account.id}
                          >
                            {syncingId === account.id ? (
                              <CircularProgress size={18} />
                            ) : (
                              <SyncIcon fontSize="small" />
                            )}
                          </IconButton>
                        </span>
                      </Tooltip>
                      {rowOAuthProvider && (
                        <Tooltip
                          title={`Reconnect ${OAUTH_PROVIDER_LABEL[rowOAuthProvider]} sign-in`}
                        >
                          <IconButton size="small" onClick={() => openReconnectDialog(account)}>
                            <LoginIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => openEditDialog(account)}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Remove">
                        <IconButton size="small" onClick={() => setDeleteTarget(account)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog
        open={dialogOpen}
        onClose={closeDialog}
        maxWidth="sm"
        fullWidth
        fullScreen={isMobile}
      >
        <Box component="form" onSubmit={handleSave}>
          <DialogTitle>{editingId === null ? "Add mailbox" : "Edit mailbox"}</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              {formError && <Alert severity="error">{formError}</Alert>}

              {editingId === null && (
                <FormControl fullWidth>
                  <InputLabel id="mail-provider-label">Email provider</InputLabel>
                  <Select
                    labelId="mail-provider-label"
                    label="Email provider"
                    value={providerId}
                    onChange={handleProviderChange}
                  >
                    {MAIL_PROVIDER_PRESETS.map((preset) => (
                      <MenuItem key={preset.id} value={preset.id}>
                        {preset.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}

              {selectedPreset?.appPasswordHint && (
                <Alert severity="info">
                  {selectedPreset.appPasswordHint}{" "}
                  {selectedPreset.appPasswordUrl && (
                    <Link
                      href={selectedPreset.appPasswordUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Set one up here
                    </Link>
                  )}
                </Alert>
              )}

              {isOAuthCreate && createOAuthProvider ? (
                <>
                  <OAuthDeviceCodePanel
                    provider={createOAuthProvider}
                    status={oauthStatus}
                    flow={oauthFlow}
                    error={oauthError}
                    onStart={() => startOAuthSignIn(createOAuthProvider)}
                  />
                  {oauthStatus === "complete" && (
                    <>
                      <TextField
                        label="Email address"
                        type="email"
                        value={form.email_address}
                        onChange={(e) => setForm({ ...form, email_address: e.target.value })}
                        required
                        fullWidth
                      />
                      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                        <TextField
                          label="Folder"
                          value={form.folder}
                          onChange={(e) => setForm({ ...form, folder: e.target.value })}
                          fullWidth
                        />
                        <TextField
                          label="Poll interval (seconds)"
                          type="number"
                          value={form.poll_interval_seconds}
                          onChange={(e) =>
                            setForm({ ...form, poll_interval_seconds: Number(e.target.value) })
                          }
                          fullWidth
                        />
                      </Stack>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={form.use_idle}
                            onChange={(e) => setForm({ ...form, use_idle: e.target.checked })}
                          />
                        }
                        label="Use IMAP IDLE"
                      />
                    </>
                  )}
                </>
              ) : (
                <>
                  <TextField
                    label="Email address"
                    type="email"
                    value={form.email_address}
                    onChange={(e) => setForm({ ...form, email_address: e.target.value })}
                    required
                    fullWidth
                    disabled={editingId !== null}
                  />

                  {isOAuthEdit && editOAuthProvider ? (
                    <Alert severity="info">
                      This mailbox uses {OAUTH_PROVIDER_LABEL[editOAuthProvider]} sign-in - use
                      "Reconnect {OAUTH_PROVIDER_LABEL[editOAuthProvider]} sign-in" from the
                      mailbox list if access needs to be renewed.
                    </Alert>
                  ) : (
                    <>
                      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                        <TextField
                          label="IMAP host"
                          value={form.imap_host}
                          onChange={(e) => setForm({ ...form, imap_host: e.target.value })}
                          required
                          fullWidth
                          placeholder="imap.gmail.com"
                        />
                        <TextField
                          label="Port"
                          type="number"
                          value={form.imap_port}
                          onChange={(e) => setForm({ ...form, imap_port: Number(e.target.value) })}
                          required
                          sx={{ width: { xs: "100%", sm: 120 } }}
                        />
                      </Stack>
                      <TextField
                        label="IMAP username"
                        value={form.imap_username}
                        onChange={(e) => setForm({ ...form, imap_username: e.target.value })}
                        required
                        fullWidth
                        helperText="Usually the same as the email address"
                      />
                      <TextField
                        label={
                          editingId === null ? "Password / app password" : "New password (optional)"
                        }
                        type="password"
                        value={form.password}
                        onChange={(e) => setForm({ ...form, password: e.target.value })}
                        required={editingId === null}
                        fullWidth
                        helperText={
                          editingId === null
                            ? "Many providers require an app password rather than your normal " +
                              "login password - see the hint above if you picked one"
                            : "Leave blank to keep the current password"
                        }
                      />
                    </>
                  )}

                  <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                    <TextField
                      label="Folder"
                      value={form.folder}
                      onChange={(e) => setForm({ ...form, folder: e.target.value })}
                      fullWidth
                    />
                    <TextField
                      label="Poll interval (seconds)"
                      type="number"
                      value={form.poll_interval_seconds}
                      onChange={(e) =>
                        setForm({ ...form, poll_interval_seconds: Number(e.target.value) })
                      }
                      fullWidth
                    />
                  </Stack>
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={{ xs: 1, sm: 3 }}>
                    {!isOAuthEdit && (
                      <FormControlLabel
                        control={
                          <Switch
                            checked={form.use_ssl}
                            onChange={(e) => setForm({ ...form, use_ssl: e.target.checked })}
                          />
                        }
                        label="Use SSL"
                      />
                    )}
                    <FormControlLabel
                      control={
                        <Switch
                          checked={form.use_idle}
                          onChange={(e) => setForm({ ...form, use_idle: e.target.checked })}
                        />
                      }
                      label="Use IMAP IDLE"
                    />
                  </Stack>
                </>
              )}
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={closeDialog}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={isSaving || (isOAuthCreate && oauthStatus !== "complete")}
            >
              {isSaving ? "Saving…" : "Save"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={reconnectTarget !== null} onClose={closeReconnectDialog} maxWidth="xs" fullWidth>
        <DialogTitle>Reconnect {reconnectTarget?.email_address}</DialogTitle>
        <DialogContent>
          {reconnectProvider && (
            <OAuthDeviceCodePanel
              provider={reconnectProvider}
              status={oauthStatus}
              flow={oauthFlow}
              error={oauthError}
              onStart={() => startOAuthSignIn(reconnectProvider)}
            />
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={closeReconnectDialog}>Close</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={deleteTarget !== null} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Remove mailbox?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This stops polling {deleteTarget?.email_address} for new shipping confirmations.
            Orders and shipments already imported from it are kept.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Remove
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={notice !== null}
        autoHideDuration={5000}
        onClose={() => setNotice(null)}
        message={notice}
      />
      <Snackbar
        open={error !== null && accounts !== null}
        autoHideDuration={5000}
        onClose={() => setError(null)}
        message={error}
      />
    </Box>
  );
}
