from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import requests
import re
import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-temporal')

# ==========================================
# BASE DE DATOS — Clever Cloud MySQL
# ==========================================
DB_HOST     = os.environ.get('MYSQL_ADDON_HOST',     'bwatsam5jk0v2lwhgolv-mysql.services.clever-cloud.com')
DB_NAME     = os.environ.get('MYSQL_ADDON_DB',       'bwatsam5jk0v2lwhgolv')
DB_USER     = os.environ.get('MYSQL_ADDON_USER',     'u5ixv9uhprvcj3zr')
DB_PASSWORD = os.environ.get('MYSQL_ADDON_PASSWORD', 'iInHvdLkMqhh7wNZt7Y7')
DB_PORT     = os.environ.get('MYSQL_ADDON_PORT',     '3306')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB máximo por subida

db = SQLAlchemy(app)

# ==========================================
# MODELOS
# ==========================================
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(100), nullable=False)
    correo   = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Imagen(db.Model):
    __tablename__ = 'imagenes'
    id       = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)

with app.app_context():
    db.create_all()

# ==========================================
# CONFIGURACIÓN SUBIDA DE IMÁGENES
# ==========================================
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# RECAPTCHA
# ==========================================
RECAPTCHA_SITE_KEY   = os.environ.get('RECAPTCHA_SITE_KEY',   '6Lc0ZVgsAAAAAGBfI0YE3l3gbEgvHn20jyNM5wtn')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6Lc0ZVgsAAAAAJU89QCO2u_EGHslGx4mqFfyLA3J')

# ==========================================
# DECORADOR LOGIN
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# VERIFICAR RECAPTCHA
# ==========================================
def verify_recaptcha(recaptcha_response):
    if not recaptcha_response:
        return False
    try:
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
            'secret': RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response,
            'remoteip': request.remote_addr
        })
        result = response.json()
        return result.get('success', False)
    except Exception as e:
        print(f"Error reCAPTCHA: {e}")
        return False

# ==========================================
# RUTAS PRINCIPALES
# ==========================================

@app.route('/')
def index():
    return render_template('index.html',
        breadcrumbs=[{'nombre': 'Inicio', 'url': url_for('index')}],
        recaptcha_site_key=RECAPTCHA_SITE_KEY)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Registro', 'url': url_for('registro')}
    ]
    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        correo   = request.form.get('correo', '').strip()
        password = request.form.get('password', '').strip()
        recaptcha_response = request.form.get('g-recaptcha-response')

        if not verify_recaptcha(recaptcha_response):
            flash('Por favor, completa la verificación de reCAPTCHA', 'error')
            return render_template('registro.html', breadcrumbs=breadcrumbs, recaptcha_site_key=RECAPTCHA_SITE_KEY)
        if not nombre or not correo or not password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('registro.html', breadcrumbs=breadcrumbs, recaptcha_site_key=RECAPTCHA_SITE_KEY)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ]+$', nombre):
            flash('El nombre solo debe contener letras', 'error')
            return render_template('registro.html', breadcrumbs=breadcrumbs, recaptcha_site_key=RECAPTCHA_SITE_KEY)
        if not re.match(r'^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$', correo):
            flash('El correo debe tener un formato válido', 'error')
            return render_template('registro.html', breadcrumbs=breadcrumbs, recaptcha_site_key=RECAPTCHA_SITE_KEY)
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            flash('La contraseña debe tener al menos 8 caracteres, mayúsculas, minúsculas y números', 'error')
            return render_template('registro.html', breadcrumbs=breadcrumbs, recaptcha_site_key=RECAPTCHA_SITE_KEY)
        if Usuario.query.filter_by(correo=correo).first():
            flash('Este correo ya está registrado', 'error')
            return render_template('registro.html', breadcrumbs=breadcrumbs, recaptcha_site_key=RECAPTCHA_SITE_KEY)

        db.session.add(Usuario(nombre=nombre, correo=correo, password=password))
        db.session.commit()
        flash('¡Registro exitoso! Ahora puedes iniciar sesión', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html', breadcrumbs=breadcrumbs, recaptcha_site_key=RECAPTCHA_SITE_KEY)

@app.route('/login', methods=['GET', 'POST'])
def login():
    breadcrumbs = [
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Iniciar Sesión', 'url': url_for('login')}
    ]
    if request.method == 'POST':
        correo   = request.form.get('correo', '').strip()
        password = request.form.get('password', '').strip()
        recaptcha_response = request.form.get('g-recaptcha-response')

        if not verify_recaptcha(recaptcha_response):
            flash('Por favor, completa la verificación de reCAPTCHA', 'error')
            return render_template('login.html', breadcrumbs=breadcrumbs, recaptcha_site_key=RECAPTCHA_SITE_KEY)

        u = Usuario.query.filter_by(correo=correo, password=password).first()
        if u:
            session['usuario']    = u.nombre
            session['usuario_id'] = u.id
            flash(f'¡Bienvenido, {u.nombre}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Correo o contraseña incorrectos', 'error')

    return render_template('login.html', breadcrumbs=breadcrumbs, recaptcha_site_key=RECAPTCHA_SITE_KEY)

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', breadcrumbs=[
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')}
    ])

