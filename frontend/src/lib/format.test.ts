import { describe, expect, it } from 'vitest'

import {
  analyserSerie,
  formaterDate,
  formaterSerie,
  redimensionnerSerie,
} from './format'

describe('redimensionnerSerie', () => {
  it('tronque la série quand l’horizon diminue', () => {
    expect(redimensionnerSerie([1, 2, 3, 4], 2)).toEqual([1, 2])
  })

  it('étend la série avec la dernière valeur quand l’horizon augmente', () => {
    expect(redimensionnerSerie([1, 2, 3], 5)).toEqual([1, 2, 3, 3, 3])
  })

  it('étend une série vide avec des zéros', () => {
    expect(redimensionnerSerie([], 3)).toEqual([0, 0, 0])
  })

  it('renvoie une série vide pour un horizon nul', () => {
    expect(redimensionnerSerie([1, 2, 3], 0)).toEqual([])
  })
})

describe('analyserSerie', () => {
  it('accepte une valeur par ligne, les lignes vides et la virgule décimale', () => {
    expect(analyserSerie('80\n\n60,5\r\n 42 ')).toEqual({
      valeurs: [80, 60.5, 42],
      erreur: null,
    })
  })

  it('rejette une valeur non numérique avec un message en français', () => {
    const resultat = analyserSerie('80\nabc\n60')

    expect(resultat.valeurs).toEqual([])
    expect(resultat.erreur).toContain('ligne 2')
    expect(resultat.erreur).toContain('nombre valide')
  })

  it('reconstruit une série à partir de son texte', () => {
    expect(formaterSerie([80, 60.5, 42])).toBe('80\n60.5\n42')
  })
})

describe('formaterDate', () => {
  it('formate une date en français', () => {
    const resultat = formaterDate('2026-01-15T12:00:00Z')

    expect(resultat).toContain('2026')
    expect(resultat).toContain('janvier')
    expect(resultat).toContain('15')
  })

  it('gère une date invalide', () => {
    expect(formaterDate('invalide')).toBe('Date inconnue')
  })
})
