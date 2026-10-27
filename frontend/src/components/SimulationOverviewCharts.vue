<script setup lang="ts">
import { computed } from 'vue'

import type { ResultatSimulation, Simulation } from '../api/types'
import {
  formaterEnergie,
  formaterEntier,
  formaterEuros,
} from '../lib/format'
import {
  statistiquesEnergie,
  statistiquesPrix,
  type SerieGraphique,
  type StatistiqueGraphique,
} from '../lib/overview'
import OverviewChartPanel from './OverviewChartPanel.vue'

const props = defineProps<{
  simulation: Simulation
  resultat: ResultatSimulation | null
}>()

interface PanneauGraphique {
  cle: 'energie' | 'prix'
  titre: string
  unite: string
  series: SerieGraphique[]
  stats: StatistiqueGraphique[]
  description: string
  formatValeur: (valeur: number) => string
  noteJour: (jour: number) => string | null
}

const horizon = computed(() =>
  Math.max(1, Math.floor(props.simulation.horizon_jours)),
)

const production = computed(
  () => props.resultat?.offre_nationale_mwh ?? [],
)
const demande = computed(() => props.resultat?.demande_mwh ?? [])
const spot = computed(() => props.simulation.prix_spot_eur_mwh)
const valeurUsage = computed(
  () => props.simulation.valeur_usage_eur_mwh,
)

const statsEnergie = computed(() =>
  statistiquesEnergie(production.value, demande.value),
)
const statsPrix = computed(() =>
  statistiquesPrix(spot.value, valeurUsage.value),
)

const panneaux = computed<PanneauGraphique[]>(() => {
  const energie = statsEnergie.value
  const prix = statsPrix.value

  return [
    {
      cle: 'energie',
      titre: 'Production agrégée et demande nationale',
      unite: 'MWh/jour',
      series: [
        {
          libelle: 'Production agrégée',
          valeurs: production.value,
          classeTrait: 'stroke-edf-teal',
          classeRemplissage: 'fill-edf-teal/20',
          classePastille: 'bg-edf-teal',
          aire: true,
        },
        {
          libelle: 'Demande nationale',
          valeurs: demande.value,
          classeTrait: 'stroke-edf-blue',
          classePastille: 'bg-edf-blue',
        },
      ],
      stats: [
        {
          libelle: 'Production totale',
          valeur: formaterEnergie(energie.productionTotale),
        },
        {
          libelle: 'Pic de demande',
          valeur: formaterEnergie(energie.picDemande),
        },
        {
          libelle: 'Jours de déficit',
          valeur: formaterEntier(energie.joursDeficit),
        },
      ],
      description: `Production agrégée et demande nationale sur ${horizon.value} jours. Production totale ${formaterEnergie(energie.productionTotale)}. Pic de demande ${formaterEnergie(energie.picDemande)}. ${formaterEntier(energie.joursDeficit)} jours de déficit.`,
      formatValeur: formaterEnergie,
      noteJour: (jour) => {
        const productionJour = production.value[jour] ?? 0
        const demandeJour = demande.value[jour] ?? 0
        return productionJour < demandeJour ? 'Déficit national' : null
      },
    },
    {
      cle: 'prix',
      titre: 'Prix spot et valeur d’usage',
      unite: '€/MWh',
      series: [
        {
          libelle: 'Prix spot',
          valeurs: spot.value,
          classeTrait: 'stroke-edf-orange',
          classePastille: 'bg-edf-orange',
        },
        {
          libelle: 'Valeur d’usage',
          valeurs: valeurUsage.value,
          classeTrait: 'stroke-edf-cyan',
          classePastille: 'bg-edf-cyan',
          pointilles: true,
        },
      ],
      stats: [
        {
          libelle: 'Spot moyen',
          valeur: formaterEuros(prix.spotMoyen),
        },
        {
          libelle: 'VU moyenne',
          valeur: formaterEuros(prix.vuMoyenne),
        },
        {
          libelle: 'Jours spot < VU',
          valeur: formaterEntier(prix.joursSpotSousVu),
        },
      ],
      description: `Prix spot et valeur d’usage sur ${horizon.value} jours. Prix spot moyen ${formaterEuros(prix.spotMoyen)}. Valeur d’usage moyenne ${formaterEuros(prix.vuMoyenne)}. ${formaterEntier(prix.joursSpotSousVu)} jours avec un prix spot sous la valeur d’usage.`,
      formatValeur: formaterEuros,
      noteJour: (jour) => {
        const spotJour = spot.value[jour]
        const vuJour = valeurUsage.value[jour]
        if (!Number.isFinite(spotJour) || !Number.isFinite(vuJour)) {
          return null
        }
        return spotJour < vuJour ? 'Spot sous la valeur d’usage' : null
      },
    },
  ]
})
</script>

<template>
  <section
    class="grid gap-5 xl:grid-cols-2"
    aria-label="Courbes de synthèse de la simulation"
  >
    <template v-if="resultat">
      <OverviewChartPanel
        v-for="panneau in panneaux"
        :key="panneau.cle"
        :titre="panneau.titre"
        :unite="panneau.unite"
        :horizon-jours="horizon"
        :series="panneau.series"
        :stats="panneau.stats"
        :format-valeur="panneau.formatValeur"
        :description="panneau.description"
        :note-jour="panneau.noteJour"
      />
    </template>

    <div
      v-else
      class="panneau flex min-h-40 items-center justify-center px-6 py-8 text-center text-sm text-slate-500 xl:col-span-2"
    >
      Les courbes de synthèse apparaîtront dès que le calcul sera disponible.
    </div>
  </section>
</template>
