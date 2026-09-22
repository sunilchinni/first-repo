FROM httpd
EXPOSE 80
MAINTAINER Sunil
LABEL This is flight ticket booking application
COPY flight.html /usr/local/apache2/htdocs/
