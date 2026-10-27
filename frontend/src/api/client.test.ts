import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  ApiError,
  chargerSimulation,
  creerSimulation,
  listerSimulations,
  modifierArrets,
  supprimerSimulation,
} from './client'
import type { SimulationCreation } from './types'

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function reponseJson(donnees: unknown, statut = 200): Response {
  return new Response(JSON.stringify(donnees), {
    status: statut,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('client API', () => {
  it('liste les simulations avec l’URL de base et le bon chemin', async () => {
    const simulations = [
      {
        simulation_id: 'abc',
        nom: 'Hiver 2027',
        cree_le: '2026-01-01T00:00:00Z',
        horizon_jours: 365,
        nombre_tranches: 2,
      },
    ]
    fetchMock.mockResolvedValue(reponseJson(simulations))

    const resultat = await listerSimulations()

    expect(resultat).toEqual(simulations)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[0][0]).toBe(
      'http://localhost:8000/simulations/',
    )
  })

  it('crée une simulation en envoyant le contrat SimulationCreation', async () => {
    const payload: SimulationCreation = {
      nom: 'Test',
      horizon_jours: 2,
      prix_spot_eur_mwh: [80, 80],
      demande_nationale_mwh: [0, 0],
      valeur_usage_eur_mwh: [60, 60],
      tranches: [],
    }
    fetchMock.mockResolvedValue(reponseJson({ simulation_id: 'abc' }, 201))

    await creerSimulation(payload)

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://localhost:8000/simulations/')
    expect(init.method).toBe('POST')
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' })
    expect(JSON.parse(init.body)).toEqual(payload)
  })

  it('transforme une erreur 404 en message français', async () => {
    fetchMock.mockResolvedValue(
      reponseJson({ detail: 'Simulation not found' }, 404),
    )

    const erreur = await chargerSimulation('abc').catch(
      (error: unknown) => error,
    )

    expect(erreur).toBeInstanceOf(ApiError)
    expect((erreur as ApiError).statut).toBe(404)
    expect((erreur as ApiError).message).toBe(
      'Simulation ou tranche introuvable.',
    )
  })

  it('transforme une erreur 422 en message français lisible', async () => {
    fetchMock.mockResolvedValue(
      reponseJson(
        {
          detail: [
            {
              type: 'missing',
              loc: ['body', 'horizon_jours'],
              msg: 'Field required',
            },
          ],
        },
        422,
      ),
    )

    const erreur = await chargerSimulation('abc').catch(
      (error: unknown) => error,
    )

    expect(erreur).toBeInstanceOf(ApiError)
    expect((erreur as ApiError).statut).toBe(422)
    expect((erreur as ApiError).message).toContain('Données invalides')
    expect((erreur as ApiError).message).toContain('horizon_jours')
    expect((erreur as ApiError).message).toContain('Champ obligatoire')
  })

  it('encode les identifiants dans les chemins de tranche', async () => {
    fetchMock.mockResolvedValue(reponseJson({ simulation_id: 'sim 1' }))

    await modifierArrets('sim 1', 'T/1', [
      { type_arret: 'ASR', jour_debut: 0, jour_fin: 30 },
    ])

    expect(fetchMock.mock.calls[0][0]).toBe(
      'http://localhost:8000/simulations/sim%201/plants/T%2F1/maintenances',
    )
  })

  it('gère une suppression sans contenu', async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    await expect(supprimerSimulation('abc')).resolves.toBeUndefined()
    expect(fetchMock.mock.calls[0][1].method).toBe('DELETE')
  })

  it('signale un serveur injoignable en français', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    const erreur = await listerSimulations().catch(
      (error: unknown) => error,
    )

    expect(erreur).toBeInstanceOf(ApiError)
    expect((erreur as ApiError).statut).toBe(0)
    expect((erreur as ApiError).message).toContain('injoignable')
  })
})
