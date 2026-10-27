import { describe, expect, it } from 'vitest'

import {
  bornerDefilement,
  bornerZoom,
  defilementDepuisScroll,
  joursVisibles,
  positionJourPct,
  scrollDepuisDefilement,
  zoomerAvecAncre,
  zoomerAuCentre,
  zoomMaximum,
} from './timelineZoom'

describe('zoomMaximum', () => {
  it('limite le zoom à une fenêtre de sept jours', () => {
    expect(zoomMaximum(365)).toBeCloseTo(365 / 7)
    expect(zoomMaximum(14)).toBe(2)
  })

  it('désactive le zoom pour un horizon court', () => {
    expect(zoomMaximum(7)).toBe(1)
    expect(zoomMaximum(1)).toBe(1)
  })
})

describe('bornerZoom', () => {
  it('borne le zoom entre 1 et le maximum', () => {
    expect(bornerZoom(0.2, 365)).toBe(1)
    expect(bornerZoom(1000, 365)).toBeCloseTo(365 / 7)
    expect(bornerZoom(2, 365)).toBe(2)
  })

  it('revient à 1 pour une valeur non finie', () => {
    expect(bornerZoom(Number.NaN, 365)).toBe(1)
  })
})

describe('bornerDefilement', () => {
  it('borne le défilement entre 0 et 1', () => {
    expect(bornerDefilement(-1)).toBe(0)
    expect(bornerDefilement(2)).toBe(1)
    expect(bornerDefilement(0.42)).toBe(0.42)
  })
})

describe('zoomerAvecAncre', () => {
  const base = {
    zoomActuel: 1,
    defilementActuel: 0,
    horizonJours: 365,
    largeurVisible: 1000,
    largeurTotale: 1000,
  }

  it('garde le jour sous le pointeur au centre', () => {
    const resultat = zoomerAvecAncre({
      ...base,
      offsetAncre: 500,
      deltaY: -120,
    })

    expect(resultat.zoom).toBeGreaterThan(1)
    expect(resultat.defilement).toBeCloseTo(0.5, 3)
    expect(resultat.defilement).toBeLessThanOrEqual(1)
  })

  it('garde le bord gauche quand le pointeur est à gauche', () => {
    const resultat = zoomerAvecAncre({
      ...base,
      offsetAncre: 0,
      deltaY: -120,
    })

    expect(resultat.zoom).toBeGreaterThan(1)
    expect(resultat.defilement).toBe(0)
  })

  it('garde le bord droit quand le pointeur est à droite', () => {
    const resultat = zoomerAvecAncre({
      ...base,
      offsetAncre: 1000,
      deltaY: -120,
    })

    expect(resultat.zoom).toBeGreaterThan(1)
    expect(resultat.defilement).toBe(1)
  })

  it('ne dépasse pas le zoom maximal', () => {
    const resultat = zoomerAvecAncre({
      ...base,
      zoomActuel: 365 / 7,
      defilementActuel: 0.4,
      largeurTotale: 1000 * (365 / 7),
      offsetAncre: 500,
      deltaY: -120,
    })

    expect(resultat.zoom).toBeCloseTo(365 / 7)
    expect(resultat.defilement).toBe(0.4)
  })
})

describe('zoomerAuCentre', () => {
  it('dézoome vers le centre de la fenêtre', () => {
    const resultat = zoomerAuCentre({
      zoomActuel: 4,
      defilementActuel: 0.5,
      horizonJours: 365,
      largeurVisible: 1000,
      largeurTotale: 4000,
      direction: -1,
    })

    expect(resultat.zoom).toBeLessThan(4)
    expect(resultat.zoom).toBeGreaterThan(1)
  })
})

describe('conversion du défilement', () => {
  it('convertit les pixels en fraction partagée', () => {
    expect(defilementDepuisScroll(500, 1000, 2000)).toBeCloseTo(0.5)
    expect(defilementDepuisScroll(500, 1000, 1000)).toBe(0)
  })

  it('convertit la fraction partagée en pixels', () => {
    expect(scrollDepuisDefilement(0.5, 1000, 2000)).toBe(500)
    expect(scrollDepuisDefilement(2, 1000, 2000)).toBe(1000)
  })
})

describe('joursVisibles', () => {
  it('retourne tout l’horizon quand la timeline tient dans la largeur', () => {
    expect(
      joursVisibles(
        { scrollLeft: 0, largeurVisible: 1000, largeurTotale: 1000 },
        100,
      ),
    ).toEqual({ debut: 0, fin: 99 })
  })

  it('calcule la fenêtre visible quand la timeline est zoomée', () => {
    expect(
      joursVisibles(
        { scrollLeft: 500, largeurVisible: 1000, largeurTotale: 2000 },
        100,
      ),
    ).toEqual({ debut: 25, fin: 74 })
  })
})

describe('positionJourPct', () => {
  it('place un jour au centre quand la timeline complète est visible', () => {
    const position = positionJourPct(
      50,
      { scrollLeft: 0, largeurVisible: 1000, largeurTotale: 1000 },
      100,
    )

    expect(position).toBeCloseTo(50.5, 1)
  })

  it('place un jour selon le défilement de la fenêtre zoomée', () => {
    const position = positionJourPct(
      25,
      { scrollLeft: 500, largeurVisible: 1000, largeurTotale: 2000 },
      100,
    )

    expect(position).toBeCloseTo(1, 1)
  })
})
