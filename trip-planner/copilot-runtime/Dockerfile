# CopilotKit runtime (Option A backend) on a small Node image (Alpine)
FROM node:22-alpine

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY server.ts ./

EXPOSE 4000
CMD ["npm", "start"]
