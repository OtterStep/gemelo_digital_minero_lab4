"""
Módulo de Mantenimiento
Gestión de órdenes de trabajo, historial de mantenimiento y repuestos.
"""
import pandas as pd
from datetime import datetime
from utils.database import get_connection

def crear_orden_trabajo(equipo_id, tipo, prioridad, titulo, descripcion, 
                        fecha_programada=None, tecnico_asignado_id=None, 
                        supervisor_id=None, costo_estimado=0):
    """Crear nueva orden de trabajo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Generar número de orden
        cursor.execute("SELECT COUNT(*) FROM ordenes_trabajo")
        count = cursor.fetchone()[0] + 1
        numero_orden = f"OT-{datetime.now().year}-{count:03d}"
        
        cursor.execute('''
        INSERT INTO ordenes_trabajo (numero_orden, equipo_id, tipo, prioridad, titulo, 
                                     descripcion, fecha_programada, tecnico_asignado_id, 
                                     supervisor_id, costo_estimado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (numero_orden, equipo_id, tipo, prioridad, titulo, descripcion,
              fecha_programada, tecnico_asignado_id, supervisor_id, costo_estimado))
        
        conn.commit()
        orden_id = cursor.lastrowid
        conn.close()
        return True, numero_orden, orden_id
    except Exception as e:
        conn.close()
        return False, str(e), None

def actualizar_orden_trabajo(orden_id, datos):
    """Actualizar orden de trabajo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for key, value in datos.items():
        if key in ['estado', 'fecha_inicio', 'fecha_fin', 'costo_real', 'tecnico_asignado_id']:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if fields:
        values.append(orden_id)
        query = f"UPDATE ordenes_trabajo SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return True

def get_ordenes_trabajo(filtro_estado=None, filtro_tipo=None):
    """Obtener órdenes de trabajo con filtros opcionales"""
    conn = get_connection()
    query = '''
    SELECT ot.*, e.nombre as equipo_nombre, e.codigo as equipo_codigo, e.tipo as equipo_tipo,
           u.nombre as tecnico_nombre, u.apellido as tecnico_apellido,
           s.nombre as supervisor_nombre, s.apellido as supervisor_apellido
    FROM ordenes_trabajo ot
    JOIN equipos e ON ot.equipo_id = e.id
    LEFT JOIN usuarios u ON ot.tecnico_asignado_id = u.id
    LEFT JOIN usuarios s ON ot.supervisor_id = s.id
    WHERE 1=1
    '''
    params = []
    
    if filtro_estado:
        query += " AND ot.estado = ?"
        params.append(filtro_estado)
    
    if filtro_tipo:
        query += " AND ot.tipo = ?"
        params.append(filtro_tipo)
    
    query += " ORDER BY ot.fecha_creacion DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_orden_por_id(orden_id):
    """Obtener orden de trabajo por ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT ot.*, e.nombre as equipo_nombre, e.codigo as equipo_codigo
    FROM ordenes_trabajo ot
    JOIN equipos e ON ot.equipo_id = e.id
    WHERE ot.id = ?
    ''', (orden_id,))
    orden = cursor.fetchone()
    conn.close()
    return dict(orden) if orden else None

def registrar_historial(orden_id, equipo_id, tipo_trabajo, descripcion, 
                        repuestos_utilizados=None, horas_invertidas=0, 
                        tecnico_id=None, observaciones=None):
    """Registrar entrada en historial de mantenimiento"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO historial_mantenimiento (orden_id, equipo_id, tipo_trabajo, descripcion,
                                         repuestos_utilizados, horas_invertidas, tecnico_id, observaciones)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (orden_id, equipo_id, tipo_trabajo, descripcion, repuestos_utilizados,
          horas_invertidas, tecnico_id, observaciones))
    
    conn.commit()
    conn.close()
    return True

