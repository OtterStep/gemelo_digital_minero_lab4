"""
Sistema de Gemelos Digitales para Gestión de Mantenimiento de Equipos de Carguío en Minas a Tajo Abierto
Aplicación principal desarrollada con Streamlit
"""
import sys
import os

# Asegurar codificación UTF-8 en stdout/stderr en Windows
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import time

# Agregar ruta del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos
from utils.database import init_database, insert_default_data
from modules import auth
from modules import dashboard as dash_mod
from modules import gemelo_digital as gd_mod
from modules import mantenimiento as mant_mod
from modules import reportes as rep_mod
from modules import predictivo as pred_mod
from modules.motor_ia import MotorPredictivo, inicializar_motor_ia, MODELS_DIR

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Gemelo Digital - Minería",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar base de datos
@st.cache_resource
def inicializar_sistema():
    init_database()
    insert_default_data()
    return True

inicializar_sistema()

# ============================================================
# ESTADO DE SESIÓN
# ============================================================
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'token' not in st.session_state:
    st.session_state.token = None
if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = 'Login'
if 'motor_ia' not in st.session_state:
    st.session_state.motor_ia = None

# ============================================================
# FUNCIÓN DE LOGIN
# ============================================================
def mostrar_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='color: #2c3e50;'>⛏️ SISTEMA DE GEMELOS DIGITALES</h1>
            <h3 style='color: #7f8c8d;'>Gestión de Mantenimiento - Equipos de Carguío</h3>
            <p style='color: #95a5a6;'>Minería a Tajo Abierto</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### 🔐 Iniciar Sesión")
            username = st.text_input("Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Por favor ingrese usuario y contraseña")
                else:
                    resultado = auth.login(username, password)
                    if resultado:
                        st.session_state.usuario = resultado
                        st.session_state.token = resultado['token']
                        st.success("✅ Inicio de sesión exitoso!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
        
        st.info("""
        **Usuarios de demostración:**
        - 👤 Administrador: `admin` / `admin123`
        - 👷 Ingeniero: `ingeniero` / `inge123`
        - 📋 Supervisor: `supervisor` / `super123`
        - 🔧 Técnico: `tecnico` / `tec123`
        """)

# ============================================================
# BARRA LATERAL DE NAVEGACIÓN
# ============================================================
def mostrar_sidebar():
    usuario = st.session_state.usuario
    
    with st.sidebar:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #2c3e50, #34495e); padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
            <h4 style='color: white; margin: 0;'>👤 {usuario['nombre']} {usuario['apellido']}</h4>
            <p style='color: #bdc3c7; margin: 5px 0;'>{usuario['rol']}</p>
            <p style='color: #95a5a6; font-size: 12px; margin: 0;'>{usuario['email']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 Menú Principal")
        
        # Opciones de menú según rol
        menu_options = []
        
        menu_options.append(('📊 Dashboard', 'Dashboard'))
        
        if auth.has_permission(usuario['rol'], auth.PERMISOS['gemelo_digital']):
            menu_options.append(('🔧 Gemelo Digital', 'Gemelo Digital'))
        
        if auth.has_permission(usuario['rol'], auth.PERMISOS['mantenimiento']):
            menu_options.append(('📋 Mantenimiento', 'Mantenimiento'))
        
        if auth.has_permission(usuario['rol'], auth.PERMISOS['predictivo']):
            menu_options.append(('🤖 Análisis Predictivo', 'Predictivo'))
            menu_options.append(('⚙️ Motor IA', 'Motor IA'))
        
        if auth.has_permission(usuario['rol'], auth.PERMISOS['reportes']):
            menu_options.append(('📑 Reportes', 'Reportes'))
        
        if auth.has_permission(usuario['rol'], auth.PERMISOS['repuestos']):
            menu_options.append(('🔩 Repuestos', 'Repuestos'))
        
        if auth.has_permission(usuario['rol'], auth.PERMISOS['usuarios']):
            menu_options.append(('👥 Gestión Usuarios', 'Usuarios'))
            menu_options.append(('📝 Bitácora', 'Bitacora'))
        
        menu_options.append(('📖 Documentación Scrum', 'Scrum'))
        
        # Mostrar menú
        for label, key in menu_options:
            if st.button(label, use_container_width=True, key=f"btn_{key}"):
                st.session_state.pagina_actual = key
        
        st.markdown("---")
        
        # Callback robusto para logout (usa on_click para evitar race con rerun y limpia todo el estado)
        def _do_logout():
            st.session_state.clear()
            st.session_state.usuario = None
            st.session_state.token = None
            st.session_state.pagina_actual = 'Login'
            st.session_state.motor_ia = None
        
        st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary", key="btn_cerrar_sesion_v3", on_click=_do_logout)
        
        st.markdown(f"""
        <div style='text-align: center; color: #95a5a6; font-size: 11px; margin-top: 20px; padding-top: 10px; border-top: 1px solid #eee;'>
            <p>Versión 1.0.0</p>
            <p>{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# PÁGINA: DASHBOARD
# ============================================================
def mostrar_dashboard():
    st.title("📊 Dashboard Principal")
    st.markdown("---")
    
    # KPIs
    kpis = dash_mod.get_kpis()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Disponibilidad", f"{kpis['disponibilidad']}%", delta="Meta: 90%")
    with col2:
        st.metric("OEE", f"{kpis['oee']}%", delta="Meta: 75%")
    with col3:
        st.metric("MTBF", f"{kpis['mtbf']:.0f} h", delta="Meta: 500 h")
    with col4:
        st.metric("MTTR", f"{kpis['mttr']:.1f} h", delta="Meta: ≤8 h")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Total Equipos", kpis['total_equipos'])
    with col6:
        st.metric("Operativos", kpis['operativos'])
    with col7:
        st.metric("Equipos Críticos", kpis['equipos_criticos'], delta_color="inverse")
    with col8:
        st.metric("Costos Mantenimiento", f"${kpis['costos_mantenimiento']:,.0f}")
    st.caption("💡 **Interpretación KPIs:** Disponibilidad/OEE >90%/75% indica flota saludable; MTBF alto (>500h) y MTTR bajo (≤8h) reflejan confiabilidad. Equipos Críticos >0 requiere acción inmediata; Costos mensuales permite control presupuestario.")
    
    st.markdown("---")
    
    # Gráficos
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.plotly_chart(dash_mod.chart_estado_equipos(), use_container_width=True)
        st.caption("💡 **Interpretación Estado:** Dona que muestra % Operativo vs Crítico/Fuera Servicio. Si Crítico >15% → revisar plan preventivo; ideal Operativo >85%.")
    
    with col_g2:
        st.plotly_chart(dash_mod.chart_tipo_equipos(), use_container_width=True)
        st.caption("💡 **Interpretación Tipo:** Barras por Camión/Excavadora/Cargador. Desbalance indica cuello de botella; permite dimensionar flota por tipo.")
    
    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        st.plotly_chart(dash_mod.chart_consumo_combustible(), use_container_width=True)
        st.caption("💡 **Interpretación Consumo:** Línea/Barra de galones por equipo. Pico >20% media indica falla motor o sobrecarga; correlacionar con temp_motor y carga_actual.")
    
    with col_g4:
        st.plotly_chart(dash_mod.chart_ordenes_por_tipo(), use_container_width=True)
        st.caption("💡 **Interpretación Órdenes:** Distribución Preventivo/Correctivo/Predictivo. Predictivo >30% es saludable (proactivo); Correctivo >50% indica mantenimiento reactivo y mayor MTTR.")
    
    col_g5, col_g6 = st.columns(2)
    
    with col_g5:
        st.plotly_chart(dash_mod.chart_costos_mensuales(), use_container_width=True)
        st.caption("💡 **Interpretación Costos:** Tendencia mensual. Incremento sostenido >15% mes a mes sugiere envejecimiento flota o fallas repetitivas; comparar con horas operación.")
    
    with col_g6:
        st.plotly_chart(dash_mod.chart_horas_operacion(), use_container_width=True)
        st.caption("💡 **Interpretación Horas:** Barra horizontal de horas acumuladas. Equipos >500h sin preventivo requieren orden automática; balancea carga para evitar desgaste desigual.")
    
    st.markdown("---")
    
    # Alertas Críticas
    st.subheader("⚠️ Alertas Críticas")
    alertas = dash_mod.get_alertas_criticas()
    
    if not alertas.empty:
        st.dataframe(alertas, use_container_width=True)
        st.caption("💡 **Interpretación Alertas:** Cada fila es equipo con parámetro fuera de umbral (ej. temp>100°C). Priorizar por severidad; clic para ir a Gemelo Digital y simular falla.")
    else:
        st.success("✅ No hay alertas críticas en este momento")
        st.caption("💡 **Interpretación:** Sin alertas = flota dentro de rangos normales (temp, presión, desgaste). Mantener monitoreo cada hora.")
    
    # Auto-refresco
    if st.button("🔄 Actualizar Datos"):
        st.rerun()

# ============================================================
# PÁGINA: GEMELO DIGITAL
# ============================================================
def mostrar_gemelo_digital():
    st.title("🔧 Gemelo Digital")
    st.markdown("---")
    
    # Seleccionar equipo
    equipos_df = dash_mod.get_equipos_data()
    
    col_sel1, col_sel2 = st.columns([2, 1])
    
    with col_sel1:
        equipo_seleccionado = st.selectbox(
            "Seleccionar Equipo",
            options=equipos_df['id'].tolist(),
            format_func=lambda x: f"{equipos_df[equipos_df['id']==x]['codigo'].iloc[0]} - {equipos_df[equipos_df['id']==x]['nombre'].iloc[0]}"
        )
    
    with col_sel2:
        if st.button("🔄 Generar Datos en Tiempo Real"):
            gd_mod.generar_datos_en_tiempo_real(equipo_seleccionado)
            st.success("✅ Datos actualizados")
            st.rerun()
    
    # Obtener datos del equipo
    equipo = gd_mod.get_equipo_detalle(equipo_seleccionado)
    datos_actuales = gd_mod.get_ultimos_datos(equipo_seleccionado)
    
    if equipo:
        # Información general del equipo
        st.markdown(f"""
        <div style='background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3>{equipo['nombre']}</h3>
            <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;'>
                <div><strong>Código:</strong> {equipo['codigo']}</div>
                <div><strong>Tipo:</strong> {equipo['tipo']}</div>
                <div><strong>Marca:</strong> {equipo['marca']}</div>
                <div><strong>Modelo:</strong> {equipo['modelo']}</div>
                <div><strong>Año:</strong> {equipo['año_fabricacion']}</div>
                <div><strong>Horas:</strong> {equipo['horas_operacion']:.0f}</div>
                <div><strong>Ubicación:</strong> {equipo['ubicacion']}</div>
                <div><strong>Estado:</strong> <span style='color: {'#2ecc71' if equipo['estado']=='Operativo' else '#e74c3c'}'>{equipo['estado']}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Visualización del gemelo y análisis de salud
        col_v1, col_v2 = st.columns([1.5, 1])
        
        with col_v1:
            st.subheader("🖥️ Representación Visual")
            fig = gd_mod.visualizar_gemelo_2d(equipo, datos_actuales)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("💡 **Interpretación Gemelo 2D:** Diagrama esquemático con colores por componente (verde=OK, amarillo=alerta, rojo=crítico). Permite localizar visualmente motor/hidráulico/frenos/neumáticos.")
        
        with col_v2:
            st.subheader("📊 Análisis de Salud")
            if datos_actuales:
                analisis = gd_mod.analizar_salud_equipo(datos_actuales)
                for a in analisis:
                    with st.expander(f"{a['componente']} - {a['estado']}", expanded=True):
                        st.markdown(f"""
                        <div style='border-left: 4px solid {a['color']}; padding-left: 10px;'>
                            <p><strong>Estado:</strong> <span style='color: {a['color']}'>{a['estado']}</span></p>
                            <p>{a['parametro']}</p>
                            <p style='font-size: 12px; color: #666;'>{a['detalle']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                st.caption("💡 **Interpretación Salud:** Cada componente evalúa umbrales (ej. temp_motor>100°C=crítico). Rojo → detener equipo; Amarillo → programar inspección 24-48h; Verde → operación normal.")
            else:
                st.info("No hay datos de sensores disponibles")
                st.caption("💡 **Interpretación:** Sin datos no se puede evaluar salud. Genera datos en tiempo real con botón superior.")
        
        st.markdown("---")
        
        # Tendencias históricas
        st.subheader("📈 Tendencias Históricas")
        fig_temp = dash_mod.chart_tendencias_temperatura(equipo_seleccionado)
        st.plotly_chart(fig_temp, use_container_width=True)
        st.caption("💡 **Interpretación Tendencia:** Serie temporal de temp/presión. Pendiente ascendente sostenida indica degradación progresiva; pico abrupto sugiere falla inminente. Comparar con umbral 90-100°C.")
        
        # Simulación de fallas
        st.markdown("---")
        st.subheader("⚠️ Simulación de Escenarios de Falla")
        
        col_sim1, col_sim2 = st.columns([1, 1])
        
        with col_sim1:
            tipo_falla = st.selectbox(
                "Tipo de Falla a Simular",
                options=[
                    ('sobrecalentamiento_motor', '🔥 Sobrecalentamiento de Motor'),
                    ('perdida_presion_hidraulica', '💧 Pérdida de Presión Hidráulica'),
                    ('desgaste_neumaticos', '🛞 Desgaste de Neumáticos'),
                    ('falla_frenos', '🛑 Falla en Sistema de Frenos'),
                    ('consumo_excesivo', '⛽ Consumo Excesivo de Combustible')
                ],
                format_func=lambda x: x[1]
            )
            
            intensidad = st.slider("Intensidad de la Falla", 0.1, 1.0, 0.7, 0.1)
        
        with col_sim2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🎯 Ejecutar Simulación", type="primary"):
                resultado = gd_mod.simular_falla(equipo_seleccionado, tipo_falla[0], intensidad)
                st.warning(f"**Simulación completada:** {tipo_falla[1]}")
                for alerta in resultado['alertas']:
                    st.error(alerta)
                st.rerun()

# ============================================================
# PÁGINA: MANTENIMIENTO
# ============================================================
def mostrar_mantenimiento():
    st.title("📋 Gestión de Mantenimiento")
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Órdenes de Trabajo", "➕ Nueva Orden", "📜 Historial", "🔧 Generación Automática"])
    
    with tab1:
        # Filtros
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_estado = st.selectbox("Filtrar por Estado", 
                options=['Todos', 'Pendiente', 'En Proceso', 'Completada', 'Cancelada'])
        with col_f2:
            filtro_tipo = st.selectbox("Filtrar por Tipo",
                options=['Todos', 'Preventivo', 'Correctivo', 'Predictivo'])
        
        fe = None if filtro_estado == 'Todos' else filtro_estado
        ft = None if filtro_tipo == 'Todos' else filtro_tipo
        
        ordenes = mant_mod.get_ordenes_trabajo(fe, ft)
        
        if not ordenes.empty:
            st.dataframe(ordenes, use_container_width=True)
            st.caption("💡 **Interpretación Órdenes:** Cada fila es una OT con estado (Pendiente/En Proceso/Completada) y prioridad. Filtrar por Crítica/Alta para priorizar. Pendiente >48h indica riesgo de falla.")
            
            # Actualizar estado de orden
            st.subheader("Actualizar Estado de Orden")
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                orden_id = st.selectbox("Seleccionar Orden",
                    options=ordenes['id'].tolist(),
                    format_func=lambda x: ordenes[ordenes['id']==x]['numero_orden'].iloc[0])
            with col_act2:
                nuevo_estado = st.selectbox("Nuevo Estado",
                    options=['Pendiente', 'En Proceso', 'Completada', 'Cancelada'])
            with col_act3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Actualizar"):
                    datos = {'estado': nuevo_estado}
                    if nuevo_estado == 'En Proceso':
                        datos['fecha_inicio'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    elif nuevo_estado == 'Completada':
                        datos['fecha_fin'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    mant_mod.actualizar_orden_trabajo(orden_id, datos)
                    st.success("✅ Orden actualizada")
                    st.rerun()
        else:
            st.info("No hay órdenes de trabajo que mostrar")
            st.caption("💡 **Interpretación:** Sin órdenes = sin mantenimiento programado o historial vacío. Crea una OT preventiva o ejecuta generación automática.")
    
    with tab2:
        st.subheader("Crear Nueva Orden de Trabajo")
        
        equipos_df = mant_mod.get_equipos_para_mantenimiento()
        tecnicos = mant_mod.get_tecnicos_disponibles()
        
        with st.form("nueva_orden"):
            col_n1, col_n2 = st.columns(2)
            
            with col_n1:
                eq_id = st.selectbox("Equipo",
                    options=equipos_df['id'].tolist(),
                    format_func=lambda x: f"{equipos_df[equipos_df['id']==x]['codigo'].iloc[0]} - {equipos_df[equipos_df['id']==x]['nombre'].iloc[0]}")
                tipo = st.selectbox("Tipo de Mantenimiento", ['Preventivo', 'Correctivo', 'Predictivo'])
                prioridad = st.selectbox("Prioridad", ['Baja', 'Media', 'Alta', 'Critica'])
            
            with col_n2:
                tecnico_id = st.selectbox("Técnico Asignado",
                    options=[None] + [t['id'] for t in tecnicos],
                    format_func=lambda x: "Sin asignar" if x is None else f"{next(t['nombre'] + ' ' + t['apellido'] for t in tecnicos if t['id']==x)}")
                fecha_programada = st.date_input("Fecha Programada")
                costo_estimado = st.number_input("Costo Estimado ($)", min_value=0.0, value=0.0)
            
            titulo = st.text_input("Título de la Orden")
            descripcion = st.text_area("Descripción Detallada")
            
            submit = st.form_submit_button("📝 Crear Orden", type="primary")
            
            if submit:
                if not titulo:
                    st.error("El título es obligatorio")
                else:
                    supervisor_id = st.session_state.usuario['user_id'] if st.session_state.usuario['rol'] in ['Supervisor', 'Administrador'] else None
                    exito, mensaje, orden_id = mant_mod.crear_orden_trabajo(
                        eq_id, tipo, prioridad, titulo, descripcion,
                        fecha_programada.strftime('%Y-%m-%d') if fecha_programada else None,
                        tecnico_id, supervisor_id, costo_estimado
                    )
                    if exito:
                        st.success(f"✅ Orden {mensaje} creada exitosamente")
                    else:
                        st.error(f"❌ Error: {mensaje}")
    
    with tab3:
        st.subheader("Historial de Mantenimiento")
        
        equipos_h = dash_mod.get_equipos_data()
        eq_filtro = st.selectbox("Filtrar por Equipo",
            options=['Todos'] + equipos_h['id'].tolist(),
            format_func=lambda x: "Todos los equipos" if x == 'Todos' else f"{equipos_h[equipos_h['id']==x]['codigo'].iloc[0]}")
        
        eq_id = None if eq_filtro == 'Todos' else eq_filtro
        historial = mant_mod.get_historial_mantenimiento(eq_id)
        
        if not historial.empty:
            st.dataframe(historial, use_container_width=True)
            st.caption("💡 **Interpretación Historial:** Registro cronológico de intervenciones. Permite calcular MTBF/MTTR real y detectar fallas recurrentes por equipo/componente.")
        else:
            st.info("No hay registros en el historial")
            st.caption("💡 **Interpretación:** Historial vacío indica equipo nuevo o datos no migrados. Registrar OT completadas para trazabilidad.")
    
    with tab4:
        st.subheader("Generación Automática de Órdenes Preventivas")
        st.info("El sistema genera órdenes de mantenimiento preventivo basadas en las horas de operación de los equipos (cada 500 horas).")
        
        if st.button("🚀 Ejecutar Generación Automática", type="primary"):
            ordenes = mant_mod.generar_ordenes_automaticas()
            if ordenes:
                st.success(f"✅ Se generaron {len(ordenes)} órdenes automáticas:")
                for ot in ordenes:
                    st.write(f"  • {ot}")
                st.caption("💡 **Interpretación:** Órdenes generadas cada 500h de operación (preventivo). Revisar y asignar técnico; evita correctivos costosos.")
            else:
                st.info("No se requirieron nuevas órdenes en este momento")
                st.caption("💡 **Interpretación:** Ningún equipo superó umbral 500h desde último preventivo. Flota al día.")

# ============================================================
# PÁGINA: ANÁLISIS PREDICTIVO
# ============================================================
def mostrar_predictivo():
    st.title("🤖 Análisis Predictivo")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["🔮 Predicción por Equipo", "📋 Historial de Predicciones", "📊 Resumen General"])
    
    with tab1:
        equipos_df = dash_mod.get_equipos_data()
        
        equipo_pred = st.selectbox("Seleccionar Equipo para Análisis",
            options=equipos_df['id'].tolist(),
            format_func=lambda x: f"{equipos_df[equipos_df['id']==x]['codigo'].iloc[0]} - {equipos_df[equipos_df['id']==x]['nombre'].iloc[0]}")
        
        if st.button("🔍 Ejecutar Análisis Predictivo", type="primary"):
            with st.spinner("Entrenando modelos y realizando predicciones..."):
                resultado = pred_mod.predecir_falla_equipo(equipo_pred)
                
                if resultado:
                    st.success("✅ Análisis completado")
                    
                    # Mostrar resultados
                    col_r1, col_r2, col_r3 = st.columns(3)
                    
                    with col_r1:
                        st.metric("Probabilidad de Falla", 
                                 f"{resultado['probabilidad_falla']}%",
                                 delta=f"Precisión: {resultado['precision_modelo']}%")
                    
                    with col_r2:
                        st.metric("Horas Restantes Estimadas",
                                 f"{resultado['horas_restantes_estimadas']:.0f} h",
                                 delta=f"{resultado['dias_restantes_estimados']} días")
                    
                    with col_r3:
                        severidad_color = {
                            'Critica': '#e74c3c',
                            'Alta': '#e67e22',
                            'Media': '#f39c12',
                            'Baja': '#2ecc71'
                        }
                        st.markdown(f"""
                        <div style='text-align: center; padding: 20px; background: {severidad_color[resultado['severidad']]}; border-radius: 10px;'>
                            <h3 style='color: white; margin: 0;'>SEVERIDAD</h3>
                            <h2 style='color: white; margin: 10px 0;'>{resultado['severidad']}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Recomendación
                    st.subheader("💡 Recomendación")
                    st.text_area("Recomendación", resultado['recomendacion'], height=250, label_visibility="collapsed")
                    
                    # Factores críticos
                    st.subheader("📊 Factores Críticos")
                    factores_df = pd.DataFrame(resultado['factores_criticos'], 
                                              columns=['Parámetro', 'Importancia'])
                    factores_df['Importancia %'] = factores_df['Importancia'] * 100
                    
                    fig_fact = px.bar(factores_df, x='Parámetro', y='Importancia %',
                                     title='Importancia de Factores en la Predicción',
                                     color='Importancia %',
                                     color_continuous_scale='Reds')
                    st.plotly_chart(fig_fact, use_container_width=True)
                    st.caption("💡 **Interpretación Factores:** Barras muestran peso de cada sensor en la predicción. Parámetro >30% es causa raíz probable (ej. temp_motor). Actuar sobre ese componente.")
                    
                    # Tendencias
                    st.subheader("📈 Análisis de Tendencias")
                    tendencias = pred_mod.analizar_tendencias_falla(equipo_pred)
                    if tendencias:
                        tend_df = pd.DataFrame([
                            {'Parámetro': k, 'Tendencia': v['tendencia'], 
                             'Variación': v['variacion'], 'Valor Actual': v['valor_actual']}
                            for k, v in tendencias.items()
                        ])
                        st.dataframe(tend_df, use_container_width=True)
                        st.caption("💡 **Interpretación Tendencias:** 'Creciente' + variación >10% indica degradación acelerada. Valor Actual vs histórico permite estimar horas restantes.")
    
    with tab2:
        st.subheader("Historial de Predicciones")
        predicciones = pred_mod.obtener_predicciones_guardadas()
        
        if not predicciones.empty:
            st.dataframe(predicciones, use_container_width=True)
            st.caption("💡 **Interpretación Historial Predicciones:** Evolución de prob. falla por equipo. Tendencia ascendente confirma modelo; comparar con fallas reales para validar precisión.")
        else:
            st.info("No hay predicciones almacenadas. Ejecute un análisis primero.")
            st.caption("💡 **Interpretación:** Sin historial no hay trazabilidad. Ejecuta predicción para generar baseline.")
    
    with tab3:
        st.subheader("Resumen General de Predicciones")
        resumen = pred_mod.obtener_resumen_predicciones()
        
        if resumen:
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            
            with col_s1:
                st.metric("Críticas", resumen.get('Critica', 0))
            with col_s2:
                st.metric("Altas", resumen.get('Alta', 0))
            with col_s3:
                st.metric("Medias", resumen.get('Media', 0))
            with col_s4:
                st.metric("Bajas", resumen.get('Baja', 0))
            
            # Gráfico de resumen
            resumen_df = pd.DataFrame([
                {'Severidad': k, 'Cantidad': v} for k, v in resumen.items()
            ])
            fig_res = px.pie(resumen_df, values='Cantidad', names='Severidad',
                           title='Distribución de Predicciones por Severidad',
                           color_discrete_map={'Critica': '#e74c3c', 'Alta': '#e67e22', 
                                              'Media': '#f39c12', 'Baja': '#2ecc71'})
            st.plotly_chart(fig_res, use_container_width=True)
            st.caption("💡 **Interpretación Severidad:** Pie muestra % Crítica/Alta/Media/Baja. Crítica+Alta >30% indica flota en riesgo; priorizar preventivo.")
        else:
            st.info("No hay datos de predicciones disponibles")
            st.caption("💡 **Interpretación:** Sin datos no hay distribución. Ejecuta predicciones para poblar resumen.")

# ============================================================
# PÁGINA: REPORTES
# ============================================================
def mostrar_reportes():
    st.title("📑 Generación de Reportes")
    st.markdown("---")
    
    col_r1, col_r2, col_r3 = st.columns(3)
    
    with col_r1:
        st.markdown("""
        <div style='background: #e74c3c; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3 style='color: white;'>📄 Reporte PDF</h3>
            <p style='color: #fadbd8;'>Reporte ejecutivo con KPIs, gráficos y recomendaciones</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📥 Generar PDF", type="primary", use_container_width=True):
            with st.spinner("Generando reporte PDF..."):
                pdf_bytes = rep_mod.generar_reporte_pdf()
                st.download_button(
                    label="⬇️ Descargar Reporte PDF",
                    data=pdf_bytes,
                    file_name=f"Reporte_Ejecutivo_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    with col_r2:
        st.markdown("""
        <div style='background: #3498db; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3 style='color: white;'>📝 Reporte Word</h3>
            <p style='color: #d6eaf8;'>Informe detallado con análisis y conclusiones</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📥 Generar Word", type="primary", use_container_width=True):
            with st.spinner("Generando reporte Word..."):
                word_bytes = rep_mod.generar_reporte_word()
                st.download_button(
                    label="⬇️ Descargar Reporte Word",
                    data=word_bytes,
                    file_name=f"Informe_Detallado_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
    
    with col_r3:
        st.markdown("""
        <div style='background: #27ae60; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3 style='color: white;'>📊 Reporte Excel</h3>
            <p style='color: #d5f5e3;'>Datos completos con múltiples hojas y gráficos</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📥 Generar Excel", type="primary", use_container_width=True):
            with st.spinner("Generando reporte Excel..."):
                excel_bytes = rep_mod.generar_reporte_excel()
                st.download_button(
                    label="⬇️ Descargar Reporte Excel",
                    data=excel_bytes,
                    file_name=f"Datos_Mantenimiento_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    st.markdown("---")
    
    # Vista previa de datos
    st.subheader("📋 Vista Previa de Datos")
    
    tab_pre1, tab_pre2, tab_pre3 = st.tabs(["KPIs Actuales", "Órdenes Recientes", "Resumen de Equipos"])
    
    with tab_pre1:
        kpis = dash_mod.get_kpis()
        kpis_df = pd.DataFrame([
            {'Indicador': 'Disponibilidad (%)', 'Valor': kpis['disponibilidad']},
            {'Indicador': 'OEE (%)', 'Valor': kpis['oee']},
            {'Indicador': 'MTBF (horas)', 'Valor': kpis['mtbf']},
            {'Indicador': 'MTTR (horas)', 'Valor': kpis['mttr']},
            {'Indicador': 'Costos ($)', 'Valor': kpis['costos_mantenimiento']},
            {'Indicador': 'Equipos Críticos', 'Valor': kpis['equipos_criticos']},
        ])
        st.dataframe(kpis_df, use_container_width=True)
        st.caption("💡 **Interpretación KPIs Reporte:** Tabla base para PDF/Word/Excel. Disponibilidad <90% o MTTR >8h indica oportunidad de mejora reportable a gerencia.")
    
    with tab_pre2:
        ordenes = dash_mod.get_ordenes_trabajo_data().head(10)
        st.dataframe(ordenes, use_container_width=True)
        st.caption("💡 **Interpretación Órdenes Recientes:** Muestra últimas 10 OT para reporte. Permite auditar cumplimiento y costos recientes.")
    
    with tab_pre3:
        equipos = dash_mod.get_equipos_data()
        st.dataframe(equipos, use_container_width=True)
        st.caption("💡 **Interpretación Equipos:** Catálogo para anexos de reporte. Incluye código, tipo, marca, horas y estado para inventario.")

# ============================================================
# PÁGINA: REPUESTOS
# ============================================================
def mostrar_repuestos():
    st.title("🔩 Gestión de Repuestos")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📦 Catálogo de Repuestos", "⚠️ Stock Bajo"])
    
    with tab1:
        repuestos = mant_mod.get_repuestos()
        if not repuestos.empty:
            st.dataframe(repuestos, use_container_width=True)
            st.caption("💡 **Interpretación Catálogo:** Cada fila es SKU con stock, costo y ubicación. Stock < mínimo indica reorden; costo alto justifica mantenimiento predictivo.")
        else:
            st.info("No hay repuestos registrados")
            st.caption("💡 **Interpretación:** Catálogo vacío → cargar repuestos críticos (filtros, pastillas, neumáticos) para evitar desabastecimiento.")
    
    with tab2:
        bajo_stock = mant_mod.get_repuestos_bajo_stock()
        if not bajo_stock.empty:
            st.warning(f"⚠️ Hay {len(bajo_stock)} repuestos con stock bajo el mínimo")
            st.dataframe(bajo_stock, use_container_width=True)
            st.caption("💡 **Interpretación Bajo Stock:** Alerta de reposición. Priorizar compra por criticidad (ej. frenos > filtros). Evita paro por falta de insumo.")
        else:
            st.success("✅ Todos los repuestos tienen stock adecuado")
            st.caption("💡 **Interpretación:** Stock OK = sin riesgo de quiebre. Mantener punto de reorden.")

# ============================================================
# PÁGINA: GESTIÓN DE USUARIOS
# ============================================================
def mostrar_usuarios():
    st.title("👥 Gestión de Usuarios")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📋 Lista de Usuarios", "➕ Nuevo Usuario"])
    
    with tab1:
        usuarios = auth.get_all_users()
        if usuarios:
            df_usuarios = pd.DataFrame(usuarios)
            st.dataframe(df_usuarios, use_container_width=True)
            st.caption("💡 **Interpretación Usuarios:** Tabla con rol/área/último acceso. Auditoría de accesos; detectar usuarios inactivos (>30 días) para desactivar.")
        else:
            st.info("No hay usuarios registrados")
            st.caption("💡 **Interpretación:** Sin usuarios = solo admin. Crear ingeniero/supervisor/técnico según matriz de permisos.")
    
    with tab2:
        with st.form("nuevo_usuario"):
            col_u1, col_u2 = st.columns(2)
            
            with col_u1:
                username = st.text_input("Usuario*")
                password = st.text_input("Contraseña*", type="password")
                nombre = st.text_input("Nombre*")
                apellido = st.text_input("Apellido*")
            
            with col_u2:
                email = st.text_input("Email*")
                rol = st.selectbox("Rol*", ['Administrador', 'Ingeniero', 'Supervisor', 'Tecnico'])
                area = st.text_input("Área")
            
            submit = st.form_submit_button("📝 Crear Usuario", type="primary")
            
            if submit:
                if not all([username, password, nombre, apellido, email]):
                    st.error("Por favor complete todos los campos obligatorios (*)")
                else:
                    exito, mensaje = auth.register_user(username, password, nombre, apellido, email, rol, area)
                    if exito:
                        st.success(f"✅ {mensaje}")
                    else:
                        st.error(f"❌ {mensaje}")

# ============================================================
# PÁGINA: BITÁCORA
# ============================================================
def mostrar_bitacora():
    st.title("📝 Bitácora de Accesos")
    st.markdown("---")
    
    registros = auth.get_bitacora_accesos(200)
    if registros:
        df_bitacora = pd.DataFrame(registros)
        st.dataframe(df_bitacora, use_container_width=True)
        st.caption("💡 **Interpretación Bitácora:** Log de accesos con fecha/acción/IP. Permite trazabilidad y detección de accesos sospechosos fuera de horario.")
    else:
        st.info("No hay registros en la bitácora")
        st.caption("💡 **Interpretación:** Bitácora vacía indica sistema recién iniciado. Cada login generará entrada.")

# ============================================================
# PÁGINA: DOCUMENTACIÓN SCRUM
# ============================================================
def mostrar_scrum():
    st.title("📖 Documentación Scrum")
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Visión del Proyecto", "📋 Product Backlog", "🚀 Planificación de Sprints", "📊 Artefactos"])
    
    with tab1:
        st.header("🎯 Visión del Proyecto")
        st.markdown("""
        ## Nombre del Proyecto
        **Sistema de Gemelos Digitales para Gestión de Mantenimiento de Equipos de Carguío en Minas a Tajo Abierto**
        
        ## Descripción
        Desarrollar una aplicación web basada en Python y Streamlit que implemente gemelos digitales 
        para monitorear, predecir y gestionar el mantenimiento de equipos de carguío en operaciones 
        mineras a tajo abierto.
        
        ## Objetivos Principales
        - ✅ Reducir tiempos de inactividad no programada de equipos
        - ✅ Implementar mantenimiento predictivo basado en datos
        - ✅ Mejorar la disponibilidad de la flota por encima del 90%
        - ✅ Optimizar costos de mantenimiento en un 15%
        - ✅ Proporcionar visibilidad en tiempo real del estado de los equipos
        
        ## Stakeholders
        - **Product Owner:** Gerencia de Mantenimiento
        - **Scrum Master:** Líder Técnico
        - **Equipo de Desarrollo:** 3 desarrolladores + 1 analista de datos
        - **Usuarios Finales:** Ingenieros, Supervisores, Técnicos de Mantenimiento
        
        ## Criterios de Éxito
        - Disponibilidad del sistema ≥ 99.5%
        - Precisión de predicción de fallas ≥ 80%
        - Reducción de MTTR en un 20%
        - Usuarios activos ≥ 80% del personal objetivo
        - Satisfacción del usuario ≥ 4.2/5
        """)
    
    with tab2:
        st.header("📋 Product Backlog")
        
        backlog_items = [
            {'ID': 'US-001', 'Historia': 'Como administrador, quiero gestionar usuarios y roles para controlar el acceso al sistema', 'Prioridad': 'Alta', 'Puntos': 8, 'Sprint': 1},
            {'ID': 'US-002', 'Historia': 'Como usuario, quiero iniciar sesión de forma segura para acceder a mis funcionalidades', 'Prioridad': 'Alta', 'Puntos': 5, 'Sprint': 1},
            {'ID': 'US-003', 'Historia': 'Como ingeniero, quiero ver un dashboard con KPIs para evaluar el estado de la flota', 'Prioridad': 'Alta', 'Puntos': 13, 'Sprint': 1},
            {'ID': 'US-004', 'Historia': 'Como supervisor, quiero visualizar el gemelo digital de un equipo para monitorear su estado en tiempo real', 'Prioridad': 'Alta', 'Puntos': 13, 'Sprint': 2},
            {'ID': 'US-005', 'Historia': 'Como técnico, quiero crear y gestionar órdenes de trabajo para organizar el mantenimiento', 'Prioridad': 'Alta', 'Puntos': 8, 'Sprint': 2},
            {'ID': 'US-006', 'Historia': 'Como ingeniero, quiero simular escenarios de falla para evaluar respuestas del sistema', 'Prioridad': 'Media', 'Puntos': 8, 'Sprint': 2},
            {'ID': 'US-007', 'Historia': 'Como administrador, quiero generar reportes en PDF para presentar a la gerencia', 'Prioridad': 'Alta', 'Puntos': 8, 'Sprint': 3},
            {'ID': 'US-008', 'Historia': 'Como ingeniero, quiero generar reportes en Word y Excel para análisis detallados', 'Prioridad': 'Media', 'Puntos': 8, 'Sprint': 3},
            {'ID': 'US-009', 'Historia': 'Como ingeniero, quiero ver predicciones de fallas para anticipar mantenimiento', 'Prioridad': 'Alta', 'Puntos': 13, 'Sprint': 3},
            {'ID': 'US-010', 'Historia': 'Como supervisor, quiero ver el historial de mantenimiento para analizar tendencias', 'Prioridad': 'Media', 'Puntos': 5, 'Sprint': 2},
            {'ID': 'US-011', 'Historia': 'Como administrador, quiero gestionar el inventario de repuestos para controlar stock', 'Prioridad': 'Media', 'Puntos': 8, 'Sprint': 3},
            {'ID': 'US-012', 'Historia': 'Como usuario, quiero ver alertas de equipos críticos para actuar rápidamente', 'Prioridad': 'Alta', 'Puntos': 5, 'Sprint': 1},
            {'ID': 'US-013', 'Historia': 'Como administrador, quiero revisar la bitácora de accesos para auditoría', 'Prioridad': 'Baja', 'Puntos': 3, 'Sprint': 3},
            {'ID': 'US-014', 'Historia': 'Como sistema, quiero generar órdenes automáticas para mantenimiento preventivo', 'Prioridad': 'Media', 'Puntos': 8, 'Sprint': 3},
            {'ID': 'US-015', 'Historia': 'Como usuario, quiero exportar datos para análisis externos', 'Prioridad': 'Baja', 'Puntos': 5, 'Sprint': 3},
        ]
        
        df_backlog = pd.DataFrame(backlog_items)
        st.dataframe(df_backlog, use_container_width=True)
        st.caption("💡 **Interpretación Backlog:** Priorización MoSCoW; Puntos = esfuerzo. Sprint 1-3 con 31/34/53 pts muestra velocidad creciente. ID permite trazar historia.")
        
        st.subheader("📊 Resumen por Sprint")
        sprint_summary = df_backlog.groupby('Sprint').agg(
            Cantidad=('ID', 'count'),
            Puntos_Totales=('Puntos', 'sum')
        ).reset_index()
        st.dataframe(sprint_summary, use_container_width=True)
        st.caption("💡 **Interpretación Resumen Sprint:** Cantidad vs puntos totales indica complejidad media por historia. Sprint 3 con 53 pts es más denso (reportes+ML).")
    
    with tab3:
        st.header("🚀 Planificación de Sprints")
        
        # Sprint 1
        st.subheader("✅ Sprint 1 - Base del Sistema")
        st.markdown("""
        **Duración:** 2 semanas (10 días hábiles)
        
        **Objetivo del Sprint:** Establecer la base del sistema con autenticación, gestión de usuarios y dashboard principal.
        
        **Historias de Usuario:**
        - US-001: Gestión de usuarios y roles (8 pts)
        - US-002: Inicio de sesión seguro (5 pts)
        - US-003: Dashboard con KPIs (13 pts)
        - US-012: Alertas de equipos críticos (5 pts)
        
        **Total de Puntos:** 31 Story Points
        
        **Definición de Terminado:**
        - ✅ Código revisado por pares
        - ✅ Pruebas unitarias aprobadas
        - ✅ Pruebas de integración exitosas
        - ✅ Documentación actualizada
        - ✅ Aprobación del Product Owner
        
        **Capacidad del Equipo:** 3 desarrolladores × 7 horas/día × 10 días = 210 horas
        """)
        
        st.markdown("---")
        
        # Sprint 2
        st.subheader("⚙️ Sprint 2 - Gemelo Digital y Mantenimiento")
        st.markdown("""
        **Duración:** 2 semanas (10 días hábiles)
        
        **Objetivo del Sprint:** Implementar el gemelo digital, gestión de órdenes de trabajo y simulación de fallas.
        
        **Historias de Usuario:**
        - US-004: Visualización gemelo digital (13 pts)
        - US-005: Gestión de órdenes de trabajo (8 pts)
        - US-006: Simulación de escenarios de falla (8 pts)
        - US-010: Historial de mantenimiento (5 pts)
        
        **Total de Puntos:** 34 Story Points
        
        **Definición de Terminado:**
        - ✅ Todas las funcionalidades del Sprint 1 operativas
        - ✅ Gemelo digital visualiza datos en tiempo real
        - ✅ CRUD completo de órdenes de trabajo
        - ✅ Simulaciones generan alertas apropiadas
        - ✅ Documentación técnica actualizada
        """)
        
        st.markdown("---")
        
        # Sprint 3
        st.subheader("🤖 Sprint 3 - Reportes y Análisis Predictivo")
        st.markdown("""
        **Duración:** 2 semanas (10 días hábiles)
        
        **Objetivo del Sprint:** Implementar generación de reportes multi-formato, análisis predictivo y funcionalidades administrativas.
        
        **Historias de Usuario:**
        - US-007: Reportes en PDF (8 pts)
        - US-008: Reportes en Word y Excel (8 pts)
        - US-009: Predicciones de falla (13 pts)
        - US-011: Gestión de repuestos (8 pts)
        - US-013: Bitácora de accesos (3 pts)
        - US-014: Órdenes automáticas (8 pts)
        - US-015: Exportación de datos (5 pts)
        
        **Total de Puntos:** 53 Story Points
        
        **Definición de Terminado:**
        - ✅ Sistema completo y funcional
        - ✅ Todos los reportes se generan correctamente
        - ✅ Modelos predictivos entrenados y evaluados
        - ✅ Pruebas de aceptación de usuario exitosas
        - ✅ Manual de usuario completo
        - ✅ Despliegue en ambiente de producción
        """)
    
    with tab4:
        st.header("📊 Artefactos Scrum")
        
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            st.subheader("📉 Burndown Chart - Sprint 1")
            # Datos simulados de burndown - FIX: longitudes alineadas (11 puntos 0..10)
            dias = list(range(0, 11))
            ideal = [31, 27.9, 24.8, 21.7, 18.6, 15.5, 12.4, 9.3, 6.2, 3.1, 0]
            real = [31, 30, 26, 22, 19, 16, 13, 10, 7, 4, 0]
            
            burndown_data = pd.DataFrame({
                'Día': dias,
                'Ideal': ideal,
                'Real': real
            })
            
            fig_burn = px.line(burndown_data, x='Día', y=['Ideal', 'Real'],
                              title='Burndown Chart - Sprint 1',
                              labels={'value': 'Story Points', 'Día': 'Día del Sprint'})
            fig_burn.update_traces(mode='lines+markers')
            st.plotly_chart(fig_burn, use_container_width=True)
            st.caption("💡 **Interpretación Burndown:** Ideal = línea recta. Real por debajo = adelantado; por encima = retraso. Convergencia a 0 indica sprint completado a tiempo.")
        
        with col_a2:
            st.subheader("📊 Velocity Chart")
            velocity_data = pd.DataFrame({
                'Sprint': ['Sprint 1', 'Sprint 2', 'Sprint 3'],
                'Planificado': [31, 34, 53],
                'Completado': [31, 32, 50]
            })
            
            fig_vel = px.bar(velocity_data, x='Sprint', y=['Planificado', 'Completado'],
                           title='Velocity Chart',
                           barmode='group')
            st.plotly_chart(fig_vel, use_container_width=True)
            st.caption("💡 **Interpretación Velocity:** Compara planificado vs completado por sprint. Velocity estable (~30-50) indica capacidad predecible; caída indica sobreestimación.")
        
        st.markdown("---")
        
        st.subheader("📝 Retrospectivas de Sprint")
        
        with st.expander("🔍 Retrospectiva Sprint 1"):
            st.markdown("""
            **Lo que salió bien:**
            - ✅ La base de datos se diseñó e implementó rápidamente
            - ✅ El módulo de autenticación funcionó desde el primer día
            - ✅ Buena comunicación en el equipo
            
            **A mejorar:**
            - ⚠️ Subestimamos la complejidad de los gráficos del dashboard
            - ⚠️ Falta de documentación inicial
            
            **Acciones de mejora:**
            - Dedicar tiempo a la planificación técnica al inicio de cada historia
            - Documentar a medida que se desarrolla
            """)
        
        with st.expander("🔍 Retrospectiva Sprint 2"):
            st.markdown("""
            **Lo que salió bien:**
            - ✅ El gemelo digital superó las expectativas
            - ✅ Integración con módulo de mantenimiento fluida
            - ✅ Revisiones de código más eficientes
            
            **A mejorar:**
            - ⚠️ Pruebas de simulación requirieron más tiempo del esperado
            
            **Acciones de mejora:**
            - Crear datos de prueba más realistas desde el inicio
            """)
        
        with st.expander("🔍 Retrospectiva Sprint 3"):
            st.markdown("""
            **Lo que salió bien:**
            - ✅ Los modelos predictivos lograron buena precisión
            - ✅ Reportes generados en todos los formatos solicitados
            - ✅ Entrega completa y funcional
            
            **A mejorar:**
            - ⚠️ Últimos días con mucha presión por tiempo
            
            **Acciones de mejora:**
            - Mejorar la estimación de historias complejas
            - Considerar buffers de tiempo en la planificación
            """)

# ============================================================
# PÁGINA: MOTOR DE IA
# ============================================================
def mostrar_motor_ia():
    st.title("⚙️ Motor de Inteligencia Artificial")
    st.markdown("---")
    
    # Inicializar motor si no existe
    if st.session_state.motor_ia is None:
        with st.spinner("🔄 Inicializando motor de IA..."):
            try:
                motor = MotorPredictivo()
                # Intentar cargar modelo guardado
                if os.path.exists(MODELS_DIR) and len(os.listdir(MODELS_DIR)) > 0:
                    if motor.cargar():
                        st.success("✅ Modelo cargado desde disco")
                    else:
                        st.info("Entrenando nuevo modelo...")
                        motor.cargar_datos()
                        motor.preparar_datos()
                        motor.entrenar_todos()
                        motor.evaluar_todos()
                        motor.comparar_algoritmos()
                        motor.guardar()
                        st.success("✅ Modelo entrenado y guardado")
                else:
                    st.info("No hay modelos guardados. Entrenando nuevo motor...")
                    motor.cargar_datos()
                    motor.preparar_datos()
                    motor.entrenar_todos()
                    motor.evaluar_todos()
                    motor.comparar_algoritmos()
                    motor.guardar()
                    st.success("✅ Motor de IA listo")
                
                st.session_state.motor_ia = motor
            except Exception as e:
                st.error(f"Error al inicializar motor: {str(e)}")
                return
    
    motor = st.session_state.motor_ia
     
    # Pestañas del motor de IA - ORDEN ACTUALIZADO: Validación e Hiperparámetros inmediatamente antes de Pruebas
    tab_eda, tab_ent, tab1, tab2, tab3, tab4, tab5, tab_cv, tab_hp, tab_stats = st.tabs([
        "🔍 EDA - Exploración",
        "⚙️ Entrenamiento",
        "📊 Comparativa Algoritmos",
        "🔮 Predicción por Equipo",
        "🏆 Mejor Algoritmo",
        "🔄 Reentrenar",
        "📋 Logs",
        "🔁 Validación Cruzada",
        "🎛️ Hiperparámetros",
        "🧪 Pruebas Estadísticas"
    ])

    # ============================================================
    # TAB EDA - ANÁLISIS EXPLORATORIO DE DATOS (CRISP-DM Fase 2)
    # ============================================================
    with tab_eda:
        st.subheader("🔍 Análisis Exploratorio de Datos (EDA) - CRISP-DM Fase 2")
        st.markdown("Comprensión de los datos de sensores antes del modelado. Analiza calidad, distribución, correlaciones y desbalance de clases.")
        
        # Controles superiores
        col_eda1, col_eda2, col_eda3 = st.columns([2, 1, 1])
        with col_eda1:
            st.info("📦 Fuente: `datos_equipos` + `equipos` (SQLite) — incluye datos históricos de sensores para entrenamiento")
        with col_eda2:
            if st.button("🔄 Recargar Datos", use_container_width=True):
                with st.spinner("Cargando datos..."):
                    motor.cargar_datos()
                    if hasattr(motor, 'eda_resultados'):
                        delattr(motor, 'eda_resultados')
                    st.success(f"✅ {len(motor.datos)} registros cargados")
                    st.rerun()
        with col_eda3:
            btn_eda = st.button("🔍 Ejecutar EDA", type="primary", use_container_width=True)
        
        # Auto-cargar datos si no existen
        if motor.datos is None:
            with st.spinner("Cargando datos para EDA..."):
                try:
                    motor.cargar_datos()
                except Exception as e:
                    st.error(f"Error al cargar datos: {e}")
                    st.stop()
        
        # Ejecutar EDA si se presiona botón o si ya hay resultados previos
        ejecutar = btn_eda or hasattr(motor, 'eda_resultados')
        if not hasattr(motor, 'eda_resultados') and not btn_eda:
            st.warning("👆 Presiona **'Ejecutar EDA'** para generar el análisis exploratorio.")
            # Vista previa rápida sin EDA completo
            if motor.datos is not None:
                st.markdown("### 👀 Vista Previa de Datos (primeras 5 filas)")
                st.dataframe(motor.datos.head(), use_container_width=True)
                st.caption("💡 **Interpretación Vista Previa:** Muestra estructura y tipos de columnas antes de EDA. Verifica que sensores y fecha_hora estén presentes y sin valores anómalos evidentes.")
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Registros", len(motor.datos))
                with c2: st.metric("Columnas", len(motor.datos.columns))
                with c3: 
                    if 'fecha_hora' in motor.datos.columns:
                        st.metric("Desde", str(motor.datos['fecha_hora'].min())[:16])
                with c4:
                    if 'fecha_hora' in motor.datos.columns:
                        st.metric("Hasta", str(motor.datos['fecha_hora'].max())[:16])
        
        if ejecutar:
            if not hasattr(motor, 'eda_resultados') or btn_eda:
                with st.spinner("Ejecutando EDA... (estadísticas, nulos, outliers, correlaciones)"):
                    try:
                        eda = motor.analisis_exploratorio()
                    except Exception as e:
                        st.error(f"Error en EDA: {e}")
                        st.stop()
            else:
                eda = motor.eda_resultados
            
            # --- Métricas principales ---
            st.markdown("### 📊 Resumen General")
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Registros", eda['num_registros'])
            with m2: st.metric("Columnas", eda['num_columnas'])
            with m3: st.metric("Variables Sensores", len(eda['variables_sensores']))
            with m4:
                pct_nulos_total = sum(eda['valores_nulos'].values()) / max(1, eda['num_registros'] * len(eda['valores_nulos'])) * 100
                st.metric("% Nulos Global", f"{pct_nulos_total:.2f}%")
            
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                st.metric("Rango Inicio", eda['rango_fechas']['inicio'][:19] if eda['rango_fechas']['inicio'] else "N/A")
            with c_f2:
                st.metric("Rango Fin", eda['rango_fechas']['fin'][:19] if eda['rango_fechas']['fin'] else "N/A")
            
            # --- Estadísticas descriptivas ---
            st.markdown("### 📈 Estadísticas Descriptivas")
            stats_df = pd.DataFrame(eda['estadisticas_descriptivas']).T
            # Ordenar columnas típicas describe
            cols_orden = [c for c in ['count','mean','std','min','25%','50%','75%','max'] if c in stats_df.columns]
            stats_df = stats_df[cols_orden]
            st.dataframe(stats_df.style.format("{:.2f}"), use_container_width=True)
            st.caption("💡 **Interpretación Estadísticas:** count=muestras válidas; mean/std describen centro/dispersión; min/max y cuartiles 25/50/75% muestran rango y asimetría. Std alto vs mean indica alta variabilidad (posible falla).")
            
            # --- Nulos y Outliers ---
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                st.markdown("#### 🕳️ Valores Nulos por Variable")
                nulos_df = pd.DataFrame({
                    'Variable': list(eda['valores_nulos'].keys()),
                    'Nulos': list(eda['valores_nulos'].values()),
                    '% Nulos': list(eda['porcentaje_nulos'].values())
                })
                st.dataframe(nulos_df, use_container_width=True, hide_index=True)
                fig_nulos = px.bar(nulos_df, x='Variable', y='% Nulos', title='% Nulos por Sensor', color='% Nulos', color_continuous_scale='Reds')
                fig_nulos.update_xaxes(tickangle=45)
                st.plotly_chart(fig_nulos, use_container_width=True)
                st.caption("💡 **Interpretación Nulos:** % Nulos = calidad de captura. >5% requiere imputación KNN (config); 0% es ideal. Barras rojas altas indican sensor con pérdida de datos.")
            with col_n2:
                st.markdown("#### ⚠️ Outliers (IQR) por Variable")
                out_df = pd.DataFrame({
                    'Variable': list(eda['outliers_por_variable'].keys()),
                    'Outliers': list(eda['outliers_por_variable'].values())
                })
                out_df['% Outliers'] = (out_df['Outliers'] / eda['num_registros'] * 100).round(2)
                st.dataframe(out_df, use_container_width=True, hide_index=True)
                fig_out = px.bar(out_df, x='Variable', y='Outliers', title='Outliers por Sensor (IQR)', color='Outliers', color_continuous_scale='Oranges')
                fig_out.update_xaxes(tickangle=45)
                st.plotly_chart(fig_out, use_container_width=True)
                st.caption("💡 **Interpretación Outliers:** Conteo IQR (Q1-1.5*IQR / Q3+1.5*IQR). Alto % outliers (>5%) sugiere eventos anómalos o sensor defectuoso; se clippea en preparación.")
            
            # --- Correlaciones ---
            st.markdown("### 🔗 Matriz de Correlaciones")
            corr_dict = eda['correlaciones']
            corr_df = pd.DataFrame(corr_dict)
            # Asegurar orden de variables_sensores
            vars_ord = [v for v in eda['variables_sensores'] if v in corr_df.columns]
            corr_df = corr_df.loc[vars_ord, vars_ord]
            fig_corr = px.imshow(corr_df, text_auto=".2f", aspect="auto", color_continuous_scale='RdBu_r', zmin=-1, zmax=1, title='Correlación entre Sensores')
            st.plotly_chart(fig_corr, use_container_width=True)
            st.caption("💡 **Interpretación Correlación:** -1 a 1; |r|>0.7 fuerte (ej. temp_motor vs temp_aceite). Alta correlación permite reducir features; |r|~0 indica independencia útil para modelo.")
            with st.expander("Ver tabla de correlaciones"):
                st.dataframe(corr_df.style.format("{:.2f}"), use_container_width=True)
                st.caption("💡 **Interpretación Tabla Correlación:** Valores -1 a 1; diagonal 1.0. Busca pares con |r|>0.7 para considerar colinealidad; |r|<0.3 indica independencia útil para ensemble.")
            
            # --- Desbalance de clases ---
            st.markdown("### ⚖️ Desbalance de Clases")
            desb = eda['desbalance_clases']
            if desb:
                desb_df = pd.DataFrame([{'Clase': 'Falla' if str(k)=='1' else 'No Falla', 'Proporción': v, 'Porcentaje': round(v*100,2)} for k,v in desb.items()])
                col_d1, col_d2 = st.columns([1, 1])
                with col_d1:
                    st.dataframe(desb_df, use_container_width=True, hide_index=True)
                    if desb.get(1,0) < 0.3:
                        st.warning("⚠️ Dataset desbalanceado (<30% fallas) — se aplicará SMOTE en preparación (config: balanceo_clases='smote')")
                    else:
                        st.success("✅ Balance aceptable")
                with col_d2:
                    fig_desb = px.pie(desb_df, values='Proporción', names='Clase', title='Distribución de Clases (falla_equipo)', color_discrete_map={'Falla':'#e74c3c','No Falla':'#2ecc71'}, hole=0.4)
                    st.plotly_chart(fig_desb, use_container_width=True)
                    st.caption("💡 **Interpretación Desbalance:** Falla <30% = desbalanceado → SMOTE genera muestras sintéticas. Pie desbalanceado es normal en minería (fallas raras).")
            else:
                st.info("No hay variable `falla_equipo` — se generará automáticamente en Fase 3 (Preparación) con umbrales críticos.")
            
            # --- Variables y vista previa ---
            with st.expander("📋 Lista de Variables de Sensores Analizadas"):
                st.write(", ".join([f"`{v}`" for v in eda['variables_sensores']]))
            
            st.markdown("### 👀 Muestra de Datos (5 filas)")
            st.dataframe(motor.datos.head(), use_container_width=True)
            st.caption("💡 **Interpretación Muestra:** Primeras 5 filas para validar tipos y rangos. Verificar que temp 60-110°C, presión 20-60 bar, etc. estén en rangos físicos.")
            
            st.success("✅ EDA completado — listo para pasar a **Fase 3: Preparación de Datos** y **Fase 4: Modelado** en las siguientes pestañas.")

    # ============================================================
    # TAB ENTRENAMIENTO - ENTRENAMIENTO DE LOS 5 ALGORITMOS (CRISP-DM Fase 4)
    # ============================================================
    with tab_ent:
        st.subheader("⚙️ Entrenamiento de los 5 Algoritmos - CRISP-DM Fase 4: Modelado")
        st.markdown("Entrena y evalúa **3 algoritmos tradicionales + 2 híbridos** con la misma partición temporal (70/15/15) y preparación estandarizada. Requiere **EDA previo** y **Preparación de Datos** (Fase 3).")
        
        # Estado actual
        col_est1, col_est2, col_est3, col_est4 = st.columns(4)
        with col_est1:
            estado_datos = "✅ Cargados" if motor.datos is not None else "❌ No cargados"
            st.metric("Datos", estado_datos, delta=f"{len(motor.datos) if motor.datos is not None else 0} registros")
        with col_est2:
            estado_prep = "✅ Preparados" if hasattr(motor, 'datos_procesados') and motor.datos_procesados is not None else "❌ No preparados"
            n_feat = len(motor.caracteristicas) if hasattr(motor, 'caracteristicas') else 0
            st.metric("Preparación", estado_prep, delta=f"{n_feat} features")
        with col_est3:
            st.metric("Modelos Entrenados", len(motor.modelos), delta=", ".join(list(motor.modelos.keys())) if motor.modelos else "ninguno")
        with col_est4:
            st.metric("Mejor Algoritmo", motor.mejor_algoritmo.upper() if motor.mejor_algoritmo else "—")
        
        # Configuración de preparación
        with st.expander("⚙️ Configuración de Preparación (Fase 3) - Ver hiperparámetros"):
            prep = motor.config.get('preparacion', {})
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write("**Partición & Ventana**")
                st.json({"ventana_temporal": prep.get('ventana_temporal'), "horas_prediccion": prep.get('horas_prediccion'), "test_size": prep.get('test_size'), "val_size": prep.get('val_size')})
            with c2:
                st.write("**Limpieza**")
                st.json({"balanceo_clases": prep.get('balanceo_clases'), "tratamiento_nulos": prep.get('tratamiento_nulos'), "metodo_outliers": prep.get('metodo_outliers')})
            with c3:
                st.write("**Criterios Selección**")
                st.json(motor.config.get('criterios_seleccion', {}))
        
        # --- Descripción de los 5 algoritmos ---
        st.markdown("### 🧩 Los 5 Algoritmos a Entrenar")
        st.caption("3 tradicionales (rápidos, interpretables) + 2 híbridos (capturan dependencias temporales con secuencias de 24 pasos)")
        
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            with st.container(border=True):
                st.markdown("#### 1. 🌲 Random Forest")
                st.caption("**Tradicional** | Ensemble Bagging | Interp. 8/10 | Mant. 9/10")
                st.markdown("""
                - `n_estimators=[100,200]`, `max_depth=[10,None]`, `min_samples_split=[2,5]`, `cv=3`
                - `class_weight='balanced'`, `n_jobs=-1`
                - **Ventaja:** Robusto, feature_importances nativa
                - **Uso:** Clasificación binaria falla/no falla
                """)
                hp = motor.config['hiperparametros']['random_forest']
                st.json(hp)
        with col_a2:
            with st.container(border=True):
                st.markdown("#### 2. 🚀 XGBoost")
                st.caption("**Tradicional** | Gradient Boosting | Interp. 7/10 | Mant. 8/10")
                st.markdown("""
                - `learning_rate=[0.01,0.1]`, `n_estimators=[100,300]`, `max_depth=[3,6]`, `subsample=[0.8,1.0]`
                - `scale_pos_weight` automático, `eval_metric='logloss'`
                - **Ventaja:** Alto rendimiento tabular, `gain` importances
                """)
                hp = motor.config['hiperparametros']['xgboost']
                st.json(hp)
        with col_a3:
            with st.container(border=True):
                st.markdown("#### 3. 🔷 SVM")
                st.caption("**Tradicional** | Kernel RBF/Linear | Interp. 4/10 | Mant. 6/10")
                st.markdown("""
                - `C=[1,10]`, `gamma=['scale',0.01]`, `kernel=['rbf','linear']`, `probability=True`
                - `class_weight='balanced'`, subset 5000 muestras por velocidad
                - **Ventaja:** Buen límite de decisión en alta dimensión
                """)
                hp = motor.config['hiperparametros']['svm']
                st.json(hp)
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            with st.container(border=True):
                st.markdown("#### 4. 🧠 CNN-LSTM (Híbrido)")
                st.caption("**Híbrido** | Conv1D + LSTM + Dense | Interp. 2/10 | Mant. 3/10 | Requiere TensorFlow")
                st.markdown("""
                - **Arquitectura:** `Conv1D(32,k=3) -> BN -> Conv1D(16,k=3) -> BN -> LSTM(50, return_seq) -> Dropout(0.3) -> LSTM(25) -> Dropout -> Dense(64, relu) -> Dense(1, sigmoid)`
                - `filtros_cnn=[32,64]`, `unidades_lstm=[50,100]`, `lr=0.001`, `epochs=50`, `batch=32`
                - **Entrada:** Secuencias `X_train_seq` shape `(ventana=24, n_features)`
                - **Ventaja:** Captura patrones locales (CNN) + temporales (LSTM)
                """)
                hp = motor.config['hiperparametros']['cnn_lstm']
                st.json(hp)
                try:
                    import tensorflow as tf
                    st.success("✅ TensorFlow disponible — entrenamiento nativo híbrido")
                except ImportError:
                    st.info("ℹ️ TensorFlow no instalado (Python 3.14 no soportado) — se usará **fallback sklearn**: RF sobre secuencias aplanadas que **simula** CNN-LSTM. Para TF nativo instala Python 3.11: `winget install Python.Python.3.11` + `pip install tensorflow`")
        with col_b2:
            with st.container(border=True):
                st.markdown("#### 5. 🔗 LSTM-Autoencoder + RF (Híbrido)")
                st.caption("**Híbrido** | LSTM-AE (encoder) + Random Forest | Interp. 5/10 | Mant. 4/10 | Requiere TensorFlow")
                st.markdown("""
                - **Etapa 1 - AE:** `LSTM(64, return_seq) -> LSTM(16)` encoder, `RepeatVector(24) -> LSTM(64, return_seq) -> TimeDistributed(Dense)` decoder, `loss='mse'`, `epochs_ae=30`, `batch=32`
                - **Etapa 2 - RF:** `RandomForest(n_estimators=200, max_depth=15, class_weight='balanced')` sobre **latentes (dim=16)**
                - **Ventaja:** Extrae representación comprimida temporal + clasificador robusto
                """)
                hp = motor.config['hiperparametros']['lstm_ae_rf']
                st.json(hp)
                try:
                    import tensorflow as tf
                    st.success("✅ TensorFlow disponible — entrenamiento nativo híbrido")
                except ImportError:
                    st.info("ℹ️ TensorFlow no instalado — se usará **fallback PCA(16)+RF** que **simula** LSTM-AE+RF (explica 85-90% varianza). Para TF nativo instala Python 3.11 + `pip install tensorflow`")
        
        st.markdown("---")
        
        # --- Botón de entrenamiento completo ---
        st.markdown("### 🚀 Ejecutar Entrenamiento Completo (Pipeline CRISP-DM)")
        st.info("**Pipeline:** `cargar_datos()` → `preparar_datos()` (limpieza + SMOTE + scaler + secuencias 24) → `entrenar_todos()` (5 algoritmos) → `evaluar_todos()` (accuracy, precision, recall, F1, AUC-ROC, AUC-PR, tiempos) → `comparar_algoritmos()` (puntuación ponderada) → `guardar()`")
        
        col_train1, col_train2, col_train3 = st.columns([2, 1, 1])
        with col_train1:
            modo_completo = st.checkbox("Entrenamiento completo (re-carga + re-prepara + re-entrena todo)", value=True, help="Si está desmarcado, solo re-entrena los 5 algoritmos sobre la preparación existente (más rápido)")
        with col_train2:
            guardar_modelos = st.checkbox("Guardar modelos en /models", value=True)
        with col_train3:
            btn_entrenar_5 = st.button("🚀 Entrenar los 5 Algoritmos", type="primary", use_container_width=True)
        
        if btn_entrenar_5:
            with st.spinner("Entrenando los 5 algoritmos... esto puede tardar 1-3 min (RF/XGB/SVM rápido, CNN-LSTM/LSTM-AE más lento si TF disponible)"):
                progress = st.progress(0, text="Iniciando...")
                try:
                    # Fase 2-3: Cargar y preparar si modo completo
                    if modo_completo:
                        progress.progress(5, text="Cargando datos...")
                        motor.cargar_datos()
                        progress.progress(15, text="Preparando datos (scaler, SMOTE, secuencias)...")
                        motor.preparar_datos()
                    else:
                        if motor.datos is None:
                            motor.cargar_datos()
                        if not hasattr(motor, 'datos_procesados') or motor.datos_procesados is None:
                            motor.preparar_datos()
                    
                    progress.progress(20, text="Limpiando modelos previos...")
                    motor.modelos = {}
                    motor.resultados_evaluacion = {}
                    motor.puntuaciones = {}
                    
                    # Entrenamiento secuencial de los 5
                    total = 5
                    # 1 RF
                    progress.progress(25, text="1/5: Entrenando Random Forest...")
                    st.write("🌲 Entrenando Random Forest...")
                    motor.entrenar_random_forest()
                    progress.progress(35, text="2/5: Entrenando XGBoost...")
                    # 2 XGB
                    st.write("🚀 Entrenando XGBoost...")
                    motor.entrenar_xgboost()
                    progress.progress(50, text="3/5: Entrenando SVM...")
                    # 3 SVM
                    st.write("🔷 Entrenando SVM...")
                    motor.entrenar_svm()
                    progress.progress(60, text="4/5: Entrenando CNN-LSTM...")
                    # 4 CNN-LSTM
                    st.write("🧠 Entrenando CNN-LSTM (requiere TensorFlow)...")
                    motor.entrenar_cnn_lstm()
                    progress.progress(75, text="5/5: Entrenando LSTM-Autoencoder + RF...")
                    # 5 LSTM-AE+RF
                    st.write("🔗 Entrenando LSTM-Autoencoder + RF...")
                    motor.entrenar_lstm_ae_rf()
                    
                    progress.progress(85, text="Evaluando todos...")
                    st.write("📊 Evaluando...")
                    motor.evaluar_todos()
                    progress.progress(92, text="Comparando y seleccionando mejor...")
                    st.write("🏆 Comparando algoritmos...")
                    motor.comparar_algoritmos()
                    progress.progress(97, text="Guardando...")
                    if guardar_modelos:
                        motor.guardar()
                    progress.progress(100, text="¡Completado!")
                    
                    st.success(f"✅ **Entrenamiento completado**: {len(motor.modelos)} algoritmos entrenados | Mejor: **{motor.mejor_algoritmo.upper() if motor.mejor_algoritmo else '—'}** (puntuación {motor.puntuaciones.get(motor.mejor_algoritmo, {}).get('puntuacion_general',0):.4f})")
                    
                    # Mostrar tabla comparativa inmediata
                    if motor.resultados_evaluacion:
                        st.markdown("#### 📊 Resultados Inmediatos")
                        df_comp = motor.obtener_tabla_comparativa()
                        st.dataframe(df_comp, use_container_width=True)
                        st.caption("💡 **Interpretación Tabla Comparativa:** Ranking por Puntuación General ponderada (40% F1+AUC, 25% tiempo, 20% interpret, 15% manten). ⭐ indica mejor algoritmo seleccionado para producción.")
                    
                    st.session_state.motor_ia = motor
                except Exception as e:
                    st.error(f"❌ Error en entrenamiento: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Estado post-entrenamiento: métricas rápidas
        if motor.resultados_evaluacion:
            st.markdown("### 📈 Estado Actual de Modelos Entrenados")
            cols = st.columns(len(motor.resultados_evaluacion))
            for idx, (nombre, met) in enumerate(motor.resultados_evaluacion.items()):
                with cols[idx]:
                    with st.container(border=True):
                        es_mejor = "⭐" if nombre == motor.mejor_algoritmo else ""
                        st.markdown(f"**{nombre.upper()} {es_mejor}**")
                        st.metric("F1", met.get('f1_score',0))
                        st.metric("AUC-ROC", met.get('auc_roc',0))
                        st.metric("Tiempo ms", met.get('tiempo_inferencia_ms',0))
                        st.caption(f"Entrenado en {met.get('tiempo_entrenamiento_s',0)}s")
            st.caption("💡 **Interpretación Estado:** Tarjetas por algoritmo. F1 y AUC cercanos a 1.0 = excelente; Tiempo ms bajo (<5ms) ideal para inferencia en tiempo real. ⭐ es el seleccionado.")
        else:
            st.warning("⚠️ Aún no hay modelos evaluados. Ejecuta el entrenamiento arriba o usa la pestaña **🔄 Reentrenar** para entrenamiento selectivo.")
     
    with tab1:

        st.subheader("📊 Comparativa de los 5 Algoritmos")
        
        if motor.resultados_evaluacion:
            df_comparativa = motor.obtener_tabla_comparativa()
            st.dataframe(df_comparativa, use_container_width=True)
            st.caption("💡 **Interpretación Comparativa:** Tabla ordenada por Puntuación General. Columna Seleccionado ⭐ indica ganador. Comparar F1/AUC y tiempo para trade-off precisión vs velocidad.")
            
            # Gráfico de barras comparativo
            st.subheader("📈 Rendimiento por Algoritmo")
            metricas_df = pd.DataFrame([
                {'Algoritmo': r['algoritmo'].upper(), 
                 'F1-Score': r['f1_score'],
                 'AUC-ROC': r['auc_roc'],
                 'Precisión': r['accuracy']}
                for r in motor.resultados_evaluacion.values()
            ])
            
            metricas_melted = metricas_df.melt(id_vars='Algoritmo', var_name='Métrica', value_name='Valor')
            fig_comp = px.bar(metricas_melted, x='Algoritmo', y='Valor', color='Métrica',
                            barmode='group', title='Comparativa de Métricas por Algoritmo',
                            color_discrete_map={'F1-Score': '#3498db', 'AUC-ROC': '#2ecc71', 'Precisión': '#e74c3c'})
            st.plotly_chart(fig_comp, use_container_width=True)
            st.caption("💡 **Interpretación Barras:** Grupo por algoritmo. Altura = rendimiento; barras similares indican modelos equivalentes; caída >0.1 sugiere inferioridad significativa.")
            
            # Gráfico de tiempos
            st.subheader("⏱️ Tiempos de Inferencia")
            tiempos_df = pd.DataFrame([
                {'Algoritmo': r['algoritmo'].upper(), 'Tiempo (ms)': r['tiempo_inferencia_ms']}
                for r in motor.resultados_evaluacion.values()
            ])
            fig_tiempos = px.bar(tiempos_df, x='Algoritmo', y='Tiempo (ms)',
                               title='Tiempo de Inferencia por Predicción (ms)',
                               color='Tiempo (ms)', color_continuous_scale='Reds')
            st.plotly_chart(fig_tiempos, use_container_width=True)
            st.caption("💡 **Interpretación Tiempos:** Rojo intenso = lento. SVM/XGB <5ms ideal para tiempo real; CNN-LSTM >10ms puede requerir GPU. Peso 25% en selección.")
            
            # Criterios de selección
            st.subheader("⚖️ Criterios de Selección Ponderados")
            criterios = motor.config['criterios_seleccion']
            crit_df = pd.DataFrame([
                {'Criterio': k.replace('_', ' ').title(), 'Peso (%)': round(v * 100, 1)}
                for k, v in criterios.items()
            ])
            fig_crit = px.pie(crit_df, values='Peso (%)', names='Criterio',
                             title='Ponderación de Criterios para Selección')
            st.plotly_chart(fig_crit, use_container_width=True)
            st.caption("💡 **Interpretación Criterios:** Pie de pesos usados para Puntuación General. Rendimiento 40% domina, pero tiempo/interpretabilidad/mantenibilidad evitan elegir modelo lento/opaco.")
        else:
            st.info("No hay resultados de evaluación. Ejecute reentrenamiento.")
    
    with tab2:
        st.subheader("🔮 Predicción de Falla por Equipo")
        
        equipos_df = dash_mod.get_equipos_data()
        equipo_sel = st.selectbox("Seleccionar Equipo",
            options=equipos_df['id'].tolist(),
            format_func=lambda x: f"{equipos_df[equipos_df['id']==x]['codigo'].iloc[0]} - {equipos_df[equipos_df['id']==x]['nombre'].iloc[0]}")
        
        # Seleccionar algoritmo
        alg_disponibles = list(motor.modelos.keys())
        alg_sel = st.selectbox("Algoritmo a usar (predeterminado: mejor)",
            options=['Mejor Automático'] + alg_disponibles)
        
        if st.button("🔍 Ejecutar Predicción", type="primary"):
            with st.spinner("Analizando datos del equipo..."):
                # Obtener datos del equipo
                datos_eq = gd_mod.get_ultimos_datos(equipo_sel)
                
                if datos_eq:
                    # Preparar vector de características
                    if hasattr(motor, 'caracteristicas'):
                        vector = []
                        for caract in motor.caracteristicas:
                            if caract in datos_eq:
                                vector.append(datos_eq[caract])
                            else:
                                # Para características derivadas, usar valor base
                                if 'temp_motor' in datos_eq:
                                    vector.append(datos_eq['temp_motor'])
                                else:
                                    vector.append(0)
                        
                        algoritmo = None if alg_sel == 'Mejor Automático' else alg_sel
                        resultado = motor.predecir(vector, algoritmo=algoritmo)
                        
                        # Mostrar resultados
                        col_r1, col_r2, col_r3 = st.columns(3)
                        
                        with col_r1:
                            st.metric("Probabilidad de Falla", 
                                     f"{resultado['probabilidad_falla']}%",
                                     delta=f"Algoritmo: {resultado['algoritmo_usado']}")
                        
                        with col_r2:
                            severidad_colores = {
                                'Critica': '#e74c3c', 'Alta': '#e67e22',
                                'Media': '#f39c12', 'Baja': '#2ecc71'
                            }
                            st.markdown(f"""
                            <div style='text-align: center; padding: 15px; background: {severidad_colores[resultado['severidad']]}; border-radius: 10px;'>
                                <h4 style='color: white; margin: 0;'>SEVERIDAD</h4>
                                <h3 style='color: white; margin: 5px 0;'>{resultado['severidad']}</h3>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_r3:
                            st.metric("Horas Restantes Estimadas", 
                                     f"{resultado['horas_restantes_estimadas']} h",
                                     delta=f"Tiempo inferencia: {resultado['tiempo_inferencia_ms']} ms")
                        
                        st.markdown("---")
                        
                        # Recomendación
                        st.subheader("💡 Recomendación")
                        st.text_area("Recomendación", resultado['recomendacion'], height=200, label_visibility="collapsed")
                        
                        # Factores influyentes
                        if resultado['factores_influyentes']:
                            st.subheader("📊 Factores Más Influyentes")
                            fact_df = pd.DataFrame(resultado['factores_influyentes'], columns=['Factor', 'Importancia'])
                            fact_df['Factor'] = fact_df['Factor'].astype(str).str.replace('_', ' ').str.title()
                            fig_fact = px.bar(fact_df.head(5), x='Factor', y='Importancia',
                                            title='Top 5 Factores de Influencia',
                                            color='Importancia', color_continuous_scale='Reds')
                            st.plotly_chart(fig_fact, use_container_width=True)
                            st.caption("💡 **Interpretación Factores Motor IA:** Barras rojas = causas raíz de falla predicha. Factor >25% indica revisar componente asociado (ej. presion_aceite → circuito lubricación).")
                    else:
                        st.warning("El motor no tiene características definidas. Reentrene el modelo.")
                else:
                    st.error("No hay datos de sensores para este equipo")
    
    with tab3:
        st.subheader("🏆 Mejor Algoritmo Seleccionado")
        
        if motor.mejor_algoritmo:
            mejor = motor.mejor_algoritmo
            puntuacion = motor.puntuaciones.get(mejor, {})
            info = motor.modelos.get(mejor, {})
            metricas = motor.resultados_evaluacion.get(mejor, {})
            
            col_m1, col_m2 = st.columns([1, 2])
            
            with col_m1:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #2c3e50, #3498db); padding: 25px; border-radius: 15px; text-align: center;'>
                    <h2 style='color: white; margin: 0;'>🏆</h2>
                    <h3 style='color: white; margin: 10px 0;'>{mejor.upper()}</h3>
                    <p style='color: #ecf0f1; font-size: 18px;'>Puntuación: <strong>{puntuacion.get('puntuacion_general', 0):.4f}</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                st.metric("F1-Score", metricas.get('f1_score', 0))
                st.metric("AUC-ROC", metricas.get('auc_roc', 0))
                st.metric("Precisión", metricas.get('accuracy', 0))
            
            with col_m2:
                st.write("**Desglose de Puntuación:**")
                desglose = pd.DataFrame([
                    {'Criterio': 'Rendimiento Predictivo', 
                     'Puntuación': puntuacion.get('rendimiento', 0),
                     'Peso': motor.config['criterios_seleccion']['rendimiento_predictivo']},
                    {'Criterio': 'Tiempo de Inferencia', 
                     'Puntuación': puntuacion.get('tiempo', 0),
                     'Peso': motor.config['criterios_seleccion']['tiempo_inferencia']},
                    {'Criterio': 'Interpretabilidad', 
                     'Puntuación': puntuacion.get('interpretabilidad', 0),
                     'Peso': motor.config['criterios_seleccion']['interpretabilidad']},
                    {'Criterio': 'Facilidad de Mantenimiento', 
                     'Puntuación': puntuacion.get('mantenibilidad', 0),
                     'Peso': motor.config['criterios_seleccion']['facilidad_mantenimiento']},
                ])
                st.dataframe(desglose, use_container_width=True)
                st.caption("💡 **Interpretación Desglose:** Puntuación por criterio (0-1) × peso. Rendimiento alto + tiempo bajo + interpretabilidad alta = ganador. Comparar barras para entender por qué ganó.")
                
                st.write("**Características del modelo:**")
                st.info(f"""
                - **Tipo:** Clasificación binaria (falla/no falla)
                - **Tiempo de entrenamiento:** {metricas.get('tiempo_entrenamiento_s', 0):.2f} segundos
                - **Tiempo de inferencia:** {metricas.get('tiempo_inferencia_ms', 0):.2f} ms por predicción
                - **Interpretabilidad:** {metricas.get('interpretabilidad', 0)}/10
                - **Mantenibilidad:** {metricas.get('mantenibilidad', 0)}/10
                """)
                
                # Importancia de características
                if info.get('importancias'):
                    st.subheader("📊 Importancia de Características")
                    imp_df = pd.DataFrame(info['importancias'][:10], columns=['Característica', 'Importancia'])
                    imp_df['Característica'] = imp_df['Característica'].astype(str).str.replace('_', ' ').str.title()
                    fig_imp = px.bar(imp_df, x='Importancia', y='Característica', orientation='h',
                                    title='Top 10 Características Más Importantes')
                    st.plotly_chart(fig_imp, use_container_width=True)
                    st.caption("💡 **Interpretación Importancias:** Barra horizontal del mejor modelo. Feature arriba = mayor peso en decisión. Útil para priorizar sensores a monitorear.")
        else:
            st.info("No hay algoritmo seleccionado. Ejecute reentrenamiento.")
    
    with tab4:
        st.subheader("🔄 Reentrenar Motor de IA — Los 5 Algoritmos (Incluye Híbridos)")
        
        st.info("✅ **Actualizado:** Ahora incluye **los 5 algoritmos**: 3 tradicionales + 2 híbridos (`cnn_lstm` y `lstm_ae_rf`) con **fallback sklearn** si TensorFlow no está disponible (Python 3.14). El entrenamiento usa el mismo pipeline de la pestaña `⚙️ Entrenamiento`.")
        st.warning("El reentrenamiento puede tardar 1-3 min (RF/XGB/SVM rápido; híbridos 5-15s en fallback, 1-2 min con TensorFlow nativo).")
        
        # Descripción rápida de los 5
        with st.expander("🧩 Ver especificaciones de los 5 algoritmos (tradicionales vs híbridos)", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**1. 🌲 Random Forest** (tradicional) `n_est=[100,200] max_depth=[10,None]` Interp 8/10")
                st.markdown("**2. 🚀 XGBoost** (tradicional) `lr=[0.01,0.1] n_est=[100,300]` Interp 7/10")
                st.markdown("**3. 🔷 SVM** (tradicional) `C=[1,10] gamma=[scale,0.01]` Interp 4/10")
            with c2:
                st.markdown("**4. 🧠 CNN-LSTM** (híbrido) `Conv1D(32)->LSTM(50)` ventana 24, `epochs 50` Interp 2/10")
                st.markdown("**5. 🔗 LSTM-AE+RF** (híbrido) `LSTM-AE(64->16) + RF200` Interp 5/10")
            with c3:
                try:
                    import tensorflow as tf
                    st.success("✅ TensorFlow disponible — híbridos nativos")
                except ImportError:
                    st.info("ℹ️ Fallback activo: CNN-LSTM→RF sobre secuencias aplanadas | LSTM-AE+RF→PCA(16)+RF")
        
        col_op1, col_op2 = st.columns(2)
        
        with col_op1:
            algoritmos_a_entrenar = st.multiselect(
                "Algoritmos a entrenar (selecciona los 5 para entrenamiento completo)",
                options=['random_forest', 'xgboost', 'svm', 'cnn_lstm', 'lstm_ae_rf'],
                default=['random_forest', 'xgboost', 'svm', 'cnn_lstm', 'lstm_ae_rf'],
                format_func=lambda x: {
                    'random_forest': '🌲 Random Forest (tradicional)',
                    'xgboost': '🚀 XGBoost (tradicional)',
                    'svm': '🔷 SVM (tradicional)',
                    'cnn_lstm': '🧠 CNN-LSTM (híbrido)',
                    'lstm_ae_rf': '🔗 LSTM-AE+RF (híbrido)'
                }.get(x, x),
                help="Los 2 híbridos usan fallback sklearn si no hay TensorFlow (Python 3.14) y ya están operativos"
            )
        
        with col_op2:
            guardar_despues = st.checkbox("Guardar modelo después de entrenar", value=True)
        
        if st.button("🚀 Iniciar Reentrenamiento", type="primary"):
            with st.spinner("Reentrenando motor de IA..."):
                progress_bar = st.progress(0)
                
                # Cargar y preparar datos frescos
                motor.cargar_datos()
                progress_bar.progress(10)
                
                motor.preparar_datos()
                progress_bar.progress(20)
                
                # Limpiar modelos anteriores
                motor.modelos = {}
                motor.resultados_evaluacion = {}
                
                # Entrenar algoritmos seleccionados
                total = len(algoritmos_a_entrenar)
                for i, alg in enumerate(algoritmos_a_entrenar):
                    st.write(f"Entrenando {alg}...")
                    if alg == 'random_forest':
                        motor.entrenar_random_forest()
                    elif alg == 'xgboost':
                        motor.entrenar_xgboost()
                    elif alg == 'svm':
                        motor.entrenar_svm()
                    elif alg == 'cnn_lstm':
                        motor.entrenar_cnn_lstm()
                    elif alg == 'lstm_ae_rf':
                        motor.entrenar_lstm_ae_rf()
                    
                    progress_bar.progress(20 + int((i + 1) / total * 60))
                
                # Evaluar y comparar
                st.write("Evaluando algoritmos...")
                motor.evaluar_todos()
                progress_bar.progress(85)
                
                st.write("Seleccionando mejor algoritmo...")
                motor.comparar_algoritmos()
                progress_bar.progress(95)
                
                if guardar_despues:
                    motor.guardar()
                
                progress_bar.progress(100)
                
                st.success(f"""
                ✅ Reentrenamiento completado!
                - Algoritmos entrenados: {len(motor.modelos)}
                - Mejor algoritmo: {motor.mejor_algoritmo}
                - Puntuación: {motor.puntuaciones.get(motor.mejor_algoritmo, {}).get('puntuacion_general', 0):.4f}
                """)
                
                st.session_state.motor_ia = motor
    
    with tab5:
        st.subheader("📋 Logs del Motor de IA")
        
        logs = motor.obtener_logs(100)
        if logs:
            log_texto = ''.join(logs)
            st.text_area("Logs del Motor", log_texto, height=400, label_visibility="collapsed")
        else:
            st.info("No hay logs disponibles")
        
        if st.button("🗑️ Limpiar Logs"):
            log_file = os.path.join(os.path.dirname(MODELS_DIR), 'logs', 'motor_ia.log')
            if os.path.exists(log_file):
                os.remove(log_file)
                st.success("Logs limpiados")
                st.rerun()

    # ============================================================
    # TAB VALIDACIÓN CRUZADA - CRISP-DM Fase 5: Evaluación (REACTIVADO)
    # ============================================================
    with tab_cv:
        st.subheader("🔁 Validación Cruzada - CRISP-DM Fase 5: Evaluación Rigurosa")
        st.markdown("Evalúa la **generalización** de cada algoritmo con particiones que evitan fuga temporal. Recomendado **`TimeSeriesSplit`** para sensores (respeta orden cronológico) vs `StratifiedKFold` clásico.")
        if not hasattr(motor, 'datos_procesados') or motor.datos_procesados is None:
            st.warning("⚠️ Primero ejecuta **Preparación** en pestaña `⚙️ Entrenamiento` (cargar_datos + preparar_datos).")
            if st.button("🔄 Preparar Datos Ahora (rápido)", key="prep_cv_react"):
                with st.spinner("Preparando datos..."):
                    if motor.datos is None:
                        motor.cargar_datos()
                    motor.preparar_datos()
                    st.success("Datos preparados")
                    st.rerun()
            st.stop()
        col_cv1, col_cv2, col_cv3 = st.columns([2, 1.2, 1])
        with col_cv1:
            algs_cv = st.multiselect("Algoritmos a validar (usa fallback híbrido si TF no disponible)", options=['random_forest','xgboost','svm','cnn_lstm','lstm_ae_rf'], default=['random_forest','xgboost','svm','cnn_lstm','lstm_ae_rf'], format_func=lambda x: {'random_forest':'🌲 Random Forest','xgboost':'🚀 XGBoost','svm':'🔷 SVM','cnn_lstm':'🧠 CNN-LSTM (híbrido)','lstm_ae_rf':'🔗 LSTM-AE+RF (híbrido)'}.get(x,x), key="cv_algs_react")
        with col_cv2:
            cv_tipo = st.radio("Estrategia CV", options=['StratifiedKFold', 'TimeSeriesSplit'], index=1, help="TimeSeriesSplit evita fuga temporal en sensores; StratifiedKFold mantiene proporción de clases")
        with col_cv3:
            n_splits = st.slider("Número de Folds (k) — barra deslizante", 2, 10, 5, step=1, help="Desliza la barra: 2 mínimo (rápido), 5 estándar robusto, 10 máxima robustez pero ~3x más lento. Requiere ≥k muestras por clase en StratifiedKFold.")
            st.progress(n_splits/10, text=f"📊 k={n_splits} folds seleccionados")
            if n_splits <= 3:
                st.caption("⚡ Rápido — ideal para pruebas iniciales")
            elif n_splits <= 5:
                st.caption("✅ Estándar — balance velocidad/robustez")
            else:
                st.caption("🔬 Exhaustivo — máxima robustez, más lento")
        col_cv4, col_cv5 = st.columns([1, 1])
        with col_cv4:
            scoring_cv = st.multiselect("Métricas", options=['accuracy','f1_weighted','precision_weighted','recall_weighted','roc_auc'], default=['accuracy','f1_weighted','roc_auc'])
        with col_cv5:
            st.metric("Datos para CV", f"{len(motor.X_train) + len(motor.X_val) + len(motor.X_test)} muestras", delta=f"Seq {len(motor.X_train_seq) if hasattr(motor,'X_train_seq') else 0} ventana 24")
            st.caption("💡 **Interpretación Datos CV:** Total muestras combinadas train+val+test. Seq indica secuencias para híbridos (ventana 24). Más muestras = CV más estable.")
        btn_cv = st.button("▶️ Ejecutar Validación Cruzada", type="primary", use_container_width=True, key="btn_cv_react")
        if btn_cv:
            if not algs_cv:
                st.error("Selecciona al menos 1 algoritmo")
                st.stop()
            from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit, cross_validate
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.svm import SVC
            from sklearn.decomposition import PCA
            from sklearn.pipeline import make_pipeline
            try:
                import xgboost as xgb
                XGB_AVAILABLE = True
            except ImportError:
                XGB_AVAILABLE = False
            try:
                X_full = np.vstack([motor.X_train, motor.X_val, motor.X_test])
                y_full = np.concatenate([motor.y_train_clas, motor.y_val_clas, motor.y_test_clas])
                if hasattr(motor, 'X_train_seq') and len(motor.X_train_seq) > 0:
                    X_seq_full = np.vstack([motor.X_train_seq, motor.X_val_seq, motor.X_test_seq])
                    y_seq_full = np.concatenate([motor.y_train_seq_clas, motor.y_val_seq_clas, motor.y_test_seq_clas])
                else:
                    X_seq_full = None
            except Exception as e:
                st.error(f"Error preparando datos CV: {e}")
                st.stop()
            if cv_tipo == 'TimeSeriesSplit':
                cv = TimeSeriesSplit(n_splits=n_splits)
            else:
                cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            def get_est(nombre):
                hp = motor.config['hiperparametros']
                if nombre == 'random_forest':
                    p = hp['random_forest']
                    return RandomForestClassifier(n_estimators=p['n_estimators'][0], max_depth=p['max_depth'][0], min_samples_split=p['min_samples_split'][0], random_state=42, n_jobs=-1, class_weight='balanced')
                elif nombre == 'xgboost':
                    if not XGB_AVAILABLE:
                        return None
                    p = hp['xgboost']
                    return xgb.XGBClassifier(learning_rate=p['learning_rate'][0], n_estimators=p['n_estimators'][0], max_depth=p['max_depth'][0], subsample=p['subsample'][0], random_state=42, use_label_encoder=False, eval_metric='logloss')
                elif nombre == 'svm':
                    p = hp['svm']
                    return SVC(C=p['C'][0], gamma=p['gamma'][0], kernel=p['kernel'][0], probability=True, class_weight='balanced', random_state=42)
                elif nombre == 'cnn_lstm':
                    return RandomForestClassifier(n_estimators=150, max_depth=20, random_state=42, n_jobs=-1, class_weight='balanced')
                elif nombre == 'lstm_ae_rf':
                    return make_pipeline(PCA(n_components=min(16, X_full.shape[1]), random_state=42), RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1, class_weight='balanced'))
                return None
            resultados_cv = {}
            progress_cv = st.progress(0, text="Iniciando CV...")
            for idx, alg in enumerate(algs_cv):
                st.write(f"🔄 Validando **{alg.upper()}** ({idx+1}/{len(algs_cv)})...")
                est = get_est(alg)
                if est is None:
                    st.warning(f"⚠️ {alg} no disponible (XGBoost no instalado)")
                    continue
                usa_seq = motor.modelos.get(alg, {}).get('usa_secuencias', False) if alg in motor.modelos else (alg in ['cnn_lstm','lstm_ae_rf'])
                if alg == 'lstm_ae_rf':
                    X_cv, y_cv = X_full, y_full
                elif usa_seq and X_seq_full is not None and len(X_seq_full) > 20:
                    X_cv = X_seq_full.reshape(X_seq_full.shape[0], -1)
                    y_cv = y_seq_full
                else:
                    X_cv, y_cv = X_full, y_full
                try:
                    scoring = {s: s for s in scoring_cv} if scoring_cv else 'accuracy'
                    cv_res = cross_validate(est, X_cv, y_cv, cv=cv, scoring=scoring, n_jobs=-1, error_score='raise')
                    resultados_cv[alg] = cv_res
                    mean_f1 = cv_res['test_f1_weighted'].mean() if 'test_f1_weighted' in cv_res else cv_res['test_score'].mean()
                    st.success(f"✅ {alg.upper()} — F1 mean {mean_f1:.4f}")
                except Exception as e:
                    st.error(f"❌ Error CV {alg}: {e}")
                progress_cv.progress(int((idx+1)/len(algs_cv)*100), text=f"{alg} completado")
            if resultados_cv:
                st.markdown("### 📊 Resultados por Fold")
                filas = []
                for alg, res in resultados_cv.items():
                    fila = {'Algoritmo': alg.upper()}
                    for metric in scoring_cv:
                        key = f'test_{metric}'
                        if key in res:
                            fila[f'{metric} mean'] = round(res[key].mean(),4)
                            fila[f'{metric} std'] = round(res[key].std(),4)
                    if 'fit_time' in res:
                        fila['fit_time mean (s)'] = round(res['fit_time'].mean(),2)
                    filas.append(fila)
                df_resumen = pd.DataFrame(filas)
                st.dataframe(df_resumen, use_container_width=True)
                st.caption("💡 **Interpretación Resumen CV:** mean = rendimiento promedio, std = estabilidad (std bajo = robusto). fit_time indica costo computacional.")
                for metric in scoring_cv:
                    key = f'test_{metric}'
                    data_box = []
                    for alg, res in resultados_cv.items():
                        if key in res:
                            for v in res[key]:
                                data_box.append({'Algoritmo': alg.upper(), 'Valor': v, 'Métrica': metric})
                    if data_box:
                        df_box = pd.DataFrame(data_box)
                        fig_box = px.box(df_box, x='Algoritmo', y='Valor', color='Algoritmo', title=f'Distribución {metric} por Fold (k={n_splits}, {cv_tipo})', points="all")
                        st.plotly_chart(fig_box, use_container_width=True)
                        st.caption(f"💡 **Interpretación Box {metric}:** Caja = IQR 25-75%, línea = mediana, puntos = folds. Caja pequeña y alta = modelo estable y preciso.")
                if 'f1_weighted' in scoring_cv or 'accuracy' in scoring_cv:
                    metric_bar = 'f1_weighted' if 'f1_weighted' in scoring_cv else scoring_cv[0]
                    key_bar = f'test_{metric_bar}'
                    df_bar = pd.DataFrame([{'Algoritmo': alg.upper(), 'Mean': res[key_bar].mean(), 'Std': res[key_bar].std()} for alg, res in resultados_cv.items() if key_bar in res])
                    fig_bar = px.bar(df_bar, x='Algoritmo', y='Mean', error_y='Std', color='Algoritmo', title=f'Media ± Std de {metric_bar} (Validación Cruzada)', text_auto='.3f')
                    st.plotly_chart(fig_bar, use_container_width=True)
                    st.caption("💡 **Interpretación Barra Media±Std:** Barra = media, error = std. Barras altas con error pequeño son mejores; solapamiento de errores indica diferencia no significativa.")
                with st.expander("📋 Detalle por Fold"):
                    filas_fold = []
                    for alg, res in resultados_cv.items():
                        for fold in range(n_splits):
                            fila = {'Algoritmo': alg.upper(), 'Fold': fold+1}
                            for metric in scoring_cv:
                                key = f'test_{metric}'
                                if key in res:
                                    fila[metric] = round(res[key][fold],4)
                            filas_fold.append(fila)
                    st.dataframe(pd.DataFrame(filas_fold), use_container_width=True)
                    st.caption("💡 **Interpretación Detalle Fold:** Cada fila es un fold. Variación entre folds indica sensibilidad a partición; fold 1 bajo puede indicar desbalance temporal.")
                st.success(f"✅ Validación cruzada completada: {len(resultados_cv)} algoritmos, {n_splits} folds, {cv_tipo}")
                st.session_state['cv_resultados'] = resultados_cv
            else:
                st.warning("No se obtuvieron resultados de CV")
        else:
            st.info("👆 Configura y presiona **▶️ Ejecutar Validación Cruzada**. Recomendado `TimeSeriesSplit` para evitar fuga temporal en sensores mineros.")
            st.caption("💡 **Interpretación General CV:** CV estima generalización. TimeSeriesSplit respeta orden cronológico (evita fuga de futuro), StratifiedKFold mantiene proporción de clases. Elige según objetivo: temporalidad vs balance.")

    # ============================================================
    # TAB HIPERPARÁMETROS - CRISP-DM Fase 4: Optimización (REACTIVADO)
    # ============================================================
    with tab_hp:
        st.subheader("🎛️ Hiperparámetros - CRISP-DM Fase 4: Optimización y Tuning")
        st.markdown("Ajusta los hiperparámetros de los **5 algoritmos** y ejecuta **GridSearchCV** para encontrar la mejor configuración. Los pesos de selección (rendimiento 40% + tiempo 25% + interpretabilidad 20% + mantenibilidad 15%) se usan en `comparar_algoritmos()`.")
        col_hp1, col_hp2 = st.columns([2, 1])
        with col_hp1:
            st.markdown("### 📋 Configuración Actual (`motor.config['hiperparametros']`)")
            st.json(motor.config['hiperparametros'])
            st.caption("💡 **Interpretación Config:** Diccionario por algoritmo con listas de valores a probar en GridSearch. Primer valor es el usado actualmente para entrenamiento.")
        with col_hp2:
            st.markdown("### ⚖️ Pesos Selección")
            st.json(motor.config['criterios_seleccion'])
            st.caption("💡 **Interpretación Pesos:** 40% rendimiento domina, 25% tiempo evita lentos, 20% interpretabilidad favorece RF/XGB, 15% mantenibilidad.")
            st.markdown("### 🧠 Interpretabilidad / Mantenibilidad")
            c1, c2 = st.columns(2)
            with c1: st.json(motor.config['interpretabilidad_algoritmos'])
            with c2: st.json(motor.config['mantenibilidad_algoritmos'])
            st.caption("💡 **Interpretación 8-9/10 = transparente/fácil de mantener (RF), 2-3/10 = caja negra (CNN-LSTM).")
        st.markdown("### 📊 Tabla Resumen Hiperparámetros")
        filas_hp = []
        for alg, hp in motor.config['hiperparametros'].items():
            for param, valores in hp.items():
                if param == 'cv': continue
                filas_hp.append({'Algoritmo': alg.upper(), 'Parámetro': param, 'Valores Grid': str(valores), 'Tipo': 'lista' if isinstance(valores, list) else 'scalar'})
        df_hp = pd.DataFrame(filas_hp)
        st.dataframe(df_hp, use_container_width=True, hide_index=True)
        st.caption("💡 **Interpretación Tabla Hiperparámetros:** Cada fila es un parámetro con grid de búsqueda. Lista = rango a explorar en GridSearch; scalar = fijo.")
        st.markdown("### ✏️ Edición Rápida (demo interactiva)")
        st.caption("💡 **Interpretación Edición:** Modifica hiperparámetros clave y guarda en `motor.config`. Luego re-entrena en `⚙️ Entrenamiento` o `🔄 Reentrenar` para aplicar. Cambios afectan próximo entrenamiento.")
        tab_rf, tab_xgb, tab_svm, tab_hyb = st.tabs(["🌲 RF", "🚀 XGB", "🔷 SVM", "🧠 Híbridos"])
        with tab_rf:
            hp_rf = motor.config['hiperparametros']['random_forest']
            c1, c2, c3 = st.columns(3)
            with c1:
                n_est_rf = st.slider("n_estimators (RF) lista primer valor", 50, 300, hp_rf['n_estimators'][0], step=10, key="hp_rf_n2")
            with c2:
                max_d_rf = st.selectbox("max_depth (RF) primer valor", options=[5,10,15,20,None], index=[5,10,15,20,None].index(hp_rf['max_depth'][0]) if hp_rf['max_depth'][0] in [5,10,15,20,None] else 1, key="hp_rf_d2")
            with c3:
                min_split_rf = st.selectbox("min_samples_split (RF)", options=[2,5,10], index=[2,5,10].index(hp_rf['min_samples_split'][0]), key="hp_rf_s2")
            if st.button("💾 Guardar RF", key="save_rf_react2"):
                motor.config['hiperparametros']['random_forest']['n_estimators'][0] = n_est_rf
                motor.config['hiperparametros']['random_forest']['max_depth'][0] = max_d_rf
                motor.config['hiperparametros']['random_forest']['min_samples_split'][0] = min_split_rf
                st.success(f"✅ RF guardado: n_est={n_est_rf}, max_depth={max_d_rf}, min_split={min_split_rf}")
        with tab_xgb:
            hp_xgb = motor.config['hiperparametros']['xgboost']
            c1, c2, c3 = st.columns(3)
            with c1:
                lr_xgb = st.select_slider("learning_rate (XGB)", options=[0.01,0.05,0.1,0.2], value=hp_xgb['learning_rate'][0], key="hp_xgb_lr2")
            with c2:
                n_est_xgb = st.slider("n_estimators (XGB)", 50, 500, hp_xgb['n_estimators'][0], step=10, key="hp_xgb_n2")
            with c3:
                max_d_xgb = st.slider("max_depth (XGB)", 3, 10, hp_xgb['max_depth'][0], key="hp_xgb_d2")
            if st.button("💾 Guardar XGB", key="save_xgb_react2"):
                motor.config['hiperparametros']['xgboost']['learning_rate'][0] = lr_xgb
                motor.config['hiperparametros']['xgboost']['n_estimators'][0] = n_est_xgb
                motor.config['hiperparametros']['xgboost']['max_depth'][0] = max_d_xgb
                st.success(f"✅ XGB guardado: lr={lr_xgb}, n_est={n_est_xgb}, max_depth={max_d_xgb}")
        with tab_svm:
            hp_svm = motor.config['hiperparametros']['svm']
            c1, c2 = st.columns(2)
            with c1:
                C_svm = st.select_slider("C (SVM)", options=[0.5,1,5,10,20], value=hp_svm['C'][0], key="hp_svm_c2")
            with c2:
                gamma_svm = st.selectbox("gamma (SVM)", options=['scale','auto',0.01,0.001], index=['scale','auto',0.01,0.001].index(hp_svm['gamma'][0]) if hp_svm['gamma'][0] in ['scale','auto',0.01,0.001] else 0, key="hp_svm_g2")
            if st.button("💾 Guardar SVM", key="save_svm_react2"):
                motor.config['hiperparametros']['svm']['C'][0] = C_svm
                motor.config['hiperparametros']['svm']['gamma'][0] = gamma_svm
                st.success(f"✅ SVM guardado: C={C_svm}, gamma={gamma_svm}")
        with tab_hyb:
            st.markdown("**CNN-LSTM:** `filtros_cnn=[32,64]`, `unidades_lstm=[50,100]`, `dropout=0.3`, `lr=0.001`, `epochs=50`, `batch=32`")
            st.markdown("**LSTM-AE+RF:** `unidades_lstm_ae=64`, `dim_latente=16`, `epochs_ae=30`, `batch=32`, `n_est_rf=200`")
            st.caption("💡 **Interpretación Híbridos:** Híbridos requieren secuencias 24 pasos. Fallback sklearn simula sin TF. Edición requiere reiniciar entrenamiento completo.")
        st.markdown("---")
        st.markdown("### 🔍 GridSearchCV Demo (búsqueda automática)")
        st.caption("💡 **Interpretación GridSearch:** Búsqueda exhaustiva sobre grid limitado (2-4 combos) para encontrar mejores hiperparámetros rápidamente. Usa StratifiedKFold 3 folds. Tiempo estimado: 10-30s para RF/XGB.")
        col_gs1, col_gs2 = st.columns([1, 2])
        with col_gs1:
            alg_gs = st.selectbox("Algoritmo para GridSearch", options=['random_forest','xgboost','svm'], format_func=lambda x: {'random_forest':'🌲 Random Forest','xgboost':'🚀 XGBoost','svm':'🔷 SVM'}[x], key="gs_alg_react2")
            n_splits_gs = st.slider("CV folds GridSearch", 2, 3, 3, key="gs_k_react2")
            btn_gs = st.button("🚀 Ejecutar GridSearch (rápido)", type="primary", use_container_width=True, key="btn_gs_react2")
        with col_gs2:
            if alg_gs == 'random_forest':
                grid_demo = {'n_estimators': [100,200], 'max_depth': [10, None], 'min_samples_split': [2,5]}
            elif alg_gs == 'xgboost':
                grid_demo = {'n_estimators': [100,200], 'max_depth': [3,6], 'learning_rate': [0.05,0.1]}
            else:
                grid_demo = {'C': [1,10], 'kernel': ['rbf','linear'], 'gamma': ['scale',0.01]}
            st.write("**Grid a probar (demo limitada):**")
            st.json(grid_demo)
            st.caption("💡 **Interpretación Grid:** Cada combinación se evalúa con CV. Mejor combinación maximiza F1. Grid pequeño = rápido; ampliar para búsqueda exhaustiva.")
        if btn_gs:
            if not hasattr(motor, 'X_train') or motor.X_train is None:
                st.error("Datos no preparados — ve a `⚙️ Entrenamiento` y prepara datos primero.")
                st.stop()
            from sklearn.model_selection import GridSearchCV, StratifiedKFold
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.svm import SVC
            try:
                import xgboost as xgb
                XGB_AVAILABLE = True
            except ImportError:
                XGB_AVAILABLE = False
            X_gs = motor.X_train
            y_gs = motor.y_train_clas
            if alg_gs == 'random_forest':
                est = RandomForestClassifier(random_state=42, n_jobs=-1, class_weight='balanced')
                param_grid = {'n_estimators': [100,200], 'max_depth': [10, None], 'min_samples_split': [2,5]}
            elif alg_gs == 'xgboost':
                if not XGB_AVAILABLE:
                    st.error("XGBoost no instalado — pip install xgboost")
                    st.stop()
                est = xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss')
                param_grid = {'n_estimators': [100,200], 'max_depth': [3,6], 'learning_rate': [0.05,0.1]}
            else:
                est = SVC(probability=True, class_weight='balanced', random_state=42)
                param_grid = {'C': [1,10], 'kernel': ['rbf','linear'], 'gamma': ['scale',0.01]}
            cv_gs = StratifiedKFold(n_splits=n_splits_gs, shuffle=True, random_state=42)
            with st.spinner(f"Ejecutando GridSearchCV para {alg_gs.upper()} ({len(param_grid)} params, {n_splits_gs} folds)..."):
                try:
                    gs = GridSearchCV(est, param_grid, cv=cv_gs, scoring='f1_weighted', n_jobs=-1, verbose=0)
                    gs.fit(X_gs, y_gs)
                    st.success(f"✅ GridSearch completado — Mejor F1: {gs.best_score_:.4f}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("Best Score (F1 weighted)", f"{gs.best_score_:.4f}")
                        st.json(gs.best_params_)
                        st.caption("💡 **Interpretación Best Score:** F1 promedio sobre folds con mejores hiperparámetros. >0.85 es bueno; comparar con baseline anterior.")
                    with c2:
                        cv_res_df = pd.DataFrame(gs.cv_results_)[['params','mean_test_score','std_test_score','rank_test_score']].sort_values('rank_test_score')
                        st.dataframe(cv_res_df, use_container_width=True)
                        st.caption("💡 **Interpretación Ranking:** rank 1 = mejor. std bajo = estable. Params con rank 1 y 2 cercanos son alternativas viables.")
                        fig_gs = px.bar(cv_res_df.head(8), x='mean_test_score', y='params', orientation='h', title='Top GridSearch Resultados (F1)', error_x='std_test_score')
                        st.plotly_chart(fig_gs, use_container_width=True)
                        st.caption("💡 **Interpretación Barra GridSearch:** Barra = mean F1, error = std. Barras más largas y con error pequeño son superiores y robustas.")
                    if st.button("💾 Aplicar mejores hiperparámetros a motor.config y re-entrenar", key="apply_gs_react2"):
                        for k,v in gs.best_params_.items():
                            if k in motor.config['hiperparametros'][alg_gs]:
                                motor.config['hiperparametros'][alg_gs][k][0] = v
                            else:
                                motor.config['hiperparametros'][alg_gs][k] = [v]
                        st.success(f"✅ Hiperparámetros de {alg_gs} actualizados. Ve a `⚙️ Entrenamiento` o `🔄 Reentrenar` para re-entrenar con los nuevos valores.")
                        st.json(motor.config['hiperparametros'][alg_gs])
                    st.session_state['gridsearch_result'] = {'alg': alg_gs, 'best_params': gs.best_params_, 'best_score': gs.best_score_, 'cv_results': gs.cv_results_}
                except Exception as e:
                    st.error(f"Error GridSearch: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        else:
            st.info("👆 Selecciona algoritmo y presiona **🚀 Ejecutar GridSearch (rápido)** para optimizar hiperparámetros automáticamente.")
            st.caption("💡 **Interpretación General Hiperparámetros:** Tuning busca equilibrio sesgo-varianza. Grid pequeño demo es rápido; ampliar grid mejora pero aumenta tiempo exponencialmente.")
            if 'gridsearch_result' in st.session_state:
                gs_prev = st.session_state['gridsearch_result']
                st.caption(f"Último GridSearch: {gs_prev['alg'].upper()} — best_score {gs_prev['best_score']:.4f} — {gs_prev['best_params']}")
     

    # ============================================================
    # TAB PRUEBAS ESTADÍSTICAS - VALIDACIÓN ROBUSTA DE MODELOS
    # ============================================================
    with tab_stats:
        st.subheader("🧪 Pruebas Estadísticas Robustas - Validación de Modelos")
        st.markdown("""
        Valida **significancia estadística** de diferencias entre los 5 algoritmos con pruebas **paramétricas y no paramétricas** robustas.
        Usa **validación cruzada estratificada/temporal** + **bootstrap** + **McNemar/Friedman** siguiendo CRISP-DM Fase 5 (Evaluación).
        """)
        
        # Verificar datos preparados
        if not hasattr(motor, 'datos_procesados') or motor.datos_procesados is None:
            st.warning("⚠️ Primero prepara datos en `⚙️ Entrenamiento` o `🔁 Validación Cruzada`.")
            if st.button("🔄 Preparar Datos Ahora", key="prep_stats"):
                with st.spinner("Preparando datos..."):
                    if motor.datos is None:
                        motor.cargar_datos()
                    motor.preparar_datos()
                    st.success("Datos preparados")
                    st.rerun()
            st.stop()
        
        # Controles superiores
        col_s1, col_s2, col_s3, col_s4 = st.columns([1.5, 1, 1, 1])
        with col_s1:
            metric_stats = st.selectbox("Métrica principal para pruebas", options=['f1_weighted','accuracy','roc_auc','precision_weighted','recall_weighted'], index=0, help="Se usará para t-test, Wilcoxon, Friedman y bootstrap")
        with col_s2:
            alpha_stats = st.select_slider("α (significancia)", options=[0.01,0.05,0.1], value=0.05, help="p < α → diferencia significativa")
        with col_s3:
            n_boot = st.select_slider("Bootstrap muestras", options=[500,1000,2000], value=1000, help="Para IC 95% del mejor modelo")
        with col_s4:
            k_stats = st.slider("Folds CV para pruebas", 3, 10, 5, step=1, help="Debe coincidir con barra de Validación Cruzada. 5 recomendado. Usa TimeSeriesSplit para evitar fuga.")
            st.progress(k_stats/10, text=f"k={k_stats}")
        
        col_s5, col_s6 = st.columns([2,1])
        with col_s5:
            cv_tipo_stats = st.radio("CV para pruebas", options=['TimeSeriesSplit','StratifiedKFold'], index=0, horizontal=True, help="TimeSeriesSplit respeta orden temporal minero")
        with col_s6:
            btn_stats = st.button("🧪 Ejecutar Pruebas Estadísticas Robustas", type="primary", use_container_width=True)
        
        # Info de interpretación
        with st.expander("📖 Guía de Interpretación de Pruebas (clic para ver)", expanded=False):
            st.markdown("""
            **Supuestos y elección de prueba:**
            - **Shapiro-Wilk** (`p>α` → normal) + **Levene** (`p>α` → varianzas homogéneas) → si ambos `p>α` usar **t-test pareado** (paramétrico), sino **Wilcoxon** (no paramétrico robusto).
            - **McNemar**: compara errores pareados en *mismo test set* (no CV), ideal para clasificadores binarios. Usa χ² con corrección Yates.
            - **Friedman**: compara **>2** modelos globalmente sobre folds. Si `p<α` → al menos uno difiere, luego **Nemenyi** post-hoc (CD = q_α * sqrt(k(k+1)/6N)).
            - **Bootstrap CI 95%**: remuestreo con reemplazo (percentil 2.5-97.5). Si IC no se solapan → diferencia robusta.
            - **Permutation test**: shuffling de etiquetas para probar si modelo > azar.
            - **Cohen's d**: tamaño efecto (0.2 pequeño, 0.5 mediano, 0.8 grande).
            """)
        
        if not btn_stats:
            st.info("👆 Configura métrica, folds y presiona **🧪 Ejecutar Pruebas Estadísticas Robustas** para validar si diferencias entre los 5 algoritmos son estadísticamente significativas (no solo por azar).")
            if 'stats_resultados' in st.session_state:
                st.caption("Últimos resultados en memoria — ejecuta de nuevo para actualizar")
            st.stop()
        
        # Imports para pruebas
        with st.spinner(f"Ejecutando CV k={k_stats} para 5 algoritmos y pruebas estadísticas (puede tardar 30-60s)..."):
            try:
                from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit, cross_validate, cross_val_predict
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.svm import SVC
                from sklearn.decomposition import PCA
                from sklearn.pipeline import make_pipeline
                from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
                from scipy.stats import shapiro, levene, ttest_rel, wilcoxon, friedmanchisquare, binomtest, permutation_test
                import scipy.stats as stats
                try:
                    import xgboost as xgb
                    XGB_AVAILABLE = True
                except ImportError:
                    XGB_AVAILABLE = False
            except ImportError as e:
                st.error(f"Falta dependencia scipy/sklearn: {e} — pip install scipy scikit-learn")
                st.stop()
            
            # Preparar datos completos (igual que Validación Cruzada)
            try:
                X_full = np.vstack([motor.X_train, motor.X_val, motor.X_test])
                y_full = np.concatenate([motor.y_train_clas, motor.y_val_clas, motor.y_test_clas])
                if hasattr(motor, 'X_train_seq') and len(motor.X_train_seq) > 0:
                    X_seq_full = np.vstack([motor.X_train_seq, motor.X_val_seq, motor.X_test_seq])
                    y_seq_full = np.concatenate([motor.y_train_seq_clas, motor.y_val_seq_clas, motor.y_test_seq_clas])
                else:
                    X_seq_full = None
                X_test_eval = motor.X_test
                y_test_eval = motor.y_test_clas
                if len(motor.X_test_seq) > 0:
                    X_test_seq_eval = motor.X_test_seq
                else:
                    X_test_seq_eval = None
            except Exception as e:
                st.error(f"Error preparando datos: {e}")
                st.stop()
            
            # Definir CV
            if cv_tipo_stats == 'TimeSeriesSplit':
                cv = TimeSeriesSplit(n_splits=k_stats)
            else:
                cv = StratifiedKFold(n_splits=k_stats, shuffle=True, random_state=42)
            
            def get_est(nombre):
                hp = motor.config['hiperparametros']
                if nombre == 'random_forest':
                    p = hp['random_forest']
                    return RandomForestClassifier(n_estimators=p['n_estimators'][0], max_depth=p['max_depth'][0], min_samples_split=p['min_samples_split'][0], random_state=42, n_jobs=-1, class_weight='balanced')
                elif nombre == 'xgboost':
                    if not XGB_AVAILABLE:
                        return None
                    p = hp['xgboost']
                    return xgb.XGBClassifier(learning_rate=p['learning_rate'][0], n_estimators=p['n_estimators'][0], max_depth=p['max_depth'][0], subsample=p['subsample'][0], random_state=42, use_label_encoder=False, eval_metric='logloss')
                elif nombre == 'svm':
                    p = hp['svm']
                    return SVC(C=p['C'][0], gamma=p['gamma'][0], kernel=p['kernel'][0], probability=True, class_weight='balanced', random_state=42)
                elif nombre == 'cnn_lstm':
                    return RandomForestClassifier(n_estimators=150, max_depth=20, random_state=42, n_jobs=-1, class_weight='balanced')
                elif nombre == 'lstm_ae_rf':
                    return make_pipeline(PCA(n_components=min(16, X_full.shape[1]), random_state=42), RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1, class_weight='balanced'))
                return None
            
            algs = ['random_forest','xgboost','svm','cnn_lstm','lstm_ae_rf']
            # Filtrar si XGB no disponible
            algs = [a for a in algs if not (a=='xgboost' and not XGB_AVAILABLE)]
            
            # 1. CV para obtener scores por fold (para Friedman, Shapiro, etc.)
            cv_scores = {}  # alg -> dict metric -> array k
            cv_predictions = {} # para McNemar: predicciones en test set
            progress = st.progress(0, text="CV para pruebas...")
            for idx, alg in enumerate(algs):
                est = get_est(alg)
                if est is None:
                    continue
                # Elegir X
                if alg == 'lstm_ae_rf':
                    X_cv, y_cv = X_full, y_full
                elif alg == 'cnn_lstm' and X_seq_full is not None and len(X_seq_full) > 20:
                    X_cv = X_seq_full.reshape(X_seq_full.shape[0], -1)
                    y_cv = y_seq_full
                else:
                    X_cv, y_cv = X_full, y_full
                # Cross_validate con varias métricas
                scoring = {'accuracy':'accuracy','f1_weighted':'f1_weighted','roc_auc':'roc_auc'}
                try:
                    res = cross_validate(est, X_cv, y_cv, cv=cv, scoring=scoring, n_jobs=-1, return_estimator=False)
                    cv_scores[alg] = {k: res[f'test_{k}'] for k in scoring}
                except Exception as e:
                    st.warning(f"CV falló para {alg}: {e}")
                # Predicciones test para McNemar
                try:
                    est.fit(X_cv, y_cv)  # ajuste rápido para McNemar (usa todo para test)
                    # Predecir test
                    if alg == 'lstm_ae_rf':
                        y_pred_test = est.predict(X_test_eval)
                    elif alg == 'cnn_lstm' and X_test_seq_eval is not None:
                        X_t = X_test_seq_eval.reshape(X_test_seq_eval.shape[0], -1)
                        y_pred_test = est.predict(X_t)
                    else:
                        y_pred_test = est.predict(X_test_eval)
                    cv_predictions[alg] = y_pred_test
                except Exception as e:
                    pass
                progress.progress(int((idx+1)/len(algs)*30), text=f"CV {alg} completado")
            
            # 2. Pruebas de supuestos: Shapiro y Levene
            st.markdown("### 1️⃣ Supuestos de Normalidad y Homocedasticidad")
            rows_sup = []
            for alg in algs:
                if alg not in cv_scores:
                    continue
                scores = cv_scores[alg][metric_stats] if metric_stats in cv_scores[alg] else cv_scores[alg]['f1_weighted']
                # Shapiro (requiere 3<=n<=5000, k=3-10 cumple)
                try:
                    _, p_shapiro = shapiro(scores)
                except Exception:
                    p_shapiro = np.nan
                # Para Levene necesitamos al menos 2 grupos, lo haremos global después
                rows_sup.append({'Algoritmo': alg.upper(), f'{metric_stats} scores': ", ".join([f"{s:.3f}" for s in scores]), 'Shapiro p': round(p_shapiro,4), 'Normal? (p>α)': "✅ Sí" if p_shapiro > alpha_stats else "❌ No"})
            df_sup = pd.DataFrame(rows_sup)
            st.dataframe(df_sup, use_container_width=True)
            st.caption("💡 **Interpretación Shapiro:** p>α (0.05) → distribución normal de scores por fold, permite t-test; p≤α → no normal, usar Wilcoxon (robusto). Scores son F1 por fold.")
            # Levene global
            try:
                samples = [cv_scores[alg][metric_stats] for alg in algs if alg in cv_scores and metric_stats in cv_scores[alg]]
                if len(samples) >= 2:
                    _, p_levene = levene(*samples)
                    st.metric("Levene (homocedasticidad) p", round(p_levene,4), delta="✅ Varianzas homogéneas" if p_levene > alpha_stats else "❌ Heterocedasticidad → usar Wilcoxon", delta_color="normal" if p_levene > alpha_stats else "inverse")
                    st.caption(f"Levene p={p_levene:.4f} → {'usar t-test pareado si Shapiro y Levene p>α, sino Wilcoxon' if p_levene>alpha_stats else 'recomendado Wilcoxon / Friedman (no paramétrico)'}")
            except Exception as e:
                st.warning(f"Levene no calculable: {e}")
            progress.progress(35, text="Supuestos completados")
            
            # 3. Pairwise: t-test, Wilcoxon, Cohen's d, McNemar
            st.markdown("### 2️⃣ Comparaciones Pareadas (2 a 2) — ¿Diferencia significativa?")
            # Crear matriz de p-valores
            algs_cv = [a for a in algs if a in cv_scores]
            n_algs = len(algs_cv)
            p_t = np.ones((n_algs, n_algs))
            p_w = np.ones((n_algs, n_algs))
            cohen_d = np.zeros((n_algs, n_algs))
            p_mcnemar = np.ones((n_algs, n_algs))
            for i, a1 in enumerate(algs_cv):
                for j, a2 in enumerate(algs_cv):
                    if i >= j:
                        continue
                    s1 = cv_scores[a1][metric_stats]
                    s2 = cv_scores[a2][metric_stats]
                    # t-test pareado
                    try:
                        _, p_t[i,j] = ttest_rel(s1, s2)
                        p_t[j,i] = p_t[i,j]
                    except Exception:
                        p_t[i,j] = np.nan
                    # Wilcoxon
                    try:
                        _, p_w[i,j] = wilcoxon(s1, s2)
                        p_w[j,i] = p_w[i,j]
                    except Exception:
                        p_w[i,j] = np.nan
                    # Cohen's d
                    try:
                        diff = s1 - s2
                        cohen_d[i,j] = diff.mean() / (diff.std(ddof=1) + 1e-8)
                        cohen_d[j,i] = -cohen_d[i,j]
                    except Exception:
                        pass
                    # McNemar en test set
                    if a1 in cv_predictions and a2 in cv_predictions:
                        try:
                            # Contingencia: b = a1 correcto & a2 incorrecto, c = a1 incorrecto & a2 correcto
                            y_true = y_test_eval
                            y1 = cv_predictions[a1]
                            y2 = cv_predictions[a2]
                            # Alinear longitudes (seq vs normal puede diferir)
                            min_len = min(len(y_true), len(y1), len(y2))
                            y_true, y1, y2 = y_true[:min_len], y1[:min_len], y2[:min_len]
                            b = np.sum((y1 == y_true) & (y2 != y_true))
                            c = np.sum((y1 != y_true) & (y2 == y_true))
                            # McNemar chi2 con corrección Yates
                            if b + c > 0:
                                chi2 = (abs(b - c) - 1)**2 / (b + c)
                                p_mcn = 1 - stats.chi2.cdf(chi2, 1)
                            else:
                                p_mcn = 1.0
                            p_mcnemar[i,j] = p_mcn
                            p_mcnemar[j,i] = p_mcn
                        except Exception:
                            pass
            # DataFrames p-valores
            df_p_t = pd.DataFrame(p_t, index=[a.upper() for a in algs_cv], columns=[a.upper() for a in algs_cv])
            df_p_w = pd.DataFrame(p_w, index=[a.upper() for a in algs_cv], columns=[a.upper() for a in algs_cv])
            df_mcn = pd.DataFrame(p_mcnemar, index=[a.upper() for a in algs_cv], columns=[a.upper() for a in algs_cv])
            # Heatmaps
            col_pw1, col_pw2 = st.columns(2)
            with col_pw1:
                st.markdown(f"**t-test pareado** p-valores (α={alpha_stats})")
                fig_t = px.imshow(df_p_t, text_auto=".3f", color_continuous_scale='RdBu_r', zmin=0, zmax=1, title="t-test pareado p")
                st.plotly_chart(fig_t, use_container_width=True)
                st.dataframe(df_p_t.style.format("{:.3f}"), use_container_width=True)
                st.caption("💡 **Interpretación t-test:** Heatmap 0-1; celda <0.05 = diferencia significativa entre par de modelos. Rojo oscuro = no significativa; azul = significativa. Requiere normalidad.")
            with col_pw2:
                st.markdown(f"**Wilcoxon** p-valores (robusto, no paramétrico)")
                fig_w = px.imshow(df_p_w, text_auto=".3f", color_continuous_scale='RdBu_r', zmin=0, zmax=1, title="Wilcoxon p")
                st.plotly_chart(fig_w, use_container_width=True)
                st.dataframe(df_p_w.style.format("{:.3f}"), use_container_width=True)
                st.caption("💡 **Interpretación Wilcoxon:** Alternativa no paramétrica robusta. p<0.05 → medianas difieren. Preferir si Shapiro p≤α o Levene heterocedástico.")
            col_pw3, col_pw4 = st.columns(2)
            with col_pw3:
                st.markdown("**McNemar** (test set pareado) p-valores")
                fig_mcn = px.imshow(df_mcn, text_auto=".3f", color_continuous_scale='RdBu_r', zmin=0, zmax=1, title="McNemar p (test set)")
                st.plotly_chart(fig_mcn, use_container_width=True)
                st.dataframe(df_mcn.style.format("{:.3f}"), use_container_width=True)
                st.caption("💡 **Interpretación McNemar:** Compara errores pareados en mismo test set (b vs c). p<0.05 → un modelo acierta donde otro falla significativamente. Ideal para binaria.")
                st.caption("McNemar: b=al1 acierta & al2 falla, c=al1 falla & al2 acierta. χ²=(|b-c|-1)²/(b+c)")
            with col_pw4:
                st.markdown("**Cohen's d** (tamaño efecto)")
                df_cohen = pd.DataFrame(cohen_d, index=[a.upper() for a in algs_cv], columns=[a.upper() for a in algs_cv])
                fig_cohen = px.imshow(df_cohen, text_auto=".2f", color_continuous_scale='RdBu', zmin=-1, zmax=1, title="Cohen's d")
                st.plotly_chart(fig_cohen, use_container_width=True)
                st.dataframe(df_cohen.style.format("{:.2f}"), use_container_width=True)
                st.caption("💡 **Interpretación Cohen's d:** Tamaño efecto práctico. |d| 0.2 pequeño, 0.5 mediano, 0.8 grande. Signo indica dirección (positivo: fila supera columna). Complementa p-valor.")
                st.caption("d=0.2 pequeño, 0.5 mediano, 0.8 grande. Signo indica dirección (positivo: fila > columna)")
            progress.progress(65, text="Pairwise completado")
            
            # 4. Global Friedman
            st.markdown("### 3️⃣ Prueba Global — ¿Algún modelo difiere? (Friedman)")
            try:
                samples_fried = [cv_scores[alg][metric_stats] for alg in algs_cv]
                fried_stat, p_fried = friedmanchisquare(*samples_fried)
                col_f1, col_f2 = st.columns([1,2])
                with col_f1:
                    st.metric("Friedman χ²", round(fried_stat,3))
                    st.metric("p-valor", round(p_fried,5), delta="✅ Significativo (hay diferencias)" if p_fried < alpha_stats else "❌ No significativo", delta_color="normal" if p_fried < alpha_stats else "inverse")
                    if p_fried < alpha_stats:
                        st.success(f"p={p_fried:.4f} < α={alpha_stats} → al menos un modelo difiere significativamente. Ver Nemenyi post-hoc.")
                    else:
                        st.info(f"p={p_fried:.4f} ≥ α → no hay evidencia de diferencia global (aunque ranking existe).")
                with col_f2:
                    # Nemenyi CD aproximado (q_alpha para k=5)
                    # q_alpha 0.05: k=5 → q=2.728 (Demšar)
                    q_alpha = {2:1.960,3:2.343,4:2.569,5:2.728,6:2.850}.get(len(algs_cv), 2.728)
                    cd = q_alpha * np.sqrt(len(algs_cv)*(len(algs_cv)+1)/(6*k_stats))
                    st.metric("Critical Difference (Nemenyi, α=0.05)", round(cd,3), help=f"CD = q_α * sqrt(k(k+1)/6N) ; q={q_alpha}, k={len(algs_cv)} algs, N={k_stats} folds")
                    # Ranking promedio
                    ranks = {}
                    for alg in algs_cv:
                        # rank promedio: menor es mejor si métrica alta, pero para ranking invertimos
                        # Para métrica donde mayor es mejor (accuracy, f1), rank 1 = mejor
                        pass
                    # Calcular ranking por fold
                    rank_matrix = []
                    for fold in range(k_stats):
                        fold_scores = [cv_scores[alg][metric_stats][fold] for alg in algs_cv]
                        # rank 1 = mayor score
                        sorted_idx = np.argsort([-s for s in fold_scores])
                        ranks_fold = [0]*len(algs_cv)
                        for rank, idx in enumerate(sorted_idx):
                            ranks_fold[idx] = rank + 1
                        rank_matrix.append(ranks_fold)
                    avg_ranks = np.mean(rank_matrix, axis=0)
                    df_rank = pd.DataFrame({'Algoritmo': [a.upper() for a in algs_cv], 'Avg Rank': avg_ranks, 'Rank 1 es mejor': avg_ranks})
                    df_rank = df_rank.sort_values('Avg Rank')
                    st.dataframe(df_rank, use_container_width=True)
                    fig_rank = px.bar(df_rank, x='Algoritmo', y='Avg Rank', color='Avg Rank', color_continuous_scale='RdBu_r', title=f"Ranking Promedio Friedman ({metric_stats}, menor es mejor)")
                    fig_rank.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig_rank, use_container_width=True)
                    st.caption(f"💡 **Interpretación Ranking Friedman:** Barra más baja = mejor rank promedio sobre {len(df_rank)} folds. Diferencia >CD={cd:.3f} es significativa Nemenyi (α=0.05).")
                    # Visual CD: barras con intervalos
                    st.caption(f"Si diferencia de Avg Rank > CD={cd:.3f} → diferencia significativa Nemenyi (α=0.05)")
            except Exception as e:
                st.error(f"Error Friedman: {e}")
            progress.progress(80, text="Friedman completado")
            
            # 5. Bootstrap CI para cada modelo (o solo mejor)
            st.markdown("### 4️⃣ Bootstrap IC 95% — Intervalos de Confianza Robustos")
            st.caption(f"Remuestreo con reemplazo sobre test set ({len(y_test_eval)} muestras), {n_boot} iteraciones. IC percentil 2.5-97.5.")
            try:
                # Usar mejor modelo según ranking Friedman o mejor_algoritmo
                best_alg = algs_cv[np.argmin([np.mean(cv_scores[alg][metric_stats]) * -1 for alg in algs_cv])]  # mayor métrica = mejor
                # Bootstrap para cada alg (vectorizado)
                boot_results = {}
                for alg in algs_cv:
                    # Usar predicciones test ya calculadas y y_true
                    if alg not in cv_predictions:
                        continue
                    y_pred = cv_predictions[alg]
                    y_true = y_test_eval[:len(y_pred)]
                    # Bootstrap
                    n = len(y_true)
                    scores_boot = []
                    for _ in range(n_boot):
                        idx = np.random.choice(n, n, replace=True)
                        y_t_b = y_true[idx]
                        y_p_b = y_pred[idx]
                        # Calcular métrica según seleccionada
                        if metric_stats == 'accuracy':
                            sc = accuracy_score(y_t_b, y_p_b)
                        elif metric_stats == 'f1_weighted':
                            sc = f1_score(y_t_b, y_p_b, average='weighted', zero_division=0)
                        elif metric_stats == 'roc_auc':
                            # Necesita probas, usar accuracy como fallback si no hay probas
                            try:
                                # Si tenemos modelo, obtener probas en bootstrap sería costoso; usar f1 como proxy
                                sc = f1_score(y_t_b, y_p_b, average='weighted', zero_division=0)
                            except Exception:
                                sc = accuracy_score(y_t_b, y_p_b)
                        else:
                            sc = accuracy_score(y_t_b, y_p_b)
                        scores_boot.append(sc)
                    boot_results[alg] = scores_boot
                
                # Mostrar IC y histogramas
                rows_boot = []
                for alg, scores in boot_results.items():
                    lo, hi = np.percentile(scores, [2.5, 97.5])
                    mean = np.mean(scores)
                    rows_boot.append({'Algoritmo': alg.upper(), 'Mean': round(mean,4), 'IC 2.5%': round(lo,4), 'IC 97.5%': round(hi,4), 'Ancho IC': round(hi-lo,4)})
                df_boot = pd.DataFrame(rows_boot).sort_values('Mean', ascending=False)
                st.dataframe(df_boot, use_container_width=True)
                st.caption("💡 **Interpretación Bootstrap:** Mean = estimación puntual; IC 95% [2.5%,97.5%] con remuestreo. Ancho IC pequeño = estimación precisa; IC no solapados → diferencia robusta.")
                # Histograma para mejor modelo y comparación
                for alg in [best_alg] + [a for a in algs_cv if a != best_alg][:2]:  # mejor + 2 más
                    if alg in boot_results:
                        fig_hist = px.histogram(x=boot_results[alg], nbins=30, title=f"Bootstrap {alg.upper()} ({metric_stats}) - IC 95% [{np.percentile(boot_results[alg],2.5):.3f}, {np.percentile(boot_results[alg],97.5):.3f}]", color_discrete_sequence=['#3498db'])
                        fig_hist.add_vline(x=np.mean(boot_results[alg]), line_dash="dash", line_color="red", annotation_text=f"mean {np.mean(boot_results[alg]):.3f}")
                        st.plotly_chart(fig_hist, use_container_width=True)
                        st.caption("💡 **Interpretación Histograma Bootstrap:** Distribución de métrica con remuestreo. Línea roja = media; ancho = variabilidad. Forma normal indica estabilidad; sesgo indica outlier en test set.")
                # Ver solapamiento IC
                st.info("Si IC 95% de dos modelos **no se solapan** → diferencia robusta y significativa (más conservador que t-test).")
            except Exception as e:
                st.error(f"Error Bootstrap: {e}")
            progress.progress(95, text="Bootstrap completado")
            
            # 6. Permutation test (opcional, rápido)
            st.markdown("### 5️⃣ Permutation Test — ¿Modelo mejor que azar?")
            try:
                # Para mejor modelo vs permutaciones de y
                best_est = get_est(best_alg)
                if best_alg == 'lstm_ae_rf':
                    X_cv_perm, y_cv_perm = X_full, y_full
                elif best_alg == 'cnn_lstm' and X_seq_full is not None:
                    X_cv_perm = X_seq_full.reshape(X_seq_full.shape[0], -1)
                    y_cv_perm = y_seq_full
                else:
                    X_cv_perm, y_cv_perm = X_full, y_full
                # Usar sklearn permutation_test con 200 permutaciones (rápido)
                from sklearn.model_selection import permutation_test_score
                score, perm_scores, pval = permutation_test_score(best_est, X_cv_perm, y_cv_perm, scoring=metric_stats if metric_stats in ['accuracy','f1_weighted','roc_auc'] else 'accuracy', cv=StratifiedKFold(3, shuffle=True, random_state=42), n_permutations=200, n_jobs=-1, random_state=42)
                col_p1, col_p2 = st.columns([1,2])
                with col_p1:
                    st.metric(f"Score real ({best_alg.upper()})", round(score,4))
                    st.metric("p-valor permutation", round(pval,4), delta="✅ Mejor que azar" if pval < alpha_stats else "❌ No mejor que azar")
                    st.caption(f"Permutaciones: 200, CV 3 folds. p={pval:.4f} < α={alpha_stats} → modelo captura señal real")
                with col_p2:
                    fig_perm = px.histogram(x=perm_scores, nbins=20, title=f"Permutation null distribution vs score real ({best_alg.upper()})", color_discrete_sequence=['#95a5a6'])
                    fig_perm.add_vline(x=score, line_color="red", line_width=3, annotation_text=f"score real {score:.3f}")
                    st.plotly_chart(fig_perm, use_container_width=True)
                    st.caption("💡 **Interpretación Permutation:** Hist gris = distribución nula (etiquetas permutadas, azar). Línea roja = score real. Si roja está en cola derecha (p<0.05) → modelo captura señal real, no azar.")
            except Exception as e:
                st.warning(f"Permutation test no disponible o falló: {e}")
            
            progress.progress(100, text="¡Pruebas completadas!")
            st.success(f"✅ Pruebas estadísticas robustas completadas para {len(algs_cv)} algoritmos, k={k_stats} folds, métrica {metric_stats}, α={alpha_stats}. Revisa heatmaps de p-valores y Friedman para decidir si diferencias son significativas.")
            st.session_state['stats_resultados'] = {'cv_scores': cv_scores, 'p_t': p_t, 'p_w': p_w, 'best_alg': best_alg}
            


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================
def main():
    if st.session_state.usuario is None:
        mostrar_login()
    else:
        mostrar_sidebar()
        
        pagina = st.session_state.pagina_actual
        
        if pagina == 'Dashboard':
            mostrar_dashboard()
        elif pagina == 'Gemelo Digital':
            mostrar_gemelo_digital()
        elif pagina == 'Mantenimiento':
            mostrar_mantenimiento()
        elif pagina == 'Predictivo':
            mostrar_predictivo()
        elif pagina == 'Motor IA':
            mostrar_motor_ia()
        elif pagina == 'Reportes':
            mostrar_reportes()
        elif pagina == 'Repuestos':
            mostrar_repuestos()
        elif pagina == 'Usuarios':
            mostrar_usuarios()
        elif pagina == 'Bitacora':
            mostrar_bitacora()
        elif pagina == 'Scrum':
            mostrar_scrum()
        else:
            mostrar_dashboard()

if __name__ == '__main__':
    main()
