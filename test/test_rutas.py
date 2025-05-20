import pytest
from app import crear_app, db
from app.modelos import Numero, Usuario, Reserva, Pago
from datetime import datetime, timedelta
import os

@pytest.fixture
def app():
    """Configura una aplicación Flask para pruebas."""
    app = crear_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Desactivar CSRF para pruebas
    with app.app_context():
        db.create_all()
        # Insertar datos iniciales
        numero = Numero(numero='01', estado='disponible')
        db.session.add(numero)
        db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    """Crea un cliente de prueba."""
    return app.test_client()

def test_inicio(client):
    """Prueba la página de inicio."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Gracias por apoyar nuestra rifa' in response.data

def test_reservar_numero(client):
    """Prueba la reserva de un número."""
    response = client.post('/reservar/01', data={
        'primer_nombre': 'Ana',
        'primer_apellido': 'Gómez',
        'correo_electronico': 'ana@example.com',
        'numero_celular': '1234567890'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Tu n\xfamero ha sido reservado' in response.data
    with client.application.app_context():
        numero = Numero.query.filter_by(numero='01').first()
        assert numero.estado == 'reservado'
        reserva = Reserva.query.first()
        assert reserva is not None
        assert reserva.estado == 'activa'

def test_reservar_numero_no_disponible(client):
    """Prueba intentar reservar un número no disponible."""
    with client.application.app_context():
        numero = Numero.query.filter_by(numero='01').first()
        numero.estado = 'pagado'
        db.session.commit()
    response = client.post('/reservar/01', data={
        'primer_nombre': 'Ana',
        'primer_apellido': 'Gómez',
        'correo_electronico': 'ana@example.com',
        'numero_celular': '1234567890'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Ese n\xfamero no est\xe1 disponible' in response.data

def test_validaciones_formulario(client):
    """Prueba validaciones de formulario."""
    response = client.post('/reservar/01', data={
        'primer_nombre': '',
        'primer_apellido': 'Gómez',
        'correo_electronico': 'ana@example.com',
        'numero_celular': '1234567890'
    })
    assert response.status_code == 200
    assert b'Por favor, completa tu nombre' in response.data

    response = client.post('/reservar/01', data={
        'primer_nombre': 'Ana',
        'primer_apellido': 'Gómez',
        'correo_electronico': 'correo_invalido',
        'numero_celular': '1234567890'
    })
    assert response.status_code == 200
    assert b'El correo electr\xf3nico no es v\xe1lido' in response.data

def test_confirmar_reserva(client):
    """Prueba confirmar una reserva con pago en efectivo."""
    with client.application.app_context():
        usuario = Usuario(
            primer_nombre='Ana',
            primer_apellido='Gómez',
            correo_electronico='ana@example.com',
            numero_celular='1234567890'
        )
        db.session.add(usuario)
        db.session.flush()
        numero = Numero.query.filter_by(numero='01').first()
        reserva = Reserva(
            numero_id=numero.id,
            usuario_id=usuario.id,
            expira_en=datetime.utcnow() + timedelta(minutes=15),
            estado='activa'
        )
        numero.estado = 'reservado'
        db.session.add(reserva)
        db.session.commit()
        reserva_id = reserva.id

    response = client.post(f'/confirmar/{reserva_id}', data={
        'metodo_pago': 'efectivo',
        'destinatario': 'Juan'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Tu pago est\xe1 en proceso' in response.data
    with client.application.app_context():
        reserva = Reserva.query.get(reserva_id)
        assert reserva.estado == 'confirmada'
        assert reserva.numero.estado == 'pagado'
        pago = Pago.query.first()
        assert pago.metodo == 'efectivo'
        assert pago.destinatario == 'Juan'

def test_concurrencia_reserva(client):
    """Prueba concurrencia simulada para reservar el mismo número."""
    def intentar_reserva():
        with client.application.app_context():
            response = client.post('/reservar/01', data={
                'primer_nombre': 'Ana',
                'primer_apellido': 'Gómez',
                'correo_electronico': 'ana@example.com',
                'numero_celular': '1234567890'
            }, follow_redirects=True)
            return response

    # Simular dos reservas simultáneas
    response1 = intentar_reserva()
    response2 = intentar_reserva()

    assert response1.status_code == 200
    assert b'Tu n\xfamero ha sido reservado' in response1.data
    assert response2.status_code == 200
    assert b'Ese n\xfamero no est\xe1 disponible' in response2.data