# ==========================================
# GALERÍA — imágenes guardadas en DB + disco
# ==========================================

@app.route('/galeria')
@login_required
def galeria():
    imagenes = Imagen.query.order_by(Imagen.id.asc()).all()
    return render_template('galeria.html', breadcrumbs=[
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')},
        {'nombre': 'Galería', 'url': url_for('galeria')}
    ], imagenes=imagenes)

@app.route('/galeria/subir', methods=['POST'])
@login_required
def subir_imagen():
    archivos = request.files.getlist('fotos')
    subidas = 0
    for archivo in archivos:
        if archivo and allowed_file(archivo.filename):
            filename = secure_filename(archivo.filename)
            base, ext = os.path.splitext(filename)
            contador = 1
            while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                filename = f"{base}_{contador}{ext}"
                contador += 1
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            archivo.save(filepath)
            db.session.add(Imagen(filename=filename, filepath=f"uploads/{filename}"))
            subidas += 1
    if subidas:
        db.session.commit()
        flash(f'{subidas} foto(s) subida(s) correctamente', 'success')
    else:
        flash('No se pudo subir ninguna imagen', 'error')
    return redirect(url_for('galeria'))

@app.route('/galeria/eliminar/<int:img_id>', methods=['POST'])
@login_required
def eliminar_imagen(img_id):
    img = Imagen.query.get(img_id)
    if not img:
        flash('Imagen no encontrada', 'error')
        return redirect(url_for('galeria'))
    filepath = os.path.join(UPLOAD_FOLDER, img.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(img)
    db.session.commit()
    flash('Imagen eliminada', 'success')
    return redirect(url_for('galeria'))

# ==========================================
# GESTIÓN DE USUARIOS (CRUD)
# ==========================================

@app.route('/usuarios')
@login_required
def usuarios():
    return render_template('usuarios.html', breadcrumbs=[
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')},
        {'nombre': 'Gestión de Usuarios', 'url': url_for('usuarios')}
    ])

@app.route('/api/usuarios')
@login_required
def api_usuarios():
    from flask import jsonify
    busqueda   = request.args.get('q', '').strip()
    pagina     = request.args.get('page', 1, type=int)
    por_pagina = 4

    query = Usuario.query.order_by(Usuario.id.asc())
    if busqueda:
        query = query.filter(Usuario.nombre.ilike(f'%{busqueda}%'))

    paginado = query.paginate(page=pagina, per_page=por_pagina, error_out=False)

    return jsonify({
        'usuarios': [{'id': u.id, 'nombre': u.nombre, 'correo': u.correo} for u in paginado.items],
        'total':    paginado.total,
        'pages':    paginado.pages,
        'page':     paginado.page,
        'has_prev': paginado.has_prev,
        'has_next': paginado.has_next,
        'prev_num': paginado.prev_num,
        'next_num': paginado.next_num,
    })

@app.route('/usuarios/crear', methods=['POST'])
@login_required
def crear_usuario():
    from flask import jsonify
    nombre   = request.form.get('nombre', '').strip()
    correo   = request.form.get('correo', '').strip()
    password = request.form.get('password', '').strip()

    if not nombre or not correo or not password:
        return jsonify({'ok': False, 'msg': 'Todos los campos son obligatorios'})
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ]+$', nombre):
        return jsonify({'ok': False, 'msg': 'El nombre solo debe contener letras'})
    if not re.match(r'^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$', correo):
        return jsonify({'ok': False, 'msg': 'Correo inválido'})
    if Usuario.query.filter_by(correo=correo).first():
        return jsonify({'ok': False, 'msg': 'Ese correo ya está registrado'})

    db.session.add(Usuario(nombre=nombre, correo=correo, password=password))
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'Usuario {nombre} creado correctamente'})

