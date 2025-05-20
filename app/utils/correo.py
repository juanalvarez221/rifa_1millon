# app/utils/correo.py

from flask_mail import Message
from flask import render_template, current_app
from app import mail

ADMIN_EMAILS = [
    "juandrp777@gmail.com",
    "vergaramariacamila7@gmail.com"
]

def get_sender():
    # Retorna el sender desde el config, o por defecto si falla el contexto
    try:
        return current_app.config["MAIL_DEFAULT_SENDER"]
    except Exception:
        return "juandrp777@gmail.com"

def enviar_correo_reserva(usuario, numeros):
    msg = Message(
        subject="¡Tu(s) número(s) han sido reservados! 🍀",
        recipients=[usuario.correo_electronico],
        sender=get_sender()
    )
    msg.html = render_template(
        'correo.html',
        usuario=usuario,
        numero=", ".join(str(n) for n in numeros),
        mensaje="¡Gracias por participar! Tus números están reservados por 15 minutos. Completa el pago para asegurarlos. ¡Mucha suerte! 💛"
    )
    mail.send(msg)

def notificar_admin_reserva(usuario, numeros):
    msg = Message(
        subject="Nueva reserva registrada - Rifa",
        recipients=ADMIN_EMAILS,
        sender=get_sender()
    )
    msg.body = (
        f"Se ha registrado una nueva reserva:\n"
        f"Participante: {usuario.primer_nombre} {usuario.primer_apellido} ({usuario.correo_electronico})\n"
        f"Números reservados: {', '.join(str(n) for n in numeros)}"
    )
    mail.send(msg)

def enviar_correo_pago_pendiente(usuario, numeros):
    msg = Message(
        subject="¡Tu pago está pendiente de revisión! 🍀",
        recipients=[usuario.correo_electronico],
        sender=get_sender()
    )
    msg.body = (
        f"Hemos recibido tu comprobante para los números: {', '.join(str(n) for n in numeros)}.\n"
        "Pronto un administrador confirmará tu participación. ¡Mucha suerte!"
    )
    mail.send(msg)

def notificar_admin_pago(usuario, numeros):
    msg = Message(
        subject="Nuevo pago por revisar - Rifa",
        recipients=ADMIN_EMAILS,
        sender=get_sender()
    )
    msg.body = (
        f"Participante: {usuario.primer_nombre} {usuario.primer_apellido} ({usuario.correo_electronico})\n"
        f"Números: {', '.join(str(n) for n in numeros)}\n"
        "Estado: Pago recibido, pendiente de confirmación por admin."
    )
    mail.send(msg)

def enviar_recordatorio_pago(usuario):
    msg = Message(
        subject="Recordatorio de pago pendiente – Rifa 1 millón",
        recipients=[usuario.correo_electronico],
        sender=get_sender()
    )
    msg.body = (
        f"Hola {usuario.primer_nombre},\n\n"
        "Recuerda que tienes números de la rifa confirmados, pero aún no has completado el pago.\n"
        "¡Asegúrate de no perder la oportunidad de ganar 1 millón de pesos!\n\n"
        "Para pagar, ingresa a tu panel, revisa tus números y sigue el proceso de pago.\n\n"
        "¡Mucha suerte! 🍀"
    )
    mail.send(msg)
