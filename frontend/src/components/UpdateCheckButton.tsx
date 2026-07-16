import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import SystemUpdateAltIcon from "@mui/icons-material/SystemUpdateAlt";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Link,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { apiClient } from "../api/client";
import type { VersionInfo } from "../types";

const UPDATE_COMMAND = "./scripts/update-server.sh";

function shortSha(sha: string | null): string {
  return sha ? sha.slice(0, 7) : "?";
}

export function UpdateCheckButton() {
  const [open, setOpen] = useState(false);
  const [info, setInfo] = useState<VersionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleOpen() {
    setOpen(true);
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<VersionInfo>("/system/version");
      setInfo(data);
    } catch {
      setError("Could not check for updates.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(UPDATE_COMMAND).then(() => setCopied(true));
  }

  return (
    <>
      <Tooltip title="Check for updates">
        <IconButton onClick={handleOpen} color="inherit">
          <SystemUpdateAltIcon />
        </IconButton>
      </Tooltip>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Updates</DialogTitle>
        <DialogContent>
          {isLoading && (
            <Box sx={{ display: "flex", justifyContent: "center", py: 3 }}>
              <CircularProgress size={28} />
            </Box>
          )}

          {!isLoading && error && <Alert severity="error">{error}</Alert>}

          {!isLoading && info && info.check_failed && (
            <Alert severity="warning">
              Could not reach GitHub to check for updates. Try again later.
            </Alert>
          )}

          {!isLoading && info && !info.check_failed && info.current_commit === null && (
            <Alert severity="info">
              Version info isn't available for this deployment - it was built without a
              <code> GIT_COMMIT</code> value. See "Checking for updates" in{" "}
              <code>docs/docker.md</code>.
            </Alert>
          )}

          {!isLoading &&
            info &&
            !info.check_failed &&
            info.current_commit !== null &&
            (info.update_available ? (
              <Stack spacing={2}>
                <Alert severity="info">A new version is available.</Alert>
                <Typography variant="body2" color="text.secondary">
                  Running <code>{shortSha(info.current_commit)}</code> · latest is{" "}
                  <code>{shortSha(info.latest_commit)}</code>
                </Typography>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    p: 1.5,
                    bgcolor: "action.hover",
                    borderRadius: 1,
                    fontFamily: "monospace",
                    fontSize: "0.85em",
                  }}
                >
                  <Box component="code" sx={{ flex: 1, wordBreak: "break-all" }}>
                    {UPDATE_COMMAND}
                  </Box>
                  <Tooltip title={copied ? "Copied!" : "Copy"}>
                    <IconButton size="small" onClick={handleCopy}>
                      <ContentCopyIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Run this on the server hosting Parcel Server (not from here - this
                  button only checks, it never updates anything by itself). Pulls the
                  latest code and rebuilds/restarts the Docker Compose stack - see
                  scripts/update-server.sh.
                </Typography>
                {info.compare_url && (
                  <Link href={info.compare_url} target="_blank" rel="noopener noreferrer">
                    View changes on GitHub <OpenInNewIcon sx={{ fontSize: 14, verticalAlign: "middle" }} />
                  </Link>
                )}
              </Stack>
            ) : (
              <Alert severity="success">
                You're running the latest version (<code>{shortSha(info.current_commit)}</code>).
              </Alert>
            ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
