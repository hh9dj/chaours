from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from manim import (
    BOLD,
    DOWN,
    LEFT,
    MEDIUM,
    NORMAL,
    RIGHT,
    UP,
    Create,
    FadeOut,
    ImageMobject,
    Rectangle,
    Scene,
    SurroundingRectangle,
    Text,
    VGroup,
    register_font,
)

NOIR_CARBONE = "#000000"
BLANC_CRAIE = "#F9F9F9"
CUIVRE_POLI = "#845400"
CUIVRE_CLAIR = "#FFB95C"
CUIVRE_CONTAINER = "#E5A040"
SABLE = "#FFDDB7"
CUIVRE_PROFOND = "#5D3A00"

WHITE_PURE = "#FFFFFF"
CRAIE_1 = "#F3F3F3"
CRAIE_2 = "#EEEEEE"
CRAIE_3 = "#E8E8E8"
CRAIE_4 = "#E2E2E2"
BROUILLARD = "#DADADA"
CARBONE_MID = "#303030"

CHARCOAL = "#1B1B1B"
ON_SURFACE_VAR = "#514536"
TEXT_ON_DARK = "#F1F1F1"
TEXT_ON_DARK_2 = "#A8A8A8"
OUTLINE = "#847564"
OUTLINE_VARIANT = "#D6C3B1"

ERROR = "#BA1A1A"
ERROR_CONTAINER = "#FFDAD6"
ON_ERROR_CONT = "#93000A"

INDIGO = {
    "light": "#E9DDFF",
    "medium": "#BA9EFE",
    "primary": "#4B3088",
    "dark": "#23005C",
}
TERRE = {
    "light": "#FFDDB7",
    "medium": "#C08B5C",
    "primary": "#6B4226",
    "dark": "#3D2100",
}
EMERAUDE = {
    "light": "#C8F5D6",
    "medium": "#6BC68F",
    "primary": "#2E8B57",
    "dark": "#0D5A2E",
}
OLIVE = {
    "light": "#E8F0C7",
    "medium": "#B0BF69",
    "primary": "#697722",
    "dark": "#414C0B",
}
AZUR = {
    "light": "#D6E8FF",
    "medium": "#88B8F5",
    "primary": "#4A90E2",
    "dark": "#1A4E8A",
}
CANARD = {
    "light": "#95F1FF",
    "medium": "#5DBBC9",
    "primary": "#007E8B",
    "dark": "#004F57",
}
PRUNE = {
    "light": "#FCD9F3",
    "medium": "#BF69A9",
    "primary": "#682757",
    "dark": "#411035",
}
ROSE = {
    "light": "#FFD9E5",
    "medium": "#F2A0BD",
    "primary": "#D66C93",
    "dark": "#8B2E52",
}
OCRE = {
    "light": "#FFF0D6",
    "medium": "#F2C878",
    "primary": "#E5A040",
    "dark": "#845400",
}
SOUVERAIN = {
    "light": "#D4E4F2",
    "medium": "#6A9AC4",
    "primary": "#2C5F8A",
    "dark": "#142D45",
}

TITRE = "Epilogue"
CORPS = "Epilogue"
LABEL = "Space Grotesk"

RACINE = Path(__file__).resolve().parent
DOSSIER_POLICES = RACINE / "fonts"
POLICE_EPILOGUE = DOSSIER_POLICES / "Epilogue[wght].ttf"
POLICE_SPACE_GROTESK = DOSSIER_POLICES / "SpaceGrotesk[wght].ttf"
LOGO_SFEIR = RACINE / "assets" / "logo-sfeir-grey.png"

ROLES = {
    "step": (CRAIE_1, CHARCOAL),
    "step_alt": (CRAIE_2, CHARCOAL),
    "manual": (SABLE, CUIVRE_PROFOND),
    "blocking": (ERROR_CONTAINER, ON_ERROR_CONT),
    "validated": (EMERAUDE["light"], EMERAUDE["dark"]),
    "neutral": (WHITE_PURE, CHARCOAL),
}

ALERTES_COULEURS = {
    "NEUTRONIC_ANOMALY": (ERROR_CONTAINER, ON_ERROR_CONT, ERROR),
    "REMIT_UMM": (PRUNE["light"], PRUNE["dark"], PRUNE["primary"]),
    "RTE_DEFICIT": (OCRE["light"], OCRE["dark"], OCRE["primary"]),
    "SPOT_BELOW_USAGE_VALUE": (AZUR["light"], AZUR["dark"], AZUR["primary"]),
}

ALERTES_LIBELLES = {
    "NEUTRONIC_ANOMALY": "JEPP",
    "REMIT_UMM": "REMIT",
    "RTE_DEFICIT": "RÉSEAU",
    "SPOT_BELOW_USAGE_VALUE": "MARCHÉ",
}


def verifier_polices() -> None:
    for chemin in (POLICE_EPILOGUE, POLICE_SPACE_GROTESK):
        if not chemin.exists():
            raise FileNotFoundError(f"Police SFEIR introuvable : {chemin}")


@contextmanager
def polices_sfeir() -> Iterator[None]:
    verifier_polices()
    with register_font(str(POLICE_EPILOGUE)), register_font(str(POLICE_SPACE_GROTESK)):
        yield


def sfeir_text(
    contenu: str,
    taille: float = 22,
    couleur: str = CHARCOAL,
    police: str = CORPS,
    poids: str = NORMAL,
) -> Text:
    return Text(
        contenu,
        font=police,
        font_size=taille,
        color=couleur,
        weight=poids,
    )


