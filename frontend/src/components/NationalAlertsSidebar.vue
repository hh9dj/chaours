<script setup lang="ts">
import { computed } from 'vue'

import type { Alerte } from '../api/types'
import { classesGravite, libellesGravite } from '../lib/couleurs'
import {
  filtrerAlertesNationales,
  libelleTypeAlerte,
} from '../lib/timeline'

const props = defineProps<{
  alertes: Alerte[]
}>()

const alertesNationales = computed(() =>
  filtrerAlertesNationales(props.alertes),
)
</script>

<template>
  <aside
    class="flex max-h-[calc(100vh-9rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
    aria-labelledby="alertes-nationales-titre"
  >
    <header class="border-b border-slate-200 px-5 py-4">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Vision nationale
          </p>
          <h2 id="alertes-nationales-titre" class="mt-0.5 text-base font-semibold text-slate-950">
            Alertes nationales
          </h2>
        </div>
        <span
          class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700"
          :aria-label="`${alertesNationales.length} alertes nationales`"
        >
          {{ alertesNationales.length }}
        </span>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto p-4">
      <div
        v-if="alertesNationales.length === 0"
        class="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center"
      >
        <p class="text-sm font-semibold text-slate-700">
          Aucune alerte nationale
        </p>
        <p class="mt-1 text-xs leading-relaxed text-slate-500">
          L’offre couvre la demande et le prix spot reste au-dessus de la valeur
          d’usage sur tout l’horizon.
        </p>
      </div>

      <ul v-else class="space-y-3">
        <li
          v-for="(alerte, index) in alertesNationales"
          :key="`${alerte.type_alerte}-${alerte.jour ?? 'sans-jour'}-${index}`"
          class="rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset"
              :class="classesGravite[alerte.gravite]"
            >
              {{ libellesGravite[alerte.gravite] }}
            </span>
            <span
              v-if="alerte.jour !== null"
              class="text-[11px] font-semibold text-slate-500"
            >
              Jour {{ alerte.jour }}
            </span>
            <span v-else class="text-[11px] text-slate-500">
              Jour non précisé
            </span>
          </div>

          <h3 class="mt-2 text-sm font-semibold text-slate-900">
            {{ libelleTypeAlerte(alerte.type_alerte) }}
          </h3>
          <p class="mt-1 text-xs leading-relaxed text-slate-600">
            {{ alerte.message }}
          </p>
        </li>
      </ul>
    </div>
  </aside>
</template>
