# run_tareas.py

from app import crear_app
from app.utils.tareas import enviar_recordatorios_a_pendientes
from app.utils.tareas import enviar_backup_boletas

app = crear_app()

with app.app_context():
    enviar_recordatorios_a_pendientes()
    
with app.app_context():
    enviar_backup_boletas()
