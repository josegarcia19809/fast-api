-- Base de datos para jugadores y clubes
CREATE DATABASE IF NOT EXISTS mundial_fifa_2026 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mundial_fifa_2026;

CREATE TABLE IF NOT EXISTS clubes (
    id_club INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(60) NOT NULL,
    liga VARCHAR(80) NOT NULL,
    estadio VARCHAR(100),
    anio_fundacion INT,
    UNIQUE KEY uq_clubes_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS jugadores (
    id_jugador INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL,
    apellido VARCHAR(60) NOT NULL,
    edad INT,
    nacionalidad VARCHAR(60),
    posicion VARCHAR(30),
    numero_camiseta INT,
    valor_mercado DECIMAL(12,2),
    altura DECIMAL(3,2),
    peso DECIMAL(5,2),
    pie_dominante VARCHAR(15),
    imagen VARCHAR(500),
    id_club INT NOT NULL,
    CONSTRAINT fk_jugadores_clubes FOREIGN KEY (id_club) REFERENCES clubes(id_club)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
