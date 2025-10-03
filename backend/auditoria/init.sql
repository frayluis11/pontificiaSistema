-- Script de inicialización para base de datos de auditoría
-- Este archivo se ejecuta automáticamente cuando se crea el contenedor MySQL

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS auditoria_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE auditoria_db;

-- Configuraciones de MySQL para mejor rendimiento con auditoría
SET GLOBAL innodb_buffer_pool_size = 256M;
SET GLOBAL innodb_log_file_size = 64M;
SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 2;

-- Configuraciones específicas para auditoría
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL sync_binlog = 0;

-- Crear usuario específico para auditoría si no existe
CREATE USER IF NOT EXISTS 'auditoria_user'@'%' IDENTIFIED BY 'auditoria_password';
GRANT ALL PRIVILEGES ON auditoria_db.* TO 'auditoria_user'@'%';

-- Permisos específicos para operaciones de auditoría
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON auditoria_db.* TO 'auditoria_user'@'%';

-- Aplicar cambios
FLUSH PRIVILEGES;

-- Configurar timezone
SET time_zone = '-05:00'; -- Colombia timezone

-- Mensaje de confirmación
SELECT 'Base de datos de auditoría inicializada correctamente' AS status;