"""Fixtures compartidos por las pruebas del foro y de las comunidades."""

from datetime import date

import pytest

from .models import Comunidad
from .models import Miembro
from .models import PerfilComunitario
from .models import Pregunta
from .models import Respuesta


@pytest.fixture
def forum(django_user_model):
    users = []
    for name in ("owner", "member", "outsider"):
        u = django_user_model.objects.create_user(
            email=name + "@example.invalid",
            name=name,
            fecha_nacimiento=date(1990, 1, 1),
            genero="otro",
            telefono="0990000000",
            direccion="Ibarra",
        )
        PerfilComunitario.objects.create(usuario=u, nombre=name, visible=True)
        users.append(u)
    owner, member, outsider = users
    group = Comunidad.objects.create(
        responsable=owner,
        nombre="Semillas compartidas",
        descripcion="Cultivamos juntos",
        grupo_virtual=True,
        estado="publicada",
    )
    membership = Miembro.objects.create(
        usuario=member,
        comunidad=group,
        fecha_nacimiento=member.fecha_nacimiento,
        estado="aprobada",
    )
    private = Pregunta.objects.create(
        autor=owner,
        comunidad=group,
        visibilidad="privado",
        titulo="Titulo exclusivo reservado",
        contenido="Contenido secreto del grupo",
        categoria="cultivo",
        huella="private",
    )
    public = Pregunta.objects.create(
        autor=owner,
        comunidad=group,
        titulo="Pregunta abierta",
        contenido="Conversación pública",
        categoria="cultivo",
        huella="public",
    )
    answer = Respuesta.objects.create(
        autor=member,
        pregunta=private,
        contenido="Comentario privado exclusivo",
        huella="secret",
    )
    return owner, member, outsider, group, membership, private, public, answer
