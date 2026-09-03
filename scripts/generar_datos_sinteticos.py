"""
Generador de datos sintéticos realistas para el Gemelo Digital Minero.

Amplía la tabla `datos_equipos` con miles de registros generados a partir de
las distribuciones y rangos observados en los datos reales, produciendo tanto
operación normal como estados previos a falla (cruces de umbrales críticos).

Esto otorga volumen suficiente para que los modelos híbridos con TensorFlow
(CNN-LSTM y LSTM-Autoencoder) no sobreajusten con solo ~300 registros.

Uso:
    python scripts/generar_datos_sinteticos.py [registros_por_equipo]
"""

import os
import sys
import sqlite3
import random
import argparse
from datetime import datetime, timedelta

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'gemelo_digital.db')

# Rangos observados en datos_equipos reales (min, max)
RANGOS = {
    'temp_motor': (75, 105),
    'presion_aceite': (35, 65),
    'rpm_motor': (1200, 2100),
    'horas_motor': (5000, 16000),
    'presion_hidraulica': (180, 250),
    'temp_aceite_hidraulico': (50, 80),
    'nivel_aceite_hidraulico': (85, 100),
    'desgaste_pastillas': (10, 85),
    'presion_neumaticos': (550, 750),
    'desgaste_neumaticos': (5, 60),
    'nivel_combustible': (10, 100),
    'consumo_combustible': (120, 280),
    'carga_actual': (0, 360),
    'velocidad': (0, 45),
}

# Umbrales críticos usados por el motor para la variable objetivo
UMBRALES = {
    'temp_motor': 100,      # falla si >
    'presion_aceite': 30,   # falla si <
    'presion_hidraulica': 170,  # falla si <
    'desgaste_neumaticos': 70,  # falla si >
    'desgaste_pastillas': 75,   # falla si >
}


def valor_normal(clave):
    """Generar un valor dentro del rango normal observado."""
    lo, hi = RANGOS[clave]
    return round(random.uniform(lo, hi), 1)


def generar_fila_normal(eq_id, fecha):
    """Registro de operación normal (sin falla)."""
    return (
        eq_id,
        fecha.strftime('%Y-%m-%d %H:%M:%S'),
        round(random.uniform(75, 98), 1),  # temp_motor (normal < 100)
        round(random.uniform(40, 65), 1),  # presion_aceite (normal > 30)
        random.randint(1200, 2100),        # rpm_motor
        round(random.uniform(5000, 16000), 1),  # horas_motor
        round(random.uniform(185, 250), 1),  # presion_hidraulica (normal > 170)
        round(random.uniform(50, 78), 1),  # temp_aceite_hidraulico
        round(random.uniform(85, 100), 1),  # nivel_aceite_hidraulico
        random.choice(['Normal', 'Normal', 'Normal', 'Revisar']),  # estado_frenos
        round(random.uniform(10, 60), 1),  # desgaste_pastillas (normal < 75)
        round(random.uniform(550, 720), 1),  # presion_neumaticos
        round(random.uniform(5, 45), 1),  # desgaste_neumaticos (normal < 70)
        round(random.uniform(10, 100), 1),  # nivel_combustible
        round(random.uniform(120, 280), 1),  # consumo_combustible
        round(random.uniform(0, 360), 1),  # carga_actual
        random.randint(0, 15),  # ciclos_completados
        round(random.uniform(0, 45), 1),  # velocidad
        '',  # alertas
    )


