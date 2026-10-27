<script setup lang="ts">
import { computed, ref } from 'vue'

import { formaterNombre } from '../lib/format'
import { echantillonnerPourApercu } from '../lib/series'

const props = withDefaults(
  defineProps<{
    valeurs: number[]
    horizonJours: number
    points?: number[] | null
    unite?: string
    plancher?: number | null
  }>(),
  {
    points: null,
    unite: '',
    plancher: null,
  },
)

const emit = defineEmits<{
  deplacerPoint: [index: number, valeur: number]
}>()

const zone = ref<HTMLElement | null>(null)
const pointGlisse = ref<number | null>(null)
const domaineFige = ref<{ minimum: number; maximum: number } | null>(null)
const survol = ref<{
  jour: number
  valeur: number
  xPct: number
  yPct: number
} | null>(null)

const domaine = computed(() => {
  const valeurs = props.valeurs.filter((valeur) => Number.isFinite(valeur))
  const points = (props.points ?? []).filter((valeur) =>
    Number.isFinite(valeur),
  )
  const toutes = [...valeurs, ...points]

  if (toutes.length === 0) {
    return { minimum: 0, maximum: 1 }
  }

  const reference = props.plancher === null ? 0 : props.plancher
  const minimum = Math.min(reference, ...toutes)
  let maximum = Math.max(reference, ...toutes)

  if (maximum === minimum) maximum = minimum + 1

  const marge = (maximum - minimum) * 0.08
  return {
    minimum: minimum >= 0 ? minimum : minimum - marge,
    maximum: maximum + marge,
  }
})

const domaineAffiche = computed(() => domaineFige.value ?? domaine.value)

const pointsApercu = computed(() =>
  echantillonnerPourApercu(
    props.valeurs.filter((valeur) => Number.isFinite(valeur)),
  ),
)

const polyligne = computed(() => {
  const valeurs = pointsApercu.value
  if (valeurs.length === 0) return ''

  const { minimum, maximum } = domaineAffiche.value
  const etendue = maximum - minimum

  return valeurs
    .map((valeur, index) => {
      const x =
        valeurs.length === 1 ? 500 : (index / (valeurs.length - 1)) * 1000
      const y = ((maximum - valeur) / etendue) * 300
      return `${x},${y}`
    })
    .join(' ')
})

const pointsAffiches = computed(() => props.points ?? [])

function positionX(index: number): number {
  const nombre = pointsAffiches.value.length
  if (nombre <= 1) return 50
  return (index / (nombre - 1)) * 100
}

function positionY(valeur: number): number {
  const { minimum, maximum } = domaineAffiche.value
  const etendue = maximum - minimum
  if (etendue === 0) return 50
  return ((maximum - valeur) / etendue) * 100
}

function jourPoint(index: number): number {
  const nombre = pointsAffiches.value.length
  const horizon = Math.max(1, Math.floor(props.horizonJours))
  if (nombre <= 1) return 0
  return Math.round((index * (horizon - 1)) / (nombre - 1))
}

function libellePoint(index: number): string {
  const valeur = pointsAffiches.value[index] ?? 0
  return `Point ${index + 1}, jour ${jourPoint(index)}, valeur ${formaterNombre(valeur)} ${props.unite}`
}

function survoler(event: PointerEvent) {
  if (!zone.value) return
  const rectangle = zone.value.getBoundingClientRect()
  if (rectangle.width === 0 || rectangle.height === 0) return

  const ratioX = Math.min(
    1,
    Math.max(0, (event.clientX - rectangle.left) / rectangle.width),
  )
  if (props.valeurs.length === 0) {
    survol.value = null
    return
  }

  const jour = Math.round(ratioX * (props.valeurs.length - 1))
  const valeur = props.valeurs[jour]
  if (!Number.isFinite(valeur)) {
    survol.value = null
    return
  }

  survol.value = {
    jour,
    valeur,
    xPct: ratioX * 100,
    yPct: positionY(valeur),
  }
}

function demarrer(index: number, event: PointerEvent) {
  if (props.points === null) return
  event.preventDefault()
  pointGlisse.value = index
  domaineFige.value = { ...domaine.value }
  const cible = event.currentTarget as HTMLElement
  cible.setPointerCapture(event.pointerId)
}

function deplacer(event: PointerEvent) {
  if (pointGlisse.value === null || !zone.value) return
  const rectangle = zone.value.getBoundingClientRect()
  if (rectangle.height === 0) return

  const { minimum, maximum } = domaineAffiche.value
  const ratio = Math.min(
    1.5,
    Math.max(-0.5, (event.clientY - rectangle.top) / rectangle.height),
  )
  const valeur = maximum - ratio * (maximum - minimum)
  const bornee =
    props.plancher === null ? valeur : Math.max(props.plancher, valeur)

  emit('deplacerPoint', pointGlisse.value, Math.round(bornee * 1000) / 1000)
}

