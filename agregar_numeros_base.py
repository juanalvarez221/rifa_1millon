# agregar_numeros_base.py
from app import crear_app, db
from app.modelos import Numero

app = crear_app()

with app.app_context():
    existentes = Numero.query.count()
    if existentes == 0:
        for i in range(1, 101):  # Cambia el rango según tus necesidades
            numero_str = f"{i:02d}"  # 2 dígitos con ceros a la izquierda (01, 02, ...)
            num = Numero(numero=numero_str, estado='disponible')
            db.session.add(num)
        db.session.commit()
        print("Números agregados correctamente.")
    else:
        print(f"Ya hay {existentes} números en la base.")
