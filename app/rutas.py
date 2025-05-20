from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField, SubmitField, validators
from app import db, bcrypt, mail
from app.modelos import Numero, Usuario, Reserva, Pago, Administrador
from app.utils.temporizador import liberar_reservas_expiradas
from app.utils.correo import enviar_correo_reserva, notificar_admin_reserva, enviar_correo_pago_pendiente, notificar_admin_pago
from datetime import datetime, timedelta
import os
import random
import re
import csv
from io import StringIO
from sqlalchemy import text
from werkzeug.utils import secure_filename
import traceback                   # <--- NUEVO IMPORT
from uuid import uuid4 
from collections import namedtuple
from sqlalchemy import func
from flask_login import login_required


main = Blueprint('main', __name__)

# Validaciones
def validar_correo(correo):
    """Valida que el correo tenga un formato válido."""
    patron = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(patron, correo) is not None

def validar_celular(celular):
    """Valida que el número de celular tenga un formato válido (solo dígitos, 7-15 caracteres)."""
    patron = r'^\d{7,15}$'
    return re.match(patron, celular) is not None

# Formulario para selección de números
class SeleccionNumerosForm(FlaskForm):
    submit = SubmitField('Seleccionar números')

# Formulario para datos del usuario
class DatosForm(FlaskForm):
    primer_nombre = StringField('Nombre', [validators.DataRequired(), validators.Length(max=50)])
    primer_apellido = StringField('Apellido', [validators.DataRequired(), validators.Length(max=50)])
    correo_electronico = StringField('Correo', [validators.DataRequired(), validators.Email(), validators.Length(max=100)])
    numero_celular = StringField('Celular', [validators.DataRequired(), validators.Regexp(r'^\d{7,15}$')])
    submit = SubmitField('Continuar')

# Página de inicio con selección de múltiples números
@main.route('/', methods=['GET', 'POST'])
def inicio():
    liberar_reservas_expiradas()
    numeros = Numero.query.with_entities(Numero.numero, Numero.estado).order_by(Numero.numero).all()
    form = SeleccionNumerosForm()
    if form.validate_on_submit():
        seleccionados = request.form.getlist('numeros')
        if not seleccionados:
            flash('Por favor, selecciona al menos un número.', 'error')
            return render_template('inicio.html', numeros=numeros, form=form)
        session['numeros_seleccionados'] = seleccionados
        return redirect(url_for('main.datos'))
    mensaje = "Elige tus números de la suerte y reta al destino. ¡Cada número es una oportunidad!"
    return render_template('inicio.html', numeros=numeros, form=form, mensaje=mensaje)


