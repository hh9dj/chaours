export interface MetriquesDefilement {
  scrollLeft: number
  largeurVisible: number
  largeurTotale: number
}

export interface EtatZoom {
  zoom: number
  defilement: number
}

export const JOURS_VISIBLES_MIN = 7

export function zoomMaximum(horizonJours: number): number {
  const horizon = Math.max(1, Math.floor(horizonJours))
  if (horizon <= JOURS_VISIBLES_MIN) return 1
  return horizon / JOURS_VISIBLES_MIN
}

export function bornerZoom(zoom: number, horizonJours: number): number {
  if (!Number.isFinite(zoom)) return 1
  return Math.min(zoomMaximum(horizonJours), Math.max(1, zoom))
}

export function bornerDefilement(defilement: number): number {
  if (!Number.isFinite(defilement)) return 0
  return Math.min(1, Math.max(0, defilement))
}

function arrondirDefilement(defilement: number): number {
  return Math.round(bornerDefilement(defilement) * 1000000) / 1000000
}

export function zoomerAvecAncre(params: {
  zoomActuel: number
  defilementActuel: number
  horizonJours: number
  largeurVisible: number
  largeurTotale: number
  offsetAncre: number
  deltaY: number
}): EtatZoom {
  const largeurVisible = Math.max(1, params.largeurVisible)
  const largeurTotale = Math.max(largeurVisible, params.largeurTotale)
  const zoomActuel = bornerZoom(params.zoomActuel, params.horizonJours)
  const facteur = Math.min(
    2,
    Math.max(0.5, Math.exp(-params.deltaY * 0.002)),
  )
  const nouveauZoom = bornerZoom(
    zoomActuel * facteur,
    params.horizonJours,
  )

  if (nouveauZoom === zoomActuel) {
    return {
      zoom: zoomActuel,
      defilement: arrondirDefilement(params.defilementActuel),
    }
  }

  const offsetAncre = Math.min(
    largeurVisible,
    Math.max(0, params.offsetAncre),
  )
  const defilementActuel = bornerDefilement(params.defilementActuel)
  const scrollActuel =
    defilementActuel * Math.max(0, largeurTotale - largeurVisible)
  const ancreGlobale = (scrollActuel + offsetAncre) / largeurTotale

  const nouvelleLargeurTotale = Math.max(
    largeurVisible,
    largeurTotale * (nouveauZoom / zoomActuel),
  )
  const nouveauScroll = ancreGlobale * nouvelleLargeurTotale - offsetAncre
  const nouveauScrollMaximum = Math.max(
    0,
    nouvelleLargeurTotale - largeurVisible,
  )

  return {
    zoom: nouveauZoom,
    defilement:
      nouveauScrollMaximum === 0
        ? 0
        : arrondirDefilement(nouveauScroll / nouveauScrollMaximum),
  }
}

export function zoomerAuCentre(params: {
  zoomActuel: number
  defilementActuel: number
  horizonJours: number
  largeurVisible: number
  largeurTotale: number
  direction: 1 | -1
}): EtatZoom {
  return zoomerAvecAncre({
    ...params,
    offsetAncre: params.largeurVisible / 2,
    deltaY: params.direction > 0 ? -120 : 120,
  })
}

export function defilementDepuisScroll(
  scrollLeft: number,
  largeurVisible: number,
  largeurTotale: number,
): number {
  const maximum = largeurTotale - largeurVisible
  if (maximum <= 0) return 0
  return arrondirDefilement(scrollLeft / maximum)
}

export function scrollDepuisDefilement(
  defilement: number,
  largeurVisible: number,
  largeurTotale: number,
): number {
  const maximum = Math.max(0, largeurTotale - largeurVisible)
  return arrondirDefilement(defilement) * maximum
}

export function joursVisibles(
  metriques: MetriquesDefilement,
  horizonJours: number,
): { debut: number; fin: number } {
  const horizon = Math.max(1, Math.floor(horizonJours))
  const largeurTotale = Math.max(1, metriques.largeurTotale)
  const largeurVisible = Math.max(1, metriques.largeurVisible)
  const scrollMaximum = Math.max(0, largeurTotale - largeurVisible)
  const scrollLeft = Math.min(
    scrollMaximum,
    Math.max(0, metriques.scrollLeft),
  )

  const debut = Math.min(
    horizon - 1,
    Math.max(0, Math.floor((scrollLeft / largeurTotale) * horizon)),
  )
  const fin = Math.max(
    debut,
    Math.min(
      horizon - 1,
      Math.ceil(((scrollLeft + largeurVisible) / largeurTotale) * horizon) -
        1,
    ),
  )

  return { debut, fin }
}

export function positionJourPct(
  jour: number,
  metriques: MetriquesDefilement,
  horizonJours: number,
): number {
  const horizon = Math.max(1, Math.floor(horizonJours))
  const largeurTotale = Math.max(1, metriques.largeurTotale)
  const largeurVisible = Math.max(1, metriques.largeurVisible)
  const scrollMaximum = Math.max(0, largeurTotale - largeurVisible)
  const scrollLeft = Math.min(
    scrollMaximum,
    Math.max(0, metriques.scrollLeft),
  )
  const jourBorne = Math.min(horizon - 1, Math.max(0, jour))
  const positionJour =
    ((jourBorne + 0.5) / horizon) * largeurTotale

  return Math.min(
    100,
    Math.max(0, ((positionJour - scrollLeft) / largeurVisible) * 100),
  )
}
