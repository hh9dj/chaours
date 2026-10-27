<script setup lang="ts">
import { computed, ref } from 'vue'

import { formaterNombre } from '../lib/format'
import {
  domaineSeries,
  echantillonnerSeries,
  jourDepuisRatio,
  type SerieGraphique,
  type StatistiqueGraphique,
} from '../lib/overview'

const props = defineProps<{
  titre: string
  unite: string
  horizonJours: number
  series: SerieGraphique[]
  stats: StatistiqueGraphique[]
  formatValeur: (valeur: number) => string
  description: string
  noteJour?: (jour: number) => string | null
}>()

const zone = ref<HTMLElement | null>(null)
const survol = ref<{
  jour: number
  xPct: number
  xBulle: number
} | null>(null)

const domaine = computed(() =>
  domaineSeries(
    props.series.map((serie) => serie.valeurs),
    { inclureZero: true },
  ),
)

const seriesAffichees = computed<SerieGraphique[]>(() => {
  const echantillon = echantillonnerSeries(
    props.series.map((serie) => serie.valeurs),
  )

  return props.series.map((serie, index) => ({
    ...serie,
    valeurs: echantillon.series[index] ?? [],
  }))
})

const dernierJour = computed(() =>
  Math.max(0, Math.floor(props.horizonJours) - 1),
)

function xPosition(index: number, longueur: number): number {
  if (longueur <= 1) return 500
  return (index / (longueur - 1)) * 1000
}

function yPosition(valeur: number): number {
  const { minimum, maximum } = domaine.value
  const etendue = maximum - minimum || 1
  return ((maximum - valeur) / etendue) * 300
}

function polyligne(valeurs: number[]): string {
  return valeurs
    .map(
      (valeur, index) =>
        `${xPosition(index, valeurs.length)},${yPosition(valeur)}`,
    )
    .join(' ')
}

function cheminAire(valeurs: number[]): string {
  if (valeurs.length === 0) return ''

  const points = valeurs.map(
    (valeur, index) =>
      `${xPosition(index, valeurs.length)},${yPosition(valeur)}`,
  )
  const premier = points[0]?.split(',')[0] ?? '0'
  const dernier = points[points.length - 1]?.split(',')[0] ?? '1000'

  return `M ${premier},300 L ${points.join(' L ')} L ${dernier},300 Z`
}

function survoler(event: PointerEvent) {
  const element = zone.value
  if (!element) return

  const rectangle = element.getBoundingClientRect()
  if (rectangle.width === 0) return

  const ratio = Math.min(
    1,
    Math.max(0, (event.clientX - rectangle.left) / rectangle.width),
  )
  const jour = jourDepuisRatio(ratio, props.horizonJours)
  const marge = Math.min(110, rectangle.width / 2)

  survol.value = {
    jour,
    xPct: ratio * 100,
    xBulle: Math.min(
      rectangle.width - marge,
      Math.max(marge, ratio * rectangle.width),
    ),
  }
}

function effacerSurvol() {
  survol.value = null
}

function notePourJour(jour: number): string | null {
  return props.noteJour?.(jour) ?? null
}
</script>

