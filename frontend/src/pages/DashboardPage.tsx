import AccessTimeIcon from "@mui/icons-material/AccessTime";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import MailIcon from "@mui/icons-material/MarkEmailUnread";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import {
  Alert,
  Box,
  CircularProgress,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { apiClient } from "../api/client";
import { ShipmentStatusChip } from "../components/ShipmentStatusChip";
import { StatCard } from "../components/StatCard";
import type { DashboardSummary } from "../types";

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<DashboardSummary>("/dashboard/summary")
      .then((response) => setSummary(response.data))
      .catch(() => setError("Could not load the dashboard summary."));
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
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Overview of your parcels and shipment confirmations.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <StatCard label="In transit" value={summary.in_transit} icon={<LocalShippingIcon />} color="primary" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <StatCard
            label="Delivered today"
            value={summary.delivered_today}
            icon={<CheckCircleIcon />}
            color="success"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <StatCard
            label="Expected tomorrow"
            value={summary.expected_tomorrow}
            icon={<AccessTimeIcon />}
            color="info"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <StatCard label="Delayed" value={summary.delayed} icon={<WarningAmberIcon />} color="warning" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <StatCard
            label="New confirmations"
            value={summary.new_confirmations}
            icon={<MailIcon />}
            color="secondary"
          />
        </Grid>
      </Grid>

      <Typography variant="h6" sx={{ fontWeight: 600 }} gutterBottom>
        Recent shipments
      </Typography>
      <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: "divider" }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Tracking number</TableCell>
              <TableCell>Carrier</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Estimated delivery</TableCell>
              <TableCell>Last update</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {summary.recent_shipments.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ color: "text.secondary", py: 4 }}>
                  No shipments yet.
                </TableCell>
              </TableRow>
            )}
            {summary.recent_shipments.map((shipment) => (
              <TableRow key={shipment.id} hover>
                <TableCell>{shipment.tracking_number}</TableCell>
                <TableCell>{shipment.carrier?.name ?? "—"}</TableCell>
                <TableCell>
                  <ShipmentStatusChip status={shipment.tracking_status} />
                </TableCell>
                <TableCell>{shipment.estimated_delivery_date ?? "—"}</TableCell>
                <TableCell>
                  {shipment.last_update ? new Date(shipment.last_update).toLocaleString() : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
