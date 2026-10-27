export interface SerieGraphique {
  libelle: string
  valeurs: number[]
  classeTrait: string
  classeRemplissage?: string
  classePastille: string
  pointilles?: boolean
  aire?: boolean
}

export interface StatistiqueGraphique {
  libelle: string
  valeur: string
}

export interface SeriesEchantillonnees {
  indices: number[]
  series: number[][]
}

export interface DomaineGraphique {
  minimum: number
  maximum: number
}

export interface StatistiquesEnergie {
  productionTotale: number
  picDemande: number
  joursDeficit: number
}

export interface StatistiquesPrix {
  spotMoyen: number
  vuMoyenne: number
  joursSpotSousVu: number
}

function valeursFinies(valeurs: number[]): number[] {
  return valeurs.filter((valeur) => Number.isFinite(valeur))
}

function moyenne(valeurs: number[]): number {
  const finies = valeursFinies(valeurs)
  if (finies.length === 0) return 0
  return finies.reduce((somme, valeur) => somme + valeur, 0) / finies.length
}

export function echantillonnerSeries(
  series: number[][],
  maximum = 600,
): SeriesEchantillonnees {
  const longueur = Math.max(0, ...series.map((valeurs) => valeurs.length))
  if (longueur === 0) return { indices: [], series: series.map(() => []) }

  const maximumSur = Math.max(1, Math.floor(maximum))
  if (longueur <= maximumSur) {
    return {
      indices: Array.from({ length: longueur }, (_, index) => index),
      series: series.map((valeurs) => valeurs.slice()),
    }
  }

  if (maximumSur === 1) {
    return {
      indices: [0],
      series: series.map((valeurs) => [valeurs[0] ?? 0]),
    }
  }

  const pas = (longueur - 1) / (maximumSur - 1)
  const indices = Array.from(
    { length: maximumSur },
    (_, index) => Math.round(index * pas),
  )

  return {
    indices,
    series: series.map((valeurs) =>
      indices.map((index) => valeurs[index] ?? 0),
    ),
  }
}

export function domaineSeries(
  series: number[][],
  options: { inclureZero?: boolean; marge?: number } = {},
): DomaineGraphique {
  const inclureZero = options.inclureZero ?? true
  const margeRatio = options.marge ?? 0.08
  const valeurs = series.flat().filter((valeur) => Number.isFinite(valeur))

  if (valeurs.length === 0) return { minimum: 0, maximum: 1 }

  let minimum = Math.min(...valeurs)
  let maximum = Math.max(...valeurs)

  if (inclureZero) {
    minimum = Math.min(0, minimum)
    maximum = Math.max(0, maximum)
  }

  if (maximum === minimum) maximum = minimum + 1

  const marge = (maximum - minimum) * margeRatio

  return {
    minimum: minimum >= 0 ? minimum : minimum - marge,
    maximum: maximum + marge,
  }
}

export function jourDepuisRatio(
  ratio: number,
  horizonJours: number,
): number {
  const horizon = Math.max(1, Math.floor(horizonJours))
  const ratioBorne = Math.min(1, Math.max(0, ratio))
  return Math.min(horizon - 1, Math.round(ratioBorne * (horizon - 1)))
}

export function statistiquesEnergie(
  production: number[],
  demande: number[],
): StatistiquesEnergie {
  const longueur = Math.min(production.length, demande.length)
  let productionTotale = 0
  let picDemande = 0
  let joursDeficit = 0

  for (let index = 0; index < longueur; index += 1) {
    const productionJour = production[index] ?? 0
    const demandeJour = demande[index] ?? 0

    if (Number.isFinite(productionJour)) {
      productionTotale += productionJour
    }
    if (Number.isFinite(demandeJour)) {
      picDemande = Math.max(picDemande, demandeJour)
    }
    if (
      Number.isFinite(productionJour) &&
      Number.isFinite(demandeJour) &&
      productionJour < demandeJour
    ) {
      joursDeficit += 1
    }
  }

  return { productionTotale, picDemande, joursDeficit }
}

export function statistiquesPrix(
  spot: number[],
  valeurUsage: number[],
): StatistiquesPrix {
  const longueur = Math.min(spot.length, valeurUsage.length)
  let joursSpotSousVu = 0

  for (let index = 0; index < longueur; index += 1) {
    const spotJour = spot[index]
    const vuJour = valeurUsage[index]
    if (
      Number.isFinite(spotJour) &&
      Number.isFinite(vuJour) &&
      spotJour < vuJour
    ) {
      joursSpotSousVu += 1
    }
  }

  return {
    spotMoyen: moyenne(spot),
    vuMoyenne: moyenne(valeurUsage),
    joursSpotSousVu,
  }
}
