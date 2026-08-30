FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY app/static /usr/share/nginx/html/static
COPY app/templates/index.html /usr/share/nginx/html/index.html

EXPOSE 80
