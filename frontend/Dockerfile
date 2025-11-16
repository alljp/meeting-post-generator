# Multi-stage build for production-ready React application
FROM node:20-alpine as builder

# Accept build arguments for environment variables
# Railway will pass this as a build argument
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration as a template
# nginx:alpine processes .template files in /etc/nginx/templates/ and creates configs in /etc/nginx/conf.d/
# Note: envsubst only supports ${VAR} syntax, not ${VAR:-default}
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy entrypoint script to ensure PORT is set before envsubst processes the template
# This runs BEFORE script 20-envsubst-on-templates.sh processes the template
COPY entrypoint.sh /docker-entrypoint.d/10-set-port.sh
RUN chmod +x /docker-entrypoint.d/10-set-port.sh

# Copy healthcheck script
COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

# Expose port (Railway will set PORT dynamically)
EXPOSE 80

# Health check - uses Railway's PORT environment variable
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD /healthcheck.sh

# nginx's default entrypoint will:
# 1. Process /etc/nginx/templates/default.conf.template
# 2. Substitute ${PORT:-80} with Railway's PORT environment variable
# 3. Create /etc/nginx/conf.d/default.conf
# 4. Start nginx on the correct port