# Página para ingresar datos del usuario
@main.route('/datos', methods=['GET', 'POST'])
def datos():
    try:
        seleccionados = session.get('numeros_seleccionados', [])
        if not seleccionados:
            flash('Por favor, selecciona al menos un número antes de continuar. 😊', 'error')
            return redirect(url_for('main.inicio'))

        # Si ya está logueado, ir directo a la reserva y luego al pago
        if session.get('usuario_id'):
            usuario = Usuario.query.get(session['usuario_id'])
            reservaciones_exitosas = []
            reservas_ids = []
            for num_str in seleccionados:
                num = Numero.query.filter_by(numero=num_str).with_for_update().first()
                if num and num.estado == 'disponible':
                    reserva = Reserva(
                        numero_id=num.id,
                        usuario_id=usuario.id,
                        expira_en=datetime.utcnow() + timedelta(minutes=15),
                        estado='activa'
                    )
                    num.estado = 'reservado'
                    db.session.add(reserva)
                    db.session.flush()
                    reservaciones_exitosas.append(num)
                    reservas_ids.append(reserva.id)

            if reservaciones_exitosas:
                db.session.commit()
                for num in reservaciones_exitosas:
                    try:
                        enviar_correo_reserva(usuario, [num.numero])
                        notificar_admin_reserva(usuario, [num.numero])
                    except Exception as e:
                        flash(f"Tu número {num.numero} fue reservado, pero no pudimos enviarte el correo.", "warning")
                session['reservas_ids'] = reservas_ids
                return redirect(url_for('main.confirmar_pago'))
            else:
                flash('No se pudo reservar ningún número. ¡Inténtalo de nuevo! 💛', 'error')
                db.session.rollback()
                return redirect(url_for('main.inicio'))
        
        # Si NO está logueado, pide el formulario como antes
        form = DatosForm()
        if form.validate_on_submit():
            usuario = Usuario.query.filter_by(correo_electronico=form.correo_electronico.data).first()
            if not usuario:
                usuario = Usuario(
                    primer_nombre=form.primer_nombre.data,
                    primer_apellido=form.primer_apellido.data,
                    correo_electronico=form.correo_electronico.data,
                    numero_celular=form.numero_celular.data
                )
                db.session.add(usuario)
                db.session.flush()
            elif usuario.numero_celular != form.numero_celular.data:
                flash('El correo ya está registrado con un número de celular diferente. 😔', 'error')
                return render_template('datos.html', form=form, numeros=seleccionados)

            session['usuario_id'] = usuario.id
            reservaciones_exitosas = []
            reservas_ids = []
            for num_str in seleccionados:
                num = Numero.query.filter_by(numero=num_str).with_for_update().first()
                if num and num.estado == 'disponible':
                    reserva = Reserva(
                        numero_id=num.id,
                        usuario_id=usuario.id,
                        expira_en=datetime.utcnow() + timedelta(minutes=15),
                        estado='activa'
                    )
                    num.estado = 'reservado'
                    db.session.add(reserva)
                    db.session.flush()
                    reservaciones_exitosas.append(num)
                    reservas_ids.append(reserva.id)

            if reservaciones_exitosas:
                db.session.commit()
                for num in reservaciones_exitosas:
                    try:
                        enviar_correo_reserva(usuario, [num.numero])
                        notificar_admin_reserva(usuario, [num.numero])
                    except Exception as e:
                        flash(f"Tu número {num.numero} fue reservado, pero no pudimos enviarte el correo.", "warning")
                session['reservas_ids'] = reservas_ids
                return redirect(url_for('main.confirmar_pago'))
            else:
                flash('No se pudo reservar ningún número. ¡Inténtalo de nuevo! 💛', 'error')
                db.session.rollback()
                return redirect(url_for('main.inicio'))

        return render_template('datos.html', form=form, numeros=seleccionados)
    except Exception as e:
        db.session.rollback()
        print(traceback.format_exc())
        flash(f'Error al procesar tus datos. Por favor, intenta de nuevo. 😔 (Error: {str(e)})', 'error')
        return redirect(url_for('main.inicio'))


