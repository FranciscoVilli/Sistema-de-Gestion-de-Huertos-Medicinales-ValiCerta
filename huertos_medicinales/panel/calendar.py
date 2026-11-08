import calendar
from .lunar import phase_on, month_phases, recomendacion
from datetime import date
from datetime import timedelta
from urllib.parse import urlencode

from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from huertos_medicinales.seguimiento.models import ActividadCalendario
from huertos_medicinales.seguimiento.models import Practica, Jardin


class ActividadForm(forms.ModelForm):
    class Meta:
        model = ActividadCalendario
        fields = ["practica", "tipo", "fecha", "hora", "tecnica", "propagacion", "parte_usada", "notas"]
        labels = {"practica": "Cultivo"}
        widgets = {"fecha": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}), "hora": forms.TimeInput(attrs={"type": "time"}), "notas": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["practica"].queryset = Practica.objects.filter(participante=user, estado="activa")
        if self.instance.pk:
            self.fields["practica"].queryset = Practica.objects.filter(participante=user)


def parse_date(value, default):
    try:
        parsed = date.fromisoformat(value)
        return parsed if 1900 <= parsed.year <= 2100 else default
    except (ValueError, TypeError):
        return default


@login_required
def calendario(request):
    today = timezone.localdate()
    selected = parse_date(request.GET.get("dia"), today)
    month = parse_date(request.GET.get("mes", "") + "-01", selected.replace(day=1))
    if (selected.year, selected.month) != (month.year, month.month):
        selected = month
    crops = Practica.objects.filter(participante=request.user)
    activities = ActividadCalendario.objects.filter(practica__participante=request.user).select_related("practica")
    tipo = request.GET.get("tipo", "")
    if tipo not in dict(ActividadCalendario.TIPOS):
        tipo = ""
    crop_id = request.GET.get("cultivo", "")
    crop = next((p for p in crops if str(p.pk) == crop_id), None)
    weather_gardens = Jardin.objects.filter(propietario=request.user)
    garden_id = request.GET.get("jardin", "")
    weather_garden = next((g for g in weather_gardens if str(g.pk) == garden_id), None)
    if weather_garden is None:
        weather_garden = next((g for g in weather_gardens if crop and g.pk == crop.jardin_id), None) or weather_gardens.first()
    filtered = activities
    if tipo:
        filtered = filtered.filter(tipo=tipo)
    if crop:
        filtered = filtered.filter(practica=crop)
    def link(day):
        return "?" + urlencode({"dia": day.isoformat(), "mes": day.strftime("%Y-%m"), "jardin":str(weather_garden.pk) if weather_garden else "", "tipo": tipo, "cultivo": str(crop.pk) if crop else ""})
    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month)
    events = list(filtered.filter(fecha__range=(weeks[0][0], weeks[-1][-1])))
    cells = []
    for week in weeks:
        row=[]
        for day in week:
            items=[e for e in events if e.fecha == day]
            row.append({"lunar":phase_on(day),"date":day,"url":link(day),"items":items[:3],"extra":max(0,len(items)-3),"outside":day.month!=month.month,"selected":day==selected,"today":day==today})
        cells.append(row)
    lunar_month = month_phases(month)
    for phase in lunar_month:
        phase["url"] = link(phase["date"])
    return render(request, "panel/calendario.html", {"weather_gardens":weather_gardens,"weather_garden":weather_garden,"lunar_selected":phase_on(selected),"lunar_month":lunar_month,"weeks":cells,"month":month,"selected":selected,"prev":link(month-timedelta(days=1)),"next":link((month+timedelta(days=32)).replace(day=1)),"today_url":link(today),"crops":crops,"crop_id":str(crop.pk) if crop else "","tipo":tipo,"types":ActividadCalendario.TIPOS,"agenda":filtered.filter(fecha=selected),"upcoming":filtered.filter(fecha__gte=today,completada=False)[:5],"today_count":activities.filter(fecha=today,completada=False).count(),"overdue":activities.filter(fecha__lt=today,completada=False).count(),"next_water":activities.filter(tipo="riego",fecha__gte=today,completada=False).first(),"active_count":crops.filter(estado="activa").count()})


@login_required
def nueva(request, pk=None):
    instance = get_object_or_404(ActividadCalendario, pk=pk, practica__participante=request.user) if pk else None
    form = ActividadForm(request.POST or None, instance=instance, user=request.user, initial={"fecha":parse_date(request.GET.get("dia"), timezone.localdate())})
    if request.method == "POST" and form.is_valid():
        activity=form.save()
        return redirect(reverse("calendar")+"?dia="+activity.fecha.isoformat())
    data = form.data if form.is_bound else form.initial
    fecha_actual = parse_date(str(data.get("fecha","")), None)
    luna = recomendacion(data.get("tipo",""), fecha_actual, data.get("parte_usada","")) if fecha_actual else None
    return render(request,"panel/calendario_form.html",{"form":form,"editing":instance is not None,"luna":luna})


@login_required
@require_POST
def completar(request, pk):
    activity=get_object_or_404(ActividadCalendario, pk=pk, practica__participante=request.user)
    # Explicit state makes retries safe; checking a task does not fabricate a photo or observation.
    done=request.POST.get("completada")=="1"
    ActividadCalendario.objects.filter(pk=activity.pk).update(completada=done,completada_en=timezone.now() if done else None)
    return redirect(reverse("calendar")+"?dia="+activity.fecha.isoformat())
