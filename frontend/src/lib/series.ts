import { analyserSerie, formaterSerie } from './format'

export type ModeSerie =
  | 'constante'
  | 'uniforme'
  | 'normale'
  | 'gaussienne'
  | 'courbe'
  | 'manuelle'

export interface EtatSerie {
  mode: ModeSerie
  constante: number
  uniformeMinimum: number
  uniformeMaximum: number
  normaleMoyenne: number
  normaleEcartType: number
  gaussienneBase: number
  gaussiennePic: number
  gaussienneJourPic: number
  gaussienneLargeur: number
  courbe: number[]
  manuelle: string
  graine: number
}

export interface ResultatSerie {
  valeurs: number[]
  erreur: string | null
}

export interface ResumeSerie {
  minimum: number
  maximum: number
  moyenne: number
}

const NOMBRE_POINTS_COURBE = 12

function valeursFinies(valeurs: number[]): number[] {
  return valeurs.filter((valeur) => Number.isFinite(valeur))
}

function moyenne(valeurs: number[]): number {
  if (valeurs.length === 0) return 0
  return valeurs.reduce((somme, valeur) => somme + valeur, 0) / valeurs.length
}

function ecartType(valeurs: number[]): number {
  if (valeurs.length === 0) return 0
  const centre = moyenne(valeurs)
  const variance =
    valeurs.reduce((somme, valeur) => somme + (valeur - centre) ** 2, 0) /
    valeurs.length
  return Math.sqrt(variance)
}

export function resumerSerie(valeurs: number[]): ResumeSerie {
  const finies = valeursFinies(valeurs)
  if (finies.length === 0) {
    return { minimum: 0, maximum: 0, moyenne: 0 }
  }
  return {
    minimum: Math.min(...finies),
    maximum: Math.max(...finies),
    moyenne: moyenne(finies),
  }
}

export function creerGraine(): number {
  return Math.floor(Math.random() * 0xffffffff) >>> 0
}

export function creerAleatoire(graine: number): () => number {
  let etat = (Math.floor(graine) >>> 0) || 1
  return () => {
    etat = (etat + 0x6d2b79f5) | 0
    let valeur = Math.imul(etat ^ (etat >>> 15), 1 | etat)
    valeur = (valeur + Math.imul(valeur ^ (valeur >>> 7), 61 | valeur)) ^ valeur
    return ((valeur ^ (valeur >>> 14)) >>> 0) / 4294967296
  }
}

export function nombrePointsCourbe(horizonJours: number): number {
  const horizon = Math.floor(horizonJours)
  if (!Number.isFinite(horizon) || horizon <= 0) return 0
  return Math.min(NOMBRE_POINTS_COURBE, horizon)
}

export function echantillonnerPoints(
  valeurs: number[],
  horizonJours: number,
): number[] {
  const horizon = Math.max(1, Math.floor(horizonJours))
  const nombre = nombrePointsCourbe(horizon)
  if (nombre === 0) return []
  if (nombre === 1) return [valeurs[0] ?? 0]

  return Array.from({ length: nombre }, (_, index) => {
    const jour = Math.round((index * (horizon - 1)) / (nombre - 1))
    return valeurs[jour] ?? 0
  })
}

export function adapterPointsCourbe(
  points: number[],
  horizonJours: number,
): number[] {
  const nombre = nombrePointsCourbe(horizonJours)
  if (nombre === 0) return []
  if (points.length === 0) return Array.from({ length: nombre }, () => 0)
  if (points.length === nombre) return [...points]
  if (nombre === 1) return [moyenne(points)]

  return Array.from({ length: nombre }, (_, index) => {
    const position = (index * (points.length - 1)) / (nombre - 1)
    const gauche = Math.floor(position)
    const droite = Math.min(points.length - 1, gauche + 1)
    const fraction = position - gauche
    return points[gauche] + (points[droite] - points[gauche]) * fraction
  })
}

export function interpolerCourbe(
  points: number[],
  horizonJours: number,
): number[] {
  const horizon = Math.max(0, Math.floor(horizonJours))
  if (horizon === 0) return []
  if (points.length === 0) return Array.from({ length: horizon }, () => 0)
  if (points.length === 1) {
    return Array.from({ length: horizon }, () => points[0])
  }
  if (horizon === 1) return [points[0]]

  return Array.from({ length: horizon }, (_, jour) => {
    const position = (jour * (points.length - 1)) / (horizon - 1)
    const gauche = Math.floor(position)
    const droite = Math.min(points.length - 1, gauche + 1)
    const fraction = position - gauche
    return points[gauche] + (points[droite] - points[gauche]) * fraction
  })
}

