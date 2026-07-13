# Parcel Server - Frontend

React + TypeScript + Vite + Material UI single-page app for Parcel Server.
See the root [`README.md`](../README.md) and
[`docs/development.md`](../docs/development.md) for the full picture.

## Scripts

- `npm run dev` - dev server with hot reload (proxies `/api` to `:8000`).
- `npm run build` - type-check (`tsc -b`) then production build.
- `npm run lint` - oxlint.
- `npm run preview` - preview the production build locally.

## Environment

- `VITE_API_BASE_URL` - overrides the API base URL used by the axios client
  (`src/api/client.ts`). Defaults to `/api/v1`, relying on the dev-server
  proxy or the Nginx reverse proxy in the production container.
