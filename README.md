Rifa Juan y Camila 🍀
¡Bienvenido a nuestra rifa! Este es un aplicativo web desarrollado con amor para organizar una rifa divertida y transparente. Gracias por tu interés y mucha suerte 💛.
Requisitos

Python 3.9+
PostgreSQL 15
pgAdmin (opcional, para administrar la base de datos)
Cuenta de correo (Gmail recomendado) para notificaciones

Instalación

Clonar el repositorio
git clone <url_del_repositorio>
cd rifa_juan_camila


Crear un entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate


Instalar dependencias
pip install -r requirements.txt


Configurar la base de datos

Inicia PostgreSQL y crea una base de datos llamada rifa_juan_camila.
Usa el usuario postgres con contraseña jfac2124 (o actualiza config.py si usas otra).
Ejecuta el esquema SQL:psql -U postgres -d rifa_juan_camila -f esquema_base_datos.sql




Configurar variables de entorno

Copia el archivo .env.example a .env y completa las variables:cp .env.example .env


Asegúrate de configurar MAIL_USERNAME y MAIL_PASSWORD con una cuenta de Gmail y una contraseña de aplicación.


Ejecutar la aplicación
python run.py


Abre tu navegador en http://localhost:5000.



Despliegue en servidor gratuito (Render)

Crea una cuenta en Render.
Crea un nuevo Web Service y conecta tu repositorio de GitHub.
Configura:
Entorno: Python
Comando de construcción: pip install -r requirements.txt
Comando de inicio: gunicorn -w 4 -b 0.0.0.0:8000 run:app


Añade variables de entorno en el panel de Render:
SECRET_KEY
MAIL_USERNAME
MAIL_PASSWORD
SQLALCHEMY_DATABASE_URI (usa una base de datos PostgreSQL proporcionada por Render).


Despliega y verifica que la aplicación esté funcionando.

Uso

Usuarios: Elige un número del 00 al 99, completa tus datos, y confirma tu pago. ¡Mucha suerte!
Administradores: Inicia sesión con las credenciales de Juan o Camila para gestionar números, pagos y usuarios.

Notas

Los números se reservan por 15 minutos. Si no confirmas, se liberan automáticamente.
Recibirás correos recordatorios si no has pagado y una notificación antes del sorteo.
Para soporte, contacta a Juan o Camila. ¡Estamos felices de ayudarte!

¡Gracias por participar y que la suerte esté contigo! 🍀
