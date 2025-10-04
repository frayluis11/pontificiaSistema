# Configuraciones de MySQL Workbench para Sistema Pontificia
# Importar estas conexiones manualmente en MySQL Workbench

# ===== CONEXIONES PARA MYSQL WORKBENCH =====

## 1. AUTH DATABASE (Puerto 3307)
Connection Name: Sistema_Pontificia_AUTH
Connection Method: Standard (TCP/IP)
Hostname: 127.0.0.1
Port: 3307
Username: root
Password: root
Default Schema: auth_db

## 2. USERS DATABASE (Puerto 3308)
Connection Name: Sistema_Pontificia_USERS
Connection Method: Standard (TCP/IP)
Hostname: 127.0.0.1
Port: 3308
Username: root
Password: root
Default Schema: users_db

## 3. ASISTENCIA DATABASE (Puerto 3309)
Connection Name: Sistema_Pontificia_ASISTENCIA
Connection Method: Standard (TCP/IP)
Hostname: 127.0.0.1
Port: 3309
Username: root
Password: root
Default Schema: asistencia_db

## 4. DOCUMENTOS DATABASE (Puerto 3310)
Connection Name: Sistema_Pontificia_DOCUMENTOS
Connection Method: Standard (TCP/IP)
Hostname: 127.0.0.1
Port: 3310
Username: root
Password: root
Default Schema: documentos_db

## 5. PAGOS DATABASE (Puerto 3311)
Connection Name: Sistema_Pontificia_PAGOS
Connection Method: Standard (TCP/IP)
Hostname: 127.0.0.1
Port: 3311
Username: root
Password: root
Default Schema: pagos_db

## 6. REPORTES DATABASE (Puerto 3312)
Connection Name: Sistema_Pontificia_REPORTES
Connection Method: Standard (TCP/IP)
Hostname: 127.0.0.1
Port: 3312
Username: root
Password: root
Default Schema: reportes_db

## 7. AUDITORIA DATABASE (Puerto 3313)
Connection Name: Sistema_Pontificia_AUDITORIA
Connection Method: Standard (TCP/IP)
Hostname: 127.0.0.1
Port: 3313
Username: root
Password: root
Default Schema: auditoria_db

# ===== COMANDOS PARA VERIFICAR CONEXIONES =====

# Desde línea de comandos puedes probar las conexiones:

# mysql -h 127.0.0.1 -P 3307 -u root -p
# mysql -h 127.0.0.1 -P 3308 -u root -p
# mysql -h 127.0.0.1 -P 3309 -u root -p
# mysql -h 127.0.0.1 -P 3310 -u root -p
# mysql -h 127.0.0.1 -P 3311 -u root -p
# mysql -h 127.0.0.1 -P 3312 -u root -p
# mysql -h 127.0.0.1 -P 3313 -u root -p

# ===== URLs DE ACCESO =====

# phpMyAdmin: http://localhost:8080
# - Usuario: root
# - Contraseña: root
# - Servidores disponibles: todos los MySQL containers

# ===== NOTAS IMPORTANTES =====

# 1. Asegúrate de que Docker esté ejecutándose
# 2. Los contenedores deben estar UP (docker-compose ps)
# 3. Espera unos segundos después de levantar los contenedores
# 4. Si hay problemas de conexión, reinicia los contenedores:
#    docker-compose restart mysql_[nombre_servicio]