# Confirmación de pago
@main.route('/confirmar_pago', methods=['GET', 'POST'])
def confirmar_pago():
    try:
        usuario_id = session.get('usuario_id')
        reservas_ids = session.get('reservas_ids', [])
        if not usuario_id or not reservas_ids:
            flash('No hay reservas activas para confirmar. 😔', 'error')
            return redirect(url_for('main.inicio'))

        reservas = Reserva.query.filter(Reserva.id.in_(reservas_ids), Reserva.estado == 'activa').all()
        if not reservas:
            flash('No hay reservas activas para confirmar. 😔', 'error')
            return redirect(url_for('main.inicio'))

        for reserva in reservas:
            if reserva.expira_en < datetime.utcnow():
                reserva.estado = 'expirada'
                reserva.numero.estado = 'disponible'
                db.session.commit()
                flash('La reserva ha expirado. ¡Elige otros números! 🍀', 'error')
                return redirect(url_for('main.inicio'))

        metodo_pago = None

        if request.method == 'POST':
            metodo_pago = request.form.get('metodo_pago')
            if metodo_pago not in ['efectivo', 'transferencia']:
                flash('Método de pago no válido. Por favor, selecciona una opción válida. 😊', 'error')
                return render_template('confirmar_pago.html', reservas=reservas, metodo_pago=metodo_pago)

            for reserva in reservas:
                pago = Pago(reserva_id=reserva.id, metodo=metodo_pago, estado='pendiente')
                # === EFECTIVO ===
                if metodo_pago == 'efectivo':
                    pago.destinatario = request.form.get('destinatario')
                    if not pago.destinatario or pago.destinatario not in ['Juan', 'Camila']:
                        flash('Por favor, selecciona a qué encargado entregarás el dinero (Juan o Camila). 😊', 'error')
                        return render_template('confirmar_pago.html', reservas=reservas, metodo_pago=metodo_pago)
                # === TRANSFERENCIA ===
                elif metodo_pago == 'transferencia':
                    comprobante = request.files.get('comprobante')
                    if not comprobante or not comprobante.filename:
                        flash('Por favor, sube un comprobante de transferencia (imagen o PDF). 😊', 'error')
                        return render_template('confirmar_pago.html', reservas=reservas, metodo_pago=metodo_pago)
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']
                    ext = os.path.splitext(comprobante.filename)[1].lower()
                    if ext not in allowed_extensions:
                        flash('El comprobante debe ser una imagen o un archivo PDF válido. 😊', 'error')
                        return render_template('confirmar_pago.html', reservas=reservas, metodo_pago=metodo_pago)
                    comprobante.seek(0, os.SEEK_END)
                    file_size = comprobante.tell()
                    if file_size > 5 * 1024 * 1024:
                        flash('El comprobante no debe exceder los 5MB. 😊', 'error')
                        return render_template('confirmar_pago.html', reservas=reservas, metodo_pago=metodo_pago)
                    comprobante.seek(0)
                    # Guardar el archivo (nombre único y extensión original)
                    filename = secure_filename(f'comprobante_{reserva.id}_{uuid4().hex}{ext}')
                    relative_path = f'comprobantes/{filename}'
                    ruta = os.path.join('app/static', relative_path)
                    os.makedirs(os.path.dirname(ruta), exist_ok=True)
                    try:
                        comprobante.save(ruta)
                        pago.comprobante_ruta = relative_path  # Guarda solo la ruta relativa
                    except Exception as e:
                        flash('Error al guardar el comprobante. Por favor, intenta de nuevo. 😔', 'error')
                        return render_template('confirmar_pago.html', reservas=reservas, metodo_pago=metodo_pago)


                reserva.estado = 'confirmada'
                reserva.numero.estado = 'pagado'
                db.session.add(pago)

            # === NOTIFICACIONES DE PAGO ===
            numeros_pagados = [reserva.numero.numero for reserva in reservas]
            usuario = Usuario.query.get(usuario_id)
            try:
                from app.utils.correo import enviar_correo_pago_pendiente, notificar_admin_pago
                enviar_correo_pago_pendiente(usuario, numeros_pagados)
            except Exception as e:
                flash("No fue posible enviarte correo de confirmación, pero tu pago fue recibido.", "warning")
            try:
                notificar_admin_pago(usuario, numeros_pagados)
            except Exception:
                pass

            db.session.commit()
            session.pop('reservas_ids', None)
            flash('¡Gracias por tu participación! Tus pagos están en proceso. ¡Mucha suerte! 💛', 'success')
            return redirect(url_for('main.perfil'))

        return render_template('confirmar_pago.html', reservas=reservas, metodo_pago=metodo_pago)

    except Exception as e:
        print("==== ERROR TRACEBACK ====")
        print(traceback.format_exc())
        print("==== SESSION VARS ====")
        print("usuario_id:", session.get('usuario_id'))
        print("reservas_ids:", session.get('reservas_ids'))
        print("reservas:", reservas if 'reservas' in locals() else None)
        flash(f'Error al procesar tu pago. Por favor, intenta de nuevo. 😔 (Error: {str(e)})', 'error')
        return redirect(url_for('main.inicio'))

    
