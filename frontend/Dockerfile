FROM node:20-alpine AS base

WORKDIR /app

# Stage 1: Install dependencies
FROM base AS deps
COPY package*.json ./
RUN npm install --omit=dev

# Stage 2: Build
FROM base AS builder
COPY package*.json ./
RUN npm install
COPY . .
RUN npx next build

# Stage 3: Production
FROM base AS runner
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
