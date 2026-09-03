import os

import numpy as np
import pytest


@pytest.fixture
def base_temporal(tmp_path, monkeypatch):
    import utils.database as database

    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test.db'))
    database.init_database()
    database.insert_default_data()
    return database


def test_mantenimiento_valida_stock_ordenes_y_historial(base_temporal):
    from modules import mantenimiento

    assert mantenimiento.actualizar_stock_repuesto(1, -1) is False
    assert mantenimiento.actualizar_stock_repuesto(1, 1, 'invalida') is False
    assert mantenimiento.actualizar_stock_repuesto(1, 999999) is False
    assert mantenimiento.actualizar_orden_trabajo(999999, {'estado': 'Completada'}) is False
    assert mantenimiento.registrar_historial(999999, 1, 'Preventivo', 'Prueba') is False

    ok, numero, orden_id = mantenimiento.crear_orden_trabajo(
        1, 'Preventivo', 'Media', 'Prueba', 'Revision'
    )
    assert ok is True
    assert numero.startswith('OT-')
    assert mantenimiento.actualizar_orden_trabajo(orden_id, {'estado': 'Completada'}) is True
    assert mantenimiento.registrar_historial(orden_id, 1, 'Preventivo', 'Revision') is True


def test_ordenes_automaticas_respetan_500_horas(base_temporal):
    from modules import mantenimiento

    conn = base_temporal.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE equipos SET horas_operacion = 499')
    cursor.execute('UPDATE datos_equipos SET horas_motor = 499')
    conn.commit()
    conn.close()
    assert mantenimiento.generar_ordenes_automaticas() == []

    conn = base_temporal.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE equipos SET horas_operacion = 500 WHERE id = 1')
    cursor.execute('UPDATE datos_equipos SET horas_motor = 500 WHERE equipo_id = 1')
    conn.commit()
    conn.close()
    assert len(mantenimiento.generar_ordenes_automaticas()) == 1
    assert mantenimiento.generar_ordenes_automaticas() == []


def test_manejo_de_equipos_inexistentes(base_temporal):
    from modules import gemelo_digital, predictivo

    assert gemelo_digital.get_equipo_detalle(999999) is None
    assert gemelo_digital.get_ultimos_datos(999999) is None
    assert gemelo_digital.simular_falla(999999, 'falla_frenos') is None
    assert gemelo_digital.generar_datos_en_tiempo_real(999999) is None
    assert predictivo.predecir_falla_equipo(999999) is None


def test_kpis_oee_y_mtbf(base_temporal):
    from modules import dashboard

    conn = base_temporal.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ordenes_trabajo
        (numero_orden, equipo_id, tipo, prioridad, titulo, estado,
         fecha_inicio, fecha_fin)
        VALUES (?, ?, 'Correctivo', 'Alta', ?, 'Completada', ?, ?)
    """, ('OT-TEST', 1, 'Falla', '2026-01-01 08:00:00', '2026-01-01 10:00:00'))
    conn.commit()
    conn.close()

    kpis = dashboard.get_kpis()
    assert kpis['oee'] == pytest.approx(kpis['disponibilidad'] * 0.85 * 0.90, abs=0.1)
    assert kpis['mtbf'] > 0
    assert kpis['mttr'] == pytest.approx(2.0, abs=0.1)


def test_autenticacion_dashboard_y_reportes(base_temporal):
    from modules import auth, dashboard, reportes

    usuario = auth.login('admin', 'admin123')
    assert usuario is not None
    assert auth.verify_token(usuario['token'])['rol'] == 'Administrador'
    assert auth.has_permission('Tecnico', auth.PERMISOS['mantenimiento'])
    assert not auth.has_permission('Tecnico', auth.PERMISOS['usuarios'])
    assert dashboard.get_kpis()['total_equipos'] == 6
    assert len(reportes.generar_reporte_pdf()) > 100
    assert len(reportes.generar_reporte_word()) > 100
    assert len(reportes.generar_reporte_excel()) > 100


def test_prediccion_y_persistencia_de_modelo(base_temporal, tmp_path):
    from modules import predictivo
    from modules.motor_ia import MotorPredictivo
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler

    prediccion = predictivo.predecir_falla_equipo(1)
    assert prediccion is not None
    assert 0 <= prediccion['probabilidad_falla'] <= 100

    motor = MotorPredictivo()
    caracteristicas = ['sensor_a', 'sensor_b']
    datos = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
    escalador = StandardScaler().fit(datos)
    modelo = RandomForestClassifier(n_estimators=5, random_state=42).fit(
        escalador.transform(datos), [0, 1, 1, 1]
    )
    motor.scaler_X = escalador
    motor.caracteristicas = caracteristicas
    motor.modelos['random_forest'] = {
        'modelo': modelo,
        'tipo': 'clasificacion',
        'tiempo_entrenamiento': 0,
        'usa_secuencias': False,
    }
    motor.mejor_algoritmo = 'random_forest'
    directorio = tmp_path / 'modelos'
    assert motor.guardar(str(directorio)) is True

    cargado = MotorPredictivo()
    assert cargado.cargar(str(directorio)) is True
    assert 'random_forest' in cargado.modelos
    resultado = cargado.predecir([0, 1])
    assert resultado['algoritmo_usado'] == 'random_forest'
    assert np.isfinite(resultado['probabilidad_falla'])