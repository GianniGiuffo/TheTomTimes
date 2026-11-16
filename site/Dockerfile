FROM ghcr.io/gohugoio/hugo:v0.163.3 AS build
WORKDIR /src
COPY . .
ENV HUGO_RESOURCEDIR=/tmp/hugo-resources
RUN hugo --minify --panicOnWarning --noBuildLock --destination /tmp/public

FROM nginx:1.31.8-alpine
COPY --from=build /tmp/public/ /usr/share/nginx/html/
