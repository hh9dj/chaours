export type TypeArret = 'ASR' | 'VP' | 'VD'

export type TypeAlerte =
  | 'NEUTRONIC_ANOMALY'
  | 'REMIT_UMM'
  | 'RTE_DEFICIT'
  | 'SPOT_BELOW_USAGE_VALUE'

export interface Tranche {
  identifiant: string
  code_eic: string
  puissance_nominale_mw: number
  jepp_initial: number
}

export interface Arret {
  type_arret: TypeArret
  jour_debut: number
  jour_fin: number
}

export interface Modulation {
  jour_debut: number
  jour_fin: number
  facteur: number
}

export interface SimulationTranche {
  tranche: Tranche
  arrets: Arret[]
  modulations: Modulation[]
}

export interface Simulation {
  simulation_id: string
  nom: string
  cree_le: string
  horizon_jours: number
  prix_spot_eur_mwh: number[]
  demande_nationale_mwh: number[]
  valeur_usage_eur_mwh: number[]
  tranches: SimulationTranche[]
}

export interface SimulationResume {
  simulation_id: string
  nom: string
  cree_le: string
  horizon_jours: number
  nombre_tranches: number
}

export interface SimulationCreation {
  nom: string
  horizon_jours: number
  prix_spot_eur_mwh: number[]
  demande_nationale_mwh: number[]
  valeur_usage_eur_mwh: number[]
  tranches: SimulationTranche[]
}

export interface ParametresSimulation {
  nom: string
  horizon_jours: number
  prix_spot_eur_mwh: number[]
  demande_nationale_mwh: number[]
  valeur_usage_eur_mwh: number[]
}

export interface ConfigurationTranche {
  code_eic: string
  puissance_nominale_mw: number
  jepp_initial: number
}

export interface ResultatTranche {
  tranche_id: string
  facteurs_production: number[]
  energie_mwh: number[]
  jepp_restant: number[]
  jours_epuisement: number[]
}

export interface Alerte {
  type_alerte: TypeAlerte
  jour: number | null
  tranche_id: string | null
  message: string
}

export interface ResultatSimulation {
  simulation_id: string
  duree_execution_ms: number
  tranches: ResultatTranche[]
  offre_nationale_mwh: number[]
  demande_mwh: number[]
  jours_deficit: number[]
  alertes: Alerte[]
}
