import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))

from example_data import (
    ALERTES_TOTAL,
    DEMANDE_MWH,
    ENERGIE_MWH,
    FACTEURS_DEMANDES,
    FACTEURS_MODULES,
    FACTEURS_REELS,
    HORIZON,
    JEPP_RESTANT,
    JOURS,
    JOURS_DEFICIT,
    MATRICE_ALERTES,
    OFFRE_MWH,
    TRANCHES,
    format_factor,
    format_mwh,
)
from sfeir_theme import (
    ALERTES_COULEURS,
    ALERTES_LIBELLES,
    CHARCOAL,
    CRAIE_1,
    CUIVRE_POLI,
    CUIVRE_PROFOND,
    ERROR,
    ERROR_CONTAINER,
    LABEL,
    OCRE,
    ON_ERROR_CONT,
    ON_SURFACE_VAR,
    OUTLINE_VARIANT,
    PRUNE,
    SABLE,
    WHITE_PURE,
    SfeirLightScene,
    polices_sfeir,
    sfeir_badge,
    sfeir_bloc,
    sfeir_body,
    sfeir_card,
    sfeir_header,
    sfeir_label,
    sfeir_legend_item,
    sfeir_logo,
    sfeir_text,
)

FOND_MODULATION = SABLE
ENCRE_MODULATION = CUIVRE_PROFOND
FOND_ARRET = ERROR_CONTAINER
ENCRE_ARRET = ON_ERROR_CONT
FOND_ENERGIE = CRAIE_1
FOND_DEFICIT = ERROR_CONTAINER


class MatrixGrid(VGroup):
    def __init__(
        self,
        valeurs,
        labels_lignes: list[str] | None = None,
        labels_colonnes: list[str] | None = None,
        largeur: float = 0.9,
        hauteur: float = 0.62,
        taille: float = 17,
        colonnes_en_bas: bool = False,
        formateur=format_factor,
    ):
        super().__init__()
        self.largeur_cellule = largeur
        self.hauteur_cellule = hauteur
        self.taille_police = taille
        self.formateur = formateur
        self.labels_lignes = []
        self.cells = []
        self.rects = []
        self.texts = []

        lignes = len(valeurs)

        for index_ligne, ligne in enumerate(valeurs):
            cellules = []
            rects = []
            texts = []
            for index_colonne, valeur in enumerate(ligne):
                rect = Rectangle(
                    width=largeur,
                    height=hauteur,
                    stroke_color=OUTLINE_VARIANT,
                    stroke_width=1.1,
                    stroke_opacity=0.55,
                    fill_color=WHITE_PURE,
                    fill_opacity=1.0,
                )
                label = sfeir_label(
                    formateur(float(valeur)),
                    taille,
                    CHARCOAL,
                    MEDIUM,
                )
                cell = VGroup(rect, label)
                cell.move_to([index_colonne * largeur, -index_ligne * hauteur, 0])
                self.add(cell)
                cellules.append(cell)
                rects.append(rect)
                texts.append(label)
            self.cells.append(cellules)
            self.rects.append(rects)
            self.texts.append(texts)

        if labels_lignes is not None:
            for index_ligne, label in enumerate(labels_lignes):
                label_mob = sfeir_label(label, 15, ON_SURFACE_VAR, NORMAL)
                label_mob.next_to(self.cells[index_ligne][0], LEFT, buff=0.18)
                self.add(label_mob)
                self.labels_lignes.append(label_mob)

        if labels_colonnes is not None:
            for index_colonne, label in enumerate(labels_colonnes):
                label_mob = sfeir_label(label, 14, ON_SURFACE_VAR, NORMAL)
                if colonnes_en_bas:
                    label_mob.next_to(
                        self.cells[lignes - 1][index_colonne],
                        DOWN,
                        buff=0.14,
                    )
                else:
                    label_mob.next_to(
                        self.cells[0][index_colonne],
                        UP,
                        buff=0.14,
                    )
                self.add(label_mob)

    def cellule(self, ligne: int, colonne: int):
        return self.cells[ligne][colonne]

    def ligne(self, ligne: int) -> VGroup:
        return VGroup(*self.cells[ligne])

    def colonne(self, colonne: int) -> VGroup:
        return VGroup(*[self.cells[ligne][colonne] for ligne in range(len(self.cells))])

    def cadre_ligne(
        self,
        ligne: int,
        colonne_debut: int,
        colonne_fin: int,
        couleur: str,
    ) -> SurroundingRectangle:
        return SurroundingRectangle(
            VGroup(*self.cells[ligne][colonne_debut:colonne_fin]),
            color=couleur,
            buff=0.04,
            stroke_width=3,
            corner_radius=0,
        )

    def cadre_colonne(self, colonne: int, couleur: str) -> SurroundingRectangle:
        return SurroundingRectangle(
            self.colonne(colonne),
            color=couleur,
            buff=0.04,
            stroke_width=3,
            corner_radius=0,
        )

    def animation_valeur(
        self,
        ligne: int,
        colonne: int,
        valeur: float | str,
        remplissage: str | None = None,
        couleur_texte: str | None = None,
    ) -> AnimationGroup:
        contenu = valeur if isinstance(valeur, str) else self.formateur(float(valeur))
        nouveau = sfeir_label(
            contenu,
            self.taille_police,
            couleur_texte or CHARCOAL,
            MEDIUM,
        ).move_to(self.texts[ligne][colonne])
        if remplissage is not None:
            self.rects[ligne][colonne].set_fill(remplissage, opacity=1.0)
        return AnimationGroup(Transform(self.texts[ligne][colonne], nouveau))

    def animation_ligne_opacite(self, ligne: int, opacite: float) -> AnimationGroup:
        animations: list[Animation] = [
            cellule.animate.set_opacity(opacite) for cellule in self.cells[ligne]
        ]
        if self.labels_lignes:
            animations.append(self.labels_lignes[ligne].animate.set_opacity(opacite))
        return AnimationGroup(*animations)

    def cacher_ligne(self, ligne: int) -> None:
        for cellule in self.cells[ligne]:
            cellule.set_opacity(0)
        if self.labels_lignes:
            self.labels_lignes[ligne].set_opacity(0)


