"""
Módulo de Gemelo Digital
Representación virtual de equipos con parámetros operativos y simulación de fallas.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import random
from datetime import datetime
from utils.database import get_connection

def get_equipo_detalle(equipo_id):
    """Obtener detalles completos de un equipo"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipos WHERE id = ?", (equipo_id,))
    equipo = cursor.fetchone()
    conn.close()
    return dict(equipo) if equipo else None

def get_ultimos_datos(equipo_id):
    """Obtener los datos más recientes de un equipo"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM datos_equipos 
    WHERE equipo_id = ? 
    ORDER BY fecha_hora DESC 
    LIMIT 1
    ''', (equipo_id,))
    datos = cursor.fetchone()
    conn.close()
    return dict(datos) if datos else None

def get_historial_datos(equipo_id, limit=100):
    """Obtener historial de datos de sensores"""
    conn = get_connection()
    df = pd.read_sql_query('''
    SELECT * FROM datos_equipos 
    WHERE equipo_id = ? 
    ORDER BY fecha_hora DESC 
    LIMIT ?
    ''', conn, params=(equipo_id, limit))
    conn.close()
    return df

def evaluar_estado_componente(valor, umbrales):
    """
    Evaluar el estado de un componente según umbrales
    umbrales = (normal_min, normal_max, alerta_min, alerta_max)
    """
    normal_min, normal_max, alerta_min, alerta_max = umbrales
    
    if normal_min <= valor <= normal_max:
        return 'Normal', '#2ecc71'
    elif alerta_min <= valor <= alerta_max:
        return 'Alerta', '#f39c12'
    else:
        return 'Crítico', '#e74c3c'

def analizar_salud_equipo(datos):
    """Analizar la salud general del equipo basado en los últimos datos"""
    if not datos:
        return []
    
    analisis = []
    
    # Motor
    estado_motor, color_motor = evaluar_estado_componente(
        datos.get('temp_motor', 0), (60, 95, 50, 105)
    )
    analisis.append({
        'componente': 'Motor',
        'parametro': f"Temperatura: {datos.get('temp_motor', 'N/A')}°C",
        'estado': estado_motor,
        'color': color_motor,
        'detalle': f"Presión Aceite: {datos.get('presion_aceite', 'N/A')} PSI | RPM: {datos.get('rpm_motor', 'N/A')}"
    })
    
    # Sistema Hidráulico
    estado_hid, color_hid = evaluar_estado_componente(
        datos.get('presion_hidraulica', 0), (190, 240, 170, 260)
    )
    analisis.append({
        'componente': 'Sistema Hidráulico',
        'parametro': f"Presión: {datos.get('presion_hidraulica', 'N/A')} PSI",
        'estado': estado_hid,
        'color': color_hid,
        'detalle': f"Temp. Aceite: {datos.get('temp_aceite_hidraulico', 'N/A')}°C | Nivel: {datos.get('nivel_aceite_hidraulico', 'N/A')}%"
    })
    
    # Frenos
    desgaste = datos.get('desgaste_pastillas', 0)
    if desgaste < 30:
        estado_frenos, color_frenos = 'Normal', '#2ecc71'
    elif desgaste < 60:
        estado_frenos, color_frenos = 'Alerta', '#f39c12'
    else:
        estado_frenos, color_frenos = 'Crítico', '#e74c3c'
    analisis.append({
        'componente': 'Sistema de Frenos',
        'parametro': f"Desgaste: {desgaste}%",
        'estado': estado_frenos,
        'color': color_frenos,
        'detalle': f"Estado General: {datos.get('estado_frenos', 'N/A')}"
    })
    
    # Neumáticos
    desgaste_neum = datos.get('desgaste_neumaticos', 0)
    if desgaste_neum < 25:
        estado_neum, color_neum = 'Normal', '#2ecc71'
    elif desgaste_neum < 50:
        estado_neum, color_neum = 'Alerta', '#f39c12'
    else:
        estado_neum, color_neum = 'Crítico', '#e74c3c'
    analisis.append({
        'componente': 'Neumáticos',
        'parametro': f"Desgaste Promedio: {desgaste_neum}%",
        'estado': estado_neum,
        'color': color_neum,
        'detalle': f"Presión: {datos.get('presion_neumaticos', 'N/A')} kPa"
    })
    
    # Combustible
    nivel = datos.get('nivel_combustible', 0)
    if nivel > 40:
        estado_comb, color_comb = 'Normal', '#2ecc71'
    elif nivel > 15:
        estado_comb, color_comb = 'Alerta', '#f39c12'
    else:
        estado_comb, color_comb = 'Crítico', '#e74c3c'
    analisis.append({
        'componente': 'Sistema de Combustible',
        'parametro': f"Nivel: {nivel}%",
        'estado': estado_comb,
        'color': color_comb,
        'detalle': f"Consumo: {datos.get('consumo_combustible', 'N/A')} L/h"
    })
    
    return analisis

def visualizar_gemelo_2d(equipo, datos):
    """Crear visualización 2D del gemelo digital"""
    tipo = equipo.get('tipo', 'Camion')
    
    fig = go.Figure()
    
    if tipo == 'Camion':
        # Dibujar camión minero simplificado
        # Chasis
        fig.add_shape(type="rect", x0=2, y0=3, x1=8, y1=5,
                     fillcolor="#34495e", line_color="#2c3e50")
        # Cabina
        fig.add_shape(type="rect", x0=6.5, y0=5, x1=8, y1=7,
                     fillcolor="#e74c3c", line_color="#c0392b")
        # Caja de carga
        fig.add_shape(type="rect", x0=2, y0=5, x1=6, y1=6.5,
                     fillcolor="#7f8c8d", line_color="#616a6b")
        # Ruedas
        fig.add_shape(type="circle", x0=2.5, y0=2, x1=3.5, y1=3,
                     fillcolor="#2c3e50", line_color="#1a252f")
        fig.add_shape(type="circle", x0=6.5, y0=2, x1=7.5, y1=3,
                     fillcolor="#2c3e50", line_color="#1a252f")
        
    elif tipo == 'Excavadora':
        # Base
        fig.add_shape(type="rect", x0=3, y0=2, x1=7, y1=4,
                     fillcolor="#34495e", line_color="#2c3e50")
        # Cabina
        fig.add_shape(type="rect", x0=4, y0=4, x1=6, y1=6,
                     fillcolor="#e67e22", line_color="#d35400")
        # Brazo
        fig.add_shape(type="rect", x0=6, y0=5, x1=9, y1=5.5,
                     fillcolor="#95a5a6", line_color="#7f8c8d")
        # Cucharón
        fig.add_shape(type="path",
                     path="M 9,5.5 L 10,4.5 L 10.5,5.5 L 10,6.5 Z",
                     fillcolor="#7f8c8d", line_color="#616a6b")
        # Orugas
        fig.add_shape(type="rect", x0=2.5, y0=1, x1=7.5, y1=2,
                     fillcolor="#2c3e50", line_color="#1a252f")
        
    elif tipo == 'Cargador':
        # Chasis
        fig.add_shape(type="rect", x0=3, y0=3, x1=7, y1=5,
                     fillcolor="#34495e", line_color="#2c3e50")
        # Cabina
        fig.add_shape(type="rect", x0=4.5, y0=5, x1=6.5, y1=7,
                     fillcolor="#1abc9c", line_color="#16a085")
        # Brazo de carga
        fig.add_shape(type="rect", x0=1, y0=4, x1=3, y1=4.5,
                     fillcolor="#95a5a6", line_color="#7f8c8d")
        # Cuchara
        fig.add_shape(type="path",
                     path="M 0.5,3.5 L 1,4.5 L 2,4.5 L 1.5,3.5 Z",
                     fillcolor="#7f8c8d", line_color="#616a6b")
        # Ruedas
        fig.add_shape(type="circle", x0=3, y0=2, x1=4, y1=3,
                     fillcolor="#2c3e50", line_color="#1a252f")
        fig.add_shape(type="circle", x0=6, y0=2, x1=7, y1=3,
                     fillcolor="#2c3e50", line_color="#1a252f")
    
    # Añadir indicadores de estado
    if datos:
        salud = analizar_salud_equipo(datos)
        for i, s in enumerate(salud):
            y_pos = 9 - i * 0.8
            fig.add_annotation(
                x=0.5, y=y_pos,
                text=f"● {s['componente']}: {s['estado']}",
                showarrow=False,
                font=dict(color=s['color'], size=12),
                xanchor='left'
            )
    
    fig.update_layout(
        title=f"Gemelo Digital - {equipo['nombre']} ({equipo['codigo']})",
        xaxis=dict(range=[0, 11], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, 10], showgrid=False, zeroline=False, showticklabels=False),
        showlegend=False,
        height=500,
        plot_bgcolor='rgba(240, 240, 240, 0.5)'
    )
    
    return fig

def simular_falla(equipo_id, tipo_falla, intensidad=0.7):
    """
    Simular un escenario de falla en el equipo
    tipos: 'sobrecalentamiento_motor', 'perdida_presion_hidraulica', 
           'desgaste_neumaticos', 'falla_frenos', 'consumo_excesivo'
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obtener últimos datos
    cursor.execute('''
    SELECT * FROM datos_equipos WHERE equipo_id = ? ORDER BY fecha_hora DESC LIMIT 1
    ''', (equipo_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return None
    ultimos = dict(fila)
    
    nuevos_datos = ultimos.copy()
    del nuevos_datos['id']
    del nuevos_datos['fecha_hora']
    
    alertas = []
    
    if tipo_falla == 'sobrecalentamiento_motor':
        nuevos_datos['temp_motor'] = round(nuevos_datos['temp_motor'] * (1 + intensidad * 0.3), 1)
        nuevos_datos['presion_aceite'] = round(nuevos_datos['presion_aceite'] * (1 - intensidad * 0.2), 1)
        alertas.append(f"⚠️ SOBRECALENTAMIENTO: Temp. motor alcanza {nuevos_datos['temp_motor']}°C")
        
    elif tipo_falla == 'perdida_presion_hidraulica':
        nuevos_datos['presion_hidraulica'] = round(nuevos_datos['presion_hidraulica'] * (1 - intensidad * 0.4), 1)
        nuevos_datos['nivel_aceite_hidraulico'] = round(nuevos_datos['nivel_aceite_hidraulico'] * (1 - intensidad * 0.15), 1)
        alertas.append(f"⚠️ PÉRDIDA PRESIÓN HIDRÁULICA: {nuevos_datos['presion_hidraulica']} PSI")
        
    elif tipo_falla == 'desgaste_neumaticos':
        nuevos_datos['desgaste_neumaticos'] = min(95, nuevos_datos['desgaste_neumaticos'] + intensidad * 40)
        nuevos_datos['presion_neumaticos'] = round(nuevos_datos['presion_neumaticos'] * (1 - intensidad * 0.2), 1)
        alertas.append(f"⚠️ DESGASTE CRÍTICO NEUMÁTICOS: {nuevos_datos['desgaste_neumaticos']}%")
        
    elif tipo_falla == 'falla_frenos':
        nuevos_datos['desgaste_pastillas'] = min(98, nuevos_datos['desgaste_pastillas'] + intensidad * 50)
        nuevos_datos['estado_frenos'] = 'Critico'
        alertas.append(f"⚠️ FALLA FRENOS: Desgaste {nuevos_datos['desgaste_pastillas']}%")
        
    elif tipo_falla == 'consumo_excesivo':
        nuevos_datos['consumo_combustible'] = round(nuevos_datos['consumo_combustible'] * (1 + intensidad * 0.5), 1)
        nuevos_datos['nivel_combustible'] = max(0, nuevos_datos['nivel_combustible'] - intensidad * 20)
        alertas.append(f"⚠️ CONSUMO EXCESIVO: {nuevos_datos['consumo_combustible']} L/h")
    
    nuevos_datos['alertas'] = ' | '.join(alertas)
    
    # Insertar datos simulados
    columns = ', '.join(nuevos_datos.keys())
    placeholders = ', '.join(['?' for _ in nuevos_datos])
    cursor.execute(f'''
    INSERT INTO datos_equipos ({columns}) VALUES ({placeholders})
    ''', list(nuevos_datos.values()))
    
    # Actualizar estado del equipo si es necesario
    if intensidad > 0.6:
        cursor.execute("UPDATE equipos SET estado = 'Critico' WHERE id = ?", (equipo_id,))
    
    conn.commit()
    conn.close()
    
    return {
        'tipo_falla': tipo_falla,
        'intensidad': intensidad,
        'alertas': alertas,
        'datos_actualizados': nuevos_datos
    }

def generar_datos_en_tiempo_real(equipo_id):
    """Generar nuevos datos simulados para el equipo"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obtener últimos datos
    cursor.execute('''
    SELECT * FROM datos_equipos WHERE equipo_id = ? ORDER BY fecha_hora DESC LIMIT 1
    ''', (equipo_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        return None
    ultimos = dict(fila)
    
    nuevos_datos = ultimos.copy()
    del nuevos_datos['id']
    del nuevos_datos['fecha_hora']
    
    # Variación aleatoria pequeña
    nuevos_datos['temp_motor'] = round(np.clip(nuevos_datos['temp_motor'] + random.uniform(-2, 2), 50, 110), 1)
    nuevos_datos['presion_aceite'] = round(np.clip(nuevos_datos['presion_aceite'] + random.uniform(-1, 1), 25, 70), 1)
    nuevos_datos['rpm_motor'] = int(np.clip(nuevos_datos['rpm_motor'] + random.uniform(-50, 50), 1000, 2200))
    nuevos_datos['presion_hidraulica'] = round(np.clip(nuevos_datos['presion_hidraulica'] + random.uniform(-3, 3), 160, 270), 1)
    nuevos_datos['nivel_combustible'] = round(np.clip(nuevos_datos['nivel_combustible'] - random.uniform(0, 0.5), 0, 100), 1)
    nuevos_datos['horas_motor'] = round(nuevos_datos['horas_motor'] + 0.01, 1)
    nuevos_datos['carga_actual'] = round(np.clip(nuevos_datos['carga_actual'] + random.uniform(-10, 10), 0, 400), 1)
    
    # Insertar nuevos datos
    columns = ', '.join(nuevos_datos.keys())
    placeholders = ', '.join(['?' for _ in nuevos_datos])
    cursor.execute(f'''
    INSERT INTO datos_equipos ({columns}) VALUES ({placeholders})
    ''', list(nuevos_datos.values()))
    
    conn.commit()
    conn.close()
    
    return nuevos_datos
