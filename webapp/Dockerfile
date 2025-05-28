FROM node:20-alpine

ARG WEBAPP_URL="https://gfts.developmentseed.org"
ARG MAPBOX_TOKEN=""

ENV NODE_ENV=production
ENV PUBLIC_URL=${WEBAPP_URL}
ENV DATA_API=${WEBAPP_URL}
ENV MAPBOX_TOKEN=${MAPBOX_TOKEN}

RUN apk add --no-cache git

WORKDIR /app
RUN git clone https://github.com/developmentseed/gfts.git /app
RUN git checkout path-test
RUN corepack enable && \
    yarn install --frozen-lockfile

RUN yarn add http-server

RUN yarn build

EXPOSE 9000

CMD ["npx", "http-server", "./dist", "-p", "9000", "--gzip"]
