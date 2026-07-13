import AccessTimeIcon from "@mui/icons-material/AccessTime";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import StorefrontIcon from "@mui/icons-material/Storefront";
import {
  Alert,
  Box,
  CircularProgress,
  Grid,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { MonthlyParcelsChart } from "../components/MonthlyParcelsChart";
import { RateMeter } from "../components/RateMeter";
import { StatCard } from "../components/StatCard";
import type { StatisticsSummary } from "../types";

export function StatisticsPage() {
  const [summary, setSummary] = useState<StatisticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<StatisticsSummary>("/statistics/summary")
      .then((response) => setSummary(response.data))
      .catch(() => setError("Could not load statistics."));
  }, []);

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!summary) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700 }} gutterBottom>
        Statistics
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        How your parcels have moved over the last {summary.parcels_per_month.length} months.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            label="Total shipments"
            value={summary.total_shipments}
            icon={<LocalShippingIcon />}
            color="primary"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            label="Avg. delivery time"
            value={
              summary.average_delivery_days === null
                ? "—"
                : `${summary.average_delivery_days} d`
            }
            icon={<AccessTimeIcon />}
            color="info"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            label="Top merchant"
            value={summary.top_merchant ?? "—"}
            icon={<StorefrontIcon />}
            color="secondary"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            label="Top carrier"
            value={summary.top_carrier ?? "—"}
            icon={<Inventory2Icon />}
            color="secondary"
          />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper elevation={0} sx={{ p: 2.5, border: 1, borderColor: "divider", height: "100%" }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Parcels per month
            </Typography>
            <MonthlyParcelsChart data={summary.parcels_per_month} />
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper elevation={0} sx={{ p: 2.5, border: 1, borderColor: "divider", height: "100%" }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Delivery outcomes
            </Typography>
            <Stack spacing={3}>
              <RateMeter label="Success rate" value={summary.success_rate} color="success" />
              <RateMeter label="Delayed rate" value={summary.delayed_rate} color="warning" />
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
