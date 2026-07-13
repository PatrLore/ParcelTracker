import { Chip } from "@mui/material";

import type { ShipmentStatus } from "../types";

const STATUS_LABELS: Record<ShipmentStatus, string> = {
  unknown: "Unknown",
  label_created: "Label created",
  in_transit: "In transit",
  out_for_delivery: "Out for delivery",
  delivered: "Delivered",
  delayed: "Delayed",
  exception: "Exception",
  returned: "Returned",
};

const STATUS_COLORS: Record<ShipmentStatus, "default" | "info" | "success" | "warning" | "error"> = {
  unknown: "default",
  label_created: "info",
  in_transit: "info",
  out_for_delivery: "info",
  delivered: "success",
  delayed: "warning",
  exception: "error",
  returned: "default",
};

export function ShipmentStatusChip({ status }: { status: ShipmentStatus }) {
  return <Chip size="small" label={STATUS_LABELS[status]} color={STATUS_COLORS[status]} />;
}
