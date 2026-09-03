"""
Motor de Inteligencia Artificial para Gemelo Digital de Equipos Mineros

Aplica la metodología CRISP-DM en 6 fases:
1. Comprensión del Negocio
2. Comprensión de los Datos
3. Preparación de los Datos
4. Modelado (5 algoritmos: RF, XGBoost, SVM, CNN-LSTM, LSTM-AE+RF)
5. Evaluación comparativa
6. Despliegue e integración

Autor: Científico de Datos Senior - Gemelos Digitales Mineros
"""

import os
import sys
import time
import json
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime

# Asegurar codificación UTF-8 en stdout/stderr en Windows
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

warnings.filterwarnings('ignore')

# Librerías de ML tradicional
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.svm import SVC, SVR
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    mean_squared_error, mean_absolute_error, r2_score
)
from sklearn.impute import SimpleImputer, KNNImputer
from imblearn.over_sampling import SMOTE, ADASYN

# XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[WARN] XGBoost no disponible. Instalar con: pip install xgboost")

# Deep Learning (TensorFlow/Keras)
try:
    import tensorflow as tf
    from tensorflow.keras.models import Model, Sequential, load_model
    from tensorflow.keras.layers import (
        Input, Conv1D, LSTM, Dense, Dropout, Flatten,
        RepeatVector, TimeDistributed, BatchNormalization
    )
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("[WARN] TensorFlow no disponible. Usar el entorno venv312 (Python 3.12): pip install tensorflow-cpu")

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)


