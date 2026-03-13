# ---- Build stage ----
# Build context: project root (DUANGO/)
FROM node:18-alpine AS builder

RUN corepack enable && corepack prepare pnpm@8.14.0 --activate

WORKDIR /app/GoWeb

# Copy GoWeb package manifests
COPY Goweb/package.json Goweb/pnpm-lock.yaml Goweb/pnpm-workspace.yaml Goweb/.npmrc ./
COPY Goweb/packages/ packages/
COPY Goweb/docs/package.json docs/
COPY Goweb/build/ build/

RUN pnpm install --frozen-lockfile --ignore-scripts

# Copy GoWeb source + nginx config
COPY Goweb/docs/ docs/
COPY Goweb/GoWeb.nginx.conf /app/GoWeb.nginx.conf

# Copy shared resources (../../../../shared/lang/ relative to docs/src/language/)
COPY shared/ /app/shared/

# Build JS/CSS only — skip vue-tsc type declarations
RUN pnpm -C packages/icons build && \
    (pnpm -C packages/layer build || true) && \
    cd packages/layui && pnpm run build:all && pnpm run build:es && pnpm run build:umd && \
    cd /app/GoWeb && pnpm build:docs

# ---- Runtime stage ----
FROM nginx:alpine

COPY --from=builder /app/GoWeb/docs/dist /usr/share/nginx/html
COPY --from=builder /app/GoWeb.nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
