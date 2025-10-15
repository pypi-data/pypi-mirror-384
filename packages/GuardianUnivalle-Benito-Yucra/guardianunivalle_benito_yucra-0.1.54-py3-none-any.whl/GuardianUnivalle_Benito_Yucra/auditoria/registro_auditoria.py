import os
import datetime
import json

# 📁 Guardar los logs dentro de una carpeta "logs"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "auditoria_guardian.log")

def registrar_evento(
    tipo: str,
    descripcion: str = "",
    severidad: str = "MEDIA",
    extra: dict | None = None,
):
    """
    Registra un evento de auditoría en un archivo JSON línea por línea.
    Cada línea representa un evento.
    """
    try:
        evento = {
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": tipo,
            "descripcion": descripcion,
            "severidad": severidad,
            "extra": extra or {},
        }

        # ✅ Crear carpeta si no existe
        os.makedirs(LOG_DIR, exist_ok=True)

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")

    except Exception as e:
        print(f"[Auditoría] Error al registrar evento: {e}")

def generar_reporte() -> str:
    """Devuelve el contenido completo del archivo de auditoría."""
    if not os.path.exists(LOG_FILE):
        return "No hay registros aún."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()
