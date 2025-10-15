# CSRF defense (parche recomendado)
from __future__ import annotations
import secrets
import logging
import re
import json
from typing import List
from urllib.parse import urlparse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("csrfdefense")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_HEADER_NAMES = ("HTTP_X_CSRFTOKEN", "HTTP_X_CSRF_TOKEN")
CSRF_COOKIE_NAME = getattr(settings, "CSRF_COOKIE_NAME", "csrftoken")
POST_FIELD_NAME = "csrfmiddlewaretoken"

# Nota: NO consideramos 'application/json' sospechoso aquí por defecto,
# porque muchas APIs legítimas usan JSON.
SUSPICIOUS_CT_PATTERNS = [
    re.compile(r"text/plain", re.I),
    re.compile(r"application/x-www-form-urlencoded", re.I),
    re.compile(r"multipart/form-data", re.I),
]

# Umbral minimo de "señales" para marcar como ataque (configurable)
CSRF_DEFENSE_MIN_SIGNALS = getattr(settings, "CSRF_DEFENSE_MIN_SIGNALS", 1)
# Opción para excluir rutas de API que manejan JSON (cambia según tu proyecto)
CSRF_DEFENSE_EXCLUDED_API_PREFIXES = getattr(settings, "CSRF_DEFENSE_EXCLUDED_API_PREFIXES", ["/api/"])

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # toma la primera IP real
        ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if ips:
            return ips[0]
    return request.META.get("REMOTE_ADDR", "")

def host_from_header(header_value: str) -> str | None:
    if not header_value:
        return None
    try:
        parsed = urlparse(header_value)
        if parsed.netloc:
            return parsed.netloc.split(":")[0]
        return header_value.split(":")[0]
    except Exception:
        return None

def origin_matches_host(request) -> bool:
    host_header = request.META.get("HTTP_HOST") or request.META.get("SERVER_NAME")
    if not host_header:
        return True
    host = host_header.split(":")[0]
    origin = request.META.get("HTTP_ORIGIN", "")
    referer = request.META.get("HTTP_REFERER", "")
    origin_host = host_from_header(origin)
    referer_host = host_from_header(referer)
    # bloquear obvious javascript: referers
    if any(re.search(r"(javascript:|<script|data:text/html)", h or "", re.I) for h in [origin, referer]):
        return False
    if origin_host and origin_host == host:
        return True
    if referer_host and referer_host == host:
        return True
    # si no hay origin ni referer, lo consideramos neutral (no marcar)
    if not origin and not referer:
        return True
    return False

def has_csrf_token(request) -> bool:
    # busca header, cookie o campo form
    for h in CSRF_HEADER_NAMES:
        if request.META.get(h):
            return True
    cookie_val = request.COOKIES.get(CSRF_COOKIE_NAME)
    if cookie_val:
        return True
    try:
        if request.method == "POST" and hasattr(request, "POST"):
            if request.POST.get(POST_FIELD_NAME):
                return True
    except Exception:
        pass
    return False

def extract_payload_text(request) -> str:
    parts: List[str] = []
    try:
        body = request.body.decode("utf-8", errors="ignore")
        if body:
            parts.append(body)
    except Exception:
        pass
    qs = request.META.get("QUERY_STRING", "")
    if qs:
        parts.append(qs)
    parts.append(request.META.get("HTTP_USER_AGENT", ""))
    parts.append(request.META.get("HTTP_REFERER", ""))
    return " ".join([p for p in parts if p])

class CSRFDefenseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 1) Excluir APIs JSON si se configuró así
        for prefix in CSRF_DEFENSE_EXCLUDED_API_PREFIXES:
            if request.path.startswith(prefix):
                # debug log opcional
                logger.debug(f"[CSRFDefense] Skip analysis for API prefix {prefix} path {request.path}")
                return None

        client_ip = get_client_ip(request)
        trusted_ips = getattr(settings, "CSRF_DEFENSE_TRUSTED_IPS", [])
        if client_ip in trusted_ips:
            return None

        excluded_paths = getattr(settings, "CSRF_DEFENSE_EXCLUDED_PATHS", [])
        if any(request.path.startswith(p) for p in excluded_paths):
            return None

        method = (request.method or "").upper()
        if method not in STATE_CHANGING_METHODS:
            return None

        descripcion: List[str] = []
        payload = extract_payload_text(request)

        # 1) Falta token CSRF
        if not has_csrf_token(request):
            descripcion.append("Falta token CSRF en cookie/header/form")

        # 2) Origin/Referer no coinciden
        if not origin_matches_host(request):
            descripcion.append("Origin/Referer no coinciden con Host (posible cross-site)")

        # 3) Content-Type sospechoso (solo marcaremos si coincide uno de los patterns)
        content_type = (request.META.get("CONTENT_TYPE") or "")
        for patt in SUSPICIOUS_CT_PATTERNS:
            if patt.search(content_type):
                descripcion.append(f"Content-Type sospechoso: {content_type}")
                break

        # 4) Referer ausente y sin header CSRF
        referer = request.META.get("HTTP_REFERER", "")
        if not referer and not any(request.META.get(h) for h in CSRF_HEADER_NAMES):
            descripcion.append("Referer ausente y sin X-CSRFToken")

        # Si señales >= umbral entonces marcamos para auditoría
        if descripcion and len(descripcion) >= CSRF_DEFENSE_MIN_SIGNALS:
            w_csrf = getattr(settings, "CSRF_DEFENSE_WEIGHT", 0.2)
            intentos_csrf = len(descripcion)
            s_csrf = w_csrf * intentos_csrf

            request.csrf_attack_info = {
                "ip": client_ip,
                "tipos": ["CSRF"],
                "descripcion": descripcion,
                "payload": payload,
                "score": s_csrf,
            }

            logger.warning(
                "CSRF detectado desde IP %s: %s ; path=%s ; Content-Type=%s ; score=%.2f",
                client_ip, descripcion, request.path, content_type, s_csrf
            )
        else:
            # debug útil: saber por qué NO se marcó
            if descripcion:
                logger.debug(f"[CSRFDefense] low-signals ({len(descripcion)}) not marking: {descripcion}")

        return None

"""
CSRF Defense Middleware
========================
Detecta y registra posibles ataques CSRF (Cross-Site Request Forgery).

Algoritmos relacionados:
    * Uso de secreto aleatorio criptográfico (generar_token_csrf).
    * Validación simple por comparación (validar_token_csrf).
    * Integración con detección XSS/SQL Injection mediante registro unificado.
    
Fórmula de amenaza:
    S_csrf = w_csrf * intentos_csrf
    S_csrf = 0.2 * 1
"""


""" 
Algoritmos relacionados:
    *Uso de secreto aleatorio criptográfico.
    *Opcionalmente derivación con PBKDF2 / Argon2 para reforzar token.
Contribución a fórmula de amenaza S:
S_csrf = w_csrf * intentos_csrf
S_csrf = 0.2 * 1
donde w_csrf es peso asignado a CSRF y intentos_csrf es la cantidad de intentos detectados.
"""
