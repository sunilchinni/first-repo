FROM nginx
EXPOSE 80
MAINTAINER Sunil
LABEL This is Movie ticket booking application
COPY index.html /usr/share/nginx/html
