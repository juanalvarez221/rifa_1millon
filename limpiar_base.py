# limpiar_base.py
from app import crear_app, db
from app.modelos import Usuario, Reserva, Pago, Numero

app = crear_app()
with app.app_context():
    # 1. Eliminar reservas y pagos
    Pago.query.delete()
    Reserva.query.delete()
    Usuario.query.delete()
    db.session.commit()
    # 2. Dejar todos los números en estado disponible
    numeros = Numero.query.all()
    for numero in numeros:
        numero.estado = "disponible"
    db.session.commit()
    print("Base limpiada. Todos los números están disponibles y listos para ser elegidos.")
