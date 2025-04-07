FROM node:20-alpine
RUN apk add --no-cache git

WORKDIR /app
RUN git clone https://github.com/developmentseed/gfts.git /app
RUN corepack enable && \
    yarn install --frozen-lockfile
RUN yarn build

EXPOSE 9000
ENV NODE_ENV=production
ENV PUBLIC_URL=${WEBAPP_URL:-https://gfts.developmentseed.org}
ENV DATA_API=${WEBAPP_URL:-https://gfts.developmentseed.org}
ENV MAPBOX_TOKEN=${MAPBOX_TOKEN}

CMD ["yarn", "serve"]
