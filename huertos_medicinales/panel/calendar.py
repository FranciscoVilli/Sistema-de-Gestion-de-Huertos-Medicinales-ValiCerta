import calendar
from datetime import date
from datetime import timedelta
from urllib.parse import urlencode

from django import forms
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from huertos_medicinales.comunidades.gamificacion import evaluar_insignias
from huertos_medicinales.seguimiento.models import ActividadCalendario
from huertos_medicinales.seguimiento.models import Practica

from .lunar import month_phases
from .lunar import phase_on
from .lunar import proxima_buena_para_sembrar
from .lunar import recomendacion

# Rango de anios aceptado en los parametros de fecha del calendario.
ANIO_MINIMO = 1900
ANIO_MAXIMO = 2100

TIPO_POR_ETIQUETA = {
    **{valor: valor for valor, _ in ActividadCalendario.TIPOS},
    **{etiqueta.lower(): valor for valor, etiqueta in ActividadCalendario.TIPOS},
}


class TipoLibreMixin:
    """`tipo` como texto libre: si coincide (sin importar mayusculas) con una de las
    categorias conocidas (riego, siembra...) se guarda como esa categoria -y se
    mantienen el aviso lunar, la estadistica de riego y los colores del calendario-;
    si no, se guarda tal cual lo escribio el usuario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"] = forms.CharField(
            label="Actividad",
            max_length=60,
            widget=forms.TextInput(
                attrs={
                    "list": "actividad-sugerencias",
                    "placeholder": "Riego, siembra, cosecha...",
                },
            ),
        )
        instancia = getattr(self, "instance", None)
        if instancia is not None and instancia.pk:
            # Al editar se muestra la etiqueta ("Siembra"), no la clave interna.
            self.initial["tipo"] = instancia.get_tipo_display()

    def clean_tipo(self):
        valor = self.cleaned_data["tipo"].strip()
        return TIPO_POR_ETIQUETA.get(valor.lower(), valor)


class ActividadForm(TipoLibreMixin, forms.ModelForm):
    class Meta:
        model = ActividadCalendario
        fields = [
            "practica",
            "tipo",
            "fecha",
            "hora",
            "tecnica",
            "propagacion",
            "parte_usada",
            "notas",
            "recordatorio_dias_antes",
        ]
        labels = {"practica": "Cultivo"}
        widgets = {
            "fecha": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "hora": forms.TimeInput(attrs={"type": "time"}),
            "notas": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["practica"].queryset = Practica.objects.filter(
            participante=user,
            estado="activa",
        )
        if self.instance.pk:
            self.fields["practica"].queryset = Practica.objects.filter(
                participante=user,
            )


class ActividadRapidaForm(TipoLibreMixin, forms.ModelForm):
    """Formulario minimo para el modal del calendario.

    Solo pide lo necesario para programar un cuidado; el resto (tecnica, notas,
    recordatorio...) se completa despues editando la actividad.
    """

    class Meta:
        model = ActividadCalendario
        fields = ["practica", "tipo", "fecha", "hora"]
        labels = {"practica": "Cultivo"}
        widgets = {
            "fecha": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "hora": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["practica"].queryset = Practica.objects.filter(
            participante=user,
            estado="activa",
        )


def parse_date(value, default):
    try:
        parsed = date.fromisoformat(value)
    except ValueError, TypeError:
        return default
    return parsed if ANIO_MINIMO <= parsed.year <= ANIO_MAXIMO else default


def notificaciones_de(user, today=None, vistas=frozenset()):
    """`vistas` son las claves que el usuario ya marco como leidas (al abrir la
    campanita). Una actividad vuelve a aparecer si cambia su estado de
    recordatorio (p.ej. ya se puso "urgente"); la luna, si cambia la fecha
    recomendada. No se vuelve a mostrar algo identico a lo ya visto."""
    today = today or timezone.localdate()
    luna = proxima_buena_para_sembrar(today)
    actividades = list(
        ActividadCalendario.objects.filter(
            practica__participante=user,
            completada=False,
            fecha__gte=today,
        )
        .select_related("practica")
        .order_by("fecha", "hora")[:8],
    )
    for item in actividades:
        item.recordatorio_activo = (
            item.recordatorio_dias_antes is not None
            and today >= item.fecha - timedelta(days=item.recordatorio_dias_antes)
        )
        item.clave = f"actividad:{item.pk}:{int(item.recordatorio_activo)}"
    luna_clave = (
        f"luna:{luna['fecha'].isoformat()}:{int(luna['hoy'])}" if luna else None
    )
    claves_actuales = [item.clave for item in actividades] + (
        [luna_clave] if luna_clave else []
    )
    actividades = [item for item in actividades if item.clave not in vistas]
    if luna_clave in vistas:
        luna = None
    total = len(actividades) + (1 if luna and luna["hoy"] else 0)
    return {
        "luna": luna,
        "actividades": actividades,
        "total": total,
        "claves": claves_actuales,
    }


@login_required
def calendario(request):
    today = timezone.localdate()
    selected = parse_date(request.GET.get("dia"), today)
    month = parse_date(request.GET.get("mes", "") + "-01", selected.replace(day=1))
    if (selected.year, selected.month) != (month.year, month.month):
        selected = month
    crops = Practica.objects.filter(participante=request.user)
    activities = ActividadCalendario.objects.filter(
        practica__participante=request.user,
    ).select_related("practica")
    tipo = request.GET.get("tipo", "")
    if tipo not in dict(ActividadCalendario.TIPOS):
        tipo = ""
    crop_id = request.GET.get("cultivo", "")
    crop = next((p for p in crops if str(p.pk) == crop_id), None)
    filtered = activities
    if tipo:
        filtered = filtered.filter(tipo=tipo)
    if crop:
        filtered = filtered.filter(practica=crop)

    def link(day):
        return "?" + urlencode(
            {
                "dia": day.isoformat(),
                "mes": day.strftime("%Y-%m"),
                "tipo": tipo,
                "cultivo": str(crop.pk) if crop else "",
            },
        )

    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(
        month.year,
        month.month,
    )
    events = list(filtered.filter(fecha__range=(weeks[0][0], weeks[-1][-1])))
    cells = []
    for week in weeks:
        row = []
        for day in week:
            items = [e for e in events if e.fecha == day]
            row.append(
                {
                    "lunar": phase_on(day),
                    "date": day,
                    "url": link(day),
                    "items": items[:3],
                    "extra": max(0, len(items) - 3),
                    "outside": day.month != month.month,
                    "selected": day == selected,
                    "today": day == today,
                },
            )
        cells.append(row)
    lunar_month = month_phases(month)
    for phase in lunar_month:
        phase["url"] = link(phase["date"])
    nueva_form = ActividadRapidaForm(user=request.user, initial={"fecha": selected})
    return render(
        request,
        "panel/calendario.html",
        {
            "lunar_selected": phase_on(selected),
            "lunar_month": lunar_month,
            "weeks": cells,
            "month": month,
            "selected": selected,
            "prev": link(month - timedelta(days=1)),
            "next": link((month + timedelta(days=32)).replace(day=1)),
            "today_url": link(today),
            "crops": crops,
            "crop_id": str(crop.pk) if crop else "",
            "tipo": tipo,
            "types": ActividadCalendario.TIPOS,
            "agenda": filtered.filter(fecha=selected),
            "today_count": activities.filter(fecha=today, completada=False).count(),
            "overdue": activities.filter(fecha__lt=today, completada=False).count(),
            "next_water": activities.filter(
                tipo="riego",
                fecha__gte=today,
                completada=False,
            ).first(),
            "active_count": crops.filter(estado="activa").count(),
            "nueva_form": nueva_form,
            "sin_cultivos_activos": not nueva_form.fields["practica"].queryset.exists(),
        },
    )


@login_required
def nueva(request, pk=None):
    instance = (
        get_object_or_404(
            ActividadCalendario,
            pk=pk,
            practica__participante=request.user,
        )
        if pk
        else None
    )
    form_class = ActividadForm if instance else ActividadRapidaForm
    form = form_class(
        request.POST or None,
        instance=instance,
        user=request.user,
        initial={"fecha": parse_date(request.GET.get("dia"), timezone.localdate())},
    )
    if request.method == "POST" and form.is_valid():
        activity = form.save()
        return redirect(reverse("calendar") + "?dia=" + activity.fecha.isoformat())
    data = form.data if form.is_bound else form.initial
    fecha_actual = parse_date(str(data.get("fecha", "")), None)
    tipo_escrito = str(data.get("tipo", "")).strip()
    tipo_clave = TIPO_POR_ETIQUETA.get(tipo_escrito.lower(), tipo_escrito)
    luna = None
    if fecha_actual:
        luna = recomendacion(tipo_clave, fecha_actual, data.get("parte_usada", ""))
    sin_cultivos_activos = (
        instance is None and not form.fields["practica"].queryset.exists()
    )
    return render(
        request,
        "panel/calendario_form.html",
        {
            "form": form,
            "editing": instance is not None,
            "luna": luna,
            "types": ActividadCalendario.TIPOS,
            "sin_cultivos_activos": sin_cultivos_activos,
        },
    )


@login_required
@require_POST
def completar(request, pk):
    activity = get_object_or_404(
        ActividadCalendario,
        pk=pk,
        practica__participante=request.user,
    )
    # Explicit state makes retries safe; completing never fabricates a photo or note.
    done = request.POST.get("completada") == "1"
    ActividadCalendario.objects.filter(pk=activity.pk).update(
        completada=done,
        completada_en=timezone.now() if done else None,
    )
    if done:
        miembro = getattr(request.user, "membresia", None)
        if miembro and miembro.estado == "aprobada":
            evaluar_insignias(miembro)
    return redirect(reverse("calendar") + "?dia=" + activity.fecha.isoformat())


@login_required
@require_POST
def marcar_notificaciones_vistas(request):
    vistas = set(request.session.get("notificaciones_vistas", []))
    vistas.update(notificaciones_de(request.user)["claves"])
    request.session["notificaciones_vistas"] = list(vistas)
    return JsonResponse({"ok": True})
