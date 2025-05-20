from app import db, crear_app

app = crear_app()

with app.app_context():
    db.create_all()
    print("¡Tablas creadas!")
