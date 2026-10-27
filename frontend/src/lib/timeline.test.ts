import { describe, expect, it } from 'vitest'

import type {
  Alerte,
  ResultatTranche,
  SimulationTranche,
} from '../api/types'
import {
  alertesTranchePourJour,
  construireJoursTimeline,
  estMaintenance,
  filtrerAlertesNationales,
  filtrerAlertesTranche,
  hauteurBarre,
  validerFenetres,
  validerModulations,
} from './timeline'

const simulationTranche: SimulationTranche = {
  tranche: {
    identifiant: 'T1',
    code_eic: 'FR-T1',
    puissance_nominale_mw: 1300,
    jepp_initial: 100,
  },
  arrets: [
    { type_arret: 'ASR', jour_debut: 0, jour_fin: 2 },
    { type_arret: 'VP', jour_debut: 5, jour_fin: 7 },
  ],
  modulations: [{ jour_debut: 2, jour_fin: 5, facteur: 0.5 }],
}

const resultat: ResultatTranche = {
  tranche_id: 'T1',
  facteurs_production: [0, 0, 0.5, 0.8, 1, 0, 0, 0.4],
  energie_mwh: [0, 0, 650, 1040, 1300, 0, 0, 520],
  jepp_restant: [100, 100, 99.5, 98.7, 97.7, 97.7, 97.7, 97.3],
  jours_epuisement: [],
}

const alertes: Alerte[] = [
  {
    type_alerte: 'NEUTRONIC_ANOMALY',
    jour: 3,
    tranche_id: 'T1',
    message: 'Stock insuffisant.',
    gravite: 'CRITICAL',
  },
  {
    type_alerte: 'REMIT_UMM',
    jour: 3,
    tranche_id: 'T2',
    message: 'Variation de puissance.',
    gravite: 'WARNING',
  },
  {
    type_alerte: 'REMIT_UMM',
    jour: null,
    tranche_id: 'T1',
    message: 'Variation hors timeline.',
    gravite: 'WARNING',
  },
  {
    type_alerte: 'RTE_DEFICIT',
    jour: 2,
    tranche_id: null,
    message: 'Offre insuffisante.',
    gravite: 'CRITICAL',
  },
  {
    type_alerte: 'SPOT_BELOW_USAGE_VALUE',
    jour: 3,
    tranche_id: null,
    message: 'Prix spot sous la valeur d’usage.',
    gravite: 'WARNING',
  },
  {
    type_alerte: 'RTE_DEFICIT',
    jour: 4,
    tranche_id: 'T1',
    message: 'Incohérence de portée.',
    gravite: 'CRITICAL',
  },
]

describe('hauteurBarre', () => {
  it('est proportionnelle au facteur de production', () => {
    expect(hauteurBarre(0)).toBe(0)
    expect(hauteurBarre(0.25)).toBe(25)
    expect(hauteurBarre(1)).toBe(100)
  })

  it('borne les facteurs hors plage', () => {
    expect(hauteurBarre(-1)).toBe(0)
    expect(hauteurBarre(2)).toBe(100)
  })
})

describe('construireJoursTimeline', () => {
  const jours = construireJoursTimeline({
    simulationTranche,
    resultat,
    alertes,
    horizonJours: 8,
  })

  it('produit un jour par jour de l’horizon', () => {
    expect(jours).toHaveLength(8)
    expect(jours[0].jour).toBe(0)
    expect(jours[7].jour).toBe(7)
  })

  it('affiche une maintenance grise et pleine hauteur', () => {
    expect(estMaintenance(1, simulationTranche.arrets)).toBe(true)
    expect(jours[1].estMaintenance).toBe(true)
    expect(jours[1].hauteurProduction).toBe(0)
    expect(jours[1].hauteurAffichee).toBe(100)
  })

  it('garde la hauteur du facteur réel hors maintenance', () => {
    expect(jours[3].estMaintenance).toBe(false)
    expect(jours[3].hauteurAffichee).toBe(80)
  })

  it('marque une modulation sans changer la hauteur réelle', () => {
    expect(jours[3].modulation?.facteur).toBe(0.5)
    expect(jours[3].marquageModulation).toBe(true)
    expect(jours[3].hauteurAffichee).toBe(80)
  })

  it('donne la priorité à la maintenance sur le marquage de modulation', () => {
    const jourChevauche = construireJoursTimeline({
      simulationTranche: {
        ...simulationTranche,
        arrets: [{ type_arret: 'ASR', jour_debut: 3, jour_fin: 4 }],
        modulations: [{ jour_debut: 3, jour_fin: 5, facteur: 0.2 }],
      },
      resultat,
      alertes,
      horizonJours: 4,
    })[3]

    expect(jourChevauche.estMaintenance).toBe(true)
    expect(jourChevauche.modulation).not.toBeNull()
    expect(jourChevauche.marquageModulation).toBe(false)
    expect(jourChevauche.hauteurAffichee).toBe(100)
  })

  it('filtre les alertes de tranche sur le bon jour', () => {
    expect(jours[3].alertes).toHaveLength(1)
    expect(jours[3].alertes[0].type_alerte).toBe('NEUTRONIC_ANOMALY')
    expect(jours[4].alertes).toHaveLength(0)
  })
})

describe('filtrage des alertes', () => {
  it('ne garde que les alertes de tranche du bon identifiant', () => {
    const resultatFiltre = filtrerAlertesTranche(alertes, 'T1')

    expect(resultatFiltre).toHaveLength(2)
    expect(
      resultatFiltre.every((alerte) => alerte.tranche_id === 'T1'),
    ).toBe(true)
    expect(
      resultatFiltre.some(
        (alerte) => alerte.type_alerte === 'RTE_DEFICIT',
      ),
    ).toBe(false)
  })

  it('exclut les alertes sans jour de la timeline', () => {
    expect(alertesTranchePourJour(alertes, 'T1', 3)).toHaveLength(1)
  })

  it('ne garde que les alertes nationales sans tranche', () => {
    const nationales = filtrerAlertesNationales(alertes)

    expect(nationales).toHaveLength(2)
    expect(
      nationales.every(
        (alerte) =>
          alerte.tranche_id === null &&
          (alerte.type_alerte === 'RTE_DEFICIT' ||
            alerte.type_alerte === 'SPOT_BELOW_USAGE_VALUE'),
      ),
    ).toBe(true)
  })
})

describe('validation des plannings', () => {
  it('accepte des fenêtres qui se touchent', () => {
    expect(
      validerFenetres(
        [
          { jour_debut: 0, jour_fin: 10 },
          { jour_debut: 10, jour_fin: 20 },
        ],
        30,
        'Arrêt',
      ),
    ).toEqual([])
  })

  it('signale un chevauchement et un dépassement d’horizon', () => {
    const erreurs = validerFenetres(
      [
        { jour_debut: 0, jour_fin: 15 },
        { jour_debut: 10, jour_fin: 40 },
      ],
      30,
      'Arrêt',
    )

    expect(erreurs.some((erreur) => erreur.message.includes('chevauche'))).toBe(
      true,
    )
    expect(
      erreurs.some((erreur) => erreur.message.includes('dépasse l’horizon')),
    ).toBe(true)
  })

  it('signale un facteur de modulation hors bornes', () => {
    const erreurs = validerModulations(
      [{ jour_debut: 0, jour_fin: 10, facteur: 1.5 }],
      30,
    )

    expect(erreurs[0].message).toContain('facteur')
  })
})
