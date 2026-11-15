from .calendar import notificaciones_de


def notificaciones(request):
    if not request.user.is_authenticated:
        return {}
    return {"notificaciones": notificaciones_de(request.user)}
