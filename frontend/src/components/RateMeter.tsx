import { Box, Typography, alpha, useTheme } from "@mui/material";

interface RateMeterProps {
  label: string;
  value: number | null;
  color: "success" | "warning";
}

export function RateMeter({ label, value, color }: RateMeterProps) {
  const theme = useTheme();
  const percent = value === null ? null : Math.round(value * 100);
  const trackColor = alpha(theme.palette[color].main, 0.15);

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {percent === null ? "—" : `${percent}%`}
        </Typography>
      </Box>
      <Box sx={{ height: 8, borderRadius: 4, bgcolor: trackColor, overflow: "hidden" }}>
        <Box
          sx={{
            height: "100%",
            borderRadius: 4,
            width: `${percent ?? 0}%`,
            bgcolor: `${color}.main`,
            transition: "width 0.3s",
          }}
        />
      </Box>
    </Box>
  );
}
