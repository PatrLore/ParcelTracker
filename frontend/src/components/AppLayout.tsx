import BarChartIcon from "@mui/icons-material/BarChart";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import DashboardIcon from "@mui/icons-material/Dashboard";
import LightModeIcon from "@mui/icons-material/LightMode";
import LogoutIcon from "@mui/icons-material/Logout";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import MailIcon from "@mui/icons-material/MarkEmailUnread";
import MenuIcon from "@mui/icons-material/Menu";
import {
  AppBar,
  Box,
  Container,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tab,
  Tabs,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { type PropsWithChildren, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { useThemeMode } from "../contexts/ThemeModeContext";
import { UpdateCheckButton } from "./UpdateCheckButton";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: <DashboardIcon fontSize="small" /> },
  { path: "/statistics", label: "Statistics", icon: <BarChartIcon fontSize="small" /> },
  { path: "/mailboxes", label: "Mailboxes", icon: <MailIcon fontSize="small" /> },
];

export function AppLayout({ children }: PropsWithChildren) {
  const { mode, toggleMode } = useThemeMode();
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [drawerOpen, setDrawerOpen] = useState(false);

  const activeTab = NAV_ITEMS.some((item) => item.path === location.pathname)
    ? location.pathname
    : false;

  function goTo(path: string) {
    setDrawerOpen(false);
    navigate(path);
  }

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar
        position="static"
        color="default"
        elevation={0}
        sx={{ borderBottom: 1, borderColor: "divider" }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton
              edge="start"
              color="inherit"
              onClick={() => setDrawerOpen(true)}
              sx={{ mr: 1 }}
              aria-label="Open navigation menu"
            >
              <MenuIcon />
            </IconButton>
          )}
          <LocalShippingIcon
            sx={{ mr: 1.5, display: { xs: "none", sm: "inline-flex" } }}
            color="primary"
          />
          <Typography
            variant="h6"
            component="div"
            noWrap
            sx={{ fontWeight: 600, mr: { xs: 1, md: 4 }, flexGrow: { xs: 1, md: 0 } }}
          >
            Parcel Server
          </Typography>
          {!isMobile && (
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
          )}
          {user && !isMobile && (
            <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }} noWrap>
              {user.email}
            </Typography>
          )}
          <UpdateCheckButton />
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

      <Drawer anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <Box sx={{ width: 260 }} role="presentation">
          {user && (
            <>
              <Typography variant="body2" color="text.secondary" noWrap sx={{ p: 2 }}>
                {user.email}
              </Typography>
              <Divider />
            </>
          )}
          <List>
            {NAV_ITEMS.map((item) => (
              <ListItemButton
                key={item.path}
                selected={activeTab === item.path}
                onClick={() => goTo(item.path)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            ))}
          </List>
        </Box>
      </Drawer>

      <Container maxWidth="lg" sx={{ py: { xs: 2, sm: 4 } }}>
        {children}
      </Container>
    </Box>
  );
}
