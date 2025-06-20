FROM node:24-alpine AS builder

ARG WEBAPP_URL="https://gfts.developmentseed.org"
ARG MAPBOX_TOKEN=""

ENV NODE_ENV=production
ENV PUBLIC_URL=${WEBAPP_URL}
ENV DATA_API=${WEBAPP_URL}
ENV MAPBOX_TOKEN=${MAPBOX_TOKEN}

RUN apk add --no-cache git

WORKDIR /app
RUN git clone https://github.com/developmentseed/gfts.git /app
# RUN git checkout path-test
RUN corepack enable && \
    yarn install --frozen-lockfile

RUN yarn build
RUN cp ./dist/index.html ./dist/404.html

FROM nginx

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