def sfeir_title(
    contenu: str,
    taille: float = 34,
    couleur: str = CHARCOAL,
) -> Text:
    return sfeir_text(contenu, taille, couleur, TITRE, BOLD)


def sfeir_body(
    contenu: str,
    taille: float = 21,
    couleur: str = CHARCOAL,
) -> Text:
    return sfeir_text(contenu, taille, couleur, CORPS, NORMAL)


def sfeir_label(
    contenu: str,
    taille: float = 17,
    couleur: str = ON_SURFACE_VAR,
    poids: str = MEDIUM,
) -> Text:
    return sfeir_text(contenu, taille, couleur, LABEL, poids)


def sfeir_eyebrow(contenu: str, taille: float = 16) -> Text:
    return sfeir_text(contenu.upper(), taille, CUIVRE_POLI, LABEL, MEDIUM)


def copper_rule(largeur: float = 0.35) -> Rectangle:
    return (
        Rectangle(width=largeur, height=0.025)
        .set_fill(CUIVRE_CONTAINER, 1)
        .set_stroke(width=0)
    )


def sfeir_header(contenu_eyebrow: str, contenu_titre: str) -> VGroup:
    barre = copper_rule()
    eyebrow = sfeir_eyebrow(contenu_eyebrow)
    ligne = VGroup(barre, eyebrow).arrange(RIGHT, buff=0.15)
    titre = sfeir_title(contenu_titre)
    titre_complet = VGroup(titre)
    titre_complet.next_to(ligne, DOWN, aligned_edge=LEFT, buff=0.13)
    filet = (
        Rectangle(width=12.9, height=0.012).set_fill("#EFE7DC", 1).set_stroke(width=0)
    )
    filet.next_to(titre_complet, DOWN, aligned_edge=LEFT, buff=0.22)
    groupe = VGroup(ligne, titre_complet, filet)
    groupe.to_corner(UP + LEFT, buff=0.55)
    return groupe


def sfeir_bloc(
    lignes: list[str],
    taille: float = 20,
    couleur: str = CHARCOAL,
    police: str = CORPS,
    largeur_max: float = 5.0,
) -> VGroup:
    groupe = VGroup(
        *[sfeir_text(ligne, taille, couleur, police) for ligne in lignes]
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    if groupe.width > largeur_max:
        groupe.scale_to_fit_width(largeur_max)
    return groupe


def sfeir_card(
    numero: str,
    titre: str,
    sous_titre: str,
    largeur: float = 3.7,
    hauteur: float = 1.35,
) -> VGroup:
    rect = (
        Rectangle(width=largeur, height=hauteur)
        .set_fill(CRAIE_1, 1)
        .set_stroke(width=0)
    )
    accent = (
        Rectangle(width=0.42, height=0.035)
        .set_fill(CUIVRE_CONTAINER, 1)
        .set_stroke(width=0)
    )
    accent.next_to(rect.get_corner(UP + LEFT), DOWN + RIGHT, buff=0.16)
    accent.align_to(rect, LEFT)
    accent.shift(RIGHT * 0.18)
    num = sfeir_label(numero, 20, CUIVRE_POLI, BOLD)
    nom = sfeir_title(titre, 20)
    detail = sfeir_label(sous_titre, 14, ON_SURFACE_VAR, NORMAL)
    contenu = VGroup(num, nom, detail).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
    contenu.move_to(
        rect.get_corner(UP + LEFT) + (RIGHT + DOWN) * 0.22, aligned_edge=UP + LEFT
    )
    return VGroup(rect, accent, contenu)


def sfeir_badge(
    type_alerte: str,
    texte: str,
    taille: float = 17,
) -> VGroup:
    fond, encre, bord = ALERTES_COULEURS[type_alerte]
    label = sfeir_label(texte, taille, encre, BOLD)
    rect = Rectangle(width=label.width + 0.5, height=label.height + 0.28)
    rect.set_fill(fond, 1).set_stroke(bord, 2)
    label.move_to(rect)
    barre = Rectangle(width=0.07, height=rect.height)
    barre.set_fill(bord, 1).set_stroke(width=0)
    barre.align_to(rect, LEFT)
    return VGroup(rect, barre, label)


def sfeir_legend_item(type_alerte: str, libelle: str, taille: float = 15) -> VGroup:
    fond, encre, bord = ALERTES_COULEURS[type_alerte]
    carre = Rectangle(width=0.17, height=0.17)
    carre.set_fill(fond, 1).set_stroke(bord, 1.5)
    texte = sfeir_label(libelle, taille, encre, MEDIUM)
    return VGroup(carre, texte).arrange(RIGHT, buff=0.12)


def sfeir_logo(hauteur: float = 0.28) -> ImageMobject:
    logo = ImageMobject(str(LOGO_SFEIR))
    logo.scale_to_fit_height(hauteur)
    return logo


class SfeirLightScene(Scene):
    def setup(self) -> None:
        super().setup()
        self.camera.background_color = BLANC_CRAIE

    def surligner(
        self, mobject, couleur: str = CUIVRE_POLI, buff: float = 0.05
    ) -> None:
        cadre = SurroundingRectangle(
            mobject,
            color=couleur,
            buff=buff,
            stroke_width=3,
            corner_radius=0,
        )
        self.play(Create(cadre), run_time=0.22)
        self.play(FadeOut(cadre), run_time=0.22)