# Login de usuarios
@main.route('/login', methods=['GET', 'POST'])
def login():
    try:
        session.pop('admin_id', None)  # Limpia la sesión admin si existe
        if request.method == 'POST':
            nombre = request.form.get('primer_nombre', '').strip()
            celular = request.form.get('numero_celular', '').strip()
            if not nombre or not celular:
                flash('Por favor, ingresa tu nombre y celular.', 'error')
                return render_template('login.html')
            usuario = Usuario.query.filter_by(primer_nombre=nombre, numero_celular=celular).first()
            if usuario:
                session['usuario_id'] = usuario.id
                flash('¡Bienvenido de nuevo!', 'success')
                return redirect(url_for('main.perfil'))
            flash('Usuario no encontrado.', 'error')
        return render_template('login.html')
    except Exception as e:
        flash('Error al iniciar sesión.', 'error')
        return render_template('login.html')


# Perfil de usuario
@main.route('/perfil')
def perfil():
    try:
        if 'usuario_id' not in session:
            flash('Por favor, inicia sesión primero. 😊', 'error')
            return redirect(url_for('main.login'))
        usuario = Usuario.query.get_or_404(session['usuario_id'])
        reservas = Reserva.query.filter_by(usuario_id=usuario.id).join(Numero).all()
        return render_template('perfil.html', usuario=usuario, reservas=reservas)
    except Exception as e:
        flash(f'Error al cargar tu perfil. Por favor, intenta de nuevo. 😔 (Error: {str(e)})', 'error')
        return redirect(url_for('main.login'))

# Login de administrador
@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    try:
        session.pop('usuario_id', None)  # Limpia la sesión usuario
        if request.method == 'POST':
            nombre_usuario = request.form.get('nombre_usuario', '').strip()
            contrasena = request.form.get('contrasena', '')
            if not nombre_usuario or not contrasena:
                flash('Por favor, completa todos los campos.', 'error')
                return render_template('admin_login.html')
            admin = Administrador.query.filter_by(nombre_usuario=nombre_usuario).first()
            if not admin:
                flash('El usuario administrador no existe. Contacta al desarrollador.', 'error')
                return render_template('admin_login.html')
            if not bcrypt.check_password_hash(admin.contrasena, contrasena):
                flash('Contraseña incorrecta.', 'error')
                return render_template('admin_login.html')
            session['admin_id'] = admin.id
            flash('¡Bienvenido, administrador!', 'success')
            return redirect(url_for('main.admin_panel'))
        return render_template('admin_login.html')
    except Exception as e:
        flash(f'Error en login admin: {e}', 'error')
        return render_template('admin_login.html')


    
# Panel de administrador
@main.route('/admin')
@main.route('/admin')
def admin_panel():
    try:
        if 'admin_id' not in session:
            flash('Por favor, inicia sesión como administrador. 😊', 'error')
            return redirect(url_for('main.admin_login'))
        usuarios = Usuario.query.order_by(Usuario.primer_nombre).all()
        pagos = Pago.query.order_by(Pago.creado_en.desc()).all()
        now = datetime.utcnow()

        total_participantes = Usuario.query.count()
        pagados = Pago.query.filter_by(estado='confirmado').count()
        pendientes = Pago.query.filter_by(estado='pendiente').count()
        expirados = Reserva.query.filter_by(estado='expirada').count()

        minutos_expiracion = 15
        minutos_urgencia = 12
        por_expirar = Reserva.query.filter(
            Reserva.estado == 'activa',
            func.extract('epoch', func.now() - Reserva.creado_en) < (minutos_expiracion * 60),
            func.extract('epoch', func.now() - Reserva.creado_en) > (minutos_urgencia * 60)
        ).count()

        Resumen = namedtuple('Resumen', ['participantes', 'pagados', 'pendientes', 'expirados', 'por_expirar'])
        resumen = Resumen(
            participantes=total_participantes,
            pagados=pagados,
            pendientes=pendientes,
            expirados=expirados,
            por_expirar=por_expirar
        )

        return render_template('admin.html', usuarios=usuarios, pagos=pagos, now=now, resumen=resumen)
    except Exception as e:
        flash(f'Error al cargar el panel de administrador. Por favor, intenta de nuevo. 😔 (Error: {str(e)})', 'error')
        return redirect(url_for('main.admin_login'))
        