function genererSerieConstante(
  horizonJours: number,
  valeur: number,
): number[] {
  const horizon = Math.max(0, Math.floor(horizonJours))
  return Array.from({ length: horizon }, () => valeur)
}

function genererSerieUniforme(options: {
  horizonJours: number
  minimum: number
  maximum: number
  graine: number
}): number[] {
  const horizon = Math.max(0, Math.floor(options.horizonJours))
  const aleatoire = creerAleatoire(options.graine)
  return Array.from(
    { length: horizon },
    () => options.minimum + (options.maximum - options.minimum) * aleatoire(),
  )
}

function genererSerieNormale(options: {
  horizonJours: number
  moyenne: number
  ecartType: number
  graine: number
}): number[] {
  const horizon = Math.max(0, Math.floor(options.horizonJours))
  if (options.ecartType === 0) {
    return Array.from({ length: horizon }, () => options.moyenne)
  }

  const aleatoire = creerAleatoire(options.graine)
  return Array.from({ length: horizon }, () => {
    const u1 = 1 - aleatoire()
    const u2 = aleatoire()
    const gaussien = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
    return options.moyenne + options.ecartType * gaussien
  })
}

function genererProfilGaussien(options: {
  horizonJours: number
  base: number
  pic: number
  jourPic: number
  largeur: number
}): number[] {
  const horizon = Math.max(0, Math.floor(options.horizonJours))
  return Array.from({ length: horizon }, (_, jour) => {
    const ecart = (jour - options.jourPic) / options.largeur
    return options.base + (options.pic - options.base) * Math.exp(-0.5 * ecart ** 2)
  })
}

function appliquerPlancher(
  valeurs: number[],
  plancher: number | null | undefined,
): number[] {
  if (plancher === null || plancher === undefined) return valeurs
  return valeurs.map((valeur) => Math.max(plancher, valeur))
}

function serieFinie(valeurs: number[]): boolean {
  return valeurs.every((valeur) => Number.isFinite(valeur))
}

function messageLongueur(obtenue: number, attendue: number): string {
  return `${obtenue} valeur${obtenue > 1 ? 's' : ''} saisie${obtenue > 1 ? 's' : ''}, ${attendue} attendue${attendue > 1 ? 's' : ''}.`
}

export function etatInitial(
  valeurs: number[],
  horizonJours: number,
): EtatSerie {
  const resume = resumerSerie(valeurs)
  const ecart = ecartType(valeursFinies(valeurs))
  const horizon = Math.max(1, Math.floor(horizonJours))
  const touteFinie =
    valeurs.length > 0 && valeurs.every((valeur) => Number.isFinite(valeur))
  const estConstante =
    touteFinie && valeurs.every((valeur) => valeur === valeurs[0])
  let jourPic = 0
  let pic = Number.NEGATIVE_INFINITY
  valeurs.forEach((valeur, jour) => {
    if (Number.isFinite(valeur) && valeur > pic) {
      pic = valeur
      jourPic = jour
    }
  })

  return {
    mode: estConstante ? 'constante' : 'manuelle',
    constante: estConstante ? valeurs[0] : resume.moyenne,
    uniformeMinimum: resume.minimum,
    uniformeMaximum: resume.maximum,
    normaleMoyenne: resume.moyenne,
    normaleEcartType: ecart > 0 ? ecart : 1,
    gaussienneBase: resume.minimum,
    gaussiennePic: Number.isFinite(pic) ? pic : resume.maximum,
    gaussienneJourPic: Math.min(jourPic, horizon - 1),
    gaussienneLargeur: Math.max(1, Math.round(horizon / 6)),
    courbe: echantillonnerPoints(valeurs, horizon),
    manuelle: formaterSerie(valeurs),
    graine: creerGraine(),
  }
}