def generar_fila_falla(eq_id, fecha):
    """
    Registro previo a falla: cruza al menos un umbral crítico.
    Se rompe un umbral aleatorio para dar diversidad de modos de falla.
    """
    modo = random.choice(list(UMBRALES.keys()))

    def base_normal():
        return generar_fila_normal(eq_id, fecha)

    fila = list(base_normal())
    # Índices de la tupla (0=eq_id, 1=fecha, ...):
    # 2: temp_motor, 3: presion_aceite, 4: rpm_motor, 5: horas_motor,
    # 6: presion_hidraulica, 7: temp_aceite_hidraulico, 8: nivel_aceite_hidraulico,
    # 9: estado_frenos, 10: desgaste_pastillas, 11: presion_neumaticos,
    # 12: desgaste_neumaticos, 13: nivel_combustible, 14: consumo_combustible,
    # 15: carga_actual, 16: ciclos_completados, 17: velocidad, 18: alertas
    idx = {
        'temp_motor': 2,
        'presion_aceite': 3,
        'presion_hidraulica': 6,
        'desgaste_neumaticos': 12,
        'desgaste_pastillas': 10,
    }

    if modo == 'temp_motor':
        fila[idx['temp_motor']] = round(random.uniform(100, 150), 1)
    elif modo == 'presion_aceite':
        fila[idx['presion_aceite']] = round(random.uniform(20, 29), 1)
    elif modo == 'presion_hidraulica':
        fila[idx['presion_hidraulica']] = round(random.uniform(120, 169), 1)
    elif modo == 'desgaste_neumaticos':
        fila[idx['desgaste_neumaticos']] = round(random.uniform(71, 95), 1)
    elif modo == 'desgaste_pastillas':
        fila[idx['desgaste_pastillas']] = round(random.uniform(76, 95), 1)

    fila[9] = 'Critico'  # estado_frenos

    # Alertas descriptiva
    alertas_txt = {
        'temp_motor': 'SOBRECALENTAMIENTO',
        'presion_aceite': 'BAJA PRESION ACEITE',
        'presion_hidraulica': 'BAJA PRESION HIDRAULICA',
        'desgaste_neumaticos': 'DESGASTE NEUMATICOS CRITICO',
        'desgaste_pastillas': 'DESGASTE PASTILLAS CRITICO',
    }
    fila[18] = alertas_txt[modo]

    return tuple(fila)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'registros_por_equipo', type=int, nargs='?', default=5000,
        help='Número de registros a generar por equipo (default 5000)'
    )
    parser.add_argument(
        '--reemplazar', action='store_true',
        help='Eliminar datos_equipos existentes antes de generar (default: anexar)'
    )
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    equipo_ids = [r[0] for r in cur.execute("SELECT id FROM equipos").fetchall()]
    if not equipo_ids:
        print("[ERROR] No hay equipos en la tabla 'equipos'. Ejecuta primero la inicialización de la BD.")
        sys.exit(1)

    if args.reemplazar:
        cur.execute("DELETE FROM datos_equipos")
        conn.commit()
        print("[INFO] Tabla datos_equipos vaciada.")

    antes = cur.execute("SELECT COUNT(*) FROM datos_equipos").fetchone()[0]

    # De cada equipo partimos de una fecha base distinta y generamos serie escalonada
    base_inicio = datetime(2024, 1, 1)

    insertar = []
    total = 0
    for eq_id in equipo_ids:
        inicio = base_inicio + timedelta(days=eq_id * 7)
        for i in range(args.registros_por_equipo):
            fecha = inicio + timedelta(minutes=30 * i, seconds=random.randint(0, 59))
            # ~88% operación normal, ~12% previo a falla
            if random.random() < 0.12:
                fila = generar_fila_falla(eq_id, fecha)
            else:
                fila = generar_fila_normal(eq_id, fecha)
            insertar.append(fila)
            total += 1
            if len(insertar) >= 5000:
                cur.executemany('''
                    INSERT INTO datos_equipos (equipo_id, fecha_hora, temp_motor, presion_aceite,
                        rpm_motor, horas_motor, presion_hidraulica, temp_aceite_hidraulico,
                        nivel_aceite_hidraulico, estado_frenos, desgaste_pastillas,
                        presion_neumaticos, desgaste_neumaticos, nivel_combustible,
                        consumo_combustible, carga_actual, ciclos_completados, velocidad, alertas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', insertar)
                insertar = []
    if insertar:
        cur.executemany('''
            INSERT INTO datos_equipos (equipo_id, fecha_hora, temp_motor, presion_aceite,
                rpm_motor, horas_motor, presion_hidraulica, temp_aceite_hidraulico,
                nivel_aceite_hidraulico, estado_frenos, desgaste_pastillas,
                presion_neumaticos, desgaste_neumaticos, nivel_combustible,
                consumo_combustible, carga_actual, ciclos_completados, velocidad, alertas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', insertar)

    conn.commit()
    despues = cur.execute("SELECT COUNT(*) FROM datos_equipos").fetchone()[0]
    conn.close()

    print(f"[OK] Registros insertados: {total}")
    print(f"[OK] datos_equipos total: {antes} -> {despues}")


if __name__ == '__main__':
    main()
