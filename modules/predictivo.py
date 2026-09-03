"""
Módulo Predictivo
Modelos simples de Machine Learning para predicción de fallas y recomendaciones.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

from utils.database import get_connection

def preparar_datos_entrenamiento():
    """Preparar datos históricos para entrenamiento de modelos"""
    conn = get_connection()
    
    # Obtener datos de sensores con información de equipos
    df = pd.read_sql_query('''
    SELECT d.*, e.tipo as equipo_tipo, e.horas_operacion as horas_totales,
           CASE WHEN e.estado IN ('Critico', 'Fuera de Servicio') THEN 1 ELSE 0 END as falla_ocurrida
    FROM datos_equipos d
    JOIN equipos e ON d.equipo_id = e.id
    ORDER BY d.fecha_hora
    ''', conn)
    
    conn.close()
    
    if df.empty:
        return None
    
    # Crear características adicionales
    df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
    
    # Variables para predicción
    features = ['temp_motor', 'presion_aceite', 'rpm_motor', 'horas_motor',
                'presion_hidraulica', 'temp_aceite_hidraulico', 'nivel_aceite_hidraulico',
                'desgaste_pastillas', 'presion_neumaticos', 'desgaste_neumaticos',
                'nivel_combustible', 'consumo_combustible', 'carga_actual']
    
    # Eliminar filas con valores nulos en características
    df_clean = df.dropna(subset=features)
    
    return df_clean, features

def entrenar_modelo_clasificacion():
    """Entrenar modelo de clasificación para predicción de fallas"""
    datos = preparar_datos_entrenamiento()
    if datos is None:
        return None, None, 0
    
    df, features = datos
    
    # Variable objetivo: ¿Ocurrirá una falla?
    # Creamos una variable sintética basada en umbrales críticos
    df['falla'] = (
        (df['temp_motor'] > 100) |
        (df['presion_aceite'] < 30) |
        (df['presion_hidraulica'] < 170) |
        (df['desgaste_neumaticos'] > 70) |
        (df['desgaste_pastillas'] > 75)
    ).astype(int)
    
    X = df[features]
    y = df['falla']
    
    # Dividir datos
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Escalar características
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Entrenar modelo
    modelo = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    modelo.fit(X_train_scaled, y_train)
    
    # Evaluar
    y_pred = modelo.predict(X_test_scaled)
    precision = accuracy_score(y_test, y_pred)
    
    return modelo, scaler, precision

def entrenar_modelo_regresion():
    """Entrenar modelo de regresión para predecir horas restantes hasta falla"""
    datos = preparar_datos_entrenamiento()
    if datos is None:
        return None, None, 0
    
    df, features = datos
    
    # Variable objetivo: horas restantes estimadas (simulada)
    # Basado en desgaste y temperatura
    df['horas_restantes'] = np.where(
        df['desgaste_neumaticos'] > 50,
        np.maximum(0, 100 - df['desgaste_neumaticos'] * 1.5),
        np.where(
            df['temp_motor'] > 95,
            np.maximum(0, 200 - (df['temp_motor'] - 95) * 20),
            500 + df['horas_motor'] * 0.1
        )
    )
    
    X = df[features]
    y = df['horas_restantes']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    modelo = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    modelo.fit(X_train_scaled, y_train)
    
    y_pred = modelo.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return modelo, scaler, rmse

def predecir_falla_equipo(equipo_id):
    """Predecir probabilidad de falla para un equipo específico"""
    conn = get_connection()
    
    # Obtener últimos datos del equipo
    df_equipo = pd.read_sql_query('''
    SELECT * FROM datos_equipos 
    WHERE equipo_id = ? 
    ORDER BY fecha_hora DESC 
    LIMIT 1
    ''', conn, params=(equipo_id,))
    
    # Obtener información del equipo
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipos WHERE id = ?", (equipo_id,))
    fila_equipo = cursor.fetchone()
    if not fila_equipo:
        conn.close()
        return None
    equipo = dict(fila_equipo)
    
    conn.close()
    
    if df_equipo.empty:
        return None
    
    # Entrenar modelo
    modelo_clas, scaler_clas, precision_clas = entrenar_modelo_clasificacion()
    modelo_reg, scaler_reg, rmse_reg = entrenar_modelo_regresion()
    
    if modelo_clas is None or modelo_reg is None:
        return None
    
    features = ['temp_motor', 'presion_aceite', 'rpm_motor', 'horas_motor',
                'presion_hidraulica', 'temp_aceite_hidraulico', 'nivel_aceite_hidraulico',
                'desgaste_pastillas', 'presion_neumaticos', 'desgaste_neumaticos',
                'nivel_combustible', 'consumo_combustible', 'carga_actual']
    
    X_nuevo = df_equipo[features]
    
    # Predicción de probabilidad de falla
    X_nuevo_scaled_clas = scaler_clas.transform(X_nuevo)
    prob_falla = modelo_clas.predict_proba(X_nuevo_scaled_clas)[0][1]
    
    # Predicción de horas restantes
    X_nuevo_scaled_reg = scaler_reg.transform(X_nuevo)
    horas_restantes = modelo_reg.predict(X_nuevo_scaled_reg)[0]
    
    # Importancia de características
    importancias = dict(zip(features, modelo_clas.feature_importances_))
    importancias_ordenadas = sorted(importancias.items(), key=lambda x: x[1], reverse=True)
    
    # Determinar severidad
    if prob_falla > 0.7:
        severidad = 'Critica'
    elif prob_falla > 0.4:
        severidad = 'Alta'
    elif prob_falla > 0.2:
        severidad = 'Media'
    else:
        severidad = 'Baja'
    
    # Generar recomendación
    recomendacion = generar_recomendacion(equipo, df_equipo.iloc[0], prob_falla, severidad, importancias_ordenadas[:3])
    
    # Guardar predicción en base de datos
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO predicciones_falla (equipo_id, componente, probabilidad_falla, dias_hasta_falla,
                                     severidad, recomendacion, modelo_utilizado)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (equipo_id, 
          importancias_ordenadas[0][0], 
          round(float(prob_falla), 4),
          max(0, int(horas_restantes / 24)),
          severidad,
          recomendacion,
          f'RandomForest (Precisión: {precision_clas:.2f})'))
    conn.commit()
    conn.close()
    
    return {
        'equipo': equipo,
        'probabilidad_falla': round(float(prob_falla) * 100, 1),
        'horas_restantes_estimadas': max(0, round(float(horas_restantes), 0)),
        'dias_restantes_estimados': max(0, int(horas_restantes / 24)),
        'severidad': severidad,
        'precision_modelo': round(float(precision_clas) * 100, 1),
        'rmse_modelo': round(float(rmse_reg), 1),
        'factores_criticos': importancias_ordenadas[:5],
        'recomendacion': recomendacion,
        'datos_actuales': df_equipo.iloc[0].to_dict()
    }

def generar_recomendacion(equipo, datos, prob_falla, severidad, factores_criticos):
    """Generar recomendación basada en la predicción"""
    recomendaciones = []
    
    recomendaciones.append(f"Análisis para {equipo['nombre']} ({equipo['codigo']}):")
    recomendaciones.append(f"")
    
    if severidad == 'Critica':
        recomendaciones.append("⚠️ ACCIÓN INMEDIATA REQUERIDA")
        recomendaciones.append("Detener el equipo y realizar inspección completa.")
    elif severidad == 'Alta':
        recomendaciones.append("⚠️ ALTA PRIORIDAD")
        recomendaciones.append("Programar mantenimiento en las próximas 24-48 horas.")
    elif severidad == 'Media':
        recomendaciones.append("⚡ MONITOREO CERCANO")
        recomendaciones.append("Incrementar frecuencia de monitoreo y planificar mantenimiento.")
    else:
        recomendaciones.append("✅ ESTADO ESTABLE")
        recomendaciones.append("Continuar con programa de mantenimiento preventivo normal.")
    
    recomendaciones.append("")
    recomendaciones.append("Factores principales a revisar:")
    for factor, importancia in factores_criticos:
        nombre_factor = {
            'temp_motor': 'Temperatura del motor',
            'presion_aceite': 'Presión de aceite',
            'rpm_motor': 'RPM del motor',
            'horas_motor': 'Horas de motor',
            'presion_hidraulica': 'Presión hidráulica',
            'temp_aceite_hidraulico': 'Temperatura aceite hidráulico',
            'nivel_aceite_hidraulico': 'Nivel aceite hidráulico',
            'desgaste_pastillas': 'Desgaste de pastillas de freno',
            'presion_neumaticos': 'Presión de neumáticos',
            'desgaste_neumaticos': 'Desgaste de neumáticos',
            'nivel_combustible': 'Nivel de combustible',
            'consumo_combustible': 'Consumo de combustible',
            'carga_actual': 'Carga actual'
        }.get(factor, factor)
        
        valor_actual = datos.get(factor, 'N/A')
        recomendaciones.append(f"  • {nombre_factor}: {valor_actual} (importancia: {importancia*100:.1f}%)")
    
    return '\n'.join(recomendaciones)

def obtener_predicciones_guardadas():
    """Obtener predicciones almacenadas en la base de datos"""
    conn = get_connection()
    df = pd.read_sql_query('''
    SELECT p.*, e.codigo as equipo_codigo, e.nombre as equipo_nombre, e.tipo as equipo_tipo
    FROM predicciones_falla p
    JOIN equipos e ON p.equipo_id = e.id
    ORDER BY p.fecha_prediccion DESC
    LIMIT 50
    ''', conn)
    conn.close()
    return df

def obtener_resumen_predicciones():
    """Obtener resumen de predicciones por severidad"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT severidad, COUNT(*) as cantidad
    FROM (
        SELECT p.*, MAX(fecha_prediccion) as ultima_fecha
        FROM predicciones_falla p
        GROUP BY p.equipo_id
    ) ultimas_predicciones
    GROUP BY severidad
    ''')
    
    resultados = cursor.fetchall()
    conn.close()
    
    return {r['severidad']: r['cantidad'] for r in resultados}

def analizar_tendencias_falla(equipo_id, dias=7):
    """Analizar tendencias de parámetros críticos para un equipo"""
    conn = get_connection()
    
    df = pd.read_sql_query('''
    SELECT fecha_hora, temp_motor, presion_aceite, presion_hidraulica,
           desgaste_neumaticos, desgaste_pastillas, consumo_combustible
    FROM datos_equipos
    WHERE equipo_id = ?
    ORDER BY fecha_hora DESC
    LIMIT ?
    ''', conn, params=(equipo_id, dias * 24))  # Aproximadamente 1 lectura por hora
    
    conn.close()
    
    if df.empty or len(df) < 2:
        return None
    
    df = df.sort_values('fecha_hora')
    
    tendencias = {}
    parametros = ['temp_motor', 'presion_aceite', 'presion_hidraulica',
                  'desgaste_neumaticos', 'desgaste_pastillas', 'consumo_combustible']
    
    for param in parametros:
        if param in df.columns:
            valores = df[param].dropna()
            if len(valores) > 1:
                # Cálculo de tendencia lineal simple
                x = np.arange(len(valores))
                y = valores.values
                pendiente = np.polyfit(x, y, 1)[0]
                
                if pendiente > 0.5:
                    tendencia = 'Tendencia al alza'
                elif pendiente < -0.5:
                    tendencia = 'Tendencia a la baja'
                else:
                    tendencia = 'Estable'
                
                tendencias[param] = {
                    'tendencia': tendencia,
                    'pendiente': round(float(pendiente), 4),
                    'valor_actual': float(valores.iloc[-1]),
                    'valor_inicial': float(valores.iloc[0]),
                    'variacion': round(float(valores.iloc[-1] - valores.iloc[0]), 2)
                }
    
    return tendencias
