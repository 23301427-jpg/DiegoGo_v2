from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import requests
import re

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura_aqui'

# ==========================================
# CONFIGURACIÓN DE reCAPTCHA
# ==========================================
# IMPORTANTE: Reemplaza estos valores con tus claves reales de Google reCAPTCHA
# Obtén tus claves en: https://www.google.com/recaptcha/admin
#RECAPTCHA_SITE_KEY = '6Lc0ZVgsAAAAAGBfI0YE3l3gbEgvHn20jyNM5wtn'  # Clave del sitio (pública)
#RECAPTCHA_SECRET_KEY = '6Lc0ZVgsAAAAAJU89QCO2u_EGHslGx4mqFfyLA3J'  # Clave secreta (privada)

import os
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-temporal')
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6Lc0ZVgsAAAAAGBfI0YE3l3gbEgvHn20jyNM5wtn')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6Lc0ZVgsAAAAAJU89QCO2u_EGHslGx4mqFfyLA3J')

# Base de datos simulada de usuarios
usuarios_db = []

# Decorador para verificar si el usuario está autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# FUNCIÓN PARA VERIFICAR reCAPTCHA
# ==========================================
def verify_recaptcha(recaptcha_response):
    """
    Verifica el token de reCAPTCHA con los servidores de Google
    
    Args:
        recaptcha_response: Token recibido del cliente
        
    Returns:
        bool: True si la verificación fue exitosa, False en caso contrario
    """
    if not recaptcha_response:
        return False
    
    # URL de verificación de Google reCAPTCHA
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    
    # Datos a enviar
    data = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response,
        'remoteip': request.remote_addr  # IP del cliente (opcional)
    }
    
    try:
        # Hacer la petición POST a Google
        response = requests.post(verify_url, data=data)
        result = response.json()
        
        # Verificar la respuesta
        if result.get('success'):
            return True
        else:
            # Opcional: registrar los errores para debugging
            print(f"reCAPTCHA falló: {result.get('error-codes', [])}")
            return False
    except Exception as e:
        print(f"Error al verificar reCAPTCHA: {str(e)}")
        return False

# Ruta principal - Home
@app.route('/')
def index():
    breadcrumbs = [{'nombre': 'Inicio', 'url': url_for('index')}]
    return render_template('index.html', 
                         breadcrumbs=breadcrumbs,
                         recaptcha_site_key=RECAPTCHA_SITE_KEY)

