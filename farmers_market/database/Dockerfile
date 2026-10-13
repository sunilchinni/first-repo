FROM mysql:8.0

# Set environment variables
ENV MYSQL_ROOT_PASSWORD=Admin@123
ENV MYSQL_DATABASE=farmer_market
ENV MYSQL_USER=farmer_user
ENV MYSQL_PASSWORD=farmer_pass

# Copy initialization script
COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 3306

CMD ["mysqld"]
