from app import crear_app, db, bcrypt
from app.modelos import Administrador

app = crear_app()
with app.app_context():
    admins = [
        {'nombre_usuario': 'Juan', 'contrasena': 'jfac2124'},
        {'nombre_usuario': 'Camila', 'contrasena': 'mcvl1002'}
    ]
    for adm in admins:
        existente = Administrador.query.filter_by(nombre_usuario=adm['nombre_usuario']).first()
        if not existente:
            nuevo_admin = Administrador(
                nombre_usuario=adm['nombre_usuario'],
                contrasena=bcrypt.generate_password_hash(adm['contrasena']).decode('utf-8')
            )
            db.session.add(nuevo_admin)
    db.session.commit()
    print("Administradores creados correctamente.")
