import { describe, expect, it } from 'vitest'

import { couleurJepp, ratioJepp, SEUILS_JEPP } from './couleurs'

describe('couleurJepp', () => {
  it('respecte le seuil vert à partir de 50 %', () => {
    expect(couleurJepp(50, 100)).toBe('vert')
    expect(couleurJepp(75, 100)).toBe('vert')
    expect(couleurJepp(SEUILS_JEPP.vert * 100, 100)).toBe('vert')
  })

  it('respecte le seuil jaune entre 20 % et 50 %', () => {
    expect(couleurJepp(49.99, 100)).toBe('jaune')
    expect(couleurJepp(20, 100)).toBe('jaune')
  })

  it('respecte le seuil orange entre 5 % et 20 %', () => {
    expect(couleurJepp(19.99, 100)).toBe('orange')
    expect(couleurJepp(5, 100)).toBe('orange')
  })

  it('passe au rouge sous 5 %', () => {
    expect(couleurJepp(4.99, 100)).toBe('rouge')
    expect(couleurJepp(0, 100)).toBe('rouge')
  })

  it('utilise le rouge quand le JEPP initial vaut 0', () => {
    expect(couleurJepp(0, 0)).toBe('rouge')
    expect(couleurJepp(10, 0)).toBe('rouge')
  })
})

describe('ratioJepp', () => {
  it('calcule le ratio du stock restant', () => {
    expect(ratioJepp(25, 100)).toBe(0.25)
  })

  it('renvoie 0 quand le JEPP initial vaut 0', () => {
    expect(ratioJepp(25, 0)).toBe(0)
  })
})
