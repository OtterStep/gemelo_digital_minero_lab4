# ⛏️ Sistema de Gemelos Digitales - Minería

## Gestión de Mantenimiento de Equipos de Carguío en Minas a Tajo Abierto

Aplicación web desarrollada con **Python + Streamlit** para monitorear, simular y gestionar el mantenimiento predictivo de equipos de carguío (camiones, excavadoras y cargadores) en operaciones mineras.

Incluye datos sintéticos de demostración, una base de datos SQLite local y modelos de Machine Learning previamente entrenados. Está preparada para ejecutarse localmente o publicarse como aplicación en Streamlit Community Cloud.

---

## 📋 Tabla de Contenidos

- [Características Principales](#características-principales)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación y Configuración](#instalación-y-configuración)
- [Publicación en Streamlit Cloud](#publicación-en-streamlit-cloud)
- [Guía de Usuario](#guía-de-usuario)
- [Roles y Permisos](#roles-y-permisos)
- [Metodología Scrum](#metodología-scrum)
- [Datos de Demostración](#datos-de-demostración)
- [Solución de Problemas](#solución-de-problemas)

---

## ✨ Características Principales

### 🔐 Módulo de Autenticación y Usuarios
- Inicio de sesión seguro con JWT
- 4 roles de usuario con permisos específicos
- Gestión completa de perfiles
- Bitácora de accesos para auditoría

### 📊 Dashboard Principal
- KPIs en tiempo real: OEE, MTBF, MTTR, Disponibilidad
- Visualizaciones interactivas con Plotly
- Alertas de equipos en estado crítico
- Gráficos de tendencias y distribución

### 🔧 Gemelo Digital
- Representación visual 2D de cada equipo
- Monitoreo de: motor, sistema hidráulico, frenos, neumáticos, combustible
- Análisis de salud por componente
- Simulación de escenarios de falla
- Generación de datos en tiempo real

### 📋 Gestión de Mantenimiento
- Órdenes de trabajo (preventivo, correctivo, predictivo)
- Generación automática de órdenes por horas de operación
- Historial completo de mantenimiento
- Asignación de técnicos
- Seguimiento de costos

### 📑 Reportes Multi-formato
- **PDF:** Reporte ejecutivo con KPIs, gráficos y recomendaciones
- **Word:** Informe detallado con análisis y conclusiones
- **Excel:** Datos completos con múltiples hojas y gráficos

### 🤖 Análisis Predictivo
- Modelos de Machine Learning (Random Forest)
- Predicción de probabilidad de falla
- Estimación de horas/días restantes hasta falla
- Identificación de factores críticos
- Recomendaciones automáticas

### 🔩 Gestión de Repuestos
- Catálogo completo de repuestos
- Control de stock mínimo
- Alertas de reabastecimiento

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────┐
│              INTERFAZ STREAMLIT                 │
│  (Dashboard, Gemelo Digital, Mantenimiento,     │
│   Reportes, Predictivo, Usuarios)               │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│            MÓDULOS DE NEGOCIO                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │   Auth   │ │ Dashboard│ │ Gemelo   │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Mantto.  │ │ Reportes │ │ Predict. │        │
│  └──────────┘ └──────────┘ └──────────┘        │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│            BASE DE DATOS SQLITE                 │
│  (Usuarios, Equipos, Datos Sensores, OT,        │
│   Historial, Repuestos, Predicciones)           │
└─────────────────────────────────────────────────┘
```

---

## 🛠️ Tecnologías Utilizadas

| Categoría | Tecnologías |
|-----------|-------------|
| **Lenguaje** | Python 3.11 |
| **Framework Web** | Streamlit 1.28+ |
| **Base de Datos** | SQLite3 |
| **Análisis de Datos** | Pandas, NumPy |
| **Visualizaciones** | Plotly 5.17+ |
| **Machine Learning** | Scikit-learn 1.3+ |
| **Reportes PDF** | ReportLab 4.0+ |
| **Reportes Word** | python-docx 1.1+ |
| **Reportes Excel** | openpyxl 3.1+ |
| **Seguridad** | PyJWT, bcrypt |

---

## 📁 Estructura del Proyecto

```
gemelo_digital_minero/
├── app.py                      # Archivo principal de la aplicación
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Este archivo
├── data/                       # Base de datos SQLite (generada automáticamente)
│   └── gemelo_digital.db
├── modules/                    # Módulos de negocio
│   ├── __init__.py
│   ├── auth.py                 # Autenticación y usuarios
│   ├── dashboard.py            # Dashboard y KPIs
│   ├── gemelo_digital.py       # Gemelo digital y simulación
│   ├── mantenimiento.py        # Órdenes de trabajo y mantenimiento
│   ├── reportes.py             # Generación de reportes
│   ├── predictivo.py           # Análisis predictivo ML
│   └── motor_ia.py             # Entrenamiento y carga de modelos
├── utils/                      # Utilidades
│   ├── __init__.py
│   └── database.py             # Gestión de base de datos
├── models/                     # Modelos y metadatos versionados
├── scripts/                    # Generación de datos sintéticos
├── tests/                      # Pruebas funcionales
├── notebooks/                  # Análisis exploratorio
└── docs/                       # Documentación adicional
```

---

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.11 (compatible con `tensorflow-cpu==2.15.0`)
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd gemelo_digital_minero
   ```

2. **Crear entorno virtual con Python 3.11**
   ```bash
   # Windows
   py -3.11 -m venv venv311
   venv311\Scripts\activate

   # Linux/Mac
   python3.11 -m venv venv311
   source venv311/bin/activate
   ```
   > **Importante:** Los modelos híbridos (CNN-LSTM y LSTM-Autoencoder) requieren
   > TensorFlow. Los modelos guardados en `models/` permiten usar la aplicación sin
   > volver a entrenar al iniciar.

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   streamlit run app.py
   ```

5. **Ampliar el dataset (opcional)**
   El repositorio incluye pocos cientos de registros reales, insuficientes para
   las redes profundas. Para generar ~30.000 registros sintéticos realistas
   (derivados de los rangos y umbrales de los sensores):
   ```bash
   python scripts/generar_datos_sinteticos.py 5000    # anexa 5000 por equipo
   # o con --reemplazar para vaciar primero la tabla
   ```

6. **Acceder al sistema**
   - Abrir navegador en: `http://localhost:8501`
   - La base de datos se inicializa automáticamente con datos de demostración

### Publicación en Streamlit Cloud

El repositorio ya incluye `requirements.txt` y `runtime.txt`. Para publicar la aplicación:

1. Sube este repositorio a GitHub, incluyendo `app.py`, `modules/`, `utils/`, `data/` y `models/`.
2. Entra a [share.streamlit.io](https://share.streamlit.io/) e inicia sesión con GitHub.
3. Selecciona **New app**, el repositorio y la rama que contiene el proyecto.
4. En **Main file path**, indica `app.py` y pulsa **Deploy**.
5. Espera a que finalice la instalación de dependencias. El primer despliegue puede tardar por TensorFlow.

No se requieren variables en **Secrets** para la demo. Si defines `JWT_SECRET_KEY`, usa una clave larga y aleatoria; en caso contrario la aplicación utiliza una clave de demostración incluida en el código.

#### Consideraciones de Streamlit Cloud

- La aplicación usa SQLite en `data/gemelo_digital.db`. Streamlit Cloud ofrece almacenamiento efímero: los cambios realizados desde la interfaz pueden perderse al reiniciar o redeployar.
- Los archivos de `models/` deben estar en el repositorio para evitar un entrenamiento costoso durante el primer uso del módulo **Motor IA**.
- El repositorio contiene credenciales de demostración. Cámbialas antes de usar la aplicación con información real.
- Para producción se recomienda sustituir SQLite por una base de datos externa y gestionar usuarios y secretos fuera del repositorio.

---

## 👥 Guía de Usuario

### Primer Acceso
Utilice cualquiera de los usuarios de demostración:

| Usuario | Contraseña | Rol | Funcionalidades |
|---------|------------|-----|-----------------|
| `admin` | `admin123` | 👤 Administrador | Acceso completo al sistema |
| `ingeniero` | `inge123` | 👷 Ingeniero | Dashboard, Gemelo Digital, Mantenimiento, Predictivo, Reportes, Repuestos |
| `supervisor` | `super123` | 📋 Supervisor | Dashboard, Gemelo Digital, Mantenimiento, Reportes, Repuestos |
| `tecnico` | `tec123` | 🔧 Técnico | Dashboard, Gemelo Digital, Mantenimiento |

### Navegación
1. **Iniciar sesión** con sus credenciales
2. Usar el **menú lateral** para navegar entre módulos
3. Cada módulo contiene pestañas y formularios para interactuar
4. Los botones de acción están claramente identificados

---

## 🔑 Roles y Permisos

| Módulo | Administrador | Ingeniero | Supervisor | Técnico |
|--------|:-------------:|:---------:|:----------:|:-------:|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Gemelo Digital | ✅ | ✅ | ✅ | ✅ |
| Mantenimiento | ✅ | ✅ | ✅ | ✅ |
| Análisis Predictivo | ✅ | ✅ | ❌ | ❌ |
| Reportes | ✅ | ✅ | ✅ | ❌ |
| Repuestos | ✅ | ✅ | ✅ | ❌ |
| Gestión Usuarios | ✅ | ❌ | ❌ | ❌ |
| Bitácora | ✅ | ❌ | ❌ | ❌ |
| Documentación Scrum | ✅ | ✅ | ✅ | ✅ |

---

## 📖 Metodología Scrum

El proyecto fue desarrollado siguiendo la metodología **Scrum** con 3 Sprints de 2 semanas cada uno.

### Sprint 1 - Base del Sistema (31 Story Points)
- Autenticación y gestión de usuarios
- Dashboard principal con KPIs
- Alertas de equipos críticos

### Sprint 2 - Gemelo Digital y Mantenimiento (34 Story Points)
- Visualización de gemelo digital
- Gestión de órdenes de trabajo
- Simulación de fallas
- Historial de mantenimiento

### Sprint 3 - Reportes y Predictivo (53 Story Points)
- Reportes en PDF, Word y Excel
- Análisis predictivo con ML
- Gestión de repuestos
- Órdenes automáticas
- Documentación completa

> 📝 **Ver documentación completa de Scrum dentro de la aplicación en la pestaña "Documentación Scrum"**

---

## 📊 Datos de Demostración

El sistema incluye datos simulados realistas basados en especificaciones de equipos mineros reales:

### Equipos Incluidos
| Código | Nombre | Tipo | Marca | Modelo |
|--------|--------|------|-------|--------|
| CAM-001 | Camión Cat 797F | Camión | Caterpillar | 797F |
| CAM-002 | Camión Komatsu 930E | Camión | Komatsu | 930E-5 |
| EXC-001 | Excavadora Cat 6060 | Excavadora | Caterpillar | 6060 FS |
| EXC-002 | Excavadora Komatsu PC8000 | Excavadora | Komatsu | PC8000-11 |
| CAR-001 | Cargador Cat 994K | Cargador | Caterpillar | 994K |
| CAR-002 | Cargador Komatsu WA900 | Cargador | Komatsu | WA900-8 |

### Datos Simulados
- 50 registros de sensores por equipo
- Parámetros realistas de operación minera
- Órdenes de trabajo de ejemplo
- Catálogo de repuestos industriales

---

## 🔧 Solución de Problemas

### Error: No se puede conectar a la base de datos
- Verifique que exista la carpeta `data/`
- La aplicación crea la base de datos automáticamente al primer inicio

### Error al instalar TensorFlow o NumPy en Streamlit Cloud
- Confirme que `runtime.txt` contiene `3.11`.
- Confirme que `requirements.txt` mantiene `tensorflow-cpu==2.15.0` y `numpy<2.0`.
- Reinicie la aplicación desde **Manage app > Reboot app** después de actualizar el repositorio.

### Error: Dependencias faltantes
- Ejecute: `pip install -r requirements.txt --upgrade`

### La aplicación no se abre en el navegador
- Verifique que Streamlit esté instalado: `streamlit --version`
- Intente con otro navegador
- Verifique que el puerto 8501 esté disponible

### Los gráficos no se muestran
- Actualice Plotly: `pip install plotly --upgrade`
- Verifique que JavaScript esté habilitado en el navegador

### Problemas con reportes PDF/Word/Excel
- Verifique las dependencias: `reportlab`, `python-docx`, `openpyxl`
- Asegúrese de tener permisos de escritura en la carpeta temporal

---

## 📚 Recursos Adicionales

### Datasets Públicos Recomendados
- [Kaggle - Predictive Maintenance Dataset](https://www.kaggle.com/datasets/shivamb/machine-predictive-maintenance-classification)
- [Kaggle - Equipment Failure Data](https://www.kaggle.com/datasets/hiro5299834/equipment-failure-data)
- [UCI Machine Learning Repository - Maintenance Data](https://archive.ics.uci.edu/ml/datasets.php)

### Normas y Referencias
- ISO 14224 - Reliability, availability and maintainability
- ISO 55000 - Asset management
- SAE J1939 - Comunicación en vehículos pesados

---

## 🤝 Contribución

Este proyecto es una práctica educativa. Para contribuir:
1. Documente bien el código
2. Siga las convenciones PEP 8
3. Pruebe las funcionalidades antes de enviar cambios

---

## 📄 Licencia

Proyecto educativo desarrollado para fines de aprendizaje sobre:
- Desarrollo de aplicaciones con Streamlit
- Gemelos digitales aplicados a la industria
- Mantenimiento predictivo en minería
- Metodologías ágiles (Scrum)

---

## 📞 Soporte

Para consultas o soporte técnico, revisar:
1. Este archivo README
2. Documentación dentro de la aplicación
3. Comentarios en el código fuente

---

**Sistema de Gemelos Digitales para Minería**
