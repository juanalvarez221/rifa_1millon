# test_envio_correo.py

from flask import Flask
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

app = Flask(__name__)

# Configura Flask-Mail con variables de tu .env o config.py
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

def enviar_prueba(destinatario):
    with app.app_context():
        try:
            msg = Message(
                subject="Prueba de envío desde Rifa Flask",
                recipients=[destinatario],
                body="¡Esto es una prueba de envío de correo desde juandrp777@gmail.com usando Flask-Mail! 😊"
            )
            mail.send(msg)
            print(f"Correo enviado correctamente a {destinatario}.")
        except Exception as e:
            print(f"Error enviando correo: {str(e)}")

if __name__ == "__main__":
    destinatario = input("¿A qué correo quieres enviar la prueba? (escribe tu email): ").strip()
    enviar_prueba(destinatario)
