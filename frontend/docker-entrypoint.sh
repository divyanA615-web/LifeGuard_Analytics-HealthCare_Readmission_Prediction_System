#!/bin/sh
set -e

# Substitute environment variables in nginx.conf if VITE_API_BACKEND is set
if [ -n "$VITE_API_BACKEND" ]; then
  echo "Configuring nginx proxy to API backend: $VITE_API_BACKEND"
  # Replace the upstream URL in nginx.conf
  # We'll replace the line: proxy_pass https://${API_BACKEND};
  # with: proxy_pass http://backend:8080; (or whatever scheme/host provided)
  # Note: VITE_API_BACKEND should include scheme, e.g. http://backend:8080
  sed -i "s|proxy_pass https://\${API_BACKEND};|proxy_pass $VITE_API_BACKEND;|g" /etc/nginx/conf.d/default.conf
else
  echo "VITE_API_BACKEND not set; using default backend: http://backend:8080"
  sed -i "s|proxy_pass https://\${API_BACKEND};|proxy_pass http://backend:8080;|g" /etc/nginx/conf.d/default.conf
fi

# Start nginx
exec "$@"