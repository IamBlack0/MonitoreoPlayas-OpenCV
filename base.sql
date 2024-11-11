-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS monitoreo_playa;
USE monitoreo_playa;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE images (
    id VARCHAR(50) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    location_name VARCHAR(255),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Tabla de segmentación
CREATE TABLE segmentations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_id VARCHAR(50),
    class_name VARCHAR(50),
    confidence FLOAT,
    FOREIGN KEY (image_id) REFERENCES images(id)
);

-- Tabla de turbidez
CREATE TABLE turbidity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_id VARCHAR(50),
    class_name VARCHAR(50),
    confidence FLOAT,
    crop_path VARCHAR(255),
    FOREIGN KEY (image_id) REFERENCES images(id)
);

-- Tabla de basura
CREATE TABLE trash (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_id VARCHAR(50),
    class_name VARCHAR(50),
    confidence FLOAT,
    location VARCHAR(100),
    FOREIGN KEY (image_id) REFERENCES images(id)
);

