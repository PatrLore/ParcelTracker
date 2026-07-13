import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import LogoutIcon from "@mui/icons-material/Logout";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import {
  AppBar,
  Box,
  Container,
  IconButton,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import type { PropsWithChildren } from "react";

import { useAuth } from "../contexts/AuthContext";
import { useThemeMode } from "../contexts/ThemeModeContext";

export function AppLayout({ children }: PropsWithChildren) {
  const { mode, toggleMode } = useThemeMode();
  const { user, logout } = useAuth();

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar position="static" color="default" elevation={0} sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Toolbar>
          <LocalShippingIcon sx={{ mr: 1.5 }} color="primary" />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            Parcel Server
          </Typography>
          {user && (
            <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
              {user.email}
            </Typography>
          )}
          <Tooltip title={mode === "dark" ? "Switch to light mode" : "Switch to dark mode"}>
            <IconButton onClick={toggleMode} color="inherit">
              {mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Sign out">
            <IconButton onClick={logout} color="inherit">
              <LogoutIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {children}
      </Container>
    </Box>
  );
}
