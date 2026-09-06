#!/bin/sh
set -euo pipefail

# Public runtime configuration lets one built frontend image target a different
# backend host without rebuilding the JavaScript bundle.
node -e '
const fs = require("fs");
const apiUrl = process.env.RUNTIME_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
fs.mkdirSync("/app/public", { recursive: true });
fs.writeFileSync(
  "/app/public/runtime-config.js",
  `window.__FINSECAI_API_URL = ${JSON.stringify(apiUrl)};\n`,
);
console.log(`Generated /app/public/runtime-config.js with API_URL=${apiUrl}`);
'

exec "$@"
