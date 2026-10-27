<script setup lang="ts">
import { RouterLink } from 'vue-router'

import type { SimulationResume } from '../api/types'
import { formaterDate, formaterEntier } from '../lib/format'

defineProps<{
  simulation: SimulationResume
}>()
</script>

<template>
  <RouterLink
    :to="`/simulations/${simulation.simulation_id}`"
    class="group panneau relative flex min-h-48 flex-col overflow-hidden p-5 transition hover:-translate-y-0.5 hover:border-sky-300 hover:shadow-md"
    :aria-label="`Ouvrir la simulation ${simulation.nom}`"
  >
    <span
      class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-sky-500 to-emerald-400"
      aria-hidden="true"
    />

    <span class="mt-1 text-xs font-semibold uppercase tracking-wider text-sky-700">
      Simulation
    </span>
    <span class="mt-2 line-clamp-2 text-lg font-semibold text-slate-950">
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
      <span class="font-semibold text-sky-700 transition group-hover:translate-x-0.5">
        Ouvrir →
      </span>
    </span>
  </RouterLink>
</template>
