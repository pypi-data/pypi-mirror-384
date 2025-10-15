# sql_defense.py
# GuardianUnivalle_Benito_Yucra/detectores/detector_sql.py

import json
import logging
import re
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger("sqlidefense")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

# =====================================================
# ===        PATRONES DE ATAQUE SQL DEFINIDOS       ===
# =====================================================
SQL_PATTERNS = [
    (re.compile(r"\bunion\b\s+(all\s+)?\bselect\b", re.I), "Uso de UNION SELECT", 0.7),
    (re.compile(r"\bor\b\s+'?\d+'?\s*=\s*'?\d+'?", re.I), "Tautología OR 1=1", 0.6),
    (re.compile(r"\bselect\b.+\bfrom\b", re.I), "Consulta SQL SELECT-FROM", 0.5),
    (re.compile(r"(--|#|/\*|\*/)", re.I), "Comentario SQL sospechoso", 0.4),
    (re.compile(r"\b(drop|truncate|delete|insert|update)\b", re.I), "Manipulación SQL", 0.5),
    (re.compile(r"exec\s*\(", re.I), "Ejecución de procedimiento almacenado", 0.6),
]

IGNORED_FIELDS = ["password", "csrfmiddlewaretoken", "token", "auth"]


def get_client_ip(request):
    """
    Obtiene la IP real del cliente.
    Primero revisa 'X-Forwarded-For', luego 'REMOTE_ADDR'.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Render y otros proxies envían múltiples IPs separados por coma
        ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if ips:
            return ips[0]  # la primera IP es la IP real del cliente
    # Si no hay X-Forwarded-For, tomar REMOTE_ADDR
    return request.META.get("REMOTE_ADDR", "")



def extract_payload(request):
    """Extrae datos útiles de la solicitud para análisis."""
    parts = []
    try:
        if "application/json" in request.META.get("CONTENT_TYPE", ""):
            data = json.loads(request.body.decode("utf-8") or "{}")
            parts.append(json.dumps(data))
        else:
            body = request.body.decode("utf-8", errors="ignore")
            if body:
                parts.append(body)
    except Exception:
        pass

    qs = request.META.get("QUERY_STRING", "")
    if qs:
        parts.append(qs)

    return " ".join(parts)


def detect_sql_injection(value):
    """Detecta patrones sospechosos en una cadena."""
    score = 0.0
    descripciones = []
    for pattern, desc, weight in SQL_PATTERNS:
        if pattern.search(value):
            score += weight
            descripciones.append(desc)
    return score, descripciones

class SQLIDefenseMiddleware(MiddlewareMixin):
    """Middleware de detección SQL Injection."""

    def process_request(self, request):
        client_ip = get_client_ip(request)
        trusted_ips = getattr(settings, "SQLI_DEFENSE_TRUSTED_IPS", [])
        trusted_urls = getattr(settings, "SQLI_DEFENSE_TRUSTED_URLS", [])

        if client_ip in trusted_ips:
            return None

        referer = request.META.get("HTTP_REFERER", "")
        host = request.get_host()
        if any(url in referer for url in trusted_urls) or any(url in host for url in trusted_urls):
            return None

        payload = extract_payload(request)
        score, descripciones = detect_sql_injection(payload)

        if score == 0:
            return None

        # Registrar ataque completo
        logger.warning(
            f"[SQLiDetect] IP={client_ip} Host={host} Referer={referer} "
            f"Score={score:.2f} Desc={descripciones} Payload={payload[:500]}"
        )

        # Guardar información del ataque en el request
        request.sql_attack_info = {
            "ip": client_ip,
            "tipos": ["SQLi"],
            "descripcion": descripciones,
            "payload": payload[:1000],  # guardar hasta 1000 caracteres
            "score": round(score, 2),
            "url": request.build_absolute_uri(),  # registrar URL completa
        }

        return None



# =====================================================
# ===              INFORMACIÓN EXTRA                ===
# =====================================================
"""
Algoritmos relacionados:
    - Se recomienda almacenar logs SQLi cifrados (AES-GCM) 
      para proteger evidencia de intentos maliciosos.

Cálculo de puntaje de amenaza:
    S_sqli = w_sqli * detecciones_sqli
    Ejemplo: S_sqli = 0.4 * 3 = 1.2

Integración:
    Este middleware puede combinarse con:
        - CSRFDefenseMiddleware
        - XSSDefenseMiddleware
    para calcular un score total de amenaza y decidir bloqueo.
"""
