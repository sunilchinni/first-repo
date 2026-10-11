-- Create database
CREATE DATABASE IF NOT EXISTS farmer_market;
USE farmer_market;

-- Farmers table
CREATE TABLE IF NOT EXISTS farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20),
    farm_location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    unit VARCHAR(20) DEFAULT 'kg',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(120) NOT NULL,
    customer_address VARCHAR(255),
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Cart table (session-based)
CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Sample data
INSERT INTO farmers (name, email, phone, farm_location) VALUES
('John Smith', 'john@farm.com', '555-0101', 'Green Valley, CA'),
('Mary Johnson', 'mary@farm.com', '555-0102', 'Sunny Acres, TX'),
('David Brown', 'david@farm.com', '555-0103', 'River Bend, OR');

INSERT INTO products (farmer_id, name, description, category, price, quantity, unit) VALUES
(1, 'Organic Tomatoes', 'Fresh vine-ripened organic tomatoes', 'Vegetables', 3.50, 100, 'kg'),
(1, 'Sweet Corn', 'Golden sweet corn picked daily', 'Vegetables', 2.00, 150, 'dozen'),
(2, 'Free-Range Eggs', 'Farm fresh brown eggs', 'Dairy & Eggs', 5.00, 80, 'dozen'),
(2, 'Raw Honey', 'Pure unfiltered wildflower honey', 'Honey', 12.00, 40, 'jar'),
(3, 'Red Apples', 'Crisp organic red apples', 'Fruits', 4.25, 200, 'kg'),
(3, 'Fresh Strawberries', 'Sweet juicy strawberries', 'Fruits', 6.50, 60, 'box');
