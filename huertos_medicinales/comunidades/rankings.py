"""Clasificación calculada con la puntuación comunitaria existente."""

from .models import Comunidad


def standings(user):
    groups = list(
        Comunidad.objects.filter(estado=Comunidad.Estado.PUBLICADA).order_by(
            "nombre",
            "pk",
        ),
    )
    rows = []
    for group in groups:
        members = list(
            group.miembros.filter(estado="aprobada").select_related("usuario"),
        )
        rows.append(
            {
                "group": group,
                "xp": sum(member.puntos for member in members),
                "members": len(members),
                "mine": user.is_authenticated
                and (
                    group.responsable_id == user.pk
                    or any(m.usuario_id == user.pk for m in members)
                ),
            },
        )
    rows.sort(
        key=lambda row: (
            -row["xp"],
            row["group"].nombre.casefold(),
            str(row["group"].pk),
        ),
    )
    previous = None
    for index, row in enumerate(rows, 1):
        row["position"] = (
            previous["position"] if previous and previous["xp"] == row["xp"] else index
        )
        row["slot"] = index
        previous = row
    for row in rows:
        row["tied"] = sum(other["xp"] == row["xp"] for other in rows) > 1
    return rows
