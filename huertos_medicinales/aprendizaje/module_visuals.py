from pathlib import Path

from django.conf import settings

# Shared artwork for module covers and chapter cards.
COVERS = {
    1: "images/huertos/login-garden.png",
    2: "images/huertos/plantas/menta.png",
    3: "images/huertos/comunidad-brote.png",
    4: "images/huertos/plantas/romero.png",
    5: "images/huertos/plantas/calendula.png",
    6: "images/huertos/terraza-ilustrada.png",
}


def module_cover(number):
    return COVERS.get(number, "images/huertos/botanica-hero-v2.png")


def chapter_cover(chapter):

    special = {
        1: "plantas/manzanilla.png",
        2: "plantas/menta.png",
        3: "comunidad-brote.png",
        4: "terraza-ilustrada.png",
        14: "plantas/menta.png",
        20: "plantas/calendula.png",
    }
    if chapter.numero in special:
        return "images/huertos/" + special[chapter.numero]
    asset = f"images/educacion/capitulo-{chapter.numero}.svg"
    if (Path(settings.BASE_DIR) / "huertos_medicinales/static" / asset).exists():
        return asset
    return module_cover(chapter.bloque.numero)
