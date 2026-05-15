# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS build
WORKDIR /app/frontend

ARG VITE_GOVFLOW_API_BASE_URL
ARG VITE_GOVFLOW_APP_NAME
ARG VITE_GOVFLOW_ENV

ENV VITE_GOVFLOW_API_BASE_URL=${VITE_GOVFLOW_API_BASE_URL}
ENV VITE_GOVFLOW_APP_NAME=${VITE_GOVFLOW_APP_NAME}
ENV VITE_GOVFLOW_ENV=${VITE_GOVFLOW_ENV}

COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
