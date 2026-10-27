<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import NationalAlertsSidebar from '../components/NationalAlertsSidebar.vue'
import SimulationSettingsDialog from '../components/SimulationSettingsDialog.vue'
import TrancheEditor from '../components/TrancheEditor.vue'
import TrancheTimeline from '../components/TrancheTimeline.vue'
import {
  formaterDate,
  formaterEntier,
  formaterNombre,
} from '../lib/format'
import { useSimulationsStore } from '../stores/simulations'

const props = defineProps<{
  simulation_id: string
}>()

const store = useSimulationsStore()
const trancheEditee = ref<string | null>(null)
const parametresOuverts = ref(false)

const simulationCourante = computed(() => store.currentSimulation)
const resultat = computed(() => store.currentResult)
const simulationIntrouvable = computed(
  () => store.errorStatus === 404 && simulationCourante.value === null,
)

const trancheSelectionnee = computed(() =>
  simulationCourante.value?.tranches.find(
    (tranche) =>
      tranche.tranche.identifiant === trancheEditee.value,
  ),
)

function resultatTranche(trancheId: string) {
  return (
    resultat.value?.tranches.find(
      (resultatTranche) => resultatTranche.tranche_id === trancheId,
    ) ?? null
  )
}

function ouvrirEditeur(trancheId: string) {
  trancheEditee.value = trancheId
}

function fermerEditeur() {
  trancheEditee.value = null
}

async function relancer() {
  try {
    await store.relancerSimulation(props.simulation_id)
  } catch {
    // L'erreur est affichée par le store.
  }
}

watch(
  () => props.simulation_id,
  (simulationId) => {
    if (simulationId) {
      trancheEditee.value = null
      parametresOuverts.value = false
      void store.chargerSimulation(simulationId)
    }
  },
  { immediate: true },
)
</script>

