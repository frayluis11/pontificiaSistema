-- Script de Verificación para Todas las Bases de Datos
-- Sistema Pontificia

-- ===== VERIFICACIÓN DE BASES DE DATOS =====

-- Conectar a cada base de datos y ejecutar estos comandos

-- 1. AUTH DATABASE (Puerto 3307)
-- mysql -h 127.0.0.1 -P 3307 -u root -p
USE auth_db;
SHOW TABLES;
SELECT 'AUTH DATABASE CONECTADA CORRECTAMENTE' as status;

-- 2. USERS DATABASE (Puerto 3308)
-- mysql -h 127.0.0.1 -P 3308 -u root -p
USE users_db;
SHOW TABLES;
SELECT 'USERS DATABASE CONECTADA CORRECTAMENTE' as status;

-- 3. ASISTENCIA DATABASE (Puerto 3309)
-- mysql -h 127.0.0.1 -P 3309 -u root -p
USE asistencia_db;
SHOW TABLES;
SELECT 'ASISTENCIA DATABASE CONECTADA CORRECTAMENTE' as status;

-- 4. DOCUMENTOS DATABASE (Puerto 3310)
-- mysql -h 127.0.0.1 -P 3310 -u root -p
USE documentos_db;
SHOW TABLES;
SELECT 'DOCUMENTOS DATABASE CONECTADA CORRECTAMENTE' as status;

-- 5. PAGOS DATABASE (Puerto 3311)
-- mysql -h 127.0.0.1 -P 3311 -u root -p
USE pagos_db;
SHOW TABLES;
SELECT 'PAGOS DATABASE CONECTADA CORRECTAMENTE' as status;

-- 6. REPORTES DATABASE (Puerto 3312)
-- mysql -h 127.0.0.1 -P 3312 -u root -p
USE reportes_db;
SHOW TABLES;
SELECT 'REPORTES DATABASE CONECTADA CORRECTAMENTE' as status;

-- 7. AUDITORIA DATABASE (Puerto 3313)
-- mysql -h 127.0.0.1 -P 3313 -u root -p
USE auditoria_db;
SHOW TABLES;
SELECT 'AUDITORIA DATABASE CONECTADA CORRECTAMENTE' as status;

-- ===== COMANDOS ÚTILES =====

-- Ver todas las bases de datos
SHOW DATABASES;

-- Ver información del servidor
SELECT VERSION() as mysql_version;
SELECT @@hostname as server_hostname;
SELECT @@port as server_port;

-- Ver variables del sistema
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';

-- Verificar usuarios
SELECT User, Host FROM mysql.user;

-- Ver el estado del servidor
SHOW STATUS LIKE 'Uptime';
SHOW STATUS LIKE 'Connections';
SHOW STATUS LIKE 'Threads_connected';