FROM node:20-alpine
RUN apk add --no-cache git
WORKDIR /app
RUN git clone https://github.com/developmentseed/gfts.git /app
RUN corepack enable
RUN yarn install
EXPOSE 9000
CMD ["yarn", "serve"]
