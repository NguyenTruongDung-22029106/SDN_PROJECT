FROM node:18
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production --no-audit --no-fund
COPY . .
EXPOSE 3001
CMD ["node", "gateway_node_server.js"]
