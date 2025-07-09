CREATE DATABASE attendancesystem;
 USE attendancesystem;
 
 CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  image_path VARCHAR(255)
);

 
 
 CREATE TABLE attendance (
id INT AUTO_INCREMENT PRIMARY KEY,
name VARCHAR(100),
day VARCHAR(20),
timestamp DATETIME,
status VARCHAR(50),
image_filename VARCHAR(255)
);

CREATE TABLE admins (
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(50) NOT NULL UNIQUE,
password VARCHAR(100) NOT NULL
);

