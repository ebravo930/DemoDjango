"""
Capa de integración externa: cliente HTTP de Supabase (PostgREST).

Módulo AISLADO que encapsula el envío de eventos de auditoría a la tabla
`task_audit_log` del proyecto Supabase (rama dev).

Diseño fail-safe: si faltan credenciales, no hay red o Supabase responde
con error, la función retorna False SIN propagar excepciones, de modo que
la aplicación local sigue funcionando al 100%.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def log_task_event_to_supabase(
    task_id: int,
    title: str,
    action: str,
    user_username: str,
    extra_data: dict = None,
) -> bool:
    """Envía un registro de auditoría a la tabla 'task_audit_log'.

    Retorna True solo si Supabase confirmó la inserción (HTTP 200/201).
    """
    if not getattr(settings, 'SUPABASE_AUDIT_ENABLED', False):
        logger.debug('[SUPABASE] Integración deshabilitada o sin credenciales.')
        return False

    url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/task_audit_log"
    headers = {
        'apikey': settings.SUPABASE_KEY,
        'Authorization': f"Bearer {settings.SUPABASE_KEY}",
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
    }
    payload = {
        'task_id': task_id,
        'task_title': title,
        'action': action,
        'user_username': user_username,
        'metadata': extra_data or {},
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=3.5)
        if response.status_code in (200, 201):
            logger.info(
                "[SUPABASE AUDIT] Evento '%s' registrado para tarea #%s.",
                action,
                task_id,
            )
            return True
        logger.warning(
            '[SUPABASE AUDIT] Error de Supabase (%s): %s',
            response.status_code,
            response.text,
        )
        return False
    except Exception as exc:  # noqa: BLE001 - fail-safe deliberado
        logger.warning('[SUPABASE AUDIT] No se pudo sincronizar evento: %s', exc)
        return False