export function construireSerie(
  etat: EtatSerie,
  horizonJours: number,
  options: { plancher?: number | null } = {},
): ResultatSerie {
  const horizon = Math.max(0, Math.floor(horizonJours))

  if (etat.mode === 'manuelle') {
    const analyse = analyserSerie(etat.manuelle)
    if (analyse.erreur) return { valeurs: [], erreur: analyse.erreur }
    if (analyse.valeurs.length !== horizon) {
      return {
        valeurs: analyse.valeurs,
        erreur: messageLongueur(analyse.valeurs.length, horizon),
      }
    }
    if (!serieFinie(analyse.valeurs)) {
      return {
        valeurs: analyse.valeurs,
        erreur: 'Les valeurs doivent être des nombres finis.',
      }
    }
    return { valeurs: analyse.valeurs, erreur: null }
  }

  let valeurs: number[]

  switch (etat.mode) {
    case 'constante': {
      if (!Number.isFinite(etat.constante)) {
        return {
          valeurs: [],
          erreur: 'La valeur constante doit être un nombre fini.',
        }
      }
      valeurs = genererSerieConstante(horizon, etat.constante)
      break
    }
    case 'uniforme': {
      if (
        !Number.isFinite(etat.uniformeMinimum) ||
        !Number.isFinite(etat.uniformeMaximum)
      ) {
        return {
          valeurs: [],
          erreur: 'Le minimum et le maximum doivent être des nombres finis.',
        }
      }
      if (etat.uniformeMinimum > etat.uniformeMaximum) {
        return {
          valeurs: [],
          erreur: 'Le minimum doit être inférieur ou égal au maximum.',
        }
      }
      valeurs = genererSerieUniforme({
        horizonJours: horizon,
        minimum: etat.uniformeMinimum,
        maximum: etat.uniformeMaximum,
        graine: etat.graine,
      })
      break
    }
    case 'normale': {
      if (
        !Number.isFinite(etat.normaleMoyenne) ||
        !Number.isFinite(etat.normaleEcartType)
      ) {
        return {
          valeurs: [],
          erreur: 'La moyenne et l’écart-type doivent être des nombres finis.',
        }
      }
      if (etat.normaleEcartType < 0) {
        return {
          valeurs: [],
          erreur: 'L’écart-type doit être positif ou nul.',
        }
      }
      valeurs = genererSerieNormale({
        horizonJours: horizon,
        moyenne: etat.normaleMoyenne,
        ecartType: etat.normaleEcartType,
        graine: etat.graine,
      })
      break
    }
    case 'gaussienne': {
      if (
        !Number.isFinite(etat.gaussienneBase) ||
        !Number.isFinite(etat.gaussiennePic) ||
        !Number.isFinite(etat.gaussienneJourPic) ||
        !Number.isFinite(etat.gaussienneLargeur)
      ) {
        return {
          valeurs: [],
          erreur: 'Les paramètres du profil gaussien doivent être des nombres finis.',
        }
      }
      if (
        !Number.isInteger(etat.gaussienneJourPic) ||
        etat.gaussienneJourPic < 0 ||
        etat.gaussienneJourPic > horizon - 1
      ) {
        return {
          valeurs: [],
          erreur: `Le jour du pic doit être un entier entre 0 et ${Math.max(0, horizon - 1)}.`,
        }
      }
      if (etat.gaussienneLargeur <= 0) {
        return {
          valeurs: [],
          erreur: 'La largeur du pic doit être supérieure à 0.',
        }
      }
      valeurs = genererProfilGaussien({
        horizonJours: horizon,
        base: etat.gaussienneBase,
        pic: etat.gaussiennePic,
        jourPic: etat.gaussienneJourPic,
        largeur: etat.gaussienneLargeur,
      })
      break
    }
    case 'courbe': {
      if (!etat.courbe.every((valeur) => Number.isFinite(valeur))) {
        return {
          valeurs: [],
          erreur: 'Les points de la courbe doivent être des nombres finis.',
        }
      }
      valeurs = interpolerCourbe(etat.courbe, horizon)
      break
    }
  }

  const valeursAvecPlancher = appliquerPlancher(valeurs, options.plancher)
  if (!serieFinie(valeursAvecPlancher)) {
    return {
      valeurs: valeursAvecPlancher,
      erreur: 'Les valeurs doivent être des nombres finis.',
    }
  }
  return { valeurs: valeursAvecPlancher, erreur: null }
}

export function echantillonnerPourApercu(
  valeurs: number[],
  maximum = 512,
): number[] {
  if (valeurs.length <= maximum) return valeurs
  if (maximum <= 1) return [valeurs[0]]
  const pas = (valeurs.length - 1) / (maximum - 1)
  return Array.from(
    { length: maximum },
    (_, index) => valeurs[Math.round(index * pas)],
  )
}
