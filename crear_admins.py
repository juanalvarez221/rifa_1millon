# crear_admins.py
from app import crear_app, db, bcrypt
from app.modelos import Administrador

def crear_admins():
    app = crear_app()
    with app.app_context():
        # Reemplaza los nombres de campos según tu modelo exacto
        admin1 = Administrador.query.filter_by(nombre_usuario="jfac2124").first()
        if not admin1:
            admin1 = Administrador(
                nombre="Juan",
                apellido="Alvarez",
                nombre_usuario="jfac2124",
                correo_electronico="juancastaneda2123@gmail.com",
                numero_celular="3156841671",
                contrasena=bcrypt.generate_password_hash("jfac2124").decode('utf-8')
            )
            db.session.add(admin1)
        
        admin2 = Administrador.query.filter_by(nombre_usuario="mcvl1002").first()
        if not admin2:
            admin2 = Administrador(
                nombre="Camila",
                apellido="Vergara",
                nombre_usuario="mcvl1002",
                correo_electronico="vergaramariacamila7@gmail.com",
                numero_celular="3004720595",
                contrasena=bcrypt.generate_password_hash("mcvl1002").decode('utf-8')
            )
            db.session.add(admin2)
        
        db.session.commit()
        print("Admins creados (si no existían)")

if __name__ == "__main__":
    crear_admins()
