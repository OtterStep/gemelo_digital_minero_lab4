"""
Módulo de Dashboard
KPIs en tiempo real, visualizaciones interactivas y alertas.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.database import get_connection

def get_kpis():
    """Obtener KPIs principales"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total de equipos
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN estado='Operativo' THEN 1 ELSE 0 END) as operativos FROM equipos")
    eq = cursor.fetchone()
    total_equipos = eq['total']
    operativos = eq['operativos']
    disponibilidad = (operativos / total_equipos * 100) if total_equipos > 0 else 0
    
    # MTBF y MTTR
    cursor.execute('''
    SELECT 
        AVG(CAST((julianday(fecha_fin) - julianday(fecha_inicio)) * 24 AS REAL)) as mttr,
        (SELECT SUM(horas_operacion) FROM equipos) /
            NULLIF((SELECT COUNT(*) FROM ordenes_trabajo
                WHERE estado = 'Completada' AND tipo = 'Correctivo'), 0) as mtbf
    FROM ordenes_trabajo 
    WHERE estado = 'Completada' AND fecha_fin IS NOT NULL AND fecha_inicio IS NOT NULL
    ''')
    mt = cursor.fetchone()
    mttr = mt['mttr'] if mt['mttr'] else 0
    mtbf = mt['mtbf'] if mt['mtbf'] else 0
    
    # OEE (Overall Equipment Effectiveness) - simplificado
    oee = disponibilidad * 0.85 * 0.90  # Disponibilidad * Rendimiento * Calidad
    
    # Costos de mantenimiento
    cursor.execute("SELECT SUM(costo_real) as total FROM ordenes_trabajo WHERE estado = 'Completada'")
    costos = cursor.fetchone()['total'] or 0
    
    # Equipos críticos
    cursor.execute("SELECT COUNT(*) as criticos FROM equipos WHERE estado = 'Critico'")
    criticos = cursor.fetchone()['criticos']
    
    # Órdenes pendientes
    cursor.execute("SELECT COUNT(*) as pendientes FROM ordenes_trabajo WHERE estado = 'Pendiente'")
    pendientes = cursor.fetchone()['pendientes']
    
    conn.close()
    
    return {
        'total_equipos': total_equipos,
        'operativos': operativos,
        'disponibilidad': round(disponibilidad, 1),
        'oee': round(oee, 1),
        'mtbf': round(mtbf, 0),
        'mttr': round(mttr, 1),
        'costos_mantenimiento': round(costos, 2),
        'equipos_criticos': criticos,
        'ordenes_pendientes': pendientes
    }

