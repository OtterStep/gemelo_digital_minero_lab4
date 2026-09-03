"""
Módulo de Base de Datos
Gestión de la conexión SQLite y creación de tablas para el sistema de gemelos digitales mineros.
"""
import sqlite3
import os
import bcrypt
from datetime import datetime

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'gemelo_digital.db')

def get_connection():
    """Obtener conexión a la base de datos"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_database():
    """Inicializar la base de datos con todas las tablas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN ('Administrador', 'Ingeniero', 'Supervisor', 'Tecnico')),
        area TEXT,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ultimo_acceso TIMESTAMP,
        activo INTEGER DEFAULT 1
    )
    ''')
    
    # Tabla de Bitácora de Accesos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bitacora_accesos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        accion TEXT NOT NULL,
        ip TEXT,
        detalle TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')
    
    # Tabla de Equipos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('Camion', 'Excavadora', 'Cargador')),
        marca TEXT NOT NULL,
        modelo TEXT NOT NULL,
        año_fabricacion INTEGER,
        numero_serie TEXT,
        horas_operacion REAL DEFAULT 0,
        estado TEXT DEFAULT 'Operativo' CHECK(estado IN ('Operativo', 'Mantenimiento', 'Fuera de Servicio', 'Critico')),
        fecha_adquisicion DATE,
        ubicacion TEXT,
        capacidad_carga REAL,
        potencia REAL
    )
    ''')
    
    # Tabla de Datos en Tiempo Real del Gemelo Digital
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS datos_equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipo_id INTEGER NOT NULL,
        fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        -- Motor
        temp_motor REAL,
        presion_aceite REAL,
        rpm_motor INTEGER,
        horas_motor REAL,
        -- Sistema Hidráulico
        presion_hidraulica REAL,
        temp_aceite_hidraulico REAL,
        nivel_aceite_hidraulico REAL,
        -- Frenos
        estado_frenos TEXT,
        desgaste_pastillas REAL,
        -- Neumáticos
        presion_neumaticos REAL,
        desgaste_neumaticos REAL,
        -- Combustible
        nivel_combustible REAL,
        consumo_combustible REAL,
        -- Operación
        carga_actual REAL,
        ciclos_completados INTEGER,
        velocidad REAL,
        -- Alertas
        alertas TEXT,
        FOREIGN KEY (equipo_id) REFERENCES equipos(id)
    )
    ''')
    
    # Tabla de Órdenes de Trabajo
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ordenes_trabajo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_orden TEXT UNIQUE NOT NULL,
        equipo_id INTEGER NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('Preventivo', 'Correctivo', 'Predictivo')),
        prioridad TEXT NOT NULL CHECK(prioridad IN ('Baja', 'Media', 'Alta', 'Critica')),
        titulo TEXT NOT NULL,
        descripcion TEXT,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_programada DATE,
        fecha_inicio TIMESTAMP,
        fecha_fin TIMESTAMP,
        estado TEXT DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'En Proceso', 'Completada', 'Cancelada')),
        tecnico_asignado_id INTEGER,
        supervisor_id INTEGER,
        costo_estimado REAL DEFAULT 0,
        costo_real REAL DEFAULT 0,
        FOREIGN KEY (equipo_id) REFERENCES equipos(id),
        FOREIGN KEY (tecnico_asignado_id) REFERENCES usuarios(id),
        FOREIGN KEY (supervisor_id) REFERENCES usuarios(id)
    )
    ''')
    
    # Tabla de Historial de Mantenimiento
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historial_mantenimiento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_id INTEGER NOT NULL,
        equipo_id INTEGER NOT NULL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tipo_trabajo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        repuestos_utilizados TEXT,
        horas_invertidas REAL,
        tecnico_id INTEGER,
        observaciones TEXT,
        FOREIGN KEY (orden_id) REFERENCES ordenes_trabajo(id),
        FOREIGN KEY (equipo_id) REFERENCES equipos(id),
        FOREIGN KEY (tecnico_id) REFERENCES usuarios(id)
    )
    ''')
    
    # Tabla de Repuestos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repuestos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        categoria TEXT,
        stock_actual INTEGER DEFAULT 0,
        stock_minimo INTEGER DEFAULT 5,
        precio_unitario REAL DEFAULT 0,
        ubicacion_almacen TEXT,
        proveedor TEXT
    )
    ''')
    
    # Tabla de Predicciones de Falla
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predicciones_falla (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipo_id INTEGER NOT NULL,
        fecha_prediccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        componente TEXT NOT NULL,
        probabilidad_falla REAL NOT NULL,
        dias_hasta_falla INTEGER,
        severidad TEXT NOT NULL CHECK(severidad IN ('Baja', 'Media', 'Alta', 'Critica')),
        recomendacion TEXT,
        modelo_utilizado TEXT,
        FOREIGN KEY (equipo_id) REFERENCES equipos(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")
def hash_password(password):
    """Generar hash de contraseña"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Verificar contraseña"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def insert_default_data():
    """Insertar datos por defecto para demostración"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existen usuarios
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        # Usuarios por defecto
        usuarios = [
            ('admin', hash_password('admin123'), 'Carlos', 'González', 'admin@minera.com', 'Administrador', 'Gerencia'),
            ('ingeniero', hash_password('inge123'), 'María', 'López', 'maria@minera.com', 'Ingeniero', 'Mantenimiento'),
            ('supervisor', hash_password('super123'), 'Juan', 'Pérez', 'juan@minera.com', 'Supervisor', 'Operaciones'),
            ('tecnico', hash_password('tec123'), 'Pedro', 'Ramírez', 'pedro@minera.com', 'Tecnico', 'Mantenimiento'),
        ]
        cursor.executemany('''
        INSERT INTO usuarios (username, password_hash, nombre, apellido, email, rol, area)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', usuarios)
    
    # Verificar si ya existen equipos
    cursor.execute("SELECT COUNT(*) FROM equipos")
    if cursor.fetchone()[0] == 0:
        equipos = [
            ('CAM-001', 'Camión Cat 797F', 'Camion', 'Caterpillar', '797F', 2020, 'CAT797F001', 12500, 'Operativo', '2020-03-15', 'Tajo Norte', 360, 2983),
            ('CAM-002', 'Camión Komatsu 930E', 'Camion', 'Komatsu', '930E-5', 2021, 'KMT930E002', 9800, 'Operativo', '2021-01-20', 'Tajo Sur', 320, 2610),
            ('EXC-001', 'Excavadora Cat 6060', 'Excavadora', 'Caterpillar', '6060 FS', 2019, 'CAT6060001', 15200, 'Operativo', '2019-08-10', 'Tajo Norte', 0, 2240),
            ('EXC-002', 'Excavadora Komatsu PC8000', 'Excavadora', 'Komatsu', 'PC8000-11', 2022, 'KMTPC800002', 6500, 'Operativo', '2022-05-05', 'Tajo Centro', 0, 3000),
            ('CAR-001', 'Cargador Cat 994K', 'Cargador', 'Caterpillar', '994K', 2021, 'CAT994K001', 8900, 'Mantenimiento', '2021-11-12', 'Tajo Sur', 0, 1297),
            ('CAR-002', 'Cargador Komatsu WA900', 'Cargador', 'Komatsu', 'WA900-8', 2020, 'KMTWA90002', 11200, 'Operativo', '2020-07-22', 'Tajo Norte', 0, 1160),
        ]
        cursor.executemany('''
        INSERT INTO equipos (codigo, nombre, tipo, marca, modelo, año_fabricacion, numero_serie, horas_operacion, estado, fecha_adquisicion, ubicacion, capacidad_carga, potencia)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', equipos)
    
    # Verificar si ya existen repuestos
    cursor.execute("SELECT COUNT(*) FROM repuestos")
    if cursor.fetchone()[0] == 0:
        repuestos = [
            ('REP-001', 'Filtro de Aceite Motor', 'Filtro principal para motor diesel', 'Filtros', 50, 10, 150.00, 'Almacén A-01', 'Caterpillar Parts'),
            ('REP-002', 'Filtro Hidráulico', 'Filtro de alta presión sistema hidráulico', 'Filtros', 35, 8, 280.00, 'Almacén A-02', 'Parker Hannifin'),
            ('REP-003', 'Pastillas de Freno', 'Juego de pastillas para freno de disco', 'Frenos', 20, 5, 450.00, 'Almacén B-01', 'Wabco'),
            ('REP-004', 'Neumático 59/80R63', 'Neumático radial para camión minero', 'Neumáticos', 12, 3, 12500.00, 'Almacén Externo', 'Bridgestone'),
            ('REP-005', 'Bomba Hidráulica', 'Bomba de pistones axial', 'Hidráulica', 5, 2, 8500.00, 'Almacén C-01', 'Rexroth'),
            ('REP-006', 'Sensor de Temperatura', 'Sensor PT100 para motor', 'Sensores', 100, 20, 75.00, 'Almacén D-01', 'IFM'),
        ]
        cursor.executemany('''
        INSERT INTO repuestos (codigo, nombre, descripcion, categoria, stock_actual, stock_minimo, precio_unitario, ubicacion_almacen, proveedor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', repuestos)
    
    # Generar datos iniciales de equipos
    cursor.execute("SELECT id FROM equipos")
    equipo_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) FROM datos_equipos")
    if cursor.fetchone()[0] == 0:
        import random
        for eq_id in equipo_ids:
            for _ in range(50):  # 50 registros por equipo
                datos = (
                    eq_id,
                    round(random.uniform(75, 105), 1),  # temp_motor
                    round(random.uniform(35, 65), 1),  # presion_aceite
                    random.randint(1200, 2100),  # rpm_motor
                    round(random.uniform(5000, 16000), 1),  # horas_motor
                    round(random.uniform(180, 250), 1),  # presion_hidraulica
                    round(random.uniform(50, 80), 1),  # temp_aceite_hidraulico
                    round(random.uniform(85, 100), 1),  # nivel_aceite_hidraulico
                    random.choice(['Normal', 'Revisar', 'Critico']),  # estado_frenos
                    round(random.uniform(10, 85), 1),  # desgaste_pastillas
                    round(random.uniform(550, 750), 1),  # presion_neumaticos
                    round(random.uniform(5, 60), 1),  # desgaste_neumaticos
                    round(random.uniform(10, 100), 1),  # nivel_combustible
                    round(random.uniform(120, 280), 1),  # consumo_combustible
                    round(random.uniform(0, 360), 1),  # carga_actual
                    random.randint(0, 15),  # ciclos_completados
                    round(random.uniform(0, 45), 1),  # velocidad
                    ''  # alertas
                )
                cursor.execute('''
                INSERT INTO datos_equipos (equipo_id, temp_motor, presion_aceite, rpm_motor, horas_motor,
                    presion_hidraulica, temp_aceite_hidraulico, nivel_aceite_hidraulico,
                    estado_frenos, desgaste_pastillas, presion_neumaticos, desgaste_neumaticos,
                    nivel_combustible, consumo_combustible, carga_actual, ciclos_completados,
                    velocidad, alertas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', datos)
    
    # Insertar órdenes de trabajo de ejemplo
    cursor.execute("SELECT COUNT(*) FROM ordenes_trabajo")
    if cursor.fetchone()[0] == 0:
        ordenes = [
            ('OT-2024-001', 1, 'Preventivo', 'Media', 'Cambio de aceite y filtros', 'Cambio programado de aceite de motor y filtros', None, None, None, 'Completada', 4, 3, 850.00, 780.00),
            ('OT-2024-002', 3, 'Correctivo', 'Alta', 'Reparación sistema hidráulico', 'Fuga en línea hidráulica principal', None, None, None, 'Completada', 4, 3, 3200.00, 3450.00),
            ('OT-2024-003', 5, 'Preventivo', 'Media', 'Inspección general', 'Inspección completa de 500 horas', None, None, None, 'En Proceso', 4, 3, 500.00, 0),
            ('OT-2024-004', 2, 'Predictivo', 'Alta', 'Monitoreo vibraciones motor', 'Análisis de vibraciones indica posible desgaste', None, None, None, 'Pendiente', None, 3, 1200.00, 0),
            ('OT-2024-005', 1, 'Correctivo', 'Critica', 'Reemplazo neumático dañado', 'Neumático trasero derecho con corte profundo', None, None, None, 'Pendiente', None, 3, 12500.00, 0),
        ]
        cursor.executemany('''
        INSERT INTO ordenes_trabajo (numero_orden, equipo_id, tipo, prioridad, titulo, descripcion, fecha_programada, fecha_inicio, fecha_fin, estado, tecnico_asignado_id, supervisor_id, costo_estimado, costo_real)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ordenes)
    
    # Insertar historial de mantenimiento de ejemplo
    cursor.execute("SELECT COUNT(*) FROM historial_mantenimiento")
    if cursor.fetchone()[0] == 0:
        historial = [
            (1, 1, 'Mantenimiento Preventivo', 'Cambio programado de aceite de motor y filtros primario/secundario', 'Filtro de Aceite Motor (x2)', 4.5, 4, 'Equipo operando en parámetros normales tras el servicio'),
            (2, 3, 'Reparación Correctiva', 'Sustitución de manguera de alta presión y purgado del sistema hidráulico', 'Filtro Hidráulico (x1)', 6.0, 4, 'Pruebas de presión satisfactorias a 240 PSI'),
        ]
        cursor.executemany('''
        INSERT INTO historial_mantenimiento (orden_id, equipo_id, tipo_trabajo, descripcion, repuestos_utilizados, horas_invertidas, tecnico_id, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', historial)
    
    conn.commit()
    conn.close()
    print("Datos por defecto insertados correctamente.")

if __name__ == '__main__':
    init_database()
    insert_default_data()