function terminer(event: PointerEvent) {
  pointGlisse.value = null
  domaineFige.value = null
  const cible = event.currentTarget as HTMLElement
  if (cible.hasPointerCapture(event.pointerId)) {
    cible.releasePointerCapture(event.pointerId)
  }
}

function ajuster(index: number, direction: number) {
  const valeur = pointsAffiches.value[index] ?? 0
  const { minimum, maximum } = domaine.value
  const pas = Math.max((maximum - minimum) / 100, 0.01)
  const nouvelle = valeur + direction * pas
  const bornee =
    props.plancher === null ? nouvelle : Math.max(props.plancher, nouvelle)

  emit('deplacerPoint', index, Math.round(bornee * 1000) / 1000)
}
</script>

<template>
  <div>
    <div
      ref="zone"
      class="relative h-52 overflow-hidden rounded-xl border border-slate-200 bg-slate-50"
      @pointermove="survoler"
      @pointerleave="survol = null"
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
        <polyline
          v-if="polyligne"
          :points="polyligne"
          fill="none"
          class="stroke-edf-blue"
          stroke-width="2"
          stroke-linejoin="round"
          stroke-linecap="round"
          vector-effect="non-scaling-stroke"
        />
      </svg>

      <span
        class="pointer-events-none absolute left-2 top-1.5 rounded bg-slate-50/90 px-1 text-[10px] font-medium text-slate-500"
      >
        {{ formaterNombre(domaineAffiche.maximum) }} {{ unite }}
      </span>
      <span
        class="pointer-events-none absolute bottom-1.5 left-2 rounded bg-slate-50/90 px-1 text-[10px] font-medium text-slate-500"
      >
        {{ formaterNombre(domaineAffiche.minimum) }} {{ unite }}
      </span>
      <span
        class="pointer-events-none absolute bottom-1.5 right-2 rounded bg-slate-50/90 px-1 text-[10px] font-medium text-slate-500"
      >
        Jour {{ Math.max(0, Math.floor(horizonJours) - 1) }}
      </span>

      <template v-if="survol">
        <span
          class="pointer-events-none absolute inset-y-0 w-px bg-edf-blue/40"
          :style="{ left: `${survol.xPct}%` }"
          aria-hidden="true"
        />
        <span
          class="pointer-events-none absolute h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-edf-blue ring-2 ring-white"
          :style="{
            left: `${survol.xPct}%`,
            top: `${survol.yPct}%`,
          }"
          aria-hidden="true"
        />
        <div
          class="pointer-events-none absolute z-10 -translate-x-1/2 whitespace-nowrap rounded-md border border-edf-blue-deep bg-edf-blue px-2 py-1 text-[11px] leading-tight text-blue-50 shadow-lg"
          :class="survol.yPct < 30 ? 'translate-y-2' : '-translate-y-full'"
          :style="{
            left: `${Math.min(84, Math.max(16, survol.xPct))}%`,
            top: `${survol.yPct}%`,
          }"
          aria-hidden="true"
        >
          <p class="font-semibold text-white">Jour {{ survol.jour }}</p>
          <p>{{ formaterNombre(survol.valeur) }} {{ unite }}</p>
        </div>
      </template>

      <button
        v-for="(valeur, index) in pointsAffiches"
        :key="index"
        type="button"
        class="absolute h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 touch-none cursor-ns-resize rounded-full border-2 border-white bg-edf-blue shadow ring-1 ring-edf-blue/40 transition hover:scale-110 focus-visible:scale-110"
        :style="{
          left: `${positionX(index)}%`,
          top: `${positionY(valeur)}%`,
        }"
        :aria-label="libellePoint(index)"
        @pointerdown="demarrer(index, $event)"
        @pointermove="deplacer"
        @pointerup="terminer"
        @pointercancel="terminer"
        @keydown.up.prevent="ajuster(index, 1)"
        @keydown.down.prevent="ajuster(index, -1)"
      />
    </div>

    <p class="mt-2 text-[11px] text-slate-500">
      Aperçu de la série sur
      {{ Math.max(0, Math.floor(horizonJours)) }} jour{{
        Math.floor(horizonJours) > 1 ? 's' : ''
      }}.
      <template v-if="pointsAffiches.length > 0">
        Glissez les points vers le haut ou le bas. Les flèches haut et bas
        ajustent le point sélectionné.
      </template>
    </p>
  </div>
</template>
