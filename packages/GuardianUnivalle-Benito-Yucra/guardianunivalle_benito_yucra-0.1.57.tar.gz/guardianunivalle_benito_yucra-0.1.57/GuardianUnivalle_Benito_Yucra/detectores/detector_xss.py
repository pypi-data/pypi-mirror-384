# xss_defense.py
# GuardianUnivalle_Benito_Yucra/detectores/xss_defense.py
from __future__ import annotations
import json
import logging
import re
from typing import List, Tuple, Any, Dict
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

# -------------------------------------------------
# Logger
# -------------------------------------------------
logger = logging.getLogger("xssdefense")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

# -------------------------------------------------
# Intentar usar bleach (si está instalado). Si no,
# seguimos con heurísticos de patrones.
# -------------------------------------------------
try:
    import bleach
    _BLEACH_AVAILABLE = True
except Exception:
    _BLEACH_AVAILABLE = False

# -------------------------------------------------
# Patrones XSS con peso (descripcion, peso)
# - pesos mayores = más severo (por ejemplo <script> o javascript:)
# - esto permite un scoring acumulativo y menos falsos positivos
# -------------------------------------------------
XSS_PATTERNS: List[Tuple[re.Pattern, str, float]] = [
    (re.compile(r"<\s*script\b", re.I), "Etiqueta <script>", 0.8),
    (re.compile(r"javascript\s*:", re.I), "URI javascript:", 0.7),
    (re.compile(r"<\s*iframe\b", re.I), "Etiqueta <iframe>", 0.7),
    (re.compile(r"<\s*embed\b", re.I), "Etiqueta <embed>", 0.7),
    (re.compile(r"<\s*object\b", re.I), "Etiqueta <object>", 0.7),
    (re.compile(r"on\w+\s*=", re.I), "Atributo de evento (on*)", 0.5),
    (re.compile(r"document\.cookie", re.I), "Acceso a document.cookie", 0.6),
    (re.compile(r"alert\s*\(", re.I), "Uso de alert() potencial", 0.4),
    # patrón para imágenes con onerror u onload (caso común)
    (re.compile(r"<\s*img\b[^>]*on\w+\s*=", re.I), "Imagen con evento on*", 0.6),
]

# -------------------------------------------------
# Campos que NO queremos analizar (contraseñas, tokens, etc.)
# -------------------------------------------------
IGNORED_FIELDS = getattr(settings, "XSS_DEFENSE_IGNORED_FIELDS", ["password", "csrfmiddlewaretoken", "token", "auth"])

# Umbral por defecto para considerar "alto riesgo" (Auditoria puede bloquear según su lógica)
XSS_DEFENSE_THRESHOLD = getattr(settings, "XSS_DEFENSE_THRESHOLD", 0.6)


# -------------------------------------------------
# Util: validación / extracción de IP (robusta)
# -------------------------------------------------
def _is_valid_ip(ip: str) -> bool:
    """Verifica que la cadena sea una IP válida (v4 o v6)."""
    try:
        import ipaddress
        ipaddress.ip_address(ip)
        return True
    except Exception:
        return False


def get_client_ip(request) -> str:
    """
    Obtiene la mejor estimación de la IP del cliente:
    - Revisa X-Forwarded-For (primera IP no vacía).
    - Luego X-Real-IP, CF-Connecting-IP.
    - Finalmente REMOTE_ADDR como fallback.
    """
    # Preferir X-Forwarded-For
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # "client, proxy1, proxy2" => tomar la primera no vacía
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[0]

    # Otros encabezados comunes
    for h in ("HTTP_X_REAL_IP", "HTTP_CF_CONNECTING_IP", "HTTP_CLIENT_IP"):
        v = request.META.get(h)
        if v and _is_valid_ip(v):
            return v

    # Fallback
    remote = request.META.get("REMOTE_ADDR")
    return remote or ""


# -------------------------------------------------
# Extraer payload pero evitando cabeceras (para reducir falsos positivos)
# - Devuelve dict si es JSON, o dict con 'raw' para otros cuerpos
# - NO añade User-Agent o Referer al texto a analizar
# -------------------------------------------------
def extract_body_as_map(request) -> Dict[str, Any]:
    """
    Extrae un diccionario con los datos a analizar:
    - Si JSON: devuelve el dict JSON.
    - Si form-data: devuelve request.POST.dict()
    - Si otro: devuelve {'raw': <texto>}
    """
    try:
        ct = request.META.get("CONTENT_TYPE", "")
        if "application/json" in ct:
            raw = request.body.decode("utf-8") or "{}"
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data
                else:
                    # si el JSON no es un objeto (ej: lista), lo devolvemos como raw
                    return {"raw": raw}
            except Exception:
                return {"raw": raw}
        else:
            # FORM data (request.POST) u otros
            try:
                post = request.POST.dict()
                if post:
                    return post
            except Exception:
                pass
            # fallback: cuerpo crudo
            raw = request.body.decode("utf-8", errors="ignore")
            if raw:
                return {"raw": raw}
    except Exception:
        pass
    return {}


