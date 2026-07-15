export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export type ShipmentStatus =
  | "unknown"
  | "label_created"
  | "in_transit"
  | "out_for_delivery"
  | "delivered"
  | "delayed"
  | "exception"
  | "returned";

export interface TrackingEvent {
  id: number;
  status: ShipmentStatus;
  description: string | null;
  location: string | null;
  occurred_at: string;
}

export interface Carrier {
  id: number;
  name: string;
  api_identifier: string | null;
  tracking_url_template: string | null;
  logo_url: string | null;
}

export interface Shipment {
  id: number;
  order_id: number | null;
  tracking_number: string;
  tracking_status: ShipmentStatus;
  ship_date: string | null;
  estimated_delivery_date: string | null;
  delivery_date: string | null;
  last_update: string | null;
  carrier: Carrier | null;
  tracking_events: TrackingEvent[];
}

export interface DashboardSummary {
  in_transit: number;
  delivered_today: number;
  expected_tomorrow: number;
  delayed: number;
  new_confirmations: number;
  recent_shipments: Shipment[];
}

export interface MonthlyCount {
  month: string;
  count: number;
}

export interface StatisticsSummary {
  parcels_per_month: MonthlyCount[];
  average_delivery_days: number | null;
  top_merchant: string | null;
  top_carrier: string | null;
  delayed_rate: number;
  success_rate: number | null;
  total_shipments: number;
}

export interface MailAccount {
  id: number;
  user_id: number;
  email_address: string;
  imap_host: string;
  imap_port: number;
  imap_username: string;
  use_ssl: boolean;
  folder: string;
  use_idle: boolean;
  poll_interval_seconds: number;
  is_active: boolean;
  last_seen_uid: number;
  last_synced_at: string | null;
  created_at: string;
}

export interface MailAccountInput {
  email_address: string;
  imap_host: string;
  imap_port: number;
  imap_username: string;
  password: string;
  use_ssl: boolean;
  folder: string;
  use_idle: boolean;
  poll_interval_seconds: number;
}

export interface MailAccountSyncResult {
  fetched_emails: number;
  matched_orders: number;
  created_shipments: number;
}
