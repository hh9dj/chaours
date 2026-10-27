import { describe, expect, it } from 'vitest'

import {
  adapterPointsCourbe,
  construireSerie,
  creerAleatoire,
  echantillonnerPoints,
  echantillonnerPourApercu,
  etatInitial,
  interpolerCourbe,
  nombrePointsCourbe,
  resumerSerie,
  type EtatSerie,
} from './series'

function etat(valeurs: number[], horizon: number): EtatSerie {
  return etatInitial(valeurs, horizon)
}

describe('resumerSerie', () => {
  it('calcule le minimum, le maximum et la moyenne', () => {
    expect(resumerSerie([10, 20, 30])).toEqual({
      minimum: 10,
      maximum: 30,
      moyenne: 20,
    })
  })

  it('ignore les valeurs non finies', () => {
    expect(resumerSerie([10, Number.NaN, 30])).toEqual({
      minimum: 10,
      maximum: 30,
      moyenne: 20,
    })
  })
})

describe('etatInitial', () => {
  it('ouvre une série constante en mode constante', () => {
    expect(etatInitial([80, 80, 80], 3).mode).toBe('constante')
  })

  it('ouvre une série variable en mode manuelle', () => {
    expect(etatInitial([80, 60, 80], 3).mode).toBe('manuelle')
  })
})

describe('creerAleatoire', () => {
  it('produit la même suite pour la même graine', () => {
    const premiere = creerAleatoire(42)
    const seconde = creerAleatoire(42)

    expect([premiere(), premiere(), premiere()]).toEqual([
      seconde(),
      seconde(),
      seconde(),
    ])
  })

  it('produit des suites différentes pour des graines différentes', () => {
    const premiere = creerAleatoire(1)
    const seconde = creerAleatoire(2)

    expect(premiere()).not.toBe(seconde())
  })
})

describe('construireSerie', () => {
  it('génère une série constante sur tout l’horizon', () => {
    const serie = { ...etat([0], 4), mode: 'constante' as const, constante: 80 }

    expect(construireSerie(serie, 4)).toEqual({
      valeurs: [80, 80, 80, 80],
      erreur: null,
    })
  })

  it('génère une série uniforme reproductible et bornée', () => {
    const source: EtatSerie = {
      ...etat([0], 10),
      mode: 'uniforme',
      uniformeMinimum: 10,
      uniformeMaximum: 20,
      graine: 7,
    }

    const premiere = construireSerie(source, 10)
    const seconde = construireSerie({ ...source }, 10)

    expect(premiere.erreur).toBeNull()
    expect(premiere.valeurs).toEqual(seconde.valeurs)
    expect(premiere.valeurs).toHaveLength(10)
    expect(premiere.valeurs.every((valeur) => valeur >= 10 && valeur <= 20)).toBe(
      true,
    )
  })

  it('rejette des bornes uniformes inversées', () => {
    const serie: EtatSerie = {
      ...etat([0], 3),
      mode: 'uniforme',
      uniformeMinimum: 20,
      uniformeMaximum: 10,
    }

    const resultat = construireSerie(serie, 3)

    expect(resultat.erreur).toContain('minimum')
    expect(resultat.valeurs).toEqual([])
  })

  it('applique le plancher à une série normale', () => {
    const serie: EtatSerie = {
      ...etat([0], 50),
      mode: 'normale',
      normaleMoyenne: 0,
      normaleEcartType: 100,
      graine: 3,
    }

    const resultat = construireSerie(serie, 50, { plancher: 0 })

    expect(resultat.erreur).toBeNull()
    expect(resultat.valeurs).toHaveLength(50)
    expect(resultat.valeurs.every((valeur) => valeur >= 0)).toBe(true)
  })

  it('place le pic du profil gaussien au jour demandé', () => {
    const serie: EtatSerie = {
      ...etat([0], 11),
      mode: 'gaussienne',
      gaussienneBase: 10,
      gaussiennePic: 90,
      gaussienneJourPic: 5,
      gaussienneLargeur: 2,
    }

    const resultat = construireSerie(serie, 11)
    const maximum = Math.max(...resultat.valeurs)

    expect(resultat.erreur).toBeNull()
    expect(resultat.valeurs[5]).toBe(maximum)
    expect(resultat.valeurs[0]).toBeLessThan(20)
  })

  it('rejette une courbe personnalisée avec des valeurs non finies', () => {
    const serie: EtatSerie = {
      ...etat([0], 5),
      mode: 'courbe',
      courbe: [1, Number.NaN, 3],
    }

    expect(construireSerie(serie, 5).erreur).toContain('nombres finis')
  })

  it('signale une longueur manuelle incorrecte', () => {
    const serie: EtatSerie = {
      ...etat([0], 5),
      mode: 'manuelle',
      manuelle: '1\n2',
    }

    const resultat = construireSerie(serie, 5)

    expect(resultat.erreur).toContain('2 valeurs')
    expect(resultat.erreur).toContain('5 attendues')
  })

  it('conserve les valeurs manuelles sans appliquer de plancher', () => {
    const serie: EtatSerie = {
      ...etat([0], 3),
      mode: 'manuelle',
      manuelle: '-1\n0\n1',
    }

    expect(construireSerie(serie, 3, { plancher: 0 })).toEqual({
      valeurs: [-1, 0, 1],
      erreur: null,
    })
  })
})

describe('courbe personnalisée', () => {
  it('interpole linéairement les points de contrôle', () => {
    expect(interpolerCourbe([0, 10], 5)).toEqual([0, 2.5, 5, 7.5, 10])
    expect(interpolerCourbe([42], 3)).toEqual([42, 42, 42])
  })

  it('échantillonne douze points au maximum', () => {
    const valeurs = Array.from({ length: 365 }, (_, jour) => jour)

    expect(nombrePointsCourbe(365)).toBe(12)
    expect(nombrePointsCourbe(5)).toBe(5)
    expect(echantillonnerPoints(valeurs, 365)).toHaveLength(12)
  })

  it('adapte le nombre de points à un horizon plus court', () => {
    const points = Array.from({ length: 12 }, (_, index) => index)

    expect(adapterPointsCourbe(points, 5)).toHaveLength(5)
    expect(adapterPointsCourbe(points, 1)).toHaveLength(1)
  })
})

describe('echantillonnerPourApercu', () => {
  it('conserve la première et la dernière valeur', () => {
    const valeurs = Array.from({ length: 1000 }, (_, index) => index)
    const apercu = echantillonnerPourApercu(valeurs, 10)

    expect(apercu).toHaveLength(10)
    expect(apercu[0]).toBe(0)
    expect(apercu[apercu.length - 1]).toBe(999)
  })

  it('renvoie la série telle quelle si elle est assez courte', () => {
    expect(echantillonnerPourApercu([1, 2, 3], 10)).toEqual([1, 2, 3])
  })
})
