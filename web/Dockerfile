# Stage 1: Build static assets
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_CARTO_API_KEY=cb1_4vxo_1_10262ecdf4f01ddd335143ec
ARG VITE_API_URL=http://localhost:8000

ENV VITE_CARTO_API_KEY=$VITE_CARTO_API_KEY
ENV VITE_API_URL=$VITE_API_URL

COPY web/package.json ./
RUN npm install

COPY web/ ./
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY web/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