# Cambiar estado de un número (admin)
@main.route('/admin/cambiar_estado/<int:numero_id>/<estado>', methods=['POST'])
def cambiar_estado_numero(numero_id, estado):
    if 'admin_id' not in session:
        flash('Acceso no autorizado.', 'error')
        return redirect(url_for('main.admin_login'))
    
    ESTADOS_VALIDOS = ['reservada', 'confirmada', 'expirada', 'cancelada', 'pagada', 'disponible']
    if estado not in ESTADOS_VALIDOS:
        flash('Estado no válido. 😔', 'danger')
        return redirect(url_for('main.admin_panel'))

    reserva = Reserva.query.filter_by(numero_id=numero_id).order_by(Reserva.creado_en.desc()).first()
    numero = Numero.query.get(numero_id)
    if not reserva or not numero:
        flash("No se encontró la reserva o número.", "danger")
        return redirect(url_for('main.admin_panel'))

    # === Cambios de estado consistentes ===
    if estado == 'pagada':
        reserva.estado = 'pagada'
        numero.estado = 'pagado'
        # Busca pago y márcalo como confirmado, o crea si no existe
        if reserva.pago:
            reserva.pago.estado = 'confirmado'
        else:
            nuevo_pago = Pago(reserva_id=reserva.id, metodo='efectivo', estado='confirmado')
            db.session.add(nuevo_pago)
    elif estado == 'confirmada':
        reserva.estado = 'confirmada'
        numero.estado = 'reservado'
        if reserva.pago:
            reserva.pago.estado = 'pendiente'
    elif estado == 'reservada':
        reserva.estado = 'activa'
        numero.estado = 'reservado'
    elif estado == 'expirada':
        reserva.estado = 'expirada'
        numero.estado = 'disponible'
        # Podrías cancelar pago aquí también si existe y no estaba confirmado
        if reserva.pago and reserva.pago.estado != 'confirmado':
            reserva.pago.estado = 'cancelada'
    elif estado == 'cancelada':
        reserva.estado = 'cancelada'
        numero.estado = 'disponible'
        if reserva.pago and reserva.pago.estado != 'confirmado':
            reserva.pago.estado = 'cancelada'
    elif estado == 'disponible':
        reserva.estado = 'cancelada'
        numero.estado = 'disponible'
        if reserva.pago and reserva.pago.estado != 'confirmado':
            reserva.pago.estado = 'cancelada'

    db.session.commit()
    flash(f"Estado cambiado correctamente a '{estado}'.", "success")
    return redirect(url_for('main.admin_panel'))

    