# -------------------------------------------------
# Analizar un solo valor (string) en busca de XSS usando patrones
# Devuelve (score, descripciones, matches_patterns)
# -------------------------------------------------
def detect_xss_in_value(value: str) -> Tuple[float, List[str], List[str]]:
    """
    Analiza una cadena y devuelve:
      - score acumulado (sum pesos)
      - lista de descripciones activadas
      - lista de patrones (regex.pattern) que matchearon
    """
    if not value:
        return 0.0, [], []

    score_total = 0.0
    descripcion = []
    matches = []

    # Si bleach está disponible, podemos "limpiar" y comparar; pero aquí solo detectamos
    for patt, msg, weight in XSS_PATTERNS:
        if patt.search(value):
            score_total += weight
            descripcion.append(msg)
            matches.append(patt.pattern)

    return round(score_total, 3), descripcion, matches


# -------------------------------------------------
# Middleware principal XSS
# -------------------------------------------------
class XSSDefenseMiddleware(MiddlewareMixin):
    """
    Middleware para detección XSS.
    - Analiza el body (campo por campo) y querystring si aplica.
    - Ignora campos sensibles (password, token).
    - No incluye User-Agent/Referer en el texto analizado (evita falsos positivos).
    - Añade request.xss_attack_info con: ip, tipos, descripcion, payload, score, url.
    """

    def process_request(self, request):
        # 1) IP y exclusiones
        client_ip = get_client_ip(request)
        trusted_ips: List[str] = getattr(settings, "XSS_DEFENSE_TRUSTED_IPS", [])
        if client_ip and client_ip in trusted_ips:
            return None

        excluded_paths: List[str] = getattr(settings, "XSS_DEFENSE_EXCLUDED_PATHS", [])
        if any(request.path.startswith(p) for p in excluded_paths):
            return None

        # 2) Extraer datos para analizar (dict)
        data = extract_body_as_map(request)

        # Incluir querystring (como campo separado) para análisis si existe
        qs = request.META.get("QUERY_STRING", "")
        if qs:
            data["_query_string"] = qs

        if not data:
            return None

        total_score = 0.0
        all_descriptions: List[str] = []
        all_matches: List[str] = []
        # payload_for_storage: guardamos un resumen/truncado para auditoría
        payload_summary = []

        # 3) Analizar campo por campo (si es dict) o el raw
        if isinstance(data, dict):
            for key, value in data.items():
                # evitar analizar campos sensibles
                if isinstance(key, str) and key.lower() in [f.lower() for f in IGNORED_FIELDS]:
                    continue

                # convertir a string si es otro tipo (list, int...)
                if isinstance(value, (dict, list)):
                    try:
                        vtext = json.dumps(value, ensure_ascii=False)
                    except Exception:
                        vtext = str(value)
                else:
                    vtext = str(value or "")

                # salto rápido: si el valor parece ser un email o password muy corto y sin signos,
                # las probabilidades de XSS son muy bajas; continúa (reduce falsos positivos).
                if key.lower() in ("email", "username") and len(vtext) < 256:
                    # aún así pasar por patrones (no lo ignoramos completamente), pero podemos bajar sensibilidad
                    pass

                s, descs, matches = detect_xss_in_value(vtext)
                total_score += s
                all_descriptions.extend(descs)
                all_matches.extend(matches)

                if s > 0:
                    # almacenar fragmento del campo para auditoría (truncado)
                    payload_summary.append({ "field": key, "snippet": vtext[:300] })

        else:
            # si no es dict, analizar el raw como texto
            raw = str(data)
            s, descs, matches = detect_xss_in_value(raw)
            total_score += s
            all_descriptions.extend(descs)
            all_matches.extend(matches)
            if s > 0:
                payload_summary.append({"field":"raw","snippet": raw[:500]})

        # 4) si no detectó nada, continuar
        if total_score == 0:
            return None

        # 5) construir info para auditoría (truncada)
        url = request.build_absolute_uri()
        score_rounded = round(total_score, 3)
        payload_for_request = json.dumps(payload_summary, ensure_ascii=False)[:2000]

        logger.warning(
            "XSS detectado desde IP %s URL=%s Score=%.3f Desc=%s",
            client_ip,
            url,
            score_rounded,
            all_descriptions,
        )

        # 6) marcar en el request (AuditoriaMiddleware lo consumirá)
        request.xss_attack_info = {
            "ip": client_ip,
            "tipos": ["XSS"],
            "descripcion": all_descriptions,
            "payload": payload_for_request,
            "score": score_rounded,
            "url": url,
        }

        # 7) NO bloquear aquí — lo hace AuditoriaMiddleware según su política
        return None

# =====================================================
# ===              INFORMACIÓN EXTRA                ===
# =====================================================
"""
Algoritmos relacionados:
    - Se recomienda almacenar los payloads XSS cifrados con AES-GCM
      para confidencialidad e integridad.

Contribución a fórmula de amenaza S:
    S_xss = w_xss * detecciones_xss
    Ejemplo: S_xss = 0.3 * 2 = 0.6
"""
