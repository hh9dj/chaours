import { describe, expect, it } from 'vitest'

import {
  domaineSeries,
  echantillonnerSeries,
  jourDepuisRatio,
  statistiquesEnergie,
  statistiquesPrix,
} from './overview'

describe('echantillonnerSeries', () => {
  it('conserve toutes les valeurs quand la série est courte', () => {
    expect(echantillonnerSeries([[1, 2, 3], [10, 20, 30]], 10)).toEqual({
      indices: [0, 1, 2],
      series: [[1, 2, 3], [10, 20, 30]],
    })
  })

  it('échantillonne plusieurs séries avec les mêmes indices', () => {
    const valeurs = Array.from({ length: 1000 }, (_, index) => index)
    const resultat = echantillonnerSeries([valeurs, valeurs.map((v) => v * 2)], 10)

    expect(resultat.indices).toHaveLength(10)
    expect(resultat.series[0]).toHaveLength(10)
    expect(resultat.series[1]).toHaveLength(10)
    expect(resultat.indices[0]).toBe(0)
    expect(resultat.indices[9]).toBe(999)
    expect(resultat.series[0][9]).toBe(999)
    expect(resultat.series[1][9]).toBe(1998)
  })

  it('gère une série vide', () => {
    expect(echantillonnerSeries([[], []], 10)).toEqual({
      indices: [],
      series: [[], []],
    })
  })
})

describe('domaineSeries', () => {
  it('inclut zéro pour des valeurs positives', () => {
    expect(domaineSeries([[10, 20, 30]])).toEqual({
      minimum: 0,
      maximum: 30 + 30 * 0.08,
    })
  })

  it('gère des valeurs négatives', () => {
    const domaine = domaineSeries([[-20, 10]], { inclureZero: true })

    expect(domaine.minimum).toBeLessThan(-20)
    expect(domaine.maximum).toBeGreaterThan(10)
  })

  it('ajoute une marge quand toutes les valeurs sont égales', () => {
    const domaine = domaineSeries([[5, 5, 5]], { inclureZero: false })

    expect(domaine.minimum).toBe(5)
    expect(domaine.maximum).toBeGreaterThan(5)
  })
})

describe('jourDepuisRatio', () => {
  it('retourne le premier, le milieu et le dernier jour', () => {
    expect(jourDepuisRatio(0, 101)).toBe(0)
    expect(jourDepuisRatio(0.5, 101)).toBe(50)
    expect(jourDepuisRatio(1, 101)).toBe(100)
  })

  it('borne le ratio et gère un horizon de un jour', () => {
    expect(jourDepuisRatio(-1, 10)).toBe(0)
    expect(jourDepuisRatio(2, 10)).toBe(9)
    expect(jourDepuisRatio(0.5, 1)).toBe(0)
  })
})

describe('statistiquesEnergie', () => {
  it('calcule la production totale, le pic et les jours de déficit', () => {
    expect(
      statistiquesEnergie([10, 5, 20], [8, 12, 15]),
    ).toEqual({
      productionTotale: 35,
      picDemande: 15,
      joursDeficit: 1,
    })
  })
})

describe('statistiquesPrix', () => {
  it('calcule les moyennes et les jours sous la valeur d’usage', () => {
    expect(statistiquesPrix([60, 80, 40], [70, 70, 70])).toEqual({
      spotMoyen: 60,
      vuMoyenne: 70,
      joursSpotSousVu: 2,
    })
  })
})
