FROM node:20-alpine AS base

WORKDIR /app

# Stage 1: Install dependencies
FROM base AS deps
COPY package*.json ./
RUN date > /tmp/buildtime.txt && npm install --omit=dev --no-cache

# Stage 2: Build
FROM base AS builder
ARG NEXT_PUBLIC_API_URL="https://lucid-serenity-production.up.railway.app"
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
COPY package*.json ./
RUN date > /tmp/buildtime.txt && npm install --no-cache
COPY . .
RUN mkdir -p public && touch public/.gitkeep
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

EXPOSE 8080

ENV PORT 8080
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