@main.route('/seleccion_inteligente', methods=['GET', 'POST'])
def seleccion_inteligente():
    disponibles = [str(n.numero) for n in Numero.query.filter_by(estado='disponible').all()]
    preguntas_contestadas = False
    sugeridos = []
    respuestas = {}

    if request.method == 'POST':
        accion = request.form.get('accion')

        if accion == "preguntas":
            cantidad = int(request.form.get('cantidad', 1))
            cantidad = max(1, min(cantidad, 10))
            pregunta1 = request.form.get('pregunta1', '').strip()
            pregunta2 = request.form.get('pregunta2', '').strip()
            pregunta3 = request.form.get('pregunta3', '').strip()
            respuestas = {"pregunta1": pregunta1, "pregunta2": pregunta2, "pregunta3": pregunta3}

            if cantidad > len(disponibles):
                flash(f"Solo hay {len(disponibles)} números disponibles en este momento.", "error")
                return render_template("seleccion_inteligente.html",
                                      sugeridos=[],
                                      preguntas_contestadas=False)
            # Puedes aquí incluir lógica para tratar de agregar el número de la suerte del usuario si está disponible
            sugeridos = random.sample(disponibles, cantidad)
            preguntas_contestadas = True
            # **GUARDAMOS los sugeridos en la sesión**
            session['numeros_sugeridos'] = sugeridos
            session['seleccion_inteligente'] = True
            session['preguntas_respuestas'] = respuestas
            return render_template("seleccion_inteligente.html",
                                   sugeridos=sugeridos,
                                   preguntas_contestadas=preguntas_contestadas,
                                   respuestas=respuestas)

        elif accion == "nueva":
            cantidad = int(request.form.get('cantidad', 1))
            cantidad = max(1, min(cantidad, 10))
            pregunta1 = request.form.get('pregunta1', '').strip()
            pregunta2 = request.form.get('pregunta2', '').strip()
            pregunta3 = request.form.get('pregunta3', '').strip()
            respuestas = {"pregunta1": pregunta1, "pregunta2": pregunta2, "pregunta3": pregunta3}
            if cantidad > len(disponibles):
                flash(f"Solo hay {len(disponibles)} números disponibles en este momento.", "error")
                return render_template("seleccion_inteligente.html",
                                      sugeridos=[],
                                      preguntas_contestadas=False)
            sugeridos = random.sample(disponibles, cantidad)
            preguntas_contestadas = True
            # **Actualizamos los sugeridos en la sesión**
            session['numeros_sugeridos'] = sugeridos
            session['seleccion_inteligente'] = True
            session['preguntas_respuestas'] = respuestas
            return render_template("seleccion_inteligente.html",
                                   sugeridos=sugeridos,
                                   preguntas_contestadas=preguntas_contestadas,
                                   respuestas=respuestas)

        elif accion == "aceptar":
            # **GUARDAMOS los sugeridos como seleccionados finales**
            sugeridos = session.get('numeros_sugeridos', [])
            if not sugeridos or not all(num in disponibles for num in sugeridos):
                flash("Algunos números ya no están disponibles. Intenta de nuevo.", "error")
                return redirect(url_for('main.seleccion_inteligente'))
            session['numeros_seleccionados'] = sugeridos
            session['seleccion_inteligente'] = True
            flash("Números seleccionados exitosamente. Completa tus datos para reservarlos.", "success")
            return redirect(url_for('main.datos'))

    # GET o inicio
    session.pop('seleccion_inteligente', None)
    session.pop('numeros_sugeridos', None)
    session.pop('preguntas_respuestas', None)
    return render_template("seleccion_inteligente.html", preguntas_contestadas=False, sugeridos=[], respuestas={})

