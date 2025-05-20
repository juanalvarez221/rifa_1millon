# app/utils/tareas.py
import pandas as pd
from datetime import datetime
from app import db, mail
from app.modelos import Reserva, Usuario, Numero, Pago
from flask_mail import Message
from app.utils.correo import enviar_recordatorio_pago


ADMIN_EMAILS = [
    "juandrp777@gmail.com",
    "vergaramariacamila7@gmail.com"
]

def enviar_recordatorios_a_pendientes():
    """Envía recordatorios a usuarios con reservas confirmadas pero NO pagadas"""
    ahora = datetime.utcnow()
    reservas_pendientes = (
        db.session.query(Reserva)
        .join(Usuario)
        .outerjoin(Pago)
        .filter(Reserva.estado == 'confirmada')
        .filter(
            (Pago.id == None) |  # No existe pago
            (Pago.estado != 'confirmado')  # O pago no confirmado
        )
        .all()
    )
    usuarios_recordados = set()
    for reserva in reservas_pendientes:
        usuario = reserva.usuario
        # Evitar enviar varios correos al mismo usuario el mismo día
        if usuario.id in usuarios_recordados:
            continue
        # Puedes guardar fecha último recordatorio si quieres, o envía cada vez que se ejecute la tarea
        try:
            enviar_recordatorio_pago(usuario)
            usuarios_recordados.add(usuario.id)
            print(f"Recordatorio enviado a {usuario.correo_electronico}")
        except Exception as e:
            print(f"Error enviando recordatorio a {usuario.correo_electronico}: {e}")
            
            
def enviar_backup_boletas():
    """Genera y envía el backup diario de boletas confirmadas y pagas a los admins"""
    # Obtén reservas confirmadas y pagas (puedes ajustar según tu modelo)
    reservas = (
        db.session.query(Reserva)
        .join(Usuario)
        .join(Numero)
        .outerjoin(Pago)
        .filter(Reserva.estado.in_(['confirmada', 'pagada']))
        .all()
    )
    data = []
    for reserva in reservas:
        usuario = reserva.usuario
        numero = reserva.numero.numero
        estado = reserva.estado
        fecha_reserva = reserva.creado_en.strftime('%Y-%m-%d %H:%M:%S')
        pago = Pago.query.filter_by(reserva_id=reserva.id).first()
        metodo_pago = pago.metodo if pago else "-"
        estado_pago = pago.estado if pago else "-"
        comprobante = pago.comprobante_ruta if pago else "-"
        data.append({
            "Número": numero,
            "Estado boleta": estado,
            "Participante": f"{usuario.primer_nombre} {usuario.primer_apellido}",
            "Correo": usuario.correo_electronico,
            "Celular": usuario.numero_celular,
            "Fecha reserva": fecha_reserva,
            "Método de pago": metodo_pago,
            "Estado pago": estado_pago,
            "Comprobante": comprobante,
        })
    df = pd.DataFrame(data)
    if df.empty:
        print("No hay reservas confirmadas ni pagas hoy. No se enviará backup.")
        return

    # Nombre y ruta del archivo
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"backup_boletas_{fecha_hoy}.xlsx"
    ruta_archivo = f"/tmp/{nombre_archivo}"
    df.to_excel(ruta_archivo, index=False)

    # Enviar correo con adjunto
    msg = Message(
        subject=f"Backup diario de boletas Rifa 1 millón - {fecha_hoy}",
        recipients=ADMIN_EMAILS,
        body=(
            "Adjunto encontrarás el respaldo diario de boletas confirmadas y pagas.\n"
            "¡Revisa y respáldalo por seguridad!\n\n"
            "Saludos,\nSistema Rifa 1 millón"
        )
    )
    with open(ruta_archivo, "rb") as f:
        msg.attach(
            filename=nombre_archivo,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            data=f.read()
        )
    mail.send(msg)
    print(f"Backup enviado a los admins: {ADMIN_EMAILS}")

# Puedes ejecutar esto con un scheduler, o llamar la función manualmente.
