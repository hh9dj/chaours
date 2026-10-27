<script setup lang="ts">
import { computed, ref } from 'vue'

import type {
  Alerte,
  ResultatTranche,
  SimulationTranche,
} from '../api/types'
import {
  classesCouleurJepp,
  libellesCouleurJepp,
} from '../lib/couleurs'
import {
  formaterEnergie,
  formaterNombre,
  formaterPourcentage,
} from '../lib/format'
import {
  construireJoursTimeline,
  libelleJourEtAlerte,
  libelleTypeArret,
  type JourTimeline,
} from '../lib/timeline'
import AlertPopover from './AlertPopover.vue'

const props = defineProps<{
  simulationTranche: SimulationTranche
  resultat: ResultatTranche | null
  alertes: Alerte[]
  horizonJours: number
}>()

const emit = defineEmits<{ ouvrirEditeur: [] }>()

const alertesOuvertes = ref<{
  jour: number
  alertes: Alerte[]
  positionPct: number
} | null>(null)

const jours = computed(() =>
  construireJoursTimeline({
    simulationTranche: props.simulationTranche,
    resultat: props.resultat,
    alertes: props.alertes,
    horizonJours: props.horizonJours,
  }),
)

const derniereJournee = computed(() => Math.max(0, props.horizonJours - 1))

function positionJour(jour: number): number {
  if (derniereJournee.value === 0) return 50
  return (jour / derniereJournee.value) * 100
}

function ouvrirAlertes(jour: JourTimeline) {
  alertesOuvertes.value = {
    jour: jour.jour,
    alertes: jour.alertes,
    positionPct: positionJour(jour.jour),
  }
}

function libelleJour(jour: JourTimeline): string {
  const parties = [
    libelleJourEtAlerte(jour.jour, jour.alertes),
    formaterPourcentage(jour.facteurProduction),
    `énergie ${formaterEnergie(jour.energieMwh)}`,
    `JEPP restant ${formaterNombre(jour.jeppRestant)} sur ${formaterNombre(jour.jeppInitial)}`,
    jour.estMaintenance && jour.arret
      ? `arrêt ${jour.arret.type_arret} en cours`
      : null,
    jour.modulation
      ? `modulation à ${formaterPourcentage(jour.modulation.facteur)}`
      : null,
    jour.alertes.length > 0
      ? `${jour.alertes.length} alerte${jour.alertes.length > 1 ? 's' : ''} de tranche`
      : null,
  ]

  return parties.filter((partie): partie is string => partie !== null).join(', ')
}
</script>

<template>
  <div class="relative">
    <div
      v-if="alertesOuvertes"
      class="fixed inset-0 z-20"
      aria-hidden="true"
      @click="alertesOuvertes = null"
    />

    <div class="mb-2 flex items-center justify-between text-[11px] text-slate-500">
      <span>Jour 0</span>
      <span>Jour {{ derniereJournee }}</span>
    </div>

    <div
      class="flex h-32 items-end rounded-lg border border-slate-200 bg-slate-50 px-2 pb-3 pt-7"
      role="group"
      :aria-label="`Timeline de la tranche ${simulationTranche.tranche.identifiant}`"
    >
      <div
        v-for="jour in jours"
        :key="jour.jour"
        class="group relative flex h-full min-w-0 flex-1 cursor-pointer items-end rounded-sm"
        role="group"
        tabindex="0"
        :aria-label="libelleJour(jour)"
        @click="emit('ouvrirEditeur')"
        @keydown.enter.self.prevent="emit('ouvrirEditeur')"
        @keydown.space.self.prevent="emit('ouvrirEditeur')"
      >
        <span
          class="w-full rounded-t-[2px] transition group-hover:brightness-110"
          :class="
            jour.estMaintenance
              ? 'bg-slate-400'
              : classesCouleurJepp[jour.couleurJepp]
          "
          :style="{ height: `${jour.hauteurAffichee}%` }"
          aria-hidden="true"
        />
        <span
          v-if="jour.marquageModulation"
          class="absolute inset-x-0 top-0 h-1 rounded-t-sm bg-sky-500"
          aria-hidden="true"
        />

        <button
          v-if="jour.alertes.length > 0"
          type="button"
          class="absolute -top-6 left-1/2 z-10 flex h-5 w-5 -translate-x-1/2 items-center justify-center rounded-full bg-amber-400 text-[11px] font-black text-amber-950 shadow ring-2 ring-white transition hover:bg-amber-300"
          :aria-label="`Voir les alertes du jour ${jour.jour}`"
          :aria-expanded="alertesOuvertes?.jour === jour.jour"
          aria-haspopup="dialog"
          @click.stop="ouvrirAlertes(jour)"
          @keydown.enter.stop
        >
          !
        </button>

        <div
          class="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 hidden w-64 -translate-x-1/2 rounded-lg border border-slate-700 bg-slate-900 p-3 text-left text-xs text-slate-100 shadow-xl group-hover:block group-focus-within:block"
        >
          <p class="font-semibold text-white">Jour {{ jour.jour }}</p>
          <dl class="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
            <dt class="text-slate-400">Production</dt>
            <dd>{{ formaterPourcentage(jour.facteurProduction) }}</dd>
            <dt class="text-slate-400">Énergie</dt>
            <dd>{{ formaterEnergie(jour.energieMwh) }}</dd>
            <dt class="text-slate-400">JEPP restant</dt>
            <dd>
              {{ formaterNombre(jour.jeppRestant) }} /
              {{ formaterNombre(jour.jeppInitial) }}
            </dd>
            <template v-if="jour.estMaintenance && jour.arret">
              <dt class="text-slate-400">Arrêt</dt>
              <dd>{{ libelleTypeArret(jour.arret.type_arret) }}</dd>
            </template>
            <template v-if="jour.modulation">
              <dt class="text-slate-400">Modulation</dt>
              <dd>{{ formaterPourcentage(jour.modulation.facteur) }}</dd>
            </template>
          </dl>
        </div>
      </div>
    </div>

    <AlertPopover
      v-if="alertesOuvertes"
      :alertes="alertesOuvertes.alertes"
      :jour="alertesOuvertes.jour"
      :position-pct="alertesOuvertes.positionPct"
      @fermer="alertesOuvertes = null"
    />

    <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-slate-600">
      <span class="font-semibold text-slate-700">Légende :</span>
      <span class="inline-flex items-center gap-1.5">
        <span class="h-3 w-2 rounded-sm bg-slate-500" aria-hidden="true" />
        hauteur = production
      </span>
      <span class="inline-flex items-center gap-1.5">
        <span class="h-3 w-2 rounded-sm bg-slate-400" aria-hidden="true" />
        maintenance
      </span>
      <span
        v-for="couleur in (['vert', 'jaune', 'orange', 'rouge'] as const)"
        :key="couleur"
        class="inline-flex items-center gap-1.5"
      >
        <span
          class="h-3 w-2 rounded-sm"
          :class="classesCouleurJepp[couleur]"
          aria-hidden="true"
        />
        {{ libellesCouleurJepp[couleur] }}
      </span>
      <span class="inline-flex items-center gap-1.5">
        <span
          class="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-amber-400 text-[8px] font-black text-amber-950"
          aria-hidden="true"
        >
          !
        </span>
        alerte de tranche
      </span>
      <span class="inline-flex items-center gap-1.5">
        <span class="h-1 w-3 rounded-sm bg-sky-500" aria-hidden="true" />
        modulation
      </span>
    </div>
  </div>
</template>
