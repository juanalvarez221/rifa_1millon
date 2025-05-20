# agregar_numeros_base.py

from app import crear_app, db
from app.modelos import Numero

app = crear_app()

with app.app_context():
    existentes = Numero.query.count()
    if existentes >= 100:
        print("Los números base ya están en la base de datos.")
    else:
        print("Repoblando números base...")
        db.session.query(Numero).delete()
        for n in range(100):
            num_str = f"{n:02d}"
            db.session.add(Numero(numero=num_str, estado='disponible'))
        db.session.commit()
        print("Números del 00 al 99 creados y disponibles.")
