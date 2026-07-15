import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
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
import type { MailAccount, MailAccountInput, MailAccountSyncResult } from "../types";

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

  function loadAccounts() {
    apiClient
      .get<MailAccount[]>("/mail-accounts")
      .then((response) => setAccounts(response.data))
      .catch(() => setError("Could not load mailboxes."));
  }

  useEffect(loadAccounts, []);

  function openAddDialog() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setProviderId(CUSTOM_PROVIDER_ID);
    setFormError(null);
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
    setDialogOpen(true);
  }

  function handleProviderChange(event: SelectChangeEvent) {
    const id = event.target.value;
    setProviderId(id);
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

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setIsSaving(true);
    try {
      if (editingId === null) {
        await apiClient.post("/mail-accounts", form);
        setNotice("Mailbox added.");
      } else {
        const { password, ...rest } = form;
        const payload = password ? { ...rest, password } : rest;
        await apiClient.patch(`/mail-accounts/${editingId}`, payload);
        setNotice("Mailbox updated.");
      }
      setDialogOpen(false);
      loadAccounts();
    } catch {
      setFormError("Could not save the mailbox. Check the IMAP details and try again.");
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
    } catch {
      setError(`Could not sync ${account.email_address} - check the mailbox is reachable.`);
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
                <TableCell colSpan={7} align="center" sx={{ color: "text.secondary", py: 4 }}>
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

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
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
                    <Link href={selectedPreset.appPasswordUrl} target="_blank" rel="noopener noreferrer">
                      Set one up here
                    </Link>
                  )}
                </Alert>
              )}

              <TextField
                label="Email address"
                type="email"
                value={form.email_address}
                onChange={(e) => setForm({ ...form, email_address: e.target.value })}
                required
                fullWidth
                disabled={editingId !== null}
              />
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
                label={editingId === null ? "Password / app password" : "New password (optional)"}
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required={editingId === null}
                fullWidth
                helperText={
                  editingId === null
                    ? "Many providers require an app password rather than your normal login " +
                      "password - see the hint above if you picked one"
                    : "Leave blank to keep the current password"
                }
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
              <Stack direction="row" spacing={3}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={form.use_ssl}
                      onChange={(e) => setForm({ ...form, use_ssl: e.target.checked })}
                    />
                  }
                  label="Use SSL"
                />
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
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={isSaving}>
              {isSaving ? "Saving…" : "Save"}
            </Button>
          </DialogActions>
        </Box>
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
