# Minimal container for the optional document-reader bridge.
# Requires CHRONO_READER_BRIDGE_TOKEN to be supplied as a platform secret at runtime.
FROM node:22-slim

ENV NODE_ENV=production
ENV PORT=8080
WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev --ignore-scripts --no-audit --no-fund   && npm cache clean --force   && chown -R node:node /app

COPY --chown=node:node read-text-document.mjs read-office-document.mjs read-document.mjs server.mjs ./

USER node
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3   CMD node -e "fetch('http://127.0.0.1:8080/health').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"
CMD ["node", "server.mjs"]
