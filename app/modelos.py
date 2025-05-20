from . import db
from datetime import datetime
from flask_login import UserMixin

class Numero(db.Model):
    __tablename__ = 'numeros'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(2), unique=True, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='disponible')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref='numeros')
    reservas = db.relationship('Reserva', backref='numero')

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    primer_nombre = db.Column(db.String(50), nullable=False)
    primer_apellido = db.Column(db.String(50), nullable=False)
    correo_electronico = db.Column(db.String(100), unique=True, nullable=False)
    numero_celular = db.Column(db.String(15), unique=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    reservas = db.relationship('Reserva', backref='usuario')

class Reserva(db.Model):
    __tablename__ = 'reservas'
    id = db.Column(db.Integer, primary_key=True)
    numero_id = db.Column(db.Integer, db.ForeignKey('numeros.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    expira_en = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='activa')
    pago = db.relationship('Pago', backref='reserva', uselist=False)

class Pago(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(db.Integer, db.ForeignKey('reservas.id'), nullable=False)
    metodo = db.Column(db.String(20), nullable=False)
    destinatario = db.Column(db.String(50))
    comprobante_ruta = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

class Administrador(db.Model):
    __tablename__ = 'administradores'
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    correo_electronico = db.Column(db.String(100), unique=True, nullable=False)
    numero_celular = db.Column(db.String(20), nullable=True)
    contrasena = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100), nullable=True)
    apellido = db.Column(db.String(100), nullable=True)
    # Si tienes más o menos, usa los correctos

