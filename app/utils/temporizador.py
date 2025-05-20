from datetime import datetime
from app import db
from app.modelos import Reserva, Numero

def liberar_reservas_expiradas():
    """Libera los números cuya reserva expiró (más de 15 minutos)"""
    ahora = datetime.utcnow()
    reservas_expiradas = Reserva.query.filter(
        Reserva.estado == "activa",
        Reserva.expira_en < ahora
    ).all()
    for reserva in reservas_expiradas:
        reserva.estado = "expirada"
        numero = Numero.query.get(reserva.numero_id)
        if numero:
            numero.estado = "disponible"
    if reservas_expiradas:
        db.session.commit()