class MotorPredictivo:
    """
    Motor predictivo completo para el gemelo digital de motores de equipos mineros.
    Implementa 5 algoritmos y sigue la metodología CRISP-DM.
    """

    def __init__(self, config=None):
        """
        Inicializar motor predictivo con configuración.
        
        Args:
            config: Diccionario de configuración personalizada
        """
        # Configuración por defecto (CRISP-DM Fase 1: Comprensión del Negocio)
        self.config = config or self._get_default_config()
        
        # Estado interno
        self.datos = None
        self.datos_procesados = None
        self.X_train = self.X_val = self.X_test = None
        self.y_train = self.y_val = self.y_test = None
        self.X_train_seq = self.X_val_seq = self.X_test_seq = None
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.modelos = {}
        self.resultados_evaluacion = {}
        self.mejor_algoritmo = None
        self.puntuaciones = {}
        self.entrenado = False
        self.cargado = False
        
        # Log
        self._log(f"MotorPredictivo inicializado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ============================================================
    # CONFIGURACIÓN (FASE 1: COMPRENSIÓN DEL NEGOCIO)
    # ============================================================
    
    def _get_default_config(self):
        """Configuración por defecto basada en objetivos de negocio"""
        return {
            # Objetivos de negocio
            'objetivos_negocio': {
                'reducir_mttr_pct': 20,
                'aumentar_disponibilidad_pct': 5,
                'reducir_costos_pct': 15,
                'costo_falla_no_detectada': 25000,  # USD
                'costo_falso_positivo': 500,        # USD
            },
            # Criterios de éxito del modelo
            'criterios_exito': {
                'precision_min': 0.85,
                'sensibilidad_min': 0.90,
                'f1_min': 0.85,
                'tiempo_inferencia_max_seg': 1.0,
            },
            # Preparación de datos
            'preparacion': {
                'ventana_temporal': 24,       # Lecturas hacia atrás para LSTM
                'horas_prediccion': 100,      # Predecir falla en próximas 100h
                'test_size': 0.15,
                'val_size': 0.15,
                'balanceo_clases': 'smote',   # smote, adasyn, class_weight
                'tratamiento_nulos': 'knn',   # mean, median, knn
                'metodo_outliers': 'iqr',     # iqr, zscore, none
            },
            # Hiperparámetros por algoritmo
            'hiperparametros': {
                'random_forest': {
                    'n_estimators': [100, 200],
                    'max_depth': [10, None],
                    'min_samples_split': [2, 5],
                    'cv': 3,
                },
                'xgboost': {
                    'learning_rate': [0.01, 0.1],
                    'n_estimators': [100, 300],
                    'max_depth': [3, 6],
                    'subsample': [0.8, 1.0],
                },
                'svm': {
                    'C': [1, 10],
                    'gamma': ['scale', 0.01],
                    'kernel': ['rbf', 'linear'],
                    'cv': 3,
                },
                'cnn_lstm': {
                    'filtros_cnn': [32, 64],
                    'unidades_lstm': [50, 100],
                    'dropout': 0.3,
                    'learning_rate': 0.001,
                    'epochs': 50,
                    'batch_size': 32,
                },
                'lstm_ae_rf': {
                    'unidades_lstm_ae': 64,
                    'dimension_latente': 16,
                    'epochs_ae': 30,
                    'batch_size_ae': 32,
                    'n_estimators_rf': 200,
                },
            },
            # Criterios de selección ponderados
            'criterios_seleccion': {
                'rendimiento_predictivo': 0.40,  # F1 + AUC
                'tiempo_inferencia': 0.25,
                'interpretabilidad': 0.20,
                'facilidad_mantenimiento': 0.15,
            },
            # Interpretabilidad cualitativa (1-10)
            'interpretabilidad_algoritmos': {
                'random_forest': 8,
                'xgboost': 7,
                'svm': 4,
                'cnn_lstm': 2,
                'lstm_ae_rf': 5,
            },
            # Facilidad de mantenimiento cualitativa (1-10)
            'mantenibilidad_algoritmos': {
                'random_forest': 9,
                'xgboost': 8,
                'svm': 6,
                'cnn_lstm': 3,
                'lstm_ae_rf': 4,
            },
        }

    # ============================================================
    # FASE 2: COMPRENSIÓN DE LOS DATOS
    # ============================================================
    
    def cargar_datos(self, datos_df=None, desde_db=True, equipo_id=None):
        """
        Cargar datos de sensores para análisis.
        
        Args:
            datos_df: DataFrame con datos (opcional)
            desde_db: Cargar desde base de datos SQLite
            equipo_id: Filtrar por equipo específico
        """
        if datos_df is not None:
            self.datos = datos_df.copy()
        elif desde_db:
            sys.path.insert(0, BASE_DIR)
            from utils.database import get_connection
            conn = get_connection()
            
            query = """
            SELECT d.*, e.tipo as equipo_tipo, e.marca, e.modelo,
                   e.horas_operacion as horas_totales_equipo,
                   CASE WHEN e.estado IN ('Critico', 'Fuera de Servicio') THEN 1 ELSE 0 END as falla_equipo
            FROM datos_equipos d
            JOIN equipos e ON d.equipo_id = e.id
            """
            params = []
            if equipo_id:
                query += " WHERE d.equipo_id = ?"
                params.append(equipo_id)
            query += " ORDER BY d.fecha_hora"
            
            self.datos = pd.read_sql_query(query, conn, params=params)
            conn.close()
        
        self._log(f"Datos cargados: {len(self.datos)} registros, {len(self.datos.columns)} columnas")
        return self.datos
    
    def analisis_exploratorio(self):
        """
        Realizar Análisis Exploratorio de Datos (EDA).
        
        Returns:
            Diccionario con estadísticas y hallazgos
        """
        if self.datos is None:
            raise ValueError("Primero debe cargar los datos con cargar_datos()")
        
        df = self.datos
        
        # Variables numéricas de sensores
        variables_sensores = [
            'temp_motor', 'presion_aceite', 'rpm_motor', 'horas_motor',
            'presion_hidraulica', 'temp_aceite_hidraulico', 'nivel_aceite_hidraulico',
            'desgaste_pastillas', 'presion_neumaticos', 'desgaste_neumaticos',
            'nivel_combustible', 'consumo_combustible', 'carga_actual'
        ]
        
        # Estadísticas descriptivas
        stats = df[variables_sensores].describe().to_dict()
        
        # Valores nulos
        nulos = df[variables_sensores].isnull().sum().to_dict()
        pct_nulos = {k: round(v / len(df) * 100, 2) for k, v in nulos.items()}
        
        # Correlaciones
        correlaciones = df[variables_sensores].corr().to_dict()
        
        # Desbalance de clases (si existe variable objetivo)
        if 'falla_equipo' in df.columns:
            desbalance = df['falla_equipo'].value_counts(normalize=True).to_dict()
        else:
            desbalance = None
        
        # Detección de outliers (IQR)
        outliers = {}
        for col in variables_sensores:
            if col in df.columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers[col] = int(((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum())
        
        eda_resultados = {
            'num_registros': len(df),
            'num_columnas': len(df.columns),
            'variables_sensores': variables_sensores,
            'estadisticas_descriptivas': stats,
            'valores_nulos': nulos,
            'porcentaje_nulos': pct_nulos,
            'correlaciones': correlaciones,
            'desbalance_clases': desbalance,
            'outliers_por_variable': outliers,
            'rango_fechas': {
                'inicio': str(df['fecha_hora'].min()) if 'fecha_hora' in df.columns else None,
                'fin': str(df['fecha_hora'].max()) if 'fecha_hora' in df.columns else None
            }
        }
        
        self._log(f"EDA completado: {len(variables_sensores)} variables analizadas")
        self.eda_resultados = eda_resultados
        return eda_resultados

    # ============================================================
    # FASE 3: PREPARACIÓN DE LOS DATOS
    # ============================================================
    
    def preparar_datos(self):
        """
        Preparar datos para modelado: limpieza, transformación,
        ingeniería de características, división y secuenciación.
        """
        if self.datos is None:
            raise ValueError("Primero debe cargar los datos")
        
        df = self.datos.copy()
        
        variables_sensores = [
            'temp_motor', 'presion_aceite', 'rpm_motor', 'horas_motor',
            'presion_hidraulica', 'temp_aceite_hidraulico', 'nivel_aceite_hidraulico',
            'desgaste_pastillas', 'presion_neumaticos', 'desgaste_neumaticos',
            'nivel_combustible', 'consumo_combustible', 'carga_actual'
        ]
        
        # Eliminar columnas no numéricas irrelevantes
        cols_utiles = variables_sensores + ['equipo_id', 'fecha_hora']
        cols_existentes = [c for c in cols_utiles if c in df.columns]
        df = df[cols_existentes].copy()
        
        # Convertir fecha_hora
        if 'fecha_hora' in df.columns:
            df['fecha_hora'] = pd.to_datetime(df['fecha_hora'])
            df = df.sort_values('fecha_hora').reset_index(drop=True)
        
        # --- Tratamiento de nulos ---
        metodo_nulos = self.config['preparacion']['tratamiento_nulos']
        for col in variables_sensores:
            if col in df.columns and df[col].isnull().sum() > 0:
                if metodo_nulos == 'mean':
                    df[col] = df[col].fillna(df[col].mean())
                elif metodo_nulos == 'median':
                    df[col] = df[col].fillna(df[col].median())
                elif metodo_nulos == 'knn':
                    imputer = KNNImputer(n_neighbors=5)
                    df[col] = imputer.fit_transform(df[[col]]).ravel()
        
        # --- Tratamiento de outliers ---
        metodo_outliers = self.config['preparacion']['metodo_outliers']
        if metodo_outliers == 'iqr':
            for col in variables_sensores:
                if col in df.columns:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    limite_inf = Q1 - 1.5 * IQR
                    limite_sup = Q3 + 1.5 * IQR
                    df[col] = df[col].clip(limite_inf, limite_sup)
        
        # --- Ingeniería de características ---
        # Variables de degradación acumulada
        if 'horas_motor' in df.columns:
            df['degradacion_horas'] = df.groupby('equipo_id')['horas_motor'].transform(
                lambda x: x - x.min()
            ) if 'equipo_id' in df.columns else (df['horas_motor'] - df['horas_motor'].min())
        
        # Estadísticas móviles (ventanas de 5, 10, 24)
        for ventana in [5, 10, 24]:
            for col in ['temp_motor', 'presion_aceite', 'rpm_motor']:
                if col in df.columns:
                    df[f'{col}_mean_{ventana}'] = df.groupby('equipo_id')[col].transform(
                        lambda x: x.rolling(window=ventana, min_periods=1).mean()
                    ) if 'equipo_id' in df.columns else df[col].rolling(window=ventana, min_periods=1).mean()
                    
                    df[f'{col}_std_{ventana}'] = df.groupby('equipo_id')[col].transform(
                        lambda x: x.rolling(window=ventana, min_periods=1).std()
                    ) if 'equipo_id' in df.columns else df[col].rolling(window=ventana, min_periods=1).std()
        
        # --- Crear variable objetivo (binaria) ---
        # Simular falla basada en umbrales críticos
        df['falla_proxima'] = (
            (df['temp_motor'] > 100) |
            (df['presion_aceite'] < 30) |
            (df['presion_hidraulica'] < 170) |
            (df['desgaste_neumaticos'] > 70) |
            (df['desgaste_pastillas'] > 75)
        ).astype(int)
        
        # Variable objetivo de regresión (horas restantes simuladas)
        df['horas_restantes'] = np.where(
            df['falla_proxima'] == 1,
            np.random.uniform(0, 50, len(df)),
            np.where(
                df['temp_motor'] > 90,
                np.random.uniform(50, 200, len(df)),
                np.random.uniform(200, 1000, len(df))
            )
        )
        
        # --- Limpieza final: eliminar cualquier NaN residual ---
        df = df.ffill().bfill()
        # Para columnas que aún tengan NaN, usar la media
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64', 'float32', 'int32'] and df[col].isnull().any():
                df[col] = df[col].fillna(df[col].mean())
        
        # --- Seleccionar características finales ---
        self.caracteristicas = [c for c in df.columns if c not in [
            'equipo_id', 'fecha_hora', 'falla_proxima', 'horas_restantes'
        ] and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
        
        X = df[self.caracteristicas].values
        y_clas = df['falla_proxima'].values
        y_reg = df['horas_restantes'].values
        
        # --- División temporal (70/15/15) ---
        n_total = len(X)
        n_train = int(n_total * (1 - self.config['preparacion']['test_size'] - self.config['preparacion']['val_size']))
        n_val = int(n_total * self.config['preparacion']['val_size'])
        
        self.X_train = X[:n_train]
        self.y_train_clas = y_clas[:n_train]
        self.y_train_reg = y_reg[:n_train]
        
        self.X_val = X[n_train:n_train + n_val]
        self.y_val_clas = y_clas[n_train:n_train + n_val]
        self.y_val_reg = y_reg[n_train:n_train + n_val]
        
        self.X_test = X[n_train + n_val:]
        self.y_test_clas = y_clas[n_train + n_val:]
        self.y_test_reg = y_reg[n_train + n_val:]
        
        # --- Estandarización ---
        self.X_train = self.scaler_X.fit_transform(self.X_train)
        self.X_val = self.scaler_X.transform(self.X_val)
        self.X_test = self.scaler_X.transform(self.X_test)
        
        # --- Balanceo de clases ---
        metodo_balanceo = self.config['preparacion']['balanceo_clases']
        if metodo_balanceo == 'smote' and np.mean(self.y_train_clas) < 0.4:
            try:
                smote = SMOTE(random_state=42)
                self.X_train_bal, self.y_train_clas_bal = smote.fit_resample(self.X_train, self.y_train_clas)
                self._log(f"SMOTE aplicado: {len(self.X_train)} → {len(self.X_train_bal)} muestras")
            except:
                self.X_train_bal, self.y_train_clas_bal = self.X_train, self.y_train_clas
        else:
            self.X_train_bal, self.y_train_clas_bal = self.X_train, self.y_train_clas
        
        # --- Crear secuencias para modelos LSTM ---
        ventana = self.config['preparacion']['ventana_temporal']
        self.X_train_seq = self._crear_secuencias(self.X_train, ventana)
        self.X_val_seq = self._crear_secuencias(self.X_val, ventana)
        self.X_test_seq = self._crear_secuencias(self.X_test, ventana)
        
        # Ajustar etiquetas para secuencias
        self.y_train_seq_clas = self.y_train_clas[ventana - 1:]
        self.y_val_seq_clas = self.y_val_clas[ventana - 1:]
        self.y_test_seq_clas = self.y_test_clas[ventana - 1:]
        
        self.y_train_seq_reg = self.y_train_reg[ventana - 1:]
        self.y_val_seq_reg = self.y_val_reg[ventana - 1:]
        self.y_test_seq_reg = self.y_test_reg[ventana - 1:]
        
        self.datos_procesados = df
        self._log(f"Datos preparados: Train={len(self.X_train)}, Val={len(self.X_val)}, Test={len(self.X_test)}")
        self._log(f"Secuencias LSTM: Train={len(self.X_train_seq)}, Val={len(self.X_val_seq)}, Test={len(self.X_test_seq)}")
        
        return True
    
    def _crear_secuencias(self, datos, ventana):
        """Crear secuencias temporales para modelos LSTM"""
        secuencias = []
        for i in range(ventana - 1, len(datos)):
            secuencias.append(datos[i - ventana + 1:i + 1])
        return np.array(secuencias)

    # ============================================================
    # FASE 4: MODELADO
    # ============================================================
    
    def entrenar_random_forest(self):
        """Entrenar modelo Random Forest"""
        self._log("Entrenando Random Forest...")
        inicio = time.time()
        
        hp = self.config['hiperparametros']['random_forest']
        
        rf = RandomForestClassifier(
            n_estimators=hp['n_estimators'][0],
            max_depth=hp['max_depth'][0],
            min_samples_split=hp['min_samples_split'][0],
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        
        rf.fit(self.X_train_bal, self.y_train_clas_bal)
        
        tiempo_entrenamiento = time.time() - inicio
        
        # Importancia de características
        importancias = dict(zip(self.caracteristicas, rf.feature_importances_))
        importancias_ordenadas = sorted(importancias.items(), key=lambda x: x[1], reverse=True)
        
        self.modelos['random_forest'] = {
            'modelo': rf,
            'tipo': 'clasificacion',
            'tiempo_entrenamiento': tiempo_entrenamiento,
            'importancias': importancias_ordenadas,
            'usa_secuencias': False,
        }
        
        self._log(f"Random Forest entrenado en {tiempo_entrenamiento:.2f}s")
        return rf
    
    def entrenar_xgboost(self):
        """Entrenar modelo XGBoost"""
        if not XGBOOST_AVAILABLE:
            self._log("⚠️ XGBoost no disponible, saltando...")
            return None
        
        self._log("Entrenando XGBoost...")
        inicio = time.time()
        
        hp = self.config['hiperparametros']['xgboost']
        
        xgb_model = xgb.XGBClassifier(
            learning_rate=hp['learning_rate'][0],
            n_estimators=hp['n_estimators'][0],
            max_depth=hp['max_depth'][0],
            subsample=hp['subsample'][0],
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss',
            scale_pos_weight=len(self.y_train_clas_bal) / max(1, sum(self.y_train_clas_bal == 0))
        )
        
        xgb_model.fit(
            self.X_train_bal, self.y_train_clas_bal,
            eval_set=[(self.X_val, self.y_val_clas)],
            verbose=False
        )
        
        tiempo_entrenamiento = time.time() - inicio
        
        # Importancia de características
        importancias = xgb_model.get_booster().get_score(importance_type='gain')
        importancias_ordenadas = sorted(importancias.items(), key=lambda x: x[1], reverse=True)
        
        self.modelos['xgboost'] = {
            'modelo': xgb_model,
            'tipo': 'clasificacion',
            'tiempo_entrenamiento': tiempo_entrenamiento,
            'importancias': importancias_ordenadas,
            'usa_secuencias': False,
        }
        
        self._log(f"XGBoost entrenado en {tiempo_entrenamiento:.2f}s")
        return xgb_model
    
    def entrenar_svm(self):
        """Entrenar modelo SVM"""
        self._log("Entrenando SVM...")
        inicio = time.time()
        
        hp = self.config['hiperparametros']['svm']
        
        svm = SVC(
            C=hp['C'][0],
            gamma=hp['gamma'][0],
            kernel=hp['kernel'][0],
            probability=True,
            random_state=42,
            class_weight='balanced'
        )
        
        # Usar subconjunto por velocidad
        n_muestras = min(5000, len(self.X_train_bal))
        svm.fit(self.X_train_bal[:n_muestras], self.y_train_clas_bal[:n_muestras])
        
        tiempo_entrenamiento = time.time() - inicio
        
        self.modelos['svm'] = {
            'modelo': svm,
            'tipo': 'clasificacion',
            'tiempo_entrenamiento': tiempo_entrenamiento,
            'importancias': None,
            'usa_secuencias': False,
        }
        
        self._log(f"SVM entrenado en {tiempo_entrenamiento:.2f}s")
        return svm
    
    def entrenar_cnn_lstm(self):
        """Entrenar modelo híbrido CNN-LSTM (fallback sklearn si TensorFlow no disponible)"""
        if not TENSORFLOW_AVAILABLE:
            self._log("⚠️ TensorFlow no disponible, usando fallback sklearn para CNN-LSTM (simulado híbrido)...")
            inicio = time.time()
            # Fallback: RandomForest sobre secuencias aplanadas (simula extracción CNN + memoria LSTM)
            try:
                from sklearn.ensemble import RandomForestClassifier
                # Usar secuencias si hay suficientes, sino datos balanceados
                if hasattr(self, 'X_train_seq') and len(self.X_train_seq) > 10:
                    X_train_fallback = self.X_train_seq.reshape(self.X_train_seq.shape[0], -1)
                    y_train_fallback = self.y_train_seq_clas
                    usa_seq = True
                else:
                    X_train_fallback = self.X_train_bal
                    y_train_fallback = self.y_train_clas_bal
                    usa_seq = False
                rf_fallback = RandomForestClassifier(n_estimators=150, max_depth=20, random_state=42, n_jobs=-1, class_weight='balanced')
                rf_fallback.fit(X_train_fallback, y_train_fallback)
                tiempo = time.time() - inicio
                self.modelos['cnn_lstm'] = {
                    'modelo': rf_fallback,
                    'tipo': 'clasificacion',
                    'tiempo_entrenamiento': tiempo,
                    'importancias': None,
                    'usa_secuencias': usa_seq,
                    'fallback': True,
                    'fallback_info': 'Simula CNN(Conv1D)+LSTM con RF sobre secuencias aplanadas (Python 3.14 sin TensorFlow)'
                }
                self._log(f"CNN-LSTM (fallback RF) entrenado en {tiempo:.2f}s - simula arquitectura híbrida")
                return rf_fallback
            except Exception as e:
                self._log(f"Error en fallback CNN-LSTM: {e}")
                return None
        
        self._log("Entrenando CNN-LSTM...")
        inicio = time.time()
        
        hp = self.config['hiperparametros']['cnn_lstm']
        input_shape = (self.X_train_seq.shape[1], self.X_train_seq.shape[2])
        
        # Arquitectura CNN-LSTM
        modelo = Sequential([
            # Capas CNN para extracción de características locales
            Conv1D(filters=hp['filtros_cnn'][0], kernel_size=3, activation='relu', input_shape=input_shape),
            BatchNormalization(),
            Conv1D(filters=hp['filtros_cnn'][0] // 2, kernel_size=3, activation='relu'),
            BatchNormalization(),
            
            # Capas LSTM para dependencias temporales
            LSTM(units=hp['unidades_lstm'][0], return_sequences=True),
            Dropout(hp['dropout']),
            LSTM(units=hp['unidades_lstm'][0] // 2),
            Dropout(hp['dropout']),
            
            # Capas densas para clasificación
            Dense(64, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        
        modelo.compile(
            optimizer=Adam(learning_rate=hp['learning_rate']),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
        )
        
        # Callbacks
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6)
        
        # Asegurar que las secuencias tengan suficientes datos
        if len(self.X_train_seq) > 0 and len(self.X_val_seq) > 0:
            historia = modelo.fit(
                self.X_train_seq, self.y_train_seq_clas,
                validation_data=(self.X_val_seq, self.y_val_seq_clas),
                epochs=hp['epochs'],
                batch_size=hp['batch_size'],
                callbacks=[early_stopping, reduce_lr],
                verbose=0
            )
        else:
            self._log("⚠️ Secuencias insuficientes para CNN-LSTM")
            return None
        
        tiempo_entrenamiento = time.time() - inicio
        
        self.modelos['cnn_lstm'] = {
            'modelo': modelo,
            'tipo': 'clasificacion',
            'tiempo_entrenamiento': tiempo_entrenamiento,
            'importancias': None,
            'usa_secuencias': True,
            'historia': historia.history,
        }
        
        self._log(f"CNN-LSTM entrenado en {tiempo_entrenamiento:.2f}s")
        return modelo
    
    def entrenar_lstm_ae_rf(self):
        """Entrenar modelo híbrido LSTM-Autoencoder + Random Forest (fallback PCA+RF si TF no disponible)"""
        if not TENSORFLOW_AVAILABLE:
            self._log("⚠️ TensorFlow no disponible, usando fallback PCA+RF para LSTM-AE+RF (simulado híbrido)...")
            inicio = time.time()
            try:
                from sklearn.decomposition import PCA
                from sklearn.ensemble import RandomForestClassifier
                # Fallback: PCA como Autoencoder lineal + RF (simula compresión temporal)
                n_comp = min(16, self.X_train_bal.shape[1])
                pca = PCA(n_components=n_comp, random_state=42)
                X_train_lat = pca.fit_transform(self.X_train_bal)
                rf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1, class_weight='balanced')
                rf.fit(X_train_lat, self.y_train_clas_bal)
                tiempo = time.time() - inicio
                varianza = float(sum(pca.explained_variance_ratio_))
                self.modelos['lstm_ae_rf'] = {
                    'modelo': rf,
                    'pca': pca,
                    'encoder': pca,  # compatibilidad con predecir/evaluar
                    'tipo': 'clasificacion',
                    'tiempo_entrenamiento': tiempo,
                    'importancias': None,
                    'usa_secuencias': False,
                    'fallback': True,
                    'fallback_info': f'Simula LSTM-AE (PCA varianza {varianza:.2%}) + RF'
                }
                self._log(f"LSTM-AE+RF (fallback PCA+RF, var={varianza:.2%}) entrenado en {tiempo:.2f}s")
                return rf
            except Exception as e:
                self._log(f"Error en fallback LSTM-AE+RF: {e}")
                return None
        
        self._log("Entrenando LSTM-Autoencoder + Random Forest...")
        inicio = time.time()
        
        hp = self.config['hiperparametros']['lstm_ae_rf']
        input_shape = (self.X_train_seq.shape[1], self.X_train_seq.shape[2])
        
        if len(self.X_train_seq) < 10:
            self._log("⚠️ Secuencias insuficientes para LSTM-AE")
            return None
        
        # --- Etapa 1: LSTM Autoencoder ---
        # Encoder
        encoder_inputs = Input(shape=input_shape)
        encoder_lstm1 = LSTM(hp['unidades_lstm_ae'], return_sequences=True)(encoder_inputs)
        encoder_lstm2 = LSTM(hp['dimension_latente'], return_sequences=False)(encoder_lstm1)
        
        # Decoder
        decoder_repeat = RepeatVector(input_shape[0])(encoder_lstm2)
        decoder_lstm1 = LSTM(hp['unidades_lstm_ae'], return_sequences=True)(decoder_repeat)
        decoder_output = TimeDistributed(Dense(input_shape[1]))(decoder_lstm1)
        
        # Modelo Autoencoder completo
        autoencoder = Model(encoder_inputs, decoder_output)
        autoencoder.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        
        # Entrenar Autoencoder
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        
        autoencoder.fit(
            self.X_train_seq, self.X_train_seq,
            validation_data=(self.X_val_seq, self.X_val_seq),
            epochs=hp['epochs_ae'],
            batch_size=hp['batch_size_ae'],
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Modelo Encoder para extracción de características
        encoder = Model(encoder_inputs, encoder_lstm2)
        
        # Extraer características latentes
        caracteristicas_latentes_train = encoder.predict(self.X_train_seq, verbose=0)
        caracteristicas_latentes_test = encoder.predict(self.X_test_seq, verbose=0)
        
        # --- Etapa 2: Random Forest con características latentes ---
        from sklearn.ensemble import RandomForestClassifier
        rf = RandomForestClassifier(
            n_estimators=hp['n_estimators_rf'],
            max_depth=15,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        )
        
        rf.fit(caracteristicas_latentes_train, self.y_train_seq_clas[:len(caracteristicas_latentes_train)])
        
        tiempo_entrenamiento = time.time() - inicio
        
        self.modelos['lstm_ae_rf'] = {
            'modelo': rf,
            'encoder': encoder,
            'autoencoder': autoencoder,
            'tipo': 'clasificacion',
            'tiempo_entrenamiento': tiempo_entrenamiento,
            'importancias': None,
            'usa_secuencias': True,
        }
        
        self._log(f"LSTM-AE + RF entrenado en {tiempo_entrenamiento:.2f}s")
        return rf
    
    def entrenar_todos(self):
        """Entrenar los 5 algoritmos secuencialmente"""
        self._log("=" * 60)
        self._log("INICIANDO ENTRENAMIENTO DE 5 ALGORITMOS")
        self._log("=" * 60)
        
        if self.datos_procesados is None:
            self.preparar_datos()
        
        self.entrenar_random_forest()
        self.entrenar_xgboost()
        self.entrenar_svm()
        self.entrenar_cnn_lstm()
        self.entrenar_lstm_ae_rf()
        
        self.entrenado = True
        self._log(f"\n✅ Entrenamiento completado: {len(self.modelos)} algoritmos listos")
        return self.modelos

    # ============================================================
    # FASE 5: EVALUACIÓN
    # ============================================================
    
    def evaluar_algoritmo(self, nombre_algoritmo):
        """Evaluar un algoritmo específico con múltiples métricas"""
        if nombre_algoritmo not in self.modelos:
            raise ValueError(f"Algoritmo {nombre_algoritmo} no entrenado")
        
        info = self.modelos[nombre_algoritmo]
        modelo = info['modelo']
        
        # Preparar datos de entrada
        if info['usa_secuencias']:
            X_eval = self.X_test_seq
            y_eval = self.y_test_seq_clas
        else:
            X_eval = self.X_test
            y_eval = self.y_test_clas
        
        if len(X_eval) == 0 or len(y_eval) == 0:
            return None
        
        # Tiempo de inferencia
        inicio = time.time()
        
        # Fallback híbrido sin TensorFlow: usar PCA/RF y secuencias aplanadas
        if info.get('fallback'):
            if nombre_algoritmo == 'lstm_ae_rf' and 'pca' in info:
                # PCA como autoencoder
                pca = info['pca']
                # X_eval puede ser secuencias o plano; si usa secuencias, aplanar primero para PCA que espera 2D
                if len(X_eval.shape) == 3:
                    X_eval_2d = X_eval.reshape(X_eval.shape[0], -1)
                    # PCA fue entrenado sobre X_train_bal (n_features), no sobre secuencias aplanadas ventana*features -> ajustar truncando o usando solo últimos pasos
                    # Si dimensiones no coinciden, usar solo último paso de la secuencia
                    if X_eval_2d.shape[1] != pca.n_features_in_:
                        X_eval_2d = X_eval[:, -1, :]  # último paso
                else:
                    X_eval_2d = X_eval
                X_latentes = pca.transform(X_eval_2d)
                y_pred = modelo.predict(X_latentes)
                y_prob = modelo.predict_proba(X_latentes)[:, 1] if hasattr(modelo, 'predict_proba') else y_pred
            elif nombre_algoritmo == 'cnn_lstm':
                # Fallback RF sobre secuencias aplanadas
                if len(X_eval.shape) == 3:
                    X_eval_2d = X_eval.reshape(X_eval.shape[0], -1)
                else:
                    X_eval_2d = X_eval
                y_pred = modelo.predict(X_eval_2d)
                y_prob = modelo.predict_proba(X_eval_2d)[:, 1] if hasattr(modelo, 'predict_proba') else y_pred
            else:
                y_pred = modelo.predict(X_eval)
                y_prob = modelo.predict_proba(X_eval)[:, 1] if hasattr(modelo, 'predict_proba') else y_pred
        elif nombre_algoritmo == 'lstm_ae_rf':
            # Primero extraer características latentes (TensorFlow)
            encoder = info['encoder']
            X_latentes = encoder.predict(X_eval, verbose=0)
            y_pred = modelo.predict(X_latentes)
            y_prob = modelo.predict_proba(X_latentes)[:, 1] if hasattr(modelo, 'predict_proba') else y_pred
        elif nombre_algoritmo == 'cnn_lstm':
            y_prob = modelo.predict(X_eval, verbose=0).flatten()
            y_pred = (y_prob > 0.5).astype(int)
        else:
            y_pred = modelo.predict(X_eval)
            y_prob = modelo.predict_proba(X_eval)[:, 1] if hasattr(modelo, 'predict_proba') else y_pred
        
        tiempo_inferencia = (time.time() - inicio) / max(1, len(X_eval)) * 1000  # ms por predicción
        
        # Métricas de clasificación
        metricas = {
            'algoritmo': nombre_algoritmo,
            'accuracy': round(float(accuracy_score(y_eval, y_pred)), 4),
            'precision': round(float(precision_score(y_eval, y_pred, average='weighted', zero_division=0)), 4),
            'recall': round(float(recall_score(y_eval, y_pred, average='weighted', zero_division=0)), 4),
            'f1_score': round(float(f1_score(y_eval, y_pred, average='weighted', zero_division=0)), 4),
            'auc_roc': round(float(roc_auc_score(y_eval, y_prob)) if len(np.unique(y_eval)) > 1 else 0.5, 4),
            'auc_pr': round(float(average_precision_score(y_eval, y_prob)), 4),
            'tiempo_entrenamiento_s': round(info['tiempo_entrenamiento'], 2),
            'tiempo_inferencia_ms': round(tiempo_inferencia, 4),
            'matriz_confusion': confusion_matrix(y_eval, y_pred).tolist(),
            'interpretabilidad': self.config['interpretabilidad_algoritmos'].get(nombre_algoritmo, 5),
            'mantenibilidad': self.config['mantenibilidad_algoritmos'].get(nombre_algoritmo, 5),
        }
        
        self.resultados_evaluacion[nombre_algoritmo] = metricas
        return metricas
    
    def evaluar_todos(self):
        """Evaluar todos los algoritmos entrenados"""
        self._log("\n" + "=" * 60)
        self._log("EVALUACIÓN COMPARATIVA DE ALGORITMOS")
        self._log("=" * 60)
        
        for nombre in self.modelos.keys():
            metricas = self.evaluar_algoritmo(nombre)
            if metricas:
                self._log(f"\n📊 {nombre.upper()}:")
                self._log(f"   Accuracy: {metricas['accuracy']:.4f}")
                self._log(f"   F1-Score: {metricas['f1_score']:.4f}")
                self._log(f"   AUC-ROC:  {metricas['auc_roc']:.4f}")
                self._log(f"   Inferencia: {metricas['tiempo_inferencia_ms']:.2f} ms")
        
        return self.resultados_evaluacion
    
    def comparar_algoritmos(self):
        """Generar tabla comparativa y seleccionar el mejor algoritmo"""
        if not self.resultados_evaluacion:
            self.evaluar_todos()
        
        resultados = list(self.resultados_evaluacion.values())
        if not resultados:
            return None
        
        df_comparativa = pd.DataFrame(resultados)
        
        # Calcular puntuación general ponderada
        criterios = self.config['criterios_seleccion']
        
        # Normalizar métricas para puntuación
        for nombre, metricas in self.resultados_evaluacion.items():
            # Rendimiento predictivo (F1 + AUC) / 2
            rendimiento = (metricas['f1_score'] + metricas['auc_roc']) / 2
            
            # Tiempo de inferencia (menor es mejor)
            max_tiempo = max(r['tiempo_inferencia_ms'] for r in resultados)
            min_tiempo = min(r['tiempo_inferencia_ms'] for r in resultados)
            if max_tiempo != min_tiempo:
                puntuacion_tiempo = 1 - (metricas['tiempo_inferencia_ms'] - min_tiempo) / (max_tiempo - min_tiempo)
            else:
                puntuacion_tiempo = 1.0
            
            # Interpretabilidad (ya normalizada 1-10)
            puntuacion_interp = metricas['interpretabilidad'] / 10.0
            
            # Mantenibilidad (ya normalizada 1-10)
            puntuacion_mant = metricas['mantenibilidad'] / 10.0
            
            # Puntuación general ponderada
            puntuacion_general = (
                rendimiento * criterios['rendimiento_predictivo'] +
                puntuacion_tiempo * criterios['tiempo_inferencia'] +
                puntuacion_interp * criterios['interpretabilidad'] +
                puntuacion_mant * criterios['facilidad_mantenimiento']
            )
            
            self.puntuaciones[nombre] = {
                'rendimiento': round(rendimiento, 4),
                'tiempo': round(puntuacion_tiempo, 4),
                'interpretabilidad': round(puntuacion_interp, 4),
                'mantenibilidad': round(puntuacion_mant, 4),
                'puntuacion_general': round(puntuacion_general, 4),
            }
        
        # Seleccionar mejor algoritmo
        self.mejor_algoritmo = max(self.puntuaciones, key=lambda k: self.puntuaciones[k]['puntuacion_general'])
        
        self._log(f"\n🏆 MEJOR ALGORITMO SELECCIONADO: {self.mejor_algoritmo.upper()}")
        self._log(f"   Puntuación general: {self.puntuaciones[self.mejor_algoritmo]['puntuacion_general']:.4f}")
        
        return df_comparativa, self.puntuaciones, self.mejor_algoritmo

    # ============================================================
    # FASE 6: DESPLIEGUE / INFERENCIA
    # ============================================================
    
    def predecir(self, datos_entrada, algoritmo=None):
        """
        Realizar predicción con el mejor algoritmo (o uno específico).
        
        Args:
            datos_entrada: Array o DataFrame con características del sensor
            algoritmo: Nombre del algoritmo a usar (None = mejor)
        
        Returns:
            Diccionario con probabilidad de falla, tiempo estimado, etc.
        """
        if not self.modelos:
            # Intentar cargar modelo guardado
            if not self.cargar():
                # Si no hay modelo, entrenar rápido con RF
                self._log("No hay modelos, entrenando versión rápida...")
                if self.datos_procesados is None:
                    self.cargar_datos()
                    self.preparar_datos()
                self.entrenar_random_forest()
                self.mejor_algoritmo = 'random_forest'
        
        alg = algoritmo or self.mejor_algoritmo or 'random_forest'
        
        if alg not in self.modelos:
            raise ValueError(f"Algoritmo {alg} no disponible")
        
        info = self.modelos[alg]
        modelo = info['modelo']
        
        # Preprocesar entrada
        if isinstance(datos_entrada, pd.DataFrame):
            X = datos_entrada[self.caracteristicas].values if hasattr(self, 'caracteristicas') else datos_entrada.values
        else:
            X = np.array(datos_entrada).reshape(1, -1)
        
        if hasattr(self, 'scaler_X') and self.scaler_X:
            X = self.scaler_X.transform(X)
        
        # Manejar secuencias si es necesario
        if info['usa_secuencias'] and len(X.shape) == 2:
            ventana = self.config['preparacion']['ventana_temporal']
            if X.shape[0] < ventana:
                # Rellenar con repeticiones si no hay suficientes datos
                X = np.vstack([X] * ventana)[:ventana]
            X = X[-ventana:].reshape(1, ventana, -1)
        
        # Realizar predicción
        inicio = time.time()
        
        if info.get('fallback'):
            if alg == 'lstm_ae_rf' and 'pca' in info:
                pca = info['pca']
                # X puede ser 3D (secuencia) o 2D; adaptar a lo esperado por PCA
                if len(X.shape) == 3:
                    # PCA entrenado sobre 2D plano; usar último paso
                    X_2d = X[:, -1, :] if X.shape[2] == pca.n_features_in_ else X.reshape(X.shape[0], -1)[:, :pca.n_features_in_]
                else:
                    X_2d = X
                X_latentes = pca.transform(X_2d)
                prob_falla = float(modelo.predict_proba(X_latentes)[0, 1]) if hasattr(modelo, 'predict_proba') else float(modelo.predict(X_latentes)[0])
            elif alg == 'cnn_lstm':
                if len(X.shape) == 3:
                    X_2d = X.reshape(X.shape[0], -1)
                else:
                    X_2d = X
                prob_falla = float(modelo.predict_proba(X_2d)[0, 1]) if hasattr(modelo, 'predict_proba') else float(modelo.predict(X_2d)[0])
            else:
                prob_falla = float(modelo.predict_proba(X)[0, 1]) if hasattr(modelo, 'predict_proba') else float(modelo.predict(X)[0])
        elif alg == 'lstm_ae_rf':
            X_latentes = info['encoder'].predict(X, verbose=0)
            prob_falla = float(modelo.predict_proba(X_latentes)[0, 1])
        elif alg == 'cnn_lstm':
            prob_falla = float(modelo.predict(X, verbose=0).flatten()[0])
        else:
            prob_falla = float(modelo.predict_proba(X)[0, 1]) if hasattr(modelo, 'predict_proba') else float(modelo.predict(X)[0])
        
        tiempo_inferencia = (time.time() - inicio) * 1000
        
        # Determinar severidad
        if prob_falla > 0.7:
            severidad = 'Critica'
            color = '#e74c3c'
        elif prob_falla > 0.4:
            severidad = 'Alta'
            color = '#e67e22'
        elif prob_falla > 0.2:
            severidad = 'Media'
            color = '#f39c12'
        else:
            severidad = 'Baja'
            color = '#2ecc71'
        
        # Estimar horas restantes (aproximación inversa a probabilidad)
        horas_restantes = max(0, int(1000 * (1 - prob_falla)))
        
        # Obtener factores influyentes
        factores = info.get('importancias', [])[:5] if info.get('importancias') else []
        
        # Generar recomendación
        recomendacion = self._generar_recomendacion(prob_falla, severidad, factores)
        
        return {
            'algoritmo_usado': alg,
            'probabilidad_falla': round(prob_falla * 100, 1),
            'severidad': severidad,
            'color': color,
            'horas_restantes_estimadas': horas_restantes,
            'tiempo_inferencia_ms': round(tiempo_inferencia, 2),
            'factores_influyentes': factores,
            'recomendacion': recomendacion,
            'fecha_prediccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    
    def _generar_recomendacion(self, prob_falla, severidad, factores):
        """Generar recomendación basada en la predicción"""
        recomendaciones = []
        
        if severidad == 'Critica':
            recomendaciones.append("⚠️ ACCIÓN INMEDIATA REQUERIDA")
            recomendaciones.append("Detener el equipo y realizar inspección completa.")
            recomendaciones.append("Asignar técnico de mantenimiento de forma urgente.")
        elif severidad == 'Alta':
            recomendaciones.append("⚠️ ALTA PRIORIDAD")
            recomendaciones.append("Programar mantenimiento en las próximas 24-48 horas.")
            recomendaciones.append("Monitorear parámetros críticos cada hora.")
        elif severidad == 'Media':
            recomendaciones.append("⚡ MONITOREO CERCANO")
            recomendaciones.append("Incrementar frecuencia de monitoreo.")
            recomendaciones.append("Planificar mantenimiento preventivo.")
        else:
            recomendaciones.append("✅ ESTADO ESTABLE")
            recomendaciones.append("Continuar con programa de mantenimiento normal.")
            recomendaciones.append("Realizar monitoreo rutinario.")
        
        if factores:
            recomendaciones.append("\nFactores principales a revisar:")
            for factor, imp in factores[:3]:
                nombre_factor = str(factor).replace('_', ' ').title()
                recomendaciones.append(f"  • {nombre_factor}")
        
        return '\n'.join(recomendaciones)
    
    # ============================================================
    # PERSISTENCIA DE MODELOS
    # ============================================================
    
    def guardar(self, directorio=None):
        """Guardar modelos y configuración en disco"""
        dir_path = directorio or MODELS_DIR
        os.makedirs(dir_path, exist_ok=True)
        
        # Guardar configuración
        config_path = os.path.join(dir_path, 'config_motor.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, default=str)
        
        # Guardar scaler
        scaler_path = os.path.join(dir_path, 'scaler_X.joblib')
        joblib.dump(self.scaler_X, scaler_path)
        
        # Guardar características
        if hasattr(self, 'caracteristicas'):
            with open(os.path.join(dir_path, 'caracteristicas.json'), 'w', encoding='utf-8') as f:
                json.dump(self.caracteristicas, f)
        
        # Guardar cada modelo
        for nombre, info in self.modelos.items():
            if nombre in ['cnn_lstm'] and TENSORFLOW_AVAILABLE:
                modelo_path = os.path.join(dir_path, f'{nombre}.h5')
                info['modelo'].save(modelo_path)
                # Guardar info adicional
                info_path = os.path.join(dir_path, f'{nombre}_info.joblib')
                info_simple = {k: v for k, v in info.items() if k not in ['modelo', 'encoder', 'autoencoder', 'historia']}
                joblib.dump(info_simple, info_path)
            elif nombre == 'lstm_ae_rf' and TENSORFLOW_AVAILABLE:
                # Guardar RF
                joblib.dump(info['modelo'], os.path.join(dir_path, f'{nombre}_rf.joblib'))
                # Guardar encoder
                info['encoder'].save(os.path.join(dir_path, f'{nombre}_encoder.h5'))
                # Guardar info
                info_path = os.path.join(dir_path, f'{nombre}_info.joblib')
                info_simple = {k: v for k, v in info.items() if k not in ['modelo', 'encoder', 'autoencoder']}
                joblib.dump(info_simple, info_path)
            else:
                modelo_path = os.path.join(dir_path, f'{nombre}.joblib')
                joblib.dump(info, modelo_path)
        
        # Guardar resultados
        if self.resultados_evaluacion:
            resultados_path = os.path.join(dir_path, 'resultados_evaluacion.json')
            with open(resultados_path, 'w', encoding='utf-8') as f:
                json.dump(self.resultados_evaluacion, f, indent=2, default=str)
        
        # Guardar mejor algoritmo
        if self.mejor_algoritmo:
            with open(os.path.join(dir_path, 'mejor_algoritmo.txt'), 'w', encoding='utf-8') as f:
                f.write(self.mejor_algoritmo)
        
        self._log(f"Modelos guardados en: {dir_path}")
        return True
    
    def cargar(self, directorio=None):
        """Cargar modelos y configuración desde disco"""
        dir_path = directorio or MODELS_DIR
        
        # Verificar que existan archivos
        config_path = os.path.join(dir_path, 'config_motor.json')
        if not os.path.exists(config_path):
            self._log("No se encontraron modelos guardados")
            return False
        
        try:
            # Cargar configuración
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Cargar scaler
            scaler_path = os.path.join(dir_path, 'scaler_X.joblib')
            if os.path.exists(scaler_path):
                self.scaler_X = joblib.load(scaler_path)
            
            # Cargar características
            caract_path = os.path.join(dir_path, 'caracteristicas.json')
            if os.path.exists(caract_path):
                with open(caract_path, 'r', encoding='utf-8') as f:
                    self.caracteristicas = json.load(f)
            
            # Cargar modelos
            algoritmos = ['random_forest', 'xgboost', 'svm', 'cnn_lstm', 'lstm_ae_rf']
            
            for nombre in algoritmos:
                if nombre == 'cnn_lstm' and TENSORFLOW_AVAILABLE:
                    modelo_path = os.path.join(dir_path, f'{nombre}.h5')
                    info_path = os.path.join(dir_path, f'{nombre}_info.joblib')
                    if os.path.exists(modelo_path):
                        modelo = load_model(modelo_path, compile=False)
                        info = joblib.load(info_path) if os.path.exists(info_path) else {}
                        info['modelo'] = modelo
                        info['usa_secuencias'] = True
                        info['tipo'] = 'clasificacion'
                        self.modelos[nombre] = info
                
                elif nombre == 'lstm_ae_rf' and TENSORFLOW_AVAILABLE:
                    rf_path = os.path.join(dir_path, f'{nombre}_rf.joblib')
                    encoder_path = os.path.join(dir_path, f'{nombre}_encoder.h5')
                    if os.path.exists(rf_path) and os.path.exists(encoder_path):
                        rf = joblib.load(rf_path)
                        encoder = load_model(encoder_path, compile=False)
                        info_path = os.path.join(dir_path, f'{nombre}_info.joblib')
                        info = joblib.load(info_path) if os.path.exists(info_path) else {}
                        info['modelo'] = rf
                        info['encoder'] = encoder
                        info['usa_secuencias'] = True
                        info['tipo'] = 'clasificacion'
                        self.modelos[nombre] = info
                
                else:
                    modelo_path = os.path.join(dir_path, f'{nombre}.joblib')
                    if os.path.exists(modelo_path):
                        self.modelos[nombre] = joblib.load(modelo_path)
            
            # Cargar resultados
            resultados_path = os.path.join(dir_path, 'resultados_evaluacion.json')
            if os.path.exists(resultados_path):
                with open(resultados_path, 'r', encoding='utf-8') as f:
                    self.resultados_evaluacion = json.load(f)
            
            # Cargar mejor algoritmo
            mejor_path = os.path.join(dir_path, 'mejor_algoritmo.txt')
            if os.path.exists(mejor_path):
                with open(mejor_path, 'r', encoding='utf-8') as f:
                    self.mejor_algoritmo = f.read().strip()
            
            self.cargado = True
            self.entrenado = True
            self._log(f"Modelos cargados exitosamente desde: {dir_path}")
            self._log(f"Algoritmos disponibles: {list(self.modelos.keys())}")
            return True
            
        except Exception as e:
            self._log(f"Error al cargar modelos: {str(e)}")
            return False

    # ============================================================
    # UTILIDADES
    # ============================================================
    
    def obtener_tabla_comparativa(self):
        """Obtener DataFrame con la comparativa de algoritmos"""
        if not self.resultados_evaluacion:
            self.evaluar_todos()
        
        if not self.puntuaciones:
            self.comparar_algoritmos()
        
        filas = []
        for nombre, metricas in self.resultados_evaluacion.items():
            puntuacion = self.puntuaciones.get(nombre, {})
            filas.append({
                'Algoritmo': nombre.upper(),
                'Precisión': metricas.get('accuracy', 0),
                'F1-Score': metricas.get('f1_score', 0),
                'AUC-ROC': metricas.get('auc_roc', 0),
                'Tiempo Entrenamiento (s)': metricas.get('tiempo_entrenamiento_s', 0),
                'Tiempo Inferencia (ms)': metricas.get('tiempo_inferencia_ms', 0),
                'Interpretabilidad': metricas.get('interpretabilidad', 0),
                'Puntuación General': puntuacion.get('puntuacion_general', 0),
                'Seleccionado': '⭐' if nombre == self.mejor_algoritmo else '',
            })
        
        df = pd.DataFrame(filas).sort_values('Puntuación General', ascending=False)
        return df
    
    def _log(self, mensaje):
        """Registro de actividades"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        linea = f"[{timestamp}] {mensaje}"
        try:
            print(linea)
        except (UnicodeEncodeError, Exception):
            try:
                encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
                print(linea.encode(encoding, errors='replace').decode(encoding, errors='replace'))
            except Exception:
                pass
        
        # Guardar en archivo de log
        log_file = os.path.join(LOGS_DIR, 'motor_ia.log')
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(linea + '\n')
        except Exception:
            pass
    
    def obtener_logs(self, ultimas_lineas=50):
        """Obtener últimas líneas del log"""
        log_file = os.path.join(LOGS_DIR, 'motor_ia.log')
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            return lineas[-ultimas_lineas:]
        return []


# ============================================================
# FUNCIÓN DE INICIALIZACIÓN RÁPIDA
# ============================================================

def inicializar_motor_ia():
    """
    Función de conveniencia para inicializar y preparar el motor de IA.
    Carga modelo guardado o entrena uno nuevo si no existe.
    
    Returns:
        Instancia de MotorPredictivo lista para usar
    """
    motor = MotorPredictivo()
    
    # Intentar cargar modelo existente
    if motor.cargar():
        print("✅ Modelo cargado exitosamente")
        return motor
    
    # Si no existe, entrenar desde cero
    print("🔄 No hay modelo guardado. Entrenando nuevo motor de IA...")
    motor.cargar_datos()
    motor.analisis_exploratorio()
    motor.preparar_datos()
    motor.entrenar_todos()
    motor.evaluar_todos()
    motor.comparar_algoritmos()
    motor.guardar()
    
    print(f"\n🎉 Motor de IA listo. Mejor algoritmo: {motor.mejor_algoritmo}")
    return motor


if __name__ == '__main__':
    # Prueba rápida del motor
    motor = inicializar_motor_ia()
    
    # Mostrar tabla comparativa
    print("\n📊 TABLA COMPARATIVA DE ALGORITMOS:")
    df = motor.obtener_tabla_comparativa()
    print(df.to_string(index=False))
    
    # Prueba de predicción
    print("\n🔮 PRUEBA DE PREDICCIÓN:")
    if hasattr(motor, 'X_test') and len(motor.X_test) > 0:
        resultado = motor.predecir(motor.X_test[0])
        for k, v in resultado.items():
            if k != 'factores_influyentes':
                print(f"  {k}: {v}")
