# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS deps
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:22-bookworm-slim AS build
WORKDIR /app/frontend

ARG VITE_GOVFLOW_API_BASE_URL
ARG VITE_GOVFLOW_APP_NAME
ARG VITE_GOVFLOW_ENV
ARG VITE_GOVFLOW_GRAPH_STREAM_PATH
ARG VITE_GOVFLOW_FEATURE_ASSISTANT
ARG VITE_GOVFLOW_FEATURE_WORKFLOW

ENV VITE_GOVFLOW_API_BASE_URL=${VITE_GOVFLOW_API_BASE_URL}
ENV VITE_GOVFLOW_APP_NAME=${VITE_GOVFLOW_APP_NAME}
ENV VITE_GOVFLOW_ENV=${VITE_GOVFLOW_ENV}
ENV VITE_GOVFLOW_GRAPH_STREAM_PATH=${VITE_GOVFLOW_GRAPH_STREAM_PATH}
ENV VITE_GOVFLOW_FEATURE_ASSISTANT=${VITE_GOVFLOW_FEATURE_ASSISTANT}
ENV VITE_GOVFLOW_FEATURE_WORKFLOW=${VITE_GOVFLOW_FEATURE_WORKFLOW}

COPY --from=deps /app/frontend/node_modules ./node_modules
COPY frontend/ .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime
WORKDIR /usr/share/nginx/html

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8080/health >/dev/null || exit 1
