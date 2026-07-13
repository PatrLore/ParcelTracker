import BarChartIcon from "@mui/icons-material/BarChart";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import DashboardIcon from "@mui/icons-material/Dashboard";
import LightModeIcon from "@mui/icons-material/LightMode";
import LogoutIcon from "@mui/icons-material/Logout";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import {
  AppBar,
  Box,
  Container,
  IconButton,
  Tab,
  Tabs,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import type { PropsWithChildren } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { useThemeMode } from "../contexts/ThemeModeContext";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: <DashboardIcon fontSize="small" /> },
  { path: "/statistics", label: "Statistics", icon: <BarChartIcon fontSize="small" /> },
];

export function AppLayout({ children }: PropsWithChildren) {
  const { mode, toggleMode } = useThemeMode();
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const activeTab = NAV_ITEMS.some((item) => item.path === location.pathname)
    ? location.pathname
    : false;

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar
        position="static"
        color="default"
        elevation={0}
        sx={{ borderBottom: 1, borderColor: "divider" }}
      >
        <Toolbar>
          <LocalShippingIcon sx={{ mr: 1.5 }} color="primary" />
          <Typography variant="h6" component="div" sx={{ fontWeight: 600, mr: 4 }}>
            Parcel Server
          </Typography>
          <Tabs
            value={activeTab}
            onChange={(_event, value) => navigate(value)}
            sx={{ flexGrow: 1, minHeight: 0 }}
            slotProps={{ indicator: { sx: { height: 2 } } }}
          >
            {NAV_ITEMS.map((item) => (
              <Tab
                key={item.path}
                value={item.path}
                label={item.label}
                icon={item.icon}
                iconPosition="start"
                sx={{ minHeight: 48 }}
              />
            ))}
          </Tabs>
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
