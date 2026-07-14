/**
 * Parcel Server Lovelace card - a HACS "plugin" resource distributed
 * separately from the custom_components/parcel_server/ integration (see
 * integrations/home_assistant/README.md). Deliberately dependency-free
 * (no lit/build step) - a single native Web Component that reads the
 * five sensors the integration creates and renders them as one card,
 * using Home Assistant's own <ha-card>/<ha-icon> elements so it inherits
 * the active theme automatically.
 */

const DEFAULT_ENTITY_PREFIX = "sensor.parcel_server_";

function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function formatDate(hass, isoDate) {
  if (!isoDate) return null;
  try {
    return new Date(`${isoDate}T00:00:00`).toLocaleDateString(hass.locale?.language || undefined, {
      month: "short",
      day: "numeric",
    });
  } catch {
    return isoDate;
  }
}

class ParcelServerCard extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    if (!config) {
      throw new Error("Invalid configuration: config is required");
    }
    this._config = {
      title: "Parcel Server",
      entity_prefix: DEFAULT_ENTITY_PREFIX,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return { type: "custom:parcel-server-card" };
  }

  _entity(key) {
    if (!this._hass) return undefined;
    const explicit = this._config[`entity_${key}`];
    const entityId = explicit || `${this._config.entity_prefix}${key}`;
    return this._hass.states[entityId];
  }

  _render() {
    if (!this._hass || !this._config) return;

    const active = this._entity("active_parcels");
    const next = this._entity("next_delivery");
    const last = this._entity("last_delivery");
    const merchant = this._entity("top_merchant");
    const carrier = this._entity("top_carrier");

    if (!active && !next && !last && !merchant && !carrier) {
      this._root.innerHTML = `
        <style>${this._css()}</style>
        <ha-card>
          <div class="warning">
            No Parcel Server sensors found. Set up the Parcel Server integration
            first, or override entity IDs in the card configuration
            (entity_active_parcels, entity_next_delivery, entity_last_delivery,
            entity_top_merchant, entity_top_carrier).
          </div>
        </ha-card>
      `;
      return;
    }

    const activeVal = active && active.state !== "unavailable" ? active.state : "-";
    const inTransit = active?.attributes?.in_transit ?? "-";
    const delayed = active?.attributes?.delayed ?? "-";
    const newConf = active?.attributes?.new_confirmations ?? "-";

    this._root.innerHTML = `
      <style>${this._css()}</style>
      <ha-card>
        <div class="header">
          <ha-icon icon="mdi:package-variant-closed"></ha-icon>
          <span class="title">${esc(this._config.title)}</span>
          <span class="active-count">${esc(activeVal)}</span>
        </div>

        <div class="breakdown">
          <span><ha-icon icon="mdi:truck-delivery-outline"></ha-icon>${esc(inTransit)} in transit</span>
          <span><ha-icon icon="mdi:clock-alert-outline"></ha-icon>${esc(delayed)} delayed</span>
          <span><ha-icon icon="mdi:new-box"></ha-icon>${esc(newConf)} new</span>
        </div>

        <div class="divider"></div>

        ${this._deliveryRow("mdi:truck-delivery-outline", "Next delivery", next)}
        ${this._deliveryRow("mdi:package-variant", "Last delivery", last)}

        <div class="divider"></div>

        <div class="footer">
          <span><ha-icon icon="mdi:storefront-outline"></ha-icon>${esc(this._stateOrDash(merchant))}</span>
          <span><ha-icon icon="mdi:truck-outline"></ha-icon>${esc(this._stateOrDash(carrier))}</span>
        </div>
      </ha-card>
    `;
  }

  _stateOrDash(entity) {
    if (!entity || entity.state === "unknown" || entity.state === "unavailable" || !entity.state) {
      return "-";
    }
    return entity.state;
  }

  _deliveryRow(icon, label, entity) {
    const date = entity && entity.state !== "unknown" && entity.state !== "unavailable"
      ? formatDate(this._hass, entity.state)
      : null;
    if (!date) {
      return `
        <div class="delivery-row">
          <ha-icon icon="${icon}"></ha-icon>
          <div class="delivery-text">
            <div class="delivery-label">${esc(label)}</div>
            <div class="delivery-detail muted">No data</div>
          </div>
        </div>
      `;
    }
    const merchant = entity.attributes?.merchant;
    const carrier = entity.attributes?.carrier;
    const detailParts = [merchant, carrier].filter(Boolean);
    const detail = detailParts.length ? detailParts.join(" via ") : "";

    return `
      <div class="delivery-row">
        <ha-icon icon="${icon}"></ha-icon>
        <div class="delivery-text">
          <div class="delivery-label">${esc(label)}</div>
          <div class="delivery-detail">${esc(date)}${detail ? ` &middot; ${esc(detail)}` : ""}</div>
        </div>
      </div>
    `;
  }

  _css() {
    return `
      ha-card {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }
      .warning {
        color: var(--warning-color, #ff9800);
        font-size: 0.9em;
      }
      .header {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .header .title {
        font-size: 1.2em;
        font-weight: 500;
        color: var(--primary-text-color);
        flex: 1;
      }
      .header ha-icon {
        color: var(--primary-color);
      }
      .active-count {
        font-size: 1.3em;
        font-weight: 600;
        color: var(--primary-color);
        background: var(--secondary-background-color);
        border-radius: 12px;
        padding: 2px 10px;
      }
      .breakdown {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }
      .breakdown span {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .breakdown ha-icon {
        --mdc-icon-size: 16px;
      }
      .divider {
        height: 1px;
        background: var(--divider-color);
      }
      .delivery-row {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      .delivery-row ha-icon {
        color: var(--primary-color);
      }
      .delivery-label {
        font-size: 0.8em;
        color: var(--secondary-text-color);
      }
      .delivery-detail {
        font-size: 0.95em;
        color: var(--primary-text-color);
      }
      .delivery-detail.muted {
        color: var(--secondary-text-color);
      }
      .footer {
        display: flex;
        justify-content: space-between;
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }
      .footer span {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .footer ha-icon {
        --mdc-icon-size: 16px;
      }
    `;
  }
}

customElements.define("parcel-server-card", ParcelServerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "parcel-server-card",
  name: "Parcel Server Card",
  description: "Active parcels, next/last delivery, and top merchant/carrier from the Parcel Server integration.",
  preview: false,
});
