CREATE TABLE clientes (
    id INT PRIMARY KEY,
    Type_document VARCHAR(10),
    Document VARCHAR(20),
    Name VARCHAR(100),
    Email VARCHAR(100),
    Phone VARCHAR(20),
    Adress VARCHAR(200),
    Whatsapp INT,
    Mail INT,
    Msgtext INT,
    `Call` INT,
    Observations VARCHAR(255),
    CustomerResponse INT,
    AnswerDate DATETIME NULL,
    UpdatedBy VARCHAR(100) NULL,
    Sign2 VARCHAR(100) NULL,
    createdAt DATETIME,
    updatedAt DATETIME
);


--Tablas del proceso
CREATE TABLE comparendos (
   id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
   codigo VARCHAR(10),
   descripcion VARCHAR(1000),
   estado BOOLEAN DEFAULT TRUE,
   fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE proceso_log (
   id INT AUTO_INCREMENT PRIMARY KEY,
   client_id INT,
   municipio VARCHAR(50),
   placa VARCHAR(20),
   documento VARCHAR(20),
   celular VARCHAR(20),
   numero_comparendo VARCHAR(100),
   codigo_comparendo VARCHAR(20),
   process_id VARCHAR(32),
   estado VARCHAR(20) DEFAULT 'pendiente',
   fecha DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE retoma_log (
   id INT AUTO_INCREMENT PRIMARY KEY,
   mes VARCHAR(7),
	`offset` INT,
   fecha DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE proceso_log ADD COLUMN fecha_comparendo VARCHAR AFTER numero_comparendo;