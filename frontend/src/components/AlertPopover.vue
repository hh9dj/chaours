<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

import type { Alerte } from '../api/types'
import { classesGravite, libellesGravite } from '../lib/couleurs'
import { libelleTypeAlerte } from '../lib/timeline'

const props = defineProps<{
  alertes: Alerte[]
  jour: number
  positionPct: number
}>()

const emit = defineEmits<{ fermer: [] }>()

const panneau = ref<HTMLElement | null>(null)

function surTouche(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('fermer')
}

onMounted(() => {
  document.addEventListener('keydown', surTouche)
  panneau.value?.focus()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', surTouche)
})
</script>

<template>
  <div
    class="absolute top-full z-30 mt-3 w-80 max-w-[calc(100vw-3rem)]"
    :style="{
      left: `${Math.min(88, Math.max(12, positionPct))}%`,
      transform: 'translateX(-50%)',
    }"
  >
    <section
      ref="panneau"
      role="dialog"
      aria-modal="false"
      :aria-label="`Alertes du jour ${jour}`"
      tabindex="-1"
      class="rounded-xl border border-slate-200 bg-white p-4 text-left shadow-xl"
    >
      <header class="flex items-start justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Alertes de tranche
          </p>
          <h3 class="mt-0.5 text-sm font-semibold text-slate-950">
            Jour {{ props.jour }}
          </h3>
        </div>
        <button
          type="button"
          class="bouton-discret -mr-1 -mt-1"
          aria-label="Fermer les alertes"
          @click="emit('fermer')"
        >
          <span aria-hidden="true" class="text-lg leading-none">×</span>
        </button>
      </header>

      <ul class="mt-3 space-y-3">
        <li
          v-for="(alerte, index) in alertes"
          :key="`${alerte.type_alerte}-${index}`"
          class="rounded-lg border border-slate-100 bg-slate-50/70 p-3"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset"
              :class="classesGravite[alerte.gravite]"
            >
              {{ libellesGravite[alerte.gravite] }}
            </span>
            <span class="text-xs font-semibold text-slate-700">
              {{ libelleTypeAlerte(alerte.type_alerte) }}
            </span>
          </div>
          <p class="mt-2 text-sm leading-relaxed text-slate-700">
            {{ alerte.message }}
          </p>
          <p
            v-if="alerte.tranche_id"
            class="mt-2 text-xs text-slate-500"
          >
            Tranche : {{ alerte.tranche_id }}
          </p>
        </li>
      </ul>
    </section>
  </div>
</template>
