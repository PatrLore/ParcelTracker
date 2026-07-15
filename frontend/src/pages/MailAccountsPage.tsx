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
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
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
} from "@mui/material";
import { type FormEvent, useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { CUSTOM_PROVIDER_ID, MAIL_PROVIDER_PRESETS } from "../constants/mailProviders";
import type {
  MailAccount,
  MailAccountInput,
  MailAccountSyncResult,
  MicrosoftOAuthFlowStart,
  MicrosoftOAuthFlowStatus,
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

type MicrosoftSignInStatus = "idle" | "starting" | "waiting" | "complete" | "error";

function errorDetail(err: unknown): string | undefined {
  const detail = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
  return typeof detail === "string" ? detail : undefined;
}

function MicrosoftDeviceCodePanel({
  status,
  flow,
  error,
  onStart,
}: {
  status: MicrosoftSignInStatus;
  flow: MicrosoftOAuthFlowStart | null;
  error: string | null;
  onStart: () => void;
}) {
  if (status === "idle") {
    return (
      <Button variant="outlined" startIcon={<LoginIcon />} onClick={onStart} fullWidth>
        Sign in with Microsoft
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
        <Alert severity="error">{error ?? "Microsoft sign-in failed."}</Alert>
        <Button variant="outlined" onClick={onStart}>
          Try again
        </Button>
      </Stack>
    );
  }

  if (status === "complete") {
    return <Alert severity="success">Signed in with Microsoft.</Alert>;
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

  const [msStatus, setMsStatus] = useState<MicrosoftSignInStatus>("idle");
  const [msFlow, setMsFlow] = useState<MicrosoftOAuthFlowStart | null>(null);
  const [msError, setMsError] = useState<string | null>(null);

  function loadAccounts() {
    apiClient
      .get<MailAccount[]>("/mail-accounts")
      .then((response) => setAccounts(response.data))
      .catch(() => setError("Could not load mailboxes."));
  }

  useEffect(loadAccounts, []);

  function resetMicrosoftSignIn() {
    setMsStatus("idle");
    setMsFlow(null);
    setMsError(null);
  }

  async function startMicrosoftSignIn() {
    setMsError(null);
    setMsStatus("starting");
    try {
      const { data } = await apiClient.post<MicrosoftOAuthFlowStart>(
        "/mail-accounts/oauth/microsoft/start",
      );
      setMsFlow(data);
      setMsStatus("waiting");
    } catch (err) {
      setMsStatus("error");
      setMsError(errorDetail(err) ?? "Could not start Microsoft sign-in.");
    }
  }

  // Polls the device-code flow while "waiting". A completed create-flow just
  // flips to "complete" so the dialog can reveal the rest of the form; a
  // completed reconnect-flow finishes the job itself (no extra fields to
  // collect) and closes its dialog.
  useEffect(() => {
    if (msStatus !== "waiting" || !msFlow) return undefined;

    const flowId = msFlow.flow_id;
    const id = window.setInterval(async () => {
      try {
        const { data } = await apiClient.get<MicrosoftOAuthFlowStatus>(
          `/mail-accounts/oauth/microsoft/poll/${flowId}`,
        );
        if (data.status !== "complete") return;

        if (reconnectTarget) {
          await apiClient.post(`/mail-accounts/${reconnectTarget.id}/oauth/microsoft/reconnect`, {
            flow_id: flowId,
          });
          setNotice(`Reconnected ${reconnectTarget.email_address}.`);
          setReconnectTarget(null);
          resetMicrosoftSignIn();
          loadAccounts();
        } else {
          setMsStatus("complete");
        }
      } catch (err) {
        setMsStatus("error");
        setMsError(errorDetail(err) ?? "Microsoft sign-in failed.");
      }
    }, msFlow.interval * 1000);

    return () => window.clearInterval(id);
  }, [msStatus, msFlow?.flow_id, reconnectTarget]);

  function openAddDialog() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setProviderId(CUSTOM_PROVIDER_ID);
    setFormError(null);
    resetMicrosoftSignIn();
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
    resetMicrosoftSignIn();
    setDialogOpen(true);
  }

  function closeDialog() {
    setDialogOpen(false);
    resetMicrosoftSignIn();
  }

  function openReconnectDialog(account: MailAccount) {
    setReconnectTarget(account);
    resetMicrosoftSignIn();
  }

  function closeReconnectDialog() {
    setReconnectTarget(null);
    resetMicrosoftSignIn();
  }

  function handleProviderChange(event: SelectChangeEvent) {
    const id = event.target.value;
    setProviderId(id);
    resetMicrosoftSignIn();
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
  const isOAuthCreate = editingId === null && selectedPreset?.authType === "oauth_microsoft";
  const editingAccount = editingId === null ? null : (accounts?.find((a) => a.id === editingId) ?? null);
  const isOAuthEdit = editingAccount?.auth_type === "oauth_microsoft";

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    if (isOAuthCreate && (!msFlow || msStatus !== "complete")) {
      setFormError("Finish signing in with Microsoft first.");
      return;
    }

    setIsSaving(true);
    try {
      if (isOAuthCreate && msFlow) {
        await apiClient.post("/mail-accounts/oauth/microsoft/finalize", {
          flow_id: msFlow.flow_id,
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
          alignItems: "flex-start",
          justifyContent: "space-between",
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
            {accounts.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ color: "text.secondary", py: 4 }}>
                  No mailboxes yet. Add one to start importing shipping confirmations.
                </TableCell>
              </TableRow>
            )}
            {accounts.map((account) => (
              <TableRow key={account.id} hover>
                <TableCell>{account.email_address}</TableCell>
                <TableCell>
                  {account.imap_host}:{account.imap_port}
                </TableCell>
                <TableCell>
                  <Chip
                    label={account.auth_type === "oauth_microsoft" ? "Microsoft" : "Password"}
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
                  {account.auth_type === "oauth_microsoft" && (
                    <Tooltip title="Reconnect Microsoft sign-in">
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
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={closeDialog} maxWidth="sm" fullWidth>
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

              {isOAuthCreate ? (
                <>
                  <MicrosoftDeviceCodePanel
                    status={msStatus}
                    flow={msFlow}
                    error={msError}
                    onStart={startMicrosoftSignIn}
                  />
                  {msStatus === "complete" && (
                    <>
                      <TextField
                        label="Email address"
                        type="email"
                        value={form.email_address}
                        onChange={(e) => setForm({ ...form, email_address: e.target.value })}
                        required
                        fullWidth
                      />
                      <Stack direction="row" spacing={2}>
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

                  {isOAuthEdit ? (
                    <Alert severity="info">
                      This mailbox uses Microsoft sign-in - use "Reconnect Microsoft sign-in" from
                      the mailbox list if access needs to be renewed.
                    </Alert>
                  ) : (
                    <>
                      <Stack direction="row" spacing={2}>
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
                          sx={{ width: 120 }}
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

                  <Stack direction="row" spacing={2}>
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
                  <Stack direction="row" spacing={3}>
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
              disabled={isSaving || (isOAuthCreate && msStatus !== "complete")}
            >
              {isSaving ? "Saving…" : "Save"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={reconnectTarget !== null} onClose={closeReconnectDialog} maxWidth="xs" fullWidth>
        <DialogTitle>Reconnect {reconnectTarget?.email_address}</DialogTitle>
        <DialogContent>
          <MicrosoftDeviceCodePanel
            status={msStatus}
            flow={msFlow}
            error={msError}
            onStart={startMicrosoftSignIn}
          />
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
