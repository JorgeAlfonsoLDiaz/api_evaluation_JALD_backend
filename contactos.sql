CREATE TABLE IF NOT EXISTS contactos (
    email TEXT PRIMARY KEY,
    nombre TEXT,
    telefono TEXT
);

INSERT INTO contactos (email, nombre, telefono)
VALUES ('juan@example.com', 'Juan Pérez', '555-123-4567');

INSERT INTO contactos (email, nombre, telefono)
VALUES ('maria@example.com', 'María García', '555-678-9012');


CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    token TEXT DEFAULT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiration_timestamp INTEGER
);

INSERT INTO users (username, password)
VALUES ('user1@example.com', '123456');

INSERT INTO users (username, password)
VALUES ('user2@example.com', '12345');