<template>
  <section class="space-y-6">
    <RouterLink
      to="/"
      class="inline-flex items-center gap-1.5 rounded-md text-sm font-medium text-slate-600 transition hover:text-slate-950"
    >
      <span aria-hidden="true">←</span>
      Retour au tableau de bord
    </RouterLink>

    <div
      v-if="store.loading && !simulationCourante"
      aria-live="polite"
      class="space-y-5"
    >
      <p class="sr-only">Chargement de la simulation…</p>
      <div class="panneau h-32 animate-pulse bg-white/70" />
      <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <div class="space-y-4">
          <div
            v-for="index in 2"
            :key="index"
            class="panneau h-64 animate-pulse bg-white/70"
          />
        </div>
        <div class="panneau h-72 animate-pulse bg-white/70" />
      </div>
    </div>

    <div
      v-else-if="store.error && !simulationCourante"
      class="panneau flex flex-col items-start gap-4 px-6 py-10"
      role="alert"
    >
      <div>
        <p class="text-xs font-semibold uppercase tracking-wider text-red-700">
          Erreur
        </p>
        <h1 class="mt-1 text-2xl font-bold text-slate-950">
          {{
            simulationIntrouvable
              ? 'Simulation introuvable'
              : 'Impossible de charger la simulation'
          }}
        </h1>
        <p class="mt-2 max-w-2xl text-sm text-slate-600">
          {{
            simulationIntrouvable
              ? 'Cette simulation n’existe pas ou a été supprimée.'
              : store.error
          }}
        </p>
      </div>
      <div class="flex flex-wrap gap-3">
        <button
          v-if="!simulationIntrouvable"
          type="button"
          class="bouton-primaire"
          @click="store.chargerSimulation(props.simulation_id)"
        >
          Réessayer
        </button>
        <RouterLink to="/" class="bouton-secondaire">
          Revenir au tableau de bord
        </RouterLink>
      </div>
    </div>

    <template v-else-if="simulationCourante">
      <header class="panneau px-6 py-5">
        <div class="flex flex-wrap items-start justify-between gap-5">
          <div class="min-w-0">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-sky-700">
              Simulation
            </p>
            <h1 class="mt-1 truncate text-3xl font-bold tracking-tight text-slate-950">
              {{ simulationCourante.nom }}
            </h1>
            <p class="mt-2 text-sm text-slate-600">
              Horizon de {{ formaterEntier(simulationCourante.horizon_jours) }} jours ·
              créée le {{ formaterDate(simulationCourante.cree_le) }} ·
              {{ simulationCourante.tranches.length }} tranche{{
                simulationCourante.tranches.length > 1 ? 's' : ''
              }}
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <span
              v-if="resultat"
              class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600"
              title="Durée d’exécution du moteur côté serveur"
            >
              Calcul serveur : {{ formaterNombre(resultat.duree_execution_ms) }} ms
            </span>
            <button
              type="button"
              class="bouton-secondaire"
              :disabled="store.saving || store.loading"
              @click="relancer"
            >
              {{ store.saving ? 'Calcul…' : 'Recalculer' }}
            </button>
            <button
              type="button"
              class="bouton-primaire"
              @click="parametresOuverts = true"
            >
              Paramètres
            </button>
          </div>
        </div>
      </header>

      <div
        v-if="store.error"
        role="alert"
        class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      >
        <p>{{ store.error }}</p>
        <button
          type="button"
          class="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-800 transition hover:bg-red-100"
          @click="store.reinitialiserErreur()"
        >
          Masquer
        </button>
      </div>

      <div class="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <div class="space-y-5">
          <article
            v-for="simulationTranche in simulationCourante.tranches"
            :key="simulationTranche.tranche.identifiant"
            class="panneau px-5 py-5"
          >
            <header class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <h2 class="text-lg font-semibold text-slate-950">
                    Tranche {{ simulationTranche.tranche.identifiant }}
                  </h2>
                  <span
                    class="rounded-full bg-sky-50 px-2 py-0.5 text-[11px] font-semibold text-sky-700 ring-1 ring-inset ring-sky-200"
                  >
                    {{ simulationTranche.tranche.code_eic }}
                  </span>
                </div>
                <dl class="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-600">
                  <div>
                    <dt class="inline text-slate-500">Puissance nominale :</dt>
                    <dd class="inline font-semibold text-slate-800">
                      {{ formaterNombre(simulationTranche.tranche.puissance_nominale_mw) }} MW
                    </dd>
                  </div>
                  <div>
                    <dt class="inline text-slate-500">JEPP initial :</dt>
                    <dd class="inline font-semibold text-slate-800">
                      {{ formaterNombre(simulationTranche.tranche.jepp_initial) }}
                    </dd>
                  </div>
                  <div>
                    <dt class="inline text-slate-500">Arrêts :</dt>
                    <dd class="inline font-semibold text-slate-800">
                      {{ simulationTranche.arrets.length }}
                    </dd>
                  </div>
                  <div>
                    <dt class="inline text-slate-500">Modulations :</dt>
                    <dd class="inline font-semibold text-slate-800">
                      {{ simulationTranche.modulations.length }}
                    </dd>
                  </div>
                </dl>
              </div>

              <button
                type="button"
                class="bouton-secondaire"
                @click="ouvrirEditeur(simulationTranche.tranche.identifiant)"
              >
                Modifier la tranche
              </button>
            </header>

            <div class="mt-5">
              <p class="mb-3 text-xs text-slate-500">
                Cliquez sur la timeline ou sur un jour pour ouvrir l’éditeur.
                Les icônes signalent les alertes de tranche.
              </p>
              <TrancheTimeline
                :simulation-tranche="simulationTranche"
                :resultat="resultatTranche(simulationTranche.tranche.identifiant)"
                :alertes="resultat?.alertes ?? []"
                :horizon-jours="simulationCourante.horizon_jours"
                @ouvrir-editeur="ouvrirEditeur(simulationTranche.tranche.identifiant)"
              />
            </div>
          </article>
        </div>

        <div class="xl:sticky xl:top-4">
          <NationalAlertsSidebar :alertes="resultat?.alertes ?? []" />
        </div>
      </div>

      <TrancheEditor
        v-if="trancheSelectionnee"
        :key="trancheSelectionnee.tranche.identifiant"
        :simulation-id="props.simulation_id"
        :simulation-tranche="trancheSelectionnee"
        :horizon-jours="simulationCourante.horizon_jours"
        @fermer="fermerEditeur"
        @enregistre="fermerEditeur"
      />

      <SimulationSettingsDialog
        v-if="parametresOuverts"
        :simulation-id="props.simulation_id"
        :simulation="simulationCourante"
        @fermer="parametresOuverts = false"
        @enregistre="parametresOuverts = false"
      />
    </template>
  </section>
</template>
