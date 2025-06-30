FROM node:22-alpine
ARG GIT_REPO=https://github.com/iptv-org/epg.git
ARG GIT_BRANCH=master
ENV GZIP=false
ENV MAX_CONNECTIONS=1
ENV DAYS=14
ENV TIMEOUT=0
ENV CONFIG_DIR=/config

WORKDIR /app

RUN apk add curl git tzdata bash \
    && npm install express body-parser dotenv xml2js -g

RUN git clone --depth 1 -b $(echo "${GIT_BRANCH} ${GIT_REPO}") . \
    && npm install

RUN apk del git curl \
    && rm -rf /var/cache/apk/*

COPY epg-server.js .
EXPOSE 3000

CMD ["node", "epg-server.js"]