# Ruta de registro
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Registro', 'url': url_for('registro')}
    ]
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        password = request.form.get('password')
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        # ==========================================
        # VERIFICACIÓN DE reCAPTCHA
        # ==========================================
        if not verify_recaptcha(recaptcha_response):
            flash('Por favor, completa la verificación de reCAPTCHA', 'error')
            return render_template('registro.html', 
                                 breadcrumbs=breadcrumbs,
                                 recaptcha_site_key=RECAPTCHA_SITE_KEY)
        
        # Validaciones del lado del servidor
        if not nombre or not correo or not password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('registro.html', 
                                 breadcrumbs=breadcrumbs,
                                 recaptcha_site_key=RECAPTCHA_SITE_KEY)
        
        # Validar formato de nombre (solo letras)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ]+$', nombre):
            flash('El nombre solo debe contener letras (sin espacios ni números)', 'error')
            return render_template('registro.html', 
                                 breadcrumbs=breadcrumbs,
                                 recaptcha_site_key=RECAPTCHA_SITE_KEY)
        
        # Validar formato de correo - acepta @ y después del último punto mínimo 2 caracteres
        if not re.match(r'^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$', correo):
            flash('El correo debe tener un formato válido (debe contener @ y terminar en dominio válido como .com, .pe, .mx - mínimo 2 letras después del punto)', 'error')
            return render_template('registro.html', 
                         breadcrumbs=breadcrumbs,
                         recaptcha_site_key=RECAPTCHA_SITE_KEY)
        
        # Validar contraseña
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            flash('La contraseña debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas y números', 'error')
            return render_template('registro.html', 
                                 breadcrumbs=breadcrumbs,
                                 recaptcha_site_key=RECAPTCHA_SITE_KEY)
        
        # Verificar si el correo ya existe
        if any(u['correo'] == correo for u in usuarios_db):
            flash('Este correo ya está registrado', 'error')
            return render_template('registro.html', 
                                 breadcrumbs=breadcrumbs,
                                 recaptcha_site_key=RECAPTCHA_SITE_KEY)
        
        # Agregar usuario a la base de datos simulada
        usuarios_db.append({
            'nombre': nombre,
            'correo': correo,
            'password': password
        })
        
        flash('¡Registro exitoso! Ahora puedes iniciar sesión', 'success')
        return redirect(url_for('login'))
    
    return render_template('registro.html', 
                         breadcrumbs=breadcrumbs,
                         recaptcha_site_key=RECAPTCHA_SITE_KEY)

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Iniciar Sesión', 'url': url_for('login')}
    ]
    
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        # ==========================================
        # VERIFICACIÓN DE reCAPTCHA
        # ==========================================
        if not verify_recaptcha(recaptcha_response):
            flash('Por favor, completa la verificación de reCAPTCHA', 'error')
            return render_template('login.html', 
                                 breadcrumbs=breadcrumbs,
                                 recaptcha_site_key=RECAPTCHA_SITE_KEY)
        
        # Buscar usuario
        usuario = next((u for u in usuarios_db if u['correo'] == correo and u['password'] == password), None)
        
        if usuario:
            session['usuario'] = usuario['nombre']
            flash(f'¡Bienvenido, {usuario["nombre"]}!', 'success')
            return redirect(url_for('usuarios'))
        else:
            flash('Correo o contraseña incorrectos', 'error')
    
    return render_template('login.html', 
                         breadcrumbs=breadcrumbs,
                         recaptcha_site_key=RECAPTCHA_SITE_KEY)

# Dashboard (requiere autenticación)
@app.route('/dashboard')
@login_required
def dashboard():
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')}
    ]
    return render_template('dashboard.html', breadcrumbs=breadcrumbs, usuarios=usuarios_db)

# Galería
@app.route('/galeria')
@login_required
def galeria():
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')},
        {'nombre': 'Galería', 'url': url_for('galeria')}
    ]
    return render_template('galeria.html', breadcrumbs=breadcrumbs)

# Gestión de usuarios
@app.route('/usuarios')
@login_required
def usuarios():
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')},
        {'nombre': 'Gestión de Usuarios', 'url': url_for('usuarios')}
    ]
    return render_template('usuarios.html', breadcrumbs=breadcrumbs, usuarios=usuarios_db)

# CRUD - Crear usuario
@app.route('/usuarios/crear', methods=['POST'])
@login_required
def crear_usuario():
    nombre   = request.form.get('nombre', '').strip()
    correo   = request.form.get('correo', '').strip()
    password = request.form.get('password', '').strip()

    if not nombre or not correo or not password:
        flash('Todos los campos son obligatorios', 'error')
        return redirect(url_for('usuarios'))

    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ]+$', nombre):
        flash('El nombre solo debe contener letras', 'error')
        return redirect(url_for('usuarios'))

    if not re.match(r'^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$', correo):
        flash('Correo inválido', 'error')
        return redirect(url_for('usuarios'))

    if any(u['correo'] == correo for u in usuarios_db):
        flash('Ese correo ya está registrado', 'error')
        return redirect(url_for('usuarios'))

    usuarios_db.append({'nombre': nombre, 'correo': correo, 'password': password})
    flash(f'Usuario {nombre} creado correctamente', 'success')
    return redirect(url_for('usuarios'))

