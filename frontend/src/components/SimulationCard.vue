<script setup lang="ts">
import { RouterLink } from 'vue-router'

import type { SimulationResume } from '../api/types'
import { formaterDate, formaterEntier } from '../lib/format'

defineProps<{
  simulation: SimulationResume
}>()

const emit = defineEmits<{
  supprimer: []
}>()
</script>

<template>
  <article
    class="group panneau relative min-h-48 overflow-hidden transition hover:-translate-y-0.5 hover:border-edf-blue hover:shadow-md"
  >
    <span
      class="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-edf-blue to-edf-orange"
      aria-hidden="true"
    />

    <RouterLink
      :to="`/simulations/${simulation.simulation_id}`"
      class="flex min-h-48 flex-col p-5"
      :aria-label="`Ouvrir la simulation ${simulation.nom}`"
    >
      <span class="mt-1 text-xs font-semibold uppercase tracking-wider text-edf-blue">
        Simulation
      </span>
      <span class="mt-2 line-clamp-2 pr-8 text-lg font-semibold text-slate-950">
        {{ simulation.nom }}
      </span>

      <span class="mt-auto grid grid-cols-2 gap-3 pt-6 text-sm">
        <span>
          <span class="block text-xs text-slate-500">Horizon</span>
          <span class="font-semibold text-slate-800">
            {{ formaterEntier(simulation.horizon_jours) }} jours
          </span>
        </span>
        <span>
          <span class="block text-xs text-slate-500">Tranches</span>
          <span class="font-semibold text-slate-800">
            {{ formaterEntier(simulation.nombre_tranches) }}
          </span>
        </span>
      </span>

      <span class="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span>Créée le {{ formaterDate(simulation.cree_le) }}</span>
        <span class="font-semibold text-edf-blue transition group-hover:translate-x-0.5 group-hover:text-edf-orange">
          Ouvrir →
        </span>
      </span>
    </RouterLink>

    <button
      type="button"
      class="absolute right-3 top-3 z-10 rounded-md p-1.5 text-slate-400 transition hover:bg-red-50 hover:text-red-700 focus-visible:bg-red-50 focus-visible:text-red-700"
      :aria-label="`Supprimer la simulation ${simulation.nom}`"
      title="Supprimer la simulation"
      @click="emit('supprimer')"
    >
      <svg
        class="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        aria-hidden="true"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M6 7h12M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m-7 0 1 13h8l1-13M10 11v5m4-5v5"
        />
      </svg>
    </button>
  </article>
</template>