class PipelineScene(SfeirLightScene):
    def construct(self):
        with polices_sfeir():
            self.vue_ensemble()
            self.matrice_nominale()
            self.modulation()
            self.arrets()
            self.jepp()
            self.energie()
            self.agregation()
            self.alertes()

    def entete(self, eyebrow: str, titre: str) -> VGroup:
        groupe = sfeir_header(eyebrow, titre)
        self.play(
            FadeIn(groupe[0], shift=RIGHT * 0.1),
            FadeIn(groupe[1], shift=DOWN * 0.08),
            Create(groupe[2]),
        )
        return groupe

    def transition(self) -> None:
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.45)
        self.clear()

    def grille_facteurs(
        self,
        valeurs,
        labels_lignes: list[str] | None = None,
        colonnes_en_bas: bool = False,
        largeur: float = 0.85,
        hauteur: float = 0.62,
        taille: float = 16,
        formateur=format_factor,
        position=LEFT * 3.2 + DOWN * 0.35,
    ) -> MatrixGrid:
        grille = MatrixGrid(
            valeurs,
            labels_lignes=labels_lignes,
            labels_colonnes=JOURS,
            largeur=largeur,
            hauteur=hauteur,
            taille=taille,
            colonnes_en_bas=colonnes_en_bas,
            formateur=formateur,
        )
        grille.move_to(position)
        return grille

    def vue_ensemble(self) -> None:
        self.entete("01 · PIPELINE", "Le pipeline de simulation")
        cartes = [
            sfeir_card(
                "01",
                "Facteur de charge nominal",
                "100 % de la puissance nominale",
            ),
            sfeir_card(
                "02",
                "Modulation manuelle",
                "F[i, début:fin] = facteur",
            ),
            sfeir_card("03", "Arrêt", "F[i, mask] = 0"),
            sfeir_card("04", "JEPP", "cumsum et déplétion"),
            sfeir_card("05", "Énergie", "E = F × P × 24"),
            sfeir_card("06", "Agrégation", "O = ΣE et déficit"),
        ]
        rangee_1 = VGroup(*cartes[:3]).arrange(RIGHT, buff=0.28)
        rangee_2 = VGroup(*cartes[3:]).arrange(RIGHT, buff=0.28)
        grille = VGroup(rangee_1, rangee_2).arrange(DOWN, buff=0.28)
        grille.move_to(DOWN * 0.25)
        logo = sfeir_logo(0.3).to_corner(DOWN + LEFT, buff=0.55)
        pied = sfeir_label(
            "DÉMONSTRATEUR CHAOURS",
            12,
            ON_SURFACE_VAR,
            MEDIUM,
        ).to_corner(DOWN + RIGHT, buff=0.55)

        self.play(FadeIn(logo), FadeIn(pied))
        self.play(
            LaggedStart(
                *[FadeIn(carte, shift=UP * 0.15) for carte in grille],
                lag_ratio=0.12,
            ),
            run_time=1.6,
        )
        self.wait(2.2)
        self.transition()

    def matrice_nominale(self) -> None:
        self.entete("02 · PRODUCTION", "Facteur de charge nominal")
        labels = [
            f"{spec.identifiant}   {spec.puissance_mw:.0f} MW" for spec in TRANCHES
        ]
        valeurs = [[1.0 for _ in range(HORIZON)] for _ in TRANCHES]
        grille = self.grille_facteurs(valeurs, labels)
        code = sfeir_bloc(
            ["F = np.ones((3, 7))"],
            23,
            CUIVRE_POLI,
            LABEL,
        ).move_to([1.5, 1.55, 0], aligned_edge=LEFT)
        note = sfeir_bloc(
            [
                "Une ligne par tranche.",
                "Une colonne par jour.",
                "Chaque tranche démarre à 100 %.",
            ],
            19,
            ON_SURFACE_VAR,
            largeur_max=5.0,
        ).next_to(code, DOWN, buff=0.4, aligned_edge=LEFT)
        legende = sfeir_label(
            "100 % DE LA PUISSANCE NOMINALE",
            13,
            ON_SURFACE_VAR,
            MEDIUM,
        )
        legende.next_to(grille, DOWN, buff=0.45)

        self.play(FadeIn(grille, shift=UP * 0.15))
        self.play(Write(code))
        self.play(FadeIn(note, shift=UP * 0.1), FadeIn(legende, shift=UP * 0.1))
        self.wait(1.8)
        self.transition()

    def modulation(self) -> None:
        self.entete("03 · MODULATION", "Modulation manuelle")
        labels = [
            f"{spec.identifiant}   {spec.puissance_mw:.0f} MW" for spec in TRANCHES
        ]
        valeurs = [[1.0 for _ in range(HORIZON)] for _ in TRANCHES]
        grille = self.grille_facteurs(valeurs, labels)
        code = sfeir_bloc(
            ["F[i, début:fin] = facteur", "0.0 ≤ facteur ≤ 1.0"],
            21,
            CUIVRE_POLI,
            LABEL,
        ).move_to([1.5, 1.55, 0], aligned_edge=LEFT)
        statut = sfeir_body("Choisissez une fenêtre.", 20, CUIVRE_POLI)
        statut.next_to(code, DOWN, buff=0.45, aligned_edge=LEFT)
        note = sfeir_bloc(
            [
                "La modulation baisse la puissance.",
                "Elle ne modifie pas le calendrier.",
            ],
            18,
            ON_SURFACE_VAR,
            largeur_max=5.0,
        ).next_to(statut, DOWN, buff=0.38, aligned_edge=LEFT)

        self.play(FadeIn(grille, shift=UP * 0.15))
        self.play(Write(code), FadeIn(statut), FadeIn(note))

        for index, spec in enumerate(TRANCHES):
            for debut, fin, facteur in spec.modulations:
                cadre = grille.cadre_ligne(index, debut, fin, CUIVRE_POLI)
                nouveau_statut = sfeir_body(
                    f"{spec.identifiant}   J{debut}:J{fin}   →   {facteur:.2f}",
                    20,
                    CUIVRE_POLI,
                )
                nouveau_statut.move_to(statut, aligned_edge=LEFT)
                animations = [
                    grille.animation_valeur(
                        index,
                        jour,
                        facteur,
                        FOND_MODULATION,
                        ENCRE_MODULATION,
                    )
                    for jour in range(debut, fin)
                ]
                self.play(Create(cadre), Transform(statut, nouveau_statut))
                self.play(
                    AnimationGroup(*animations, lag_ratio=0.08),
                    run_time=0.8,
                )
                self.play(FadeOut(cadre))

        self.wait(1.2)
        self.transition()

    def arrets(self) -> None:
        self.entete("04 · ARRÊTS", "Arrêt de tranche")
        labels = [
            f"{spec.identifiant}   {spec.puissance_mw:.0f} MW" for spec in TRANCHES
        ]
        grille = self.grille_facteurs(FACTEURS_MODULES, labels)
        code = sfeir_bloc(
            ["mask[a:b] = True", "F[i, mask] = 0"],
            21,
            ERROR,
            LABEL,
        ).move_to([1.5, 1.55, 0], aligned_edge=LEFT)
        statut = sfeir_body("L'arrêt force la production à zéro.", 20, CHARCOAL)
        statut.next_to(code, DOWN, buff=0.45, aligned_edge=LEFT)
        note = sfeir_bloc(
            [
                "Appliqué après la modulation.",
                "L'arrêt gagne toujours.",
            ],
            18,
            ERROR,
            largeur_max=5.0,
        ).next_to(statut, DOWN, buff=0.38, aligned_edge=LEFT)

        self.play(FadeIn(grille, shift=UP * 0.15))
        self.play(Write(code), FadeIn(statut), FadeIn(note))

        for index, spec in enumerate(TRANCHES):
            for debut, fin in spec.arrets:
                cadre = grille.cadre_ligne(index, debut, fin, ERROR)
                nouveau_statut = sfeir_body(
                    f"{spec.identifiant}   arrêt J{debut}:J{fin}   →   0.00",
                    19,
                    ERROR,
                )
                nouveau_statut.move_to(statut, aligned_edge=LEFT)
                animations = [
                    grille.animation_valeur(
                        index,
                        jour,
                        0.0,
                        FOND_ARRET,
                        ENCRE_ARRET,
                    )
                    for jour in range(debut, fin)
                ]
                self.play(Create(cadre), Transform(statut, nouveau_statut))
                self.play(
                    AnimationGroup(*animations, lag_ratio=0.08),
                    run_time=0.7,
                )
                self.play(FadeOut(cadre))

        rappel = sfeir_body(
            "P2 J3 : la modulation donne 0.80, l'arrêt impose 0.00.",
            21,
            ERROR,
        ).move_to(DOWN * 2.85)
        self.play(FadeIn(rappel, shift=UP * 0.12))
        self.wait(1.6)
        self.transition()

    def jepp(self) -> None:
        self.entete("05 · JEPP", "Cycles et déplétion")
        cumsum_p1 = [1.0, 1.5, 2.0, 3.0, 3.0, 3.0, 1.0]
        valeurs = [
            list(FACTEURS_DEMANDES[0]),
            cumsum_p1,
            list(JEPP_RESTANT[0]),
        ]
        grille = MatrixGrid(
            valeurs,
            labels_lignes=["P1 demandé", "cumsum", "JEPP restant"],
            labels_colonnes=JOURS,
            largeur=0.88,
            hauteur=0.64,
            taille=17,
            colonnes_en_bas=True,
            formateur=format_factor,
        )
        grille.move_to([-2.8, -0.45, 0])
        grille.cacher_ligne(1)
        grille.cacher_ligne(2)

        cycle_1 = Brace(
            VGroup(*grille.cells[0][0:6]),
            UP,
            buff=0.08,
            color=CUIVRE_POLI,
        )
        label_cycle_1 = sfeir_label("cycle 1", 14, CUIVRE_POLI, MEDIUM)
        label_cycle_1.next_to(cycle_1, UP, buff=0.08)
        cycle_2 = Brace(
            grille.cells[0][6],
            UP,
            buff=0.08,
            color=CUIVRE_POLI,
        )
        label_cycle_2 = sfeir_label("cycle 2", 14, CUIVRE_POLI, MEDIUM)
        label_cycle_2.next_to(cycle_2, UP, buff=0.08)

        frontiere = DashedLine(
            grille.cellule(0, 5).get_right(),
            grille.cellule(2, 5).get_right(),
            color=OCRE["primary"],
            dash_length=0.08,
            stroke_width=3,
        )
        recharge = sfeir_label("recharge à J6", 13, OCRE["dark"], MEDIUM)
        recharge.next_to(grille.cellule(2, 6), DOWN, buff=0.55)

        code = sfeir_bloc(
            ["np.cumsum(F[0, 0:6])", "[1, 1.5, 2, 3, 3, 3]", "stock = 2.5"],
            20,
            CUIVRE_POLI,
            LABEL,
        ).move_to([1.5, 1.55, 0], aligned_edge=LEFT)
        statut = sfeir_body(
            "Le stock se consomme jour après jour.",
            18,
            ON_SURFACE_VAR,
        )
        statut.next_to(code, DOWN, buff=0.35, aligned_edge=LEFT)

        self.play(FadeIn(grille, shift=UP * 0.12))
        self.play(
            FadeIn(cycle_1),
            FadeIn(label_cycle_1),
            FadeIn(cycle_2),
            FadeIn(label_cycle_2),
            Create(frontiere),
            FadeIn(recharge),
        )
        self.play(Write(code), FadeIn(statut))

        self.play(grille.animation_ligne_opacite(1, 1))
        statut_2 = sfeir_body("J3 : 3.0 > 2.5", 20, ERROR)
        statut_2.move_to(statut, aligned_edge=LEFT)
        self.play(Transform(statut, statut_2))
        self.surligner(grille.cellule(1, 3), CUIVRE_POLI)
        self.play(
            grille.animation_valeur(
                0,
                3,
                0.5,
                FOND_ARRET,
                ENCRE_ARRET,
            )
        )
        self.play(grille.animation_ligne_opacite(2, 1))
        statut_3 = sfeir_body(
            "J3 : production limitée au stock restant.",
            18,
            ERROR,
        )
        statut_3.move_to(statut, aligned_edge=LEFT)
        self.play(Transform(statut, statut_3))
        self.surligner(grille.cellule(2, 3), ERROR)
        statut_4 = sfeir_body(
            "J4-J5 : arrêt. J6 : recharge.",
            17,
            CUIVRE_POLI,
        )
        statut_4.move_to(statut, aligned_edge=LEFT)
        self.play(Transform(statut, statut_4))
        self.surligner(grille.cellule(2, 6), CUIVRE_POLI)

        badge = sfeir_badge(
            "NEUTRONIC_ANOMALY",
            "NEUTRONIC_ANOMALY · P1 · J3",
            14,
        )
        badge.next_to(statut_4, DOWN, buff=0.45, aligned_edge=LEFT)
        note = sfeir_body(
            "Aucune baisse automatique.",
            14,
            ON_SURFACE_VAR,
        )
        note.next_to(badge, DOWN, buff=0.18, aligned_edge=LEFT)
        self.play(FadeIn(badge, shift=UP * 0.1), FadeIn(note))
        self.wait(1.8)
        self.transition()

    def energie(self) -> None:
        self.entete("06 · ÉNERGIE", "Énergie journalière")
        labels = [
            f"{spec.identifiant}   {spec.puissance_mw:.0f} MW" for spec in TRANCHES
        ]
        grille = self.grille_facteurs(
            FACTEURS_REELS,
            labels,
            largeur=0.88,
            hauteur=0.6,
            taille=14,
            position=LEFT * 3.0 + DOWN * 0.55,
        )
        code = sfeir_bloc(
            ["E = F × P × 24", "P = [1000, 1300, 900]"],
            21,
            CUIVRE_POLI,
            LABEL,
        ).move_to([1.5, 1.55, 0], aligned_edge=LEFT)
        statut = sfeir_body(
            "P est la puissance nominale en MW.",
            18,
            ON_SURFACE_VAR,
        )
        statut.next_to(code, DOWN, buff=0.35, aligned_edge=LEFT)
        exemple = sfeir_body(
            "0.50 × 1 000 × 24 = 12 000 MWh",
            18,
            CUIVRE_POLI,
        )
        exemple.next_to(statut, DOWN, buff=0.3, aligned_edge=LEFT)
        note = sfeir_bloc(
            [
                "Le facteur de charge est multiplié",
                "par la puissance, puis par 24 heures.",
            ],
            17,
            ON_SURFACE_VAR,
            largeur_max=5.0,
        ).next_to(exemple, DOWN, buff=0.28, aligned_edge=LEFT)

        self.play(FadeIn(grille, shift=UP * 0.12))
        self.play(Write(code), FadeIn(statut), FadeIn(exemple), FadeIn(note))

        cadre = grille.cadre_colonne(1, CUIVRE_POLI)
        self.play(Create(cadre))
        self.wait(0.6)
        self.play(FadeOut(cadre))

        animations = []
        for index in range(len(TRANCHES)):
            for jour in range(HORIZON):
                animations.append(
                    grille.animation_valeur(
                        index,
                        jour,
                        format_mwh(ENERGIE_MWH[index][jour]),
                        FOND_ENERGIE,
                        CHARCOAL,
                    )
                )
        self.play(
            LaggedStart(*animations, lag_ratio=0.03),
            run_time=2.0,
        )

        badge = sfeir_badge("REMIT_UMM", "REMIT_UMM · 8 alertes", 14)
        badge.next_to(note, DOWN, buff=0.35, aligned_edge=LEFT)
        regle = sfeir_label("|ΔP| > 100 MW entre deux jours", 14, PRUNE["dark"])
        regle.next_to(badge, DOWN, buff=0.16, aligned_edge=LEFT)
        exemple_remit = sfeir_label("P2 J3 : -1 040 MW", 14, PRUNE["dark"])
        exemple_remit.next_to(regle, DOWN, buff=0.1, aligned_edge=LEFT)
        self.play(FadeIn(badge, shift=UP * 0.1), FadeIn(regle), FadeIn(exemple_remit))
        self.wait(1.8)
        self.transition()

    def agregation(self) -> None:
        self.entete("07 · AGRÉGATION", "Offre nationale et déficit")
        valeurs = [
            list(ENERGIE_MWH[0]),
            list(ENERGIE_MWH[1]),
            list(ENERGIE_MWH[2]),
            list(OFFRE_MWH),
            list(DEMANDE_MWH),
        ]
        grille = MatrixGrid(
            valeurs,
            labels_lignes=["P1", "P2", "P3", "Offre", "Demande"],
            labels_colonnes=JOURS,
            largeur=0.88,
            hauteur=0.5,
            taille=13,
            colonnes_en_bas=True,
            formateur=format_mwh,
        )
        grille.move_to([-2.8, -0.45, 0])
        grille.cacher_ligne(3)
        grille.cacher_ligne(4)

        code = sfeir_bloc(
            ["O = E.sum(axis=0)", "déficit = O < D"],
            21,
            ERROR,
            LABEL,
        ).move_to([1.5, 1.75, 0], aligned_edge=LEFT)
        statut = sfeir_body(
            "Somme des trois tranches, jour par jour.",
            17,
            ON_SURFACE_VAR,
        )
        statut.next_to(code, DOWN, buff=0.32, aligned_edge=LEFT)
        calcul = sfeir_body(
            "12 000 + 24 960 + 21 600 = 58 560",
            16,
            CUIVRE_POLI,
        )
        calcul.next_to(statut, DOWN, buff=0.28, aligned_edge=LEFT)
        note = sfeir_bloc(
            [
                "Si l'offre est inférieure",
                "à la demande, le jour est en déficit.",
            ],
            16,
            ERROR,
            largeur_max=5.0,
        ).next_to(calcul, DOWN, buff=0.3, aligned_edge=LEFT)

        self.play(FadeIn(grille, shift=UP * 0.12))
        self.play(Write(code), FadeIn(statut), FadeIn(note))
        cadre = grille.cadre_colonne(1, CUIVRE_POLI)
        self.play(Create(cadre), FadeIn(calcul))
        self.wait(0.6)
        self.play(FadeOut(cadre))

        self.play(grille.animation_ligne_opacite(3, 1))
        statut_2 = sfeir_body("L'offre nationale est calculée.", 17, CUIVRE_POLI)
        statut_2.move_to(statut, aligned_edge=LEFT)
        self.play(Transform(statut, statut_2))
        self.play(grille.animation_ligne_opacite(4, 1))
        statut_3 = sfeir_body("On compare avec la demande.", 17, OCRE["dark"])
        statut_3.move_to(statut, aligned_edge=LEFT)
        self.play(Transform(statut, statut_3))

        cadres = []
        for jour in JOURS_DEFICIT:
            cadres.append(
                SurroundingRectangle(
                    VGroup(grille.cellule(3, jour), grille.cellule(4, jour)),
                    color=ERROR,
                    buff=0.02,
                    stroke_width=3,
                    corner_radius=0,
                )
            )
        animations = []
        for jour in JOURS_DEFICIT:
            animations.append(
                grille.animation_valeur(
                    3,
                    jour,
                    format_mwh(OFFRE_MWH[jour]),
                    FOND_DEFICIT,
                    ENCRE_ARRET,
                )
            )
            animations.append(
                grille.animation_valeur(
                    4,
                    jour,
                    format_mwh(DEMANDE_MWH[jour]),
                    FOND_DEFICIT,
                    ENCRE_ARRET,
                )
            )
        self.play(
            LaggedStart(*animations, lag_ratio=0.05),
            *[Create(cadre) for cadre in cadres],
        )
        statut_4 = sfeir_body(
            "Déficit national : J1, J2, J3 et J4.",
            19,
            ERROR,
        )
        statut_4.move_to(statut, aligned_edge=LEFT)
        self.play(Transform(statut, statut_4))

        badge = sfeir_badge("RTE_DEFICIT", "RTE_DEFICIT · J1-J4", 14)
        badge.next_to(note, DOWN, buff=0.35, aligned_edge=LEFT)
        self.play(FadeIn(badge, shift=UP * 0.1))
        self.wait(1.8)
        self.transition()

    def alertes(self) -> None:
        self.entete("08 · ALERTES", "Alertes")
        types = (
            "NEUTRONIC_ANOMALY",
            "REMIT_UMM",
            "RTE_DEFICIT",
            "SPOT_BELOW_USAGE_VALUE",
        )
        valeurs = [list(MATRICE_ALERTES[type_alerte]) for type_alerte in types]
        grille = MatrixGrid(
            valeurs,
            labels_lignes=[ALERTES_LIBELLES[t] for t in types],
            labels_colonnes=JOURS,
            largeur=0.88,
            hauteur=0.62,
            taille=17,
            colonnes_en_bas=True,
            formateur=lambda valeur: "·" if int(valeur) == 0 else str(int(valeur)),
        )
        grille.move_to([-2.9, -0.35, 0])

        for index, type_alerte in enumerate(types):
            fond, encre, _ = ALERTES_COULEURS[type_alerte]
            for jour in range(HORIZON):
                if int(MATRICE_ALERTES[type_alerte][jour]) > 0:
                    grille.rects[index][jour].set_fill(fond, 1)
                    nouveau = sfeir_label(
                        str(int(MATRICE_ALERTES[type_alerte][jour])),
                        18,
                        encre,
                        BOLD,
                    ).move_to(grille.texts[index][jour])
                    grille.texts[index][jour].become(nouveau)

        stat_num = sfeir_text(str(ALERTES_TOTAL), 76, CUIVRE_POLI, LABEL, BOLD)
        stat_label = sfeir_label(
            f"ALERTES SUR {HORIZON} JOURS",
            13,
            ON_SURFACE_VAR,
            MEDIUM,
        )
        stat_groupe = VGroup(stat_num, stat_label).arrange(
            DOWN, aligned_edge=LEFT, buff=0.05
        )
        stat_groupe.move_to([1.6, 1.9, 0], aligned_edge=LEFT)
        legende = VGroup(
            *[
                sfeir_legend_item(
                    type_alerte,
                    f"{type_alerte} · {sum(MATRICE_ALERTES[type_alerte])}",
                    13,
                )
                for type_alerte in types
            ]
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        legende.move_to([1.6, 0.4, 0], aligned_edge=LEFT)
        if legende.width > 5.1:
            legende.scale_to_fit_width(5.1)

        self.play(FadeIn(grille, shift=UP * 0.12))
        self.play(FadeIn(stat_groupe, shift=UP * 0.1))
        self.play(
            LaggedStart(
                *[FadeIn(item, shift=RIGHT * 0.1) for item in legende],
                lag_ratio=0.1,
            )
        )
        self.wait(1.4)

        cadre = grille.cadre_colonne(3, CUIVRE_POLI)
        self.play(Create(cadre))
        self.wait(0.8)

        details = VGroup(
            sfeir_body("J3 · 5 alertes", 20, CUIVRE_POLI),
            sfeir_legend_item("NEUTRONIC_ANOMALY", "JEPP épuisé · P1", 14),
            sfeir_legend_item("REMIT_UMM", "REMIT · P2 -1 040 MW · P3 -360 MW", 14),
            sfeir_legend_item("RTE_DEFICIT", "Déficit · offre < demande", 14),
            sfeir_legend_item(
                "SPOT_BELOW_USAGE_VALUE",
                "Spot < valeur d'usage · 70 < 80 €/MWh",
                14,
            ),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        details.move_to([1.6, 0.1, 0], aligned_edge=LEFT)
        if details.width > 5.2:
            details.scale_to_fit_width(5.2)
        self.play(FadeOut(legende), FadeIn(details, shift=UP * 0.1))
        self.wait(1.2)

        message = sfeir_body(
            "Le moteur alerte, l'utilisateur arbitre.",
            20,
            CHARCOAL,
        )
        message.next_to(details, DOWN, buff=0.45, aligned_edge=LEFT)
        if message.width > 5.2:
            message.scale_to_fit_width(5.2)
        self.play(FadeIn(message, shift=UP * 0.1))
        logo = sfeir_logo(0.3).to_corner(DOWN + LEFT, buff=0.55)
        final = sfeir_label(
            "SFEIR · DÉMONSTRATEUR CHAOURS",
            13,
            ON_SURFACE_VAR,
            MEDIUM,
        ).to_corner(DOWN + RIGHT, buff=0.55)
        self.play(FadeIn(logo), FadeIn(final))
        self.wait(1.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.0)
