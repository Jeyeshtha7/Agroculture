CREATE DATABASE IF NOT EXISTS agroculture_project;
USE agroculture_project;

CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100)
);

CREATE TABLE buyers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100)
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    quantity VARCHAR(50),
    price DECIMAL(10, 2),
    description TEXT,
    farmer_id INT,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
);

CREATE TABLE  cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    buyer_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
