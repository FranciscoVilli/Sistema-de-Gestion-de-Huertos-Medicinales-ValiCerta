from .calendar import notificaciones_de


def notificaciones(request):
    if not request.user.is_authenticated:
        return {}
    vistas = frozenset(request.session.get("notificaciones_vistas", []))
    return {"notificaciones": notificaciones_de(request.user, vistas=vistas)}
