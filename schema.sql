CREATE TABLE Customers (
    Cro_id INT AUTO_INCREMENT PRIMARY KEY,  -- Auto-incrementing customer ID
    Name VARCHAR(50) NOT NULL,
    Device VARCHAR(50),
    Email VARCHAR(50),
    Tech_number INT NOT NULL
    Phone_number VARCHAR(15) NOT NULL,
    Fault VARCHAR(255),
    Comment VARCHAR(255),
    Physical_Address VARCHAR(100),
    Checked_in DATE NOT NULL,
);



CREATE TABLE Workshop (
    Diagnostic_id INT AUTO_INCREMENT PRIMARY KEY,
    Cro_id INT NOT NULL,
    Status ENUM('done', 'busy', 'pending') DEFAULT 'pending',
    Purchased_Items VARCHAR(255),
    Diagnostic VARCHAR(255) NULL,
    Checked_out DATE DEFAULT NULL,
    FOREIGN KEY (Cro_id) REFERENCES Customers(Cro_id) 
);


Create TABLE Technicians(
    Tech_number  INT AUTO_INCREMENT PRIMARY KEY
    Name VARCHAR(50) NOT NULL
    Surname VARCHAR(50) NOT NULL
    Email address VARCHAR(50) NOT NULL
    Phone number INTEGER NOT NULL
    Physical address  VARCHAR(255) NOT NULL
);

CREATE TABLE PSSWORDS(
    Tech_number INT NOT NULL
    password_hash VARCHAR(255) NOT NULL,
    FOREIGN KEY (Tech_number) REFERENCES Technicians(Tech_number)  
);
--when we crreeate a user for the database we create a password for them, we add a salt vaalue, hash it and then store it in the database
--the hashed value is stored in the database
--we need to changed bookin and add (technicians,passwords as tables in the database)