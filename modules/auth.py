"""
Módulo de Autenticación y Gestión de Usuarios
Maneja el login, registro, gestión de roles y bitácora de accesos.
"""
import jwt
import datetime
import os
from utils.database import get_connection, verify_password, hash_password

SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = "minera_gemelo_digital_2024_secret_key_jwt"
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 8

def generate_token(user_id, username, rol):
    """Generar token JWT"""
    payload = {
        'user_id': user_id,
        'username': username,
        'rol': rol,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token):
    """Verificar token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login(username, password):
    """Iniciar sesión"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM usuarios WHERE username = ? AND activo = 1", (username,))
    user = cursor.fetchone()
    
    if user and verify_password(password, user['password_hash']):
        # Actualizar último acceso
        cursor.execute("UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
        # Registrar en bitácora
        cursor.execute("INSERT INTO bitacora_accesos (usuario_id, accion, detalle) VALUES (?, ?, ?)",
                      (user['id'], 'LOGIN', f'Inicio de sesión exitoso para {username}'))
        conn.commit()
        
        token = generate_token(user['id'], user['username'], user['rol'])
        conn.close()
        return {
            'token': token,
            'user_id': user['id'],
            'username': user['username'],
            'nombre': user['nombre'],
            'apellido': user['apellido'],
            'email': user['email'],
            'rol': user['rol'],
            'area': user['area']
        }
    else:
        # Registrar intento fallido
        if user:
            cursor.execute("INSERT INTO bitacora_accesos (usuario_id, accion, detalle) VALUES (?, ?, ?)",
                          (user['id'], 'LOGIN_FAILED', f'Intento fallido de inicio de sesión'))
        conn.commit()
        conn.close()
        return None

def register_user(username, password, nombre, apellido, email, rol, area=None):
    """Registrar nuevo usuario"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        insert_query = '''
        INSERT INTO usuarios (username, password_hash, nombre, apellido, email, rol, area)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(insert_query, (username, hash_password(password), nombre, apellido, email, rol, area))
        conn.commit()
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        inserted_user = cursor.fetchone()
        user_id = inserted_user['id'] if inserted_user else None
        cursor.execute("INSERT INTO bitacora_accesos (usuario_id, accion, detalle) VALUES (?, ?, ?)",
                      (user_id, 'REGISTER', f'Usuario {username} registrado en el sistema'))
        conn.commit()
        conn.close()
        return True, "Usuario registrado exitosamente"
    except Exception as e:
        conn.close()
        return False, f"Error al registrar usuario: {str(e)}"

def get_all_users():
    """Obtener todos los usuarios"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, nombre, apellido, email, rol, area, fecha_creacion, ultimo_acceso, activo FROM usuarios ORDER BY nombre")
    users = cursor.fetchall()
    conn.close()
    return [dict(user) for user in users]

def update_user(user_id, data):
    """Actualizar datos de usuario"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for key, value in data.items():
        if key == 'password':
            fields.append("password_hash = ?")
            values.append(hash_password(value))
        elif key in ['nombre', 'apellido', 'email', 'rol', 'area', 'activo']:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if fields:
        values.append(user_id)
        query = f"UPDATE usuarios SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return True

def get_bitacora_accesos(limit=100):
    """Obtener bitácora de accesos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT b.id, b.fecha_hora, b.accion, b.detalle, u.username, u.nombre, u.apellido
    FROM bitacora_accesos b
    LEFT JOIN usuarios u ON b.usuario_id = u.id
    ORDER BY b.fecha_hora DESC
    LIMIT ?
    ''', (limit,))
    records = cursor.fetchall()
    conn.close()
    return [dict(r) for r in records]

def get_user_by_id(user_id):
    """Obtener usuario por ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def has_permission(user_rol, required_roles):
    """Verificar si el usuario tiene permiso"""
    return user_rol in required_roles

# Definición de permisos por módulo
PERMISOS = {
    'usuarios': ['Administrador'],
    'dashboard': ['Administrador', 'Ingeniero', 'Supervisor', 'Tecnico'],
    'gemelo_digital': ['Administrador', 'Ingeniero', 'Supervisor', 'Tecnico'],
    'mantenimiento': ['Administrador', 'Ingeniero', 'Supervisor', 'Tecnico'],
    'reportes': ['Administrador', 'Ingeniero', 'Supervisor'],
    'predictivo': ['Administrador', 'Ingeniero'],
    'repuestos': ['Administrador', 'Ingeniero', 'Supervisor'],
}
