# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json vite.config.ts tsconfig.json index.html ./
RUN npm install
COPY src ./src
RUN npm run build

# Runtime stage with nginx
FROM nginx:1.25-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
HEALTHCHECK CMD wget -qO- http://localhost:8080/healthz || exit 1
CMD ["nginx", "-g", "daemon off;"]