@app.route('/usuarios/editar', methods=['POST'])
@login_required
def editar_usuario():
    from flask import jsonify
    try:
        uid      = int(request.form.get('idx'))
        nombre   = request.form.get('nombre', '').strip()
        correo   = request.form.get('correo', '').strip()
        password = request.form.get('password', '').strip()
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'msg': 'Solicitud inválida'})

    u = Usuario.query.get(uid)
    if not u:
        return jsonify({'ok': False, 'msg': 'Usuario no encontrado'})
    if not nombre or not correo:
        return jsonify({'ok': False, 'msg': 'Nombre y correo son obligatorios'})

    duplicado = Usuario.query.filter_by(correo=correo).first()
    if duplicado and duplicado.id != uid:
        return jsonify({'ok': False, 'msg': 'Ese correo ya está en uso'})

    u.nombre = nombre
    u.correo = correo
    if password:
        u.password = password
    db.session.commit()
    return jsonify({'ok': True, 'msg': 'Usuario actualizado correctamente'})

@app.route('/usuarios/eliminar/<int:uid>', methods=['POST'])
@login_required
def eliminar_usuario(uid):
    from flask import jsonify
    u = Usuario.query.get(uid)
    if not u:
        return jsonify({'ok': False, 'msg': 'Usuario no encontrado'})
    nombre = u.nombre
    db.session.delete(u)
    db.session.commit()
    return jsonify({'ok': True, 'msg': f'Usuario {nombre} eliminado'})

# ==========================================
# PERFIL Y CONFIGURACIÓN
# ==========================================

@app.route('/perfil')
@login_required
def perfil():
    u = Usuario.query.get(session.get('usuario_id'))
    return render_template('perfil.html', breadcrumbs=[
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')},
        {'nombre': 'Mi Perfil', 'url': url_for('perfil')}
    ], usuario=u)

@app.route('/configuracion')
@login_required
def configuracion():
    return render_template('configuracion.html', breadcrumbs=[
        {'nombre': 'Inicio', 'url': url_for('index')},
        {'nombre': 'Panel de Control', 'url': url_for('dashboard')},
        {'nombre': 'Configuración', 'url': url_for('configuracion')}
    ])

@app.route('/simular-error')
def simular_error():
    resultado = 1 / 0
    return "Esto nunca se ejecutará"

# ==========================================
# MANEJO DE ERRORES
# ==========================================

@app.errorhandler(404)
def error_404(error):
    return render_template('error.html',
        breadcrumbs=[{'nombre': 'Inicio', 'url': url_for('index')}, {'nombre': 'Error 404', 'url': '#'}],
        error_code=404, error_title='Página no encontrada',
        error_message='La página que buscas no existe o fue movida.'), 404

@app.errorhandler(500)
def error_500(error):
    return render_template('error.html',
        breadcrumbs=[{'nombre': 'Inicio', 'url': url_for('index')}, {'nombre': 'Error 500', 'url': '#'}],
        error_code=500, error_title='Error del servidor',
        error_message='Ocurrió un error inesperado. Por favor, inténtalo más tarde.'), 500

@app.errorhandler(Exception)
def error_general(error):
    return render_template('error.html',
        breadcrumbs=[{'nombre': 'Inicio', 'url': url_for('index')}, {'nombre': 'Error', 'url': '#'}],
        error_code='ERROR', error_title='Ocurrió un problema',
        error_message=f'Se produjo una excepción: {str(error)}'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

@app.route('/api/usuarios/todos')
@login_required
def api_usuarios_todos():
    from flask import jsonify
    usuarios = Usuario.query.order_by(Usuario.id.asc()).all()
    return jsonify([{'id': u.id, 'nombre': u.nombre, 'correo': u.correo} for u in usuarios])
