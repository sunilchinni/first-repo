FROM nginx
EXPOSE 80
MAINTAINER Sunil
LABEL This is flight ticket booking application
COPY flight.html /usr/share/nginx/html