# Confirmar o rechazar pago (admin)
@main.route('/admin/pago/<int:pago_id>/<string:accion>', methods=['POST'])
def gestionar_pago(pago_id, accion):
    try:
        if 'admin_id' not in session:
            flash('Acceso no autorizado. 😊', 'error')
            return redirect(url_for('main.admin_login'))
        
        pago = Pago.query.get_or_404(pago_id)
        if accion not in ['confirmar', 'rechazar']:
            flash('Acción no válida. 😔', 'error')
            return redirect(url_for('main.admin_panel'))
        
        if accion == 'confirmar':
            pago.estado = 'confirmado'
            flash('Pago confirmado. ¡Gracias por gestionar la rifa! 💛', 'success')
        elif accion == 'rechazar':
            pago.estado = 'rechazado'
            pago.reserva.numero.estado = 'disponible'
            pago.reserva.estado = 'cancelada'
            flash('Pago rechazado. El número ha sido liberado. 🍀', 'success')
        db.session.commit()
        return redirect(url_for('main.admin_panel'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al gestionar el pago. Por favor, intenta de nuevo. 😔 (Error: {str(e)})', 'error')
        return redirect(url_for('main.admin_panel'))
    
    
@main.route('/admin/pago/<int:pago_id>/confirmar', methods=['POST'])
def confirmar_pago_admin(pago_id):
    if 'admin_id' not in session:
        flash('Acceso no autorizado', 'error')
        return redirect(url_for('main.admin_login'))

    pago = Pago.query.get_or_404(pago_id)
    reserva = pago.reserva

    try:
        pago.estado = 'confirmado'
        reserva.estado = 'pagada'
        reserva.numero.estado = 'pagado'
        db.session.commit()
        flash('Pago confirmado y boleta marcada como pagada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al confirmar el pago: {str(e)}', 'error')
    return redirect(url_for('main.admin_panel'))

    

# Exportar datos a CSV (admin)
@main.route('/admin/exportar_csv', methods=['GET'])
def exportar_csv():
    try:
        if 'admin_id' not in session:
            flash('Acceso no autorizado. 😊', 'error')
            return redirect(url_for('main.admin_login'))
        
        si = StringIO()
        cw = csv.writer(si, lineterminator='\n')
        
        cw.writerow(['Números'])
        cw.writerow(['Número', 'Estado', 'Usuario', 'Creado En'])
        numeros = Numero.query.join(Usuario, Numero.usuario_id == Usuario.id, isouter=True).order_by(Numero.numero).all()
        for numero in numeros:
            usuario = f"{numero.usuario.primer_nombre} {numero.usuario.primer_apellido}" if numero.usuario else '-'
            cw.writerow([numero.numero, numero.estado, usuario, numero.creado_en])
        
        cw.writerow([])
        cw.writerow(['Usuarios'])
        cw.writerow(['Nombre', 'Apellido', 'Correo', 'Celular', 'Creado En'])
        usuarios = Usuario.query.order_by(Usuario.primer_nombre).all()
        for usuario in usuarios:
            cw.writerow([usuario.primer_nombre, usuario.primer_apellido, usuario.correo_electronico, usuario.numero_celular, usuario.creado_en])
        
        cw.writerow([])
        cw.writerow(['Reservas'])
        cw.writerow(['Número', 'Usuario', 'Creado En', 'Expira En', 'Estado'])
        reservas = Reserva.query.join(Numero).join(Usuario).order_by(Reserva.creado_en.desc()).all()
        for reserva in reservas:
            usuario = f"{reserva.usuario.primer_nombre} {reserva.usuario.primer_apellido}"
            cw.writerow([reserva.numero.numero, usuario, reserva.creado_en, reserva.expira_en, reserva.estado])
        
        cw.writerow([])
        cw.writerow(['Pagos'])
        cw.writerow(['Número', 'Usuario', 'Método', 'Destinatario', 'Comprobante', 'Estado', 'Creado En'])
        pagos = Pago.query.join(Reserva).join(Numero).join(Usuario).order_by(Pago.creado_en.desc()).all()
        for pago in pagos:
            usuario = f"{pago.reserva.usuario.primer_nombre} {pago.reserva.usuario.primer_apellido}"
            cw.writerow([pago.reserva.numero.numero, usuario, pago.metodo, pago.destinatario or '-', pago.comprobante_ruta or '-', pago.estado, pago.creado_en])
        
        output = si.getvalue()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=rifa_datos_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    except Exception as e:
        flash(f'Error al exportar los datos. Por favor, intenta de nuevo. 😔 (Error: {str(e)})', 'error')
        return redirect(url_for('main.admin_panel'))

# Cierre de sesión de usuario
@main.route('/logout')
def logout():
    session.pop('usuario_id', None)
    session.pop('admin_id', None)
    flash('¡Sesión cerrada!', 'success')
    return redirect(url_for('main.inicio'))

@main.route('/admin/logout')
def admin_logout():
    session.pop('usuario_id', None)
    session.pop('admin_id', None)
    flash('Sesión admin cerrada.', 'success')
    return redirect(url_for('main.admin_login'))
