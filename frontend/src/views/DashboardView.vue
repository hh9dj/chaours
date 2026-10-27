<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import type { Simulation, SimulationResume } from '../api/types'
import AddSimulationCard from '../components/AddSimulationCard.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import CreateSimulationDialog from '../components/CreateSimulationDialog.vue'
import SimulationCard from '../components/SimulationCard.vue'
import { useSimulationsStore } from '../stores/simulations'

const store = useSimulationsStore()
const router = useRouter()
const dialogueCreation = ref(false)
const simulationASupprimer = ref<SimulationResume | null>(null)

const nombreSimulations = computed(() => store.simulations.length)

function ouvrirCreation() {
  store.reinitialiserErreur()
  dialogueCreation.value = true
}

async function simulationCreee(simulation: Simulation) {
  dialogueCreation.value = false
  await router.push(`/simulations/${simulation.simulation_id}`)
}

function demanderSuppression(simulation: SimulationResume) {
  store.reinitialiserErreur()
  simulationASupprimer.value = simulation
}

function annulerSuppression() {
  simulationASupprimer.value = null
}

async function confirmerSuppression() {
  const simulation = simulationASupprimer.value
  if (!simulation) return

  try {
    await store.supprimerSimulation(simulation.simulation_id)
    simulationASupprimer.value = null
  } catch {
    // L'erreur est affichée par le store.
    simulationASupprimer.value = null
  }
}

onMounted(() => {
  void store.chargerListe()
})
</script>

<template>
  <section class="space-y-7">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-edf-blue">
          Tableau de bord
        </p>
        <h1 class="mt-1 text-3xl font-bold tracking-tight text-edf-blue">
          Simulations
        </h1>
        <p class="mt-2 max-w-2xl text-sm text-slate-600">
          Consulter ou créer une simulation
        </p>
      </div>

      <div class="flex items-center gap-3">
        <span
          v-if="!store.loading"
          class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm"
        >
          {{ nombreSimulations }}
          simulation{{ nombreSimulations > 1 ? 's' : '' }}
        </span>
        <button type="button" class="bouton-primaire" @click="ouvrirCreation">
          <span class="text-edf-orange" aria-hidden="true">+</span>
          Nouvelle simulation
        </button>
      </div>
    </header>

    <div
      v-if="store.error"
      role="alert"
      class="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <p>{{ store.error }}</p>
      <button
        type="button"
        class="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-semibold text-red-800 transition hover:bg-red-100"
        @click="store.chargerListe()"
      >
        Réessayer
      </button>
    </div>

    <div v-if="store.loading && store.simulations.length === 0" aria-live="polite">
      <p class="sr-only">Chargement des simulations…</p>
      <div class="grid gap-5 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        <div
          v-for="index in 3"
          :key="index"
          class="h-48 animate-pulse rounded-2xl border border-slate-200 bg-white/70 p-5"
        >
          <div class="h-3 w-24 rounded bg-slate-200" />
          <div class="mt-4 h-5 w-2/3 rounded bg-slate-200" />
          <div class="mt-12 h-3 w-1/2 rounded bg-slate-100" />
          <div class="mt-3 h-3 w-1/3 rounded bg-slate-100" />
        </div>
      </div>
    </div>

    <template v-else>
      <div
        v-if="store.simulations.length === 0 && !store.error"
        class="panneau flex flex-col items-start gap-3 border-dashed px-6 py-8 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h2 class="text-base font-semibold text-slate-900">
            Aucune simulation pour le moment
          </h2>
          <p class="mt-1 text-sm text-slate-600">
            Créez une première simulation pour visualiser la timeline des
            tranches et les alertes nationales.
          </p>
        </div>
        <button type="button" class="bouton-secondaire" @click="ouvrirCreation">
          Créer une simulation
        </button>
      </div>

      <div class="grid gap-5 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        <SimulationCard
          v-for="simulation in store.simulations"
          :key="simulation.simulation_id"
          :simulation="simulation"
          @supprimer="demanderSuppression(simulation)"
        />
        <AddSimulationCard @creer="ouvrirCreation" />
      </div>
    </template>

    <CreateSimulationDialog
      v-if="dialogueCreation"
      @fermer="dialogueCreation = false"
      @cree="simulationCreee"
    />

    <ConfirmDialog
      v-if="simulationASupprimer"
      titre="Supprimer la simulation"
      :message="`La simulation « ${simulationASupprimer.nom} », ses tranches, ses arrêts et ses modulations seront définitivement supprimés.`"
      libelle-confirmation="Supprimer la simulation"
      :occupe="store.saving"
      @fermer="annulerSuppression"
      @confirmer="confirmerSuppression"
    />
  </section>
</template>