def get_equipos_data():
    """Obtener datos de equipos para visualización"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM equipos", conn)
    conn.close()
    return df

def get_datos_sensores(equipo_id=None, limit=100):
    """Obtener datos de sensores"""
    conn = get_connection()
    if equipo_id:
        df = pd.read_sql_query("SELECT * FROM datos_equipos WHERE equipo_id = ? ORDER BY fecha_hora DESC LIMIT ?", conn, params=(equipo_id, limit))
    else:
        df = pd.read_sql_query("SELECT * FROM datos_equipos ORDER BY fecha_hora DESC LIMIT ?", conn, params=(limit,))
    conn.close()
    return df

def get_ordenes_trabajo_data():
    """Obtener datos de órdenes de trabajo"""
    conn = get_connection()
    df = pd.read_sql_query('''
    SELECT ot.*, e.nombre as equipo_nombre, e.codigo as equipo_codigo,
           u.nombre as tecnico_nombre, u.apellido as tecnico_apellido
    FROM ordenes_trabajo ot
    JOIN equipos e ON ot.equipo_id = e.id
    LEFT JOIN usuarios u ON ot.tecnico_asignado_id = u.id
    ORDER BY ot.fecha_creacion DESC
    ''', conn)
    conn.close()
    return df

def chart_estado_equipos():
    """Gráfico de distribución de estados de equipos"""
    df = get_equipos_data()
    estado_counts = df['estado'].value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Cantidad']
    
    colores = {
        'Operativo': '#2ecc71',
        'Mantenimiento': '#f39c12',
        'Fuera de Servicio': '#e74c3c',
        'Critico': '#9b59b6'
    }
    
    fig = px.pie(estado_counts, values='Cantidad', names='Estado',
                 title='Distribución de Estados de Equipos',
                 color='Estado', color_discrete_map=colores,
                 hole=0.4)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def chart_tipo_equipos():
    """Gráfico de tipos de equipos"""
    df = get_equipos_data()
    tipo_counts = df['tipo'].value_counts().reset_index()
    tipo_counts.columns = ['Tipo', 'Cantidad']
    
    fig = px.bar(tipo_counts, x='Tipo', y='Cantidad',
                 title='Equipos por Tipo',
                 color='Tipo',
                 color_discrete_map={'Camion': '#3498db', 'Excavadora': '#e67e22', 'Cargador': '#1abc9c'})
    return fig

def chart_tendencias_temperatura(equipo_id):
    """Gráfico de tendencias de temperatura"""
    df = get_datos_sensores(equipo_id, limit=50)
    if df.empty:
        return go.Figure()
    
    df = df.sort_values('fecha_hora')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['fecha_hora'], y=df['temp_motor'],
                            mode='lines+markers', name='Temp. Motor (°C)',
                            line=dict(color='#e74c3c')))
    fig.add_trace(go.Scatter(x=df['fecha_hora'], y=df['temp_aceite_hidraulico'],
                            mode='lines+markers', name='Temp. Hidráulico (°C)',
                            line=dict(color='#f39c12')))
    
    fig.update_layout(title='Tendencias de Temperatura',
                     xaxis_title='Fecha/Hora',
                     yaxis_title='Temperatura (°C)')
    return fig

def chart_consumo_combustible():
    """Gráfico de consumo de combustible por equipo"""
    conn = get_connection()
    df = pd.read_sql_query('''
    SELECT e.codigo, e.nombre, AVG(d.consumo_combustible) as consumo_promedio
    FROM datos_equipos d
    JOIN equipos e ON d.equipo_id = e.id
    GROUP BY d.equipo_id
    ''', conn)
    conn.close()
    
    fig = px.bar(df, x='codigo', y='consumo_promedio',
                 title='Consumo Promedio de Combustible (L/h)',
                 labels={'codigo': 'Equipo', 'consumo_promedio': 'Consumo (L/h)'},
                 color='consumo_promedio',
                 color_continuous_scale='Reds')
    return fig

def chart_ordenes_por_tipo():
    """Gráfico de órdenes de trabajo por tipo"""
    df = get_ordenes_trabajo_data()
    if df.empty:
        return go.Figure()
    
    tipo_counts = df['tipo'].value_counts().reset_index()
    tipo_counts.columns = ['Tipo', 'Cantidad']
    
    fig = px.bar(tipo_counts, x='Tipo', y='Cantidad',
                 title='Órdenes de Trabajo por Tipo',
                 color='Tipo',
                 color_discrete_map={'Preventivo': '#3498db', 'Correctivo': '#e74c3c', 'Predictivo': '#2ecc71'})
    return fig

def chart_costos_mensuales():
    """Gráfico de costos mensuales de mantenimiento"""
    conn = get_connection()
    df = pd.read_sql_query('''
    SELECT strftime('%Y-%m', fecha_creacion) as mes, SUM(costo_real) as total
    FROM ordenes_trabajo
    WHERE estado = 'Completada'
    GROUP BY mes
    ORDER BY mes
    ''', conn)
    conn.close()
    
    if df.empty:
        return go.Figure()
    
    fig = px.line(df, x='mes', y='total', markers=True,
                  title='Costos Mensuales de Mantenimiento',
                  labels={'mes': 'Mes', 'total': 'Costo Total ($)'})
    fig.update_traces(line=dict(color='#2ecc71', width=3))
    return fig

def chart_horas_operacion():
    """Gráfico de horas de operación por equipo"""
    df = get_equipos_data()
    
    fig = px.bar(df, x='codigo', y='horas_operacion',
                 title='Horas de Operación por Equipo',
                 labels={'codigo': 'Equipo', 'horas_operacion': 'Horas'},
                 color='horas_operacion',
                 color_continuous_scale='Blues')
    return fig

def get_alertas_criticas():
    """Obtener alertas críticas de equipos"""
    conn = get_connection()
    df = pd.read_sql_query('''
    SELECT e.codigo, e.nombre, e.estado, d.temp_motor, d.presion_aceite, d.desgaste_neumaticos, d.fecha_hora
    FROM equipos e
    JOIN (SELECT equipo_id, MAX(fecha_hora) as max_fecha FROM datos_equipos GROUP BY equipo_id) latest
        ON e.id = latest.equipo_id
    JOIN datos_equipos d ON d.equipo_id = e.id AND d.fecha_hora = latest.max_fecha
    WHERE e.estado IN ('Critico', 'Fuera de Servicio')
       OR d.temp_motor > 100
       OR d.presion_aceite < 30
       OR d.desgaste_neumaticos > 70
    ORDER BY e.estado DESC
    ''', conn)
    conn.close()
    return df