# CRUD - Editar usuario
@app.route('/usuarios/editar', methods=['POST'])
@login_required
def editar_usuario():
    try:
        idx      = int(request.form.get('idx'))
        nombre   = request.form.get('nombre', '').strip()
        correo   = request.form.get('correo', '').strip()
        password = request.form.get('password', '').strip()
    except (TypeError, ValueError):
        flash('Solicitud inválida', 'error')
        return redirect(url_for('usuarios'))

    if idx < 0 or idx >= len(usuarios_db):
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('usuarios'))

    if not nombre or not correo:
        flash('Nombre y correo son obligatorios', 'error')
        return redirect(url_for('usuarios'))

    # Verificar correo duplicado (ignorar el propio)
    if any(u['correo'] == correo for i, u in enumerate(usuarios_db) if i != idx):
        flash('Ese correo ya está en uso por otro usuario', 'error')
        return redirect(url_for('usuarios'))

    usuarios_db[idx]['nombre'] = nombre
    usuarios_db[idx]['correo'] = correo
    if password:
        usuarios_db[idx]['password'] = password

    # Actualizar sesión si el usuario editó su propio perfil
    if session.get('usuario') == usuarios_db[idx]['nombre'] or True:
        pass  # no forzamos logout, solo actualizamos datos

    flash(f'Usuario actualizado correctamente', 'success')
    return redirect(url_for('usuarios'))

# CRUD - Eliminar usuario
@app.route('/usuarios/eliminar/<int:idx>', methods=['POST'])
@login_required
def eliminar_usuario(idx):
    if idx < 0 or idx >= len(usuarios_db):
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('usuarios'))

    nombre = usuarios_db[idx]['nombre']
    usuarios_db.pop(idx)
    flash(f'Usuario {nombre} eliminado', 'success')
    return redirect(url_for('usuarios'))

# Perfil de usuario
@app.route('/perfil')
@login_required
def perfil():
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')},
        {'nombre': 'Mi Perfil', 'url': url_for('perfil')}
    ]
    
    # Buscar datos del usuario actual
    usuario = next((u for u in usuarios_db if u['nombre'] == session['usuario']), None)
    
    return render_template('perfil.html', breadcrumbs=breadcrumbs, usuario=usuario)

# Configuraciones
@app.route('/configuracion')
@login_required
def configuracion():
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')},
        {'nombre': 'Configuración', 'url': url_for('configuracion')}
    ]
    return render_template('configuracion.html', breadcrumbs=breadcrumbs)

# Ruta para simular un error
@app.route('/simular-error')
def simular_error():
    # Esto causará una división por cero
    resultado = 1 / 0
    return "Esto nunca se ejecutará"

# Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('index'))

# Manejador de errores 404
@app.errorhandler(404)
def error_404(error):
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Error 404', 'url': '#'}
    ]
    return render_template('error.html', 
                         breadcrumbs=breadcrumbs,
                         error_code=404,
                         error_title='Página no encontrada',
                         error_message='La página que buscas no existe o fue movida.'), 404

# Manejador de errores 500
@app.errorhandler(500)
def error_500(error):
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Error 500', 'url': '#'}
    ]
    return render_template('error.html',
                         breadcrumbs=breadcrumbs,
                         error_code=500,
                         error_title='Error del servidor',
                         error_message='Ocurrió un error inesperado en el servidor. Por favor, inténtalo más tarde.'), 500

# Manejador general de excepciones
@app.errorhandler(Exception)
def error_general(error):
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Error', 'url': '#'}
    ]
    return render_template('error.html',
                         breadcrumbs=breadcrumbs,
                         error_code='ERROR',
                         error_title='Ocurrió un problema',
                         error_message=f'Se produjo una excepción: {str(error)}'), 500

if __name__ == '__main__':
    #app.run(debug=True, host='0.0.0.0', port=5000) 
    # REMPLAZA ESTO:
    # app.run(debug=True, host='0.0.0.0', port=5000)
    
    # CON ESTO:
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)