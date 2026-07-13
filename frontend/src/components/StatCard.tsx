import { Paper, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: number;
  icon: ReactNode;
  color: "primary" | "success" | "info" | "warning" | "secondary";
}

export function StatCard({ label, value, icon, color }: StatCardProps) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        border: 1,
        borderColor: "divider",
        display: "flex",
        alignItems: "center",
        gap: 2,
        height: "100%",
      }}
    >
      <Stack
        sx={{
          bgcolor: `${color}.main`,
          color: `${color}.contrastText`,
          borderRadius: 2,
          width: 48,
          height: 48,
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        {icon}
      </Stack>
      <Stack>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      </Stack>
    </Paper>
  );
}
