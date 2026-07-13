import { Box, CircularProgress } from "@mui/material";
import type { PropsWithChildren } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

export function ProtectedRoute({ children }: PropsWithChildren) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
