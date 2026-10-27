import type {
  Alerte,
  Arret,
  Modulation,
  ResultatTranche,
  SimulationTranche,
  TypeAlerte,
  TypeArret,
} from '../api/types'
import { couleurJepp, type CouleurJepp } from './couleurs'

export const TYPES_ALERTES_TRANCHE: TypeAlerte[] = [
  'NEUTRONIC_ANOMALY',
  'REMIT_UMM',
]

export const TYPES_ALERTES_NATIONALES: TypeAlerte[] = [
  'RTE_DEFICIT',
  'SPOT_BELOW_USAGE_VALUE',
]

export interface JourTimeline {
  jour: number
  facteurProduction: number
  hauteurProduction: number
  hauteurAffichee: number
  energieMwh: number
  jeppRestant: number
  jeppInitial: number
  couleurJepp: CouleurJepp
  estMaintenance: boolean
  arret: Arret | null
  modulation: Modulation | null
  marquageModulation: boolean
  alertes: Alerte[]
}

export function estMaintenance(jour: number, arrets: Arret[]): boolean {
  return arrets.some(
    (arret) => jour >= arret.jour_debut && jour < arret.jour_fin,
  )
}

export function trouverArret(jour: number, arrets: Arret[]): Arret | null {
  return (
    arrets.find(
      (arret) => jour >= arret.jour_debut && jour < arret.jour_fin,
    ) ?? null
  )
}

export function trouverModulation(
  jour: number,
  modulations: Modulation[],
): Modulation | null {
  return (
    modulations.find(
      (modulation) =>
        jour >= modulation.jour_debut && jour < modulation.jour_fin,
    ) ?? null
  )
}

export function hauteurBarre(facteurProduction: number): number {
  if (!Number.isFinite(facteurProduction)) return 0
  return Math.min(1, Math.max(0, facteurProduction)) * 100
}

export function construireJoursTimeline(params: {
  simulationTranche: SimulationTranche
  resultat: ResultatTranche | null
  alertes: Alerte[]
  horizonJours: number
}): JourTimeline[] {
  const { simulationTranche, resultat, alertes, horizonJours } = params
  const { tranche, arrets, modulations } = simulationTranche

  return Array.from({ length: horizonJours }, (_, jour) => {
    const arret = trouverArret(jour, arrets)
    const modulation = trouverModulation(jour, modulations)
    const facteurProduction = resultat?.facteurs_production[jour] ?? 0
    const jeppRestant = resultat?.jepp_restant[jour] ?? 0
    const hauteurProduction = hauteurBarre(facteurProduction)

    return {
      jour,
      facteurProduction,
      hauteurProduction,
      hauteurAffichee: arret ? 100 : hauteurProduction,
      energieMwh: resultat?.energie_mwh[jour] ?? 0,
      jeppRestant,
      jeppInitial: tranche.jepp_initial,
      couleurJepp: couleurJepp(jeppRestant, tranche.jepp_initial),
      estMaintenance: arret !== null,
      arret,
      modulation,
      marquageModulation: modulation !== null && arret === null,
      alertes: alertesTranchePourJour(
        alertes,
        tranche.identifiant,
        jour,
      ),
    }
  })
}

export function estAlerteTranche(alerte: Alerte): boolean {
  return TYPES_ALERTES_TRANCHE.includes(alerte.type_alerte)
}

export function estAlerteNationale(alerte: Alerte): boolean {
  return (
    alerte.tranche_id === null &&
    TYPES_ALERTES_NATIONALES.includes(alerte.type_alerte)
  )
}

export function filtrerAlertesTranche(
  alertes: Alerte[],
  trancheId: string,
): Alerte[] {
  return alertes.filter(
    (alerte) =>
      alerte.tranche_id === trancheId &&
      estAlerteTranche(alerte),
  )
}

export function alertesTranchePourJour(
  alertes: Alerte[],
  trancheId: string,
  jour: number,
): Alerte[] {
  return filtrerAlertesTranche(alertes, trancheId).filter(
    (alerte) => alerte.jour !== null && alerte.jour === jour,
  )
}

export function filtrerAlertesNationales(alertes: Alerte[]): Alerte[] {
  return alertes.filter(estAlerteNationale)
}

export function libelleTypeAlerte(type: TypeAlerte): string {
  const libelles: Record<TypeAlerte, string> = {
    NEUTRONIC_ANOMALY: 'Anomalie neutronique',
    REMIT_UMM: 'Transparence REMIT',
    RTE_DEFICIT: 'Déficit national RTE',
    SPOT_BELOW_USAGE_VALUE: 'Prix spot sous la valeur d’usage',
  }
  return libelles[type]
}

export function libelleTypeArret(type: TypeArret): string {
  const libelles: Record<TypeArret, string> = {
    ASR: 'ASR — arrêt simple pour rechargement',
    VP: 'VP — visite partielle',
    VD: 'VD — visite décennale',
  }
  return libelles[type]
}

export function libelleJourEtAlerte(
  jour: number,
  alerts: Alerte[],
): string {
  const base = `Jour ${jour}, facteur de production`
  if (alerts.length === 0) return base
  return `${base}, ${alerts.length} alerte${alerts.length > 1 ? 's' : ''}`
}

export interface ErreurPlanning {
  index: number
  message: string
}

interface Fenetre {
  jour_debut: number
  jour_fin: number
}

export function validerFenetres(
  fenetres: Fenetre[],
  horizonJours: number,
  libelle: string,
): ErreurPlanning[] {
  const erreurs: ErreurPlanning[] = []

  fenetres.forEach((fenetre, index) => {
    if (!Number.isInteger(fenetre.jour_debut) || fenetre.jour_debut < 0) {
      erreurs.push({
        index,
        message: `${libelle} ${index + 1} : le jour de début doit être entier et positif ou nul.`,
      })
    }
    if (!Number.isInteger(fenetre.jour_fin) || fenetre.jour_fin <= fenetre.jour_debut) {
      erreurs.push({
        index,
        message: `${libelle} ${index + 1} : le jour de fin doit être supérieur au jour de début.`,
      })
    }
    if (fenetre.jour_fin > horizonJours) {
      erreurs.push({
        index,
        message: `${libelle} ${index + 1} : la fenêtre dépasse l’horizon de ${horizonJours} jours.`,
      })
    }
  })

  const triees = fenetres
    .map((fenetre, index) => ({ ...fenetre, index }))
    .sort((a, b) => a.jour_debut - b.jour_debut)

  for (let position = 1; position < triees.length; position += 1) {
    const precedente = triees[position - 1]
    const courante = triees[position]
    if (courante.jour_debut < precedente.jour_fin) {
      erreurs.push({
        index: courante.index,
        message: `${libelle} ${courante.index + 1} : la fenêtre chevauche la ${libelle.toLowerCase()} ${precedente.index + 1}.`,
      })
    }
  }

  return erreurs
}

export function validerModulations(
  modulations: Modulation[],
  horizonJours: number,
): ErreurPlanning[] {
  const erreurs = validerFenetres(modulations, horizonJours, 'Modulation')

  modulations.forEach((modulation, index) => {
    if (
      !Number.isFinite(modulation.facteur) ||
      modulation.facteur < 0 ||
      modulation.facteur > 1
    ) {
      erreurs.push({
        index,
        message: `Modulation ${index + 1} : le facteur doit être compris entre 0 et 1.`,
      })
    }
  })

  return erreurs
}
