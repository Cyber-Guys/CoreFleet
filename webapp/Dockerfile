# --- build stage ---
FROM node:20-alpine AS build

# The browser only talks to the webapp's origin and nginx forwards the calls.
# The default is the proxy path, so the bundle contains no backend host or IP.
ARG VITE_REPORT_API_URL=/report-api
ENV VITE_REPORT_API_URL=$VITE_REPORT_API_URL

WORKDIR /app
COPY package.json package-lock.json* ./
# use ci when a lockfile is present, fall back to install otherwise
RUN npm ci 2>/dev/null || npm install
COPY . .
RUN npm run build

# --- serve stage ---
FROM nginx:1.27-alpine AS serve

# Upstreams (overridable for a distributed deployment). The nginx image runs
# envsubst over templates at startup.
ENV REPORT_SERVICE_URL=http://fleet-report:8080
ENV ZENOH_REST_URL=http://zenoh-router:8000

COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