<template>
  <article class="panneau flex min-w-0 flex-col p-5">
    <header class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-sm font-semibold text-slate-950">{{ titre }}</h2>
        <p class="mt-0.5 text-xs text-slate-500">
          {{ unite }} · horizon de {{ Math.max(1, Math.floor(horizonJours)) }}
          jour{{ Math.floor(horizonJours) > 1 ? 's' : '' }}
        </p>
      </div>

      <dl class="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500">
        <div
          v-for="stat in stats"
          :key="stat.libelle"
          class="flex items-baseline gap-1"
        >
          <dt>{{ stat.libelle }}</dt>
          <dd class="font-semibold text-slate-800">{{ stat.valeur }}</dd>
        </div>
      </dl>
    </header>

    <div
      ref="zone"
      class="relative mt-4 h-44 cursor-crosshair"
      role="img"
      :aria-label="description"
      @pointermove="survoler"
      @pointerleave="effacerSurvol"
    >
      <svg
        class="absolute inset-0 h-full w-full"
        viewBox="0 0 1000 300"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <line
          v-for="ligne in [0, 75, 150, 225, 300]"
          :key="`h-${ligne}`"
          x1="0"
          :y1="ligne"
          x2="1000"
          :y2="ligne"
          class="stroke-slate-200"
          stroke-width="1"
          vector-effect="non-scaling-stroke"
        />
        <line
          v-for="colonne in [250, 500, 750]"
          :key="`v-${colonne}`"
          :x1="colonne"
          y1="0"
          :x2="colonne"
          y2="300"
          class="stroke-slate-200"
          stroke-width="1"
          vector-effect="non-scaling-stroke"
        />

        <template v-for="serie in seriesAffichees" :key="serie.libelle">
          <path
            v-if="serie.aire && serie.classeRemplissage"
            :d="cheminAire(serie.valeurs)"
            :class="serie.classeRemplissage"
            stroke="none"
          />
          <polyline
            v-if="polyligne(serie.valeurs)"
            :points="polyligne(serie.valeurs)"
            fill="none"
            :class="serie.classeTrait"
            stroke-width="2"
            stroke-linejoin="round"
            stroke-linecap="round"
            :stroke-dasharray="serie.pointilles ? '6 4' : undefined"
            vector-effect="non-scaling-stroke"
          />
        </template>
      </svg>

      <span
        class="pointer-events-none absolute left-2 top-1.5 rounded bg-white/85 px-1 text-[10px] font-medium text-slate-500"
      >
        {{ formaterNombre(domaine.maximum) }} {{ unite }}
      </span>
      <span
        class="pointer-events-none absolute bottom-1.5 left-2 rounded bg-white/85 px-1 text-[10px] font-medium text-slate-500"
      >
        {{ formaterNombre(domaine.minimum) }} {{ unite }}
      </span>
      <span
        class="pointer-events-none absolute bottom-1.5 right-2 rounded bg-white/85 px-1 text-[10px] font-medium text-slate-500"
      >
        Jour {{ dernierJour }}
      </span>

      <template v-if="survol">
        <span
          class="pointer-events-none absolute inset-y-0 w-px bg-edf-blue/40"
          :style="{ left: `${survol.xPct}%` }"
          aria-hidden="true"
        />
        <div
          class="pointer-events-none absolute top-2 z-10 w-52 -translate-x-1/2 whitespace-nowrap rounded-md border border-edf-blue-deep bg-edf-blue px-2 py-1.5 text-[11px] text-blue-50 shadow-lg"
          :style="{ left: `${survol.xBulle}px` }"
          aria-hidden="true"
        >
          <p class="font-semibold text-white">Jour {{ survol.jour }}</p>
          <p
            v-for="serie in series"
            :key="serie.libelle"
            class="mt-0.5 flex items-center justify-between gap-3"
          >
            <span class="flex items-center gap-1.5 text-blue-100/75">
              <span
                class="h-1.5 w-1.5 rounded-full"
                :class="serie.classePastille"
                aria-hidden="true"
              />
              {{ serie.libelle }}
            </span>
            <span class="font-semibold">
              {{ formatValeur(serie.valeurs[survol.jour] ?? 0) }}
            </span>
          </p>
          <p
            v-if="notePourJour(survol.jour)"
            class="mt-1 border-t border-edf-blue-deep pt-1 font-semibold text-orange-200"
          >
            {{ notePourJour(survol.jour) }}
          </p>
        </div>
      </template>
    </div>

    <ul
      class="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-[11px] text-slate-600"
    >
      <li
        v-for="serie in series"
        :key="serie.libelle"
        class="inline-flex items-center gap-1.5"
      >
        <span
          class="h-2.5 w-4 rounded-sm"
          :class="serie.classePastille"
          aria-hidden="true"
        />
        {{ serie.libelle }}
      </li>
    </ul>
  </article>
</template>