def get_historial_mantenimiento(equipo_id=None):
    """Obtener historial de mantenimiento"""
    conn = get_connection()
    query = '''
    SELECT h.*, e.nombre as equipo_nombre, e.codigo as equipo_codigo,
           u.nombre as tecnico_nombre, u.apellido as tecnico_apellido,
           ot.numero_orden
    FROM historial_mantenimiento h
    JOIN equipos e ON h.equipo_id = e.id
    LEFT JOIN usuarios u ON h.tecnico_id = u.id
    LEFT JOIN ordenes_trabajo ot ON h.orden_id = ot.id
    '''
    params = []
    
    if equipo_id:
        query += " WHERE h.equipo_id = ?"
        params.append(equipo_id)
    
    query += " ORDER BY h.fecha DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_repuestos():
    """Obtener catálogo de repuestos"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM repuestos ORDER BY nombre", conn)
    conn.close()
    return df

def actualizar_stock_repuesto(repuesto_id, cantidad, operacion='restar'):
    """Actualizar stock de repuesto"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if operacion == 'restar':
        cursor.execute("UPDATE repuestos SET stock_actual = stock_actual - ? WHERE id = ?",
                      (cantidad, repuesto_id))
    elif operacion == 'sumar':
        cursor.execute("UPDATE repuestos SET stock_actual = stock_actual + ? WHERE id = ?",
                      (cantidad, repuesto_id))
    
    conn.commit()
    conn.close()
    return True

def get_repuestos_bajo_stock():
    """Obtener repuestos con stock bajo el mínimo"""
    conn = get_connection()
    df = pd.read_sql_query('''
    SELECT * FROM repuestos 
    WHERE stock_actual <= stock_minimo
    ORDER BY (stock_actual * 1.0 / stock_minimo) ASC
    ''', conn)
    conn.close()
    return df

def get_tecnicos_disponibles():
    """Obtener lista de técnicos disponibles"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, nombre, apellido, area 
    FROM usuarios 
    WHERE rol = 'Tecnico' AND activo = 1
    ORDER BY nombre
    ''')
    tecnicos = cursor.fetchall()
    conn.close()
    return [dict(t) for t in tecnicos]

def get_equipos_para_mantenimiento():
    """Obtener equipos que pueden necesitar mantenimiento"""
    conn = get_connection()
    df = pd.read_sql_query('''
    SELECT e.*, 
           (SELECT COUNT(*) FROM ordenes_trabajo ot WHERE ot.equipo_id = e.id AND ot.estado = 'Pendiente') as ordenes_pendientes
    FROM equipos e
    ORDER BY ordenes_pendientes DESC, horas_operacion DESC
    ''', conn)
    conn.close()
    return df

def generar_ordenes_automaticas():
    """
    Generar órdenes de trabajo automáticas basadas en horas de operación
    Regla: Cada 500 horas -> Mantenimiento preventivo
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar equipos que superen umbrales sin mantenimiento preventivo
    cursor.execute('''
    SELECT e.id, e.codigo, e.nombre, e.horas_operacion,
           (SELECT MAX(d.horas_motor) FROM datos_equipos d WHERE d.equipo_id = e.id) as ultimas_horas,
           (SELECT MAX(ot.fecha_creacion) FROM ordenes_trabajo ot 
            WHERE ot.equipo_id = e.id AND ot.tipo = 'Preventivo') as ultimo_mantenimiento
    FROM equipos e
    WHERE e.estado != 'Fuera de Servicio'
    ''')
    
    equipos = cursor.fetchall()
    ordenes_generadas = []
    
    for eq in equipos:
        horas = eq['ultimas_horas'] or eq['horas_operacion']
        ultimo_mant = eq['ultimo_mantenimiento']
        
        # Si han pasado más de 500 horas desde el último mantenimiento o nunca se hizo
        if horas > 0 and (ultimo_mant is None or horas % 500 < 10):
            # Verificar que no exista una orden pendiente similar
            cursor.execute('''
            SELECT COUNT(*) FROM ordenes_trabajo 
            WHERE equipo_id = ? AND tipo = 'Preventivo' AND estado IN ('Pendiente', 'En Proceso')
            ''', (eq['id'],))
            
            if cursor.fetchone()[0] == 0:
                count = cursor.execute("SELECT COUNT(*) FROM ordenes_trabajo").fetchone()[0] + 1
                numero_orden = f"OT-{datetime.now().year}-{count:03d}"
                
                cursor.execute('''
                INSERT INTO ordenes_trabajo (numero_orden, equipo_id, tipo, prioridad, titulo, descripcion, costo_estimado)
                VALUES (?, ?, 'Preventivo', 'Media', ?, ?, ?)
                ''', (numero_orden, eq['id'],
                      f'Mantenimiento Preventivo {int(horas)} horas - {eq["nombre"]}',
                      f'Mantenimiento programado por horas de operación. Revisión general de sistemas, cambio de filtros y lubricación.',
                      500.00))
                
                ordenes_generadas.append(numero_orden)
    
    conn.commit()
    conn.close()
    return ordenes_generadas
