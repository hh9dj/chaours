import type {
  Arret,
  ConfigurationTranche,
  Modulation,
  ParametresSimulation,
  ResultatSimulation,
  Simulation,
  SimulationCreation,
  SimulationResume,
} from './types'

const DEFAULT_API_BASE_URL = 'http://localhost:8000'

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL
).replace(/\/+$/, '')

const traductionsValidation: Array<[RegExp, string]> = [
  [/^Field required$/i, 'Champ obligatoire.'],
  [/^Input should be a valid number$/i, 'Valeur numérique attendue.'],
  [/^Input should be a valid integer$/i, 'Nombre entier attendu.'],
  [
    /^Input should be greater than or equal to 0$/i,
    'La valeur doit être supérieure ou égale à 0.',
  ],
  [
    /^Input should be less than or equal to 1$/i,
    'La valeur doit être inférieure ou égale à 1.',
  ],
  [/^Input should be greater than 0$/i, 'La valeur doit être supérieure à 0.'],
  [
    /^String should have at least 1 character$/i,
    'Ce champ est obligatoire.',
  ],
  [
    /^String should have at most 200 characters$/i,
    'La valeur ne doit pas dépasser 200 caractères.',
  ],
  [/^Input should be a valid list$/i, 'Une liste de valeurs est attendue.'],
  [
    /end_day must be greater than start_day/i,
    'Le jour de fin doit être supérieur au jour de début.',
  ],
  [
    /overlapping (maintenance|modulation) windows/i,
    'Les fenêtres ne doivent pas se chevaucher.',
  ],
  [
    /window must be inside the horizon/i,
    'Une fenêtre dépasse l’horizon de la simulation.',
  ],
  [
    /length must equal horizon_days/i,
    'La longueur d’une série ne correspond pas à l’horizon.',
  ],
  [
    /simulation must contain at least one plant/i,
    'La simulation doit contenir au moins une tranche.',
  ],
  [/plant ids must be unique/i, 'Les identifiants de tranche doivent être uniques.'],
  [/must be finite/i, 'Les valeurs doivent être des nombres finis.'],
  [/must be non-negative/i, 'Les valeurs ne doivent pas être négatives.'],
]

function traduireMessageValidation(message: string): string {
  for (const [motif, traduction] of traductionsValidation) {
    if (motif.test(message)) return traduction
  }
  return 'Valeur invalide pour ce champ.'
}

interface DetailValidation {
  loc?: unknown[]
  msg?: unknown
}

function extraireDetailValidation(detail: unknown): string | null {
  if (Array.isArray(detail)) {
    const messages = detail
      .map((element) => {
        if (typeof element !== 'object' || element === null) return null
        const entree = element as DetailValidation
        const message =
          typeof entree.msg === 'string'
            ? traduireMessageValidation(entree.msg)
            : 'Valeur invalide pour ce champ.'
        const champs = Array.isArray(entree.loc)
          ? entree.loc
              .filter((partie) => partie !== 'body' && partie !== 'query')
              .map(String)
          : []

        return champs.length > 0
          ? `Champ « ${champs.join('.')} » : ${message}`
          : message
      })
      .filter((message): message is string => message !== null)

    return messages.length > 0 ? messages.join(' ; ') : null
  }

  if (typeof detail === 'object' && detail !== null && 'detail' in detail) {
    return extraireDetailValidation((detail as { detail: unknown }).detail)
  }

  if (typeof detail === 'string' && detail.trim().length > 0) {
    return traduireMessageValidation(detail)
  }

  return null
}

function messagePourStatut(statut: number, detail: unknown): string {
  if (statut === 404) return 'Simulation ou tranche introuvable.'
  if (statut === 422) {
    const message = extraireDetailValidation(detail)
    return message
      ? `Données invalides. ${message}`
      : 'Données invalides. Vérifiez les champs du formulaire.'
  }
  if (statut === 400) return 'La requête est invalide.'
  if (statut >= 500) {
    return 'Le serveur a rencontré une erreur. Réessayez dans un instant.'
  }
  return 'La requête a échoué. Réessayez.'
}

export class ApiError extends Error {
  readonly statut: number
  readonly detail: unknown

  constructor(statut: number, detail: unknown, message?: string) {
    super(message ?? messagePourStatut(statut, detail))
    this.name = 'ApiError'
    this.statut = statut
    this.detail = detail
  }
}

export function messageErreur(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message
  }
  return 'Une erreur inattendue est survenue.'
}

async function requete<T>(
  chemin: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${chemin}`, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError(
      0,
      null,
      'Le serveur est injoignable. Vérifiez que l’API est démarrée.',
    )
  }

  if (!response.ok) {
    let detail: unknown = null
    try {
      detail = await response.json()
    } catch {
      detail = null
    }
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export function listerSimulations(): Promise<SimulationResume[]> {
  return requete<SimulationResume[]>('/simulations/')
}

export function creerSimulation(
  payload: SimulationCreation,
): Promise<Simulation> {
  return requete<Simulation>('/simulations/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function chargerSimulation(simulationId: string): Promise<Simulation> {
  return requete<Simulation>(
    `/simulations/${encodeURIComponent(simulationId)}`,
  )
}

export function modifierSimulation(
  simulationId: string,
  payload: ParametresSimulation,
): Promise<Simulation> {
  return requete<Simulation>(
    `/simulations/${encodeURIComponent(simulationId)}`,
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
  )
}

export function supprimerSimulation(simulationId: string): Promise<void> {
  return requete<void>(`/simulations/${encodeURIComponent(simulationId)}`, {
    method: 'DELETE',
  })
}

export function modifierConfigurationTranche(
  simulationId: string,
  trancheId: string,
  payload: ConfigurationTranche,
): Promise<Simulation> {
  return requete<Simulation>(
    `/simulations/${encodeURIComponent(simulationId)}/plants/${encodeURIComponent(trancheId)}`,
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
  )
}

export function modifierArrets(
  simulationId: string,
  trancheId: string,
  arrets: Arret[],
): Promise<Simulation> {
  return requete<Simulation>(
    `/simulations/${encodeURIComponent(simulationId)}/plants/${encodeURIComponent(trancheId)}/maintenances`,
    {
      method: 'PUT',
      body: JSON.stringify(arrets),
    },
  )
}

export function modifierModulations(
  simulationId: string,
  trancheId: string,
  modulations: Modulation[],
): Promise<Simulation> {
  return requete<Simulation>(
    `/simulations/${encodeURIComponent(simulationId)}/plants/${encodeURIComponent(trancheId)}/modulations`,
    {
      method: 'PUT',
      body: JSON.stringify(modulations),
    },
  )
}

export function executerSimulation(
  simulationId: string,
): Promise<ResultatSimulation> {
  return requete<ResultatSimulation>(
    `/simulations/${encodeURIComponent(simulationId)}/run`,
    { method: 'POST' },
  )
}

export const api = {
  listerSimulations,
  creerSimulation,
  chargerSimulation,
  modifierSimulation,
  supprimerSimulation,
  modifierConfigurationTranche,
  modifierArrets,
  modifierModulations,
  executerSimulation,
}
