<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch,
} from 'vue'

import type {
  Alerte,
  ResultatTranche,
  SimulationTranche,
} from '../api/types'
import {
  classesBadgeTypeAlerte,
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
import {
  bornerZoom,
  defilementDepuisScroll,
  joursVisibles,
  positionJourPct,
  scrollDepuisDefilement,
  zoomerAvecAncre,
  zoomerAuCentre,
  zoomMaximum,
} from '../lib/timelineZoom'
import AlertPopover from './AlertPopover.vue'

const props = defineProps<{
  simulationTranche: SimulationTranche
  resultat: ResultatTranche | null
  alertes: Alerte[]
  horizonJours: number
  zoom: number
  defilement: number
}>()

const emit = defineEmits<{
  ouvrirEditeur: []
  majZoom: [zoom: number]
  majDefilement: [defilement: number]
  reinitialiserZoom: []
}>()

const conteneurDefilement = ref<HTMLElement | null>(null)
const enveloppe = ref<HTMLElement | null>(null)
const metriques = reactive({
  scrollLeft: 0,
  largeurVisible: 0,
  largeurTotale: 0,
})
const alertesOuvertes = ref<{
  jour: number
  alertes: Alerte[]
} | null>(null)
const survol = ref<{
  jour: JourTimeline
  x: number
  y: number
} | null>(null)
const applicationProgrammatique = ref(false)

let frameDefilement: number | null = null
let frameApplication: number | null = null
let observateurRedimensionnement: ResizeObserver | null = null

const jours = computed(() =>
  construireJoursTimeline({
    simulationTranche: props.simulationTranche,
    resultat: props.resultat,
    alertes: props.alertes,
    horizonJours: props.horizonJours,
  }),
)

const zoomMax = computed(() => zoomMaximum(props.horizonJours))
const zoomCourant = computed(() =>
  bornerZoom(props.zoom, props.horizonJours),
)
const joursVisiblesCourants = computed(() =>
  joursVisibles(metriques, props.horizonJours),
)
const positionAlertes = computed(() =>
  alertesOuvertes.value
    ? positionJourPct(
        alertesOuvertes.value.jour,
        metriques,
        props.horizonJours,
      )
    : 0,
)

function actualiserMetriques() {
  const conteneur = conteneurDefilement.value
  if (!conteneur) return
  metriques.scrollLeft = conteneur.scrollLeft
  metriques.largeurVisible = conteneur.clientWidth
  metriques.largeurTotale = conteneur.scrollWidth
}

async function appliquerDefilement() {
  await nextTick()
  const conteneur = conteneurDefilement.value
  if (!conteneur) return

  const cible = scrollDepuisDefilement(
    props.defilement,
    conteneur.clientWidth,
    conteneur.scrollWidth,
  )

  if (Math.abs(conteneur.scrollLeft - cible) > 1) {
    applicationProgrammatique.value = true
    conteneur.scrollLeft = cible
    if (frameApplication !== null) cancelAnimationFrame(frameApplication)
    frameApplication = requestAnimationFrame(() => {
      applicationProgrammatique.value = false
      frameApplication = null
      actualiserMetriques()
    })
  }

  actualiserMetriques()
}

function annulerDefilementEnAttente() {
  if (frameDefilement !== null) {
    cancelAnimationFrame(frameDefilement)
    frameDefilement = null
  }
}

function surDefilement() {
  actualiserMetriques()
  survol.value = null
  alertesOuvertes.value = null

  if (
    applicationProgrammatique.value ||
    frameDefilement !== null
  ) {
    return
  }

  frameDefilement = requestAnimationFrame(() => {
    frameDefilement = null
    if (applicationProgrammatique.value) return
    const conteneur = conteneurDefilement.value
    if (!conteneur) return
    emit(
      'majDefilement',
      defilementDepuisScroll(
        conteneur.scrollLeft,
        conteneur.clientWidth,
        conteneur.scrollWidth,
      ),
    )
  })
}

function zoomer(event: WheelEvent) {
  const conteneur = conteneurDefilement.value
  if (!conteneur || zoomMax.value <= 1) return

  event.preventDefault()
  const rectangle = conteneur.getBoundingClientRect()
  const resultat = zoomerAvecAncre({
    zoomActuel: zoomCourant.value,
    defilementActuel: props.defilement,
    horizonJours: props.horizonJours,
    largeurVisible: conteneur.clientWidth,
    largeurTotale: conteneur.scrollWidth,
    offsetAncre: event.clientX - rectangle.left,
    deltaY: event.deltaY,
  })

  annulerDefilementEnAttente()
  survol.value = null
  alertesOuvertes.value = null
  emit('majZoom', resultat.zoom)
  emit('majDefilement', resultat.defilement)
}

function zoomerBouton(direction: 1 | -1) {
  const conteneur = conteneurDefilement.value
  if (!conteneur) return

  const resultat = zoomerAuCentre({
    zoomActuel: zoomCourant.value,
    defilementActuel: props.defilement,
    horizonJours: props.horizonJours,
    largeurVisible: conteneur.clientWidth,
    largeurTotale: conteneur.scrollWidth,
    direction,
  })

  annulerDefilementEnAttente()
  survol.value = null
  alertesOuvertes.value = null
  emit('majZoom', resultat.zoom)
  emit('majDefilement', resultat.defilement)
}

function reinitialiserZoom() {
  annulerDefilementEnAttente()
  survol.value = null
  alertesOuvertes.value = null
  emit('reinitialiserZoom')
}

function classeBadgeAlerte(jour: JourTimeline): string {
  const alerte = jour.alertes[0]
  return alerte ? classesBadgeTypeAlerte[alerte.type_alerte] : ''
}

function ouvrirAlertes(jour: JourTimeline) {
  actualiserMetriques()
  survol.value = null
  alertesOuvertes.value = {
    jour: jour.jour,
    alertes: jour.alertes,
  }
}

function afficherSurvol(jour: JourTimeline, event: Event) {
  const cible = event.currentTarget as HTMLElement | null
  const enveloppeElement = enveloppe.value
  if (!cible || !enveloppeElement) return

  const rectangleCible = cible.getBoundingClientRect()
  const rectangleEnveloppe = enveloppeElement.getBoundingClientRect()
  const largeur = rectangleEnveloppe.width
  const marge = Math.min(140, largeur / 2)
  const x = rectangleCible.left + rectangleCible.width / 2 -
    rectangleEnveloppe.left

  survol.value = {
    jour,
    x:
      largeur > marge * 2
        ? Math.min(largeur - marge, Math.max(marge, x))
        : x,
    y: rectangleCible.top - rectangleEnveloppe.top,
  }
}

function effacerSurvol() {
  survol.value = null
}

function quitterFocusSurvol(event: FocusEvent) {
  const groupe = event.currentTarget as HTMLElement | null
  if (
    groupe &&
    event.relatedTarget instanceof Node &&
    groupe.contains(event.relatedTarget)
  ) {
    return
  }
  survol.value = null
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

watch(
  () => [props.zoom, props.defilement] as const,
  () => {
    void appliquerDefilement()
  },
)

watch(
  () => props.horizonJours,
  () => {
    survol.value = null
    alertesOuvertes.value = null
  },
)

onMounted(() => {
  actualiserMetriques()
  void appliquerDefilement()

  const conteneur = conteneurDefilement.value
  if (conteneur && typeof ResizeObserver !== 'undefined') {
    observateurRedimensionnement = new ResizeObserver(() => {
      actualiserMetriques()
      void appliquerDefilement()
    })
    observateurRedimensionnement.observe(conteneur)
  }
})

onBeforeUnmount(() => {
  observateurRedimensionnement?.disconnect()
  if (frameDefilement !== null) cancelAnimationFrame(frameDefilement)
  if (frameApplication !== null) cancelAnimationFrame(frameApplication)
})
</script>

<template>
  <div ref="enveloppe" class="relative">
    <div
      v-if="alertesOuvertes"
      class="fixed inset-0 z-20"
      aria-hidden="true"
      @click="alertesOuvertes = null"
    />

    <div
      class="mb-2 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500"
    >
      <span>
        Jour {{ joursVisiblesCourants.debut }} – Jour
        {{ joursVisiblesCourants.fin }}
      </span>

      <div class="flex flex-wrap items-center gap-1">
        <span class="hidden text-slate-400 sm:inline">
          Ctrl + molette pour zoomer
        </span>
        <button
          type="button"
          class="bouton-discret h-7 min-w-7 px-1 text-base leading-none disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Dézoomer la timeline"
          :disabled="zoomCourant <= 1"
          @click="zoomerBouton(-1)"
        >
          −
        </button>
        <button
          type="button"
          class="bouton-discret h-7 min-w-7 px-1 text-base leading-none disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Zoomer la timeline"
          :disabled="zoomCourant >= zoomMax"
          @click="zoomerBouton(1)"
        >
          +
        </button>
        <button
          v-if="zoomCourant > 1"
          type="button"
          class="bouton-discret h-7 px-2 text-[11px]"
          @click="reinitialiserZoom"
        >
          Tout afficher
        </button>
      </div>
    </div>

    <div
      ref="conteneurDefilement"
      class="h-[9.5rem] overflow-x-auto overflow-y-hidden rounded-lg border border-slate-200 bg-slate-50"
      role="group"
      :aria-label="`Timeline de la tranche ${simulationTranche.tranche.identifiant}. Ctrl plus molette pour zoomer, flèches pour défiler.`"
      tabindex="0"
      @wheel.ctrl="zoomer"
      @scroll.passive="surDefilement"
    >
      <div
        class="flex h-full min-w-full items-end px-2 pb-9 pt-7"
        :style="{ width: `${zoomCourant * 100}%` }"
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
          @pointerenter="afficherSurvol(jour, $event)"
          @pointerleave="effacerSurvol"
          @focusin="afficherSurvol(jour, $event)"
          @focusout="quitterFocusSurvol"
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
          <button
            v-if="jour.alertes.length > 0"
            type="button"
            class="absolute -bottom-8 left-1/2 z-10 flex h-5 w-5 -translate-x-1/2 items-center justify-center rounded-full text-[11px] font-black shadow ring-2 ring-white transition hover:brightness-110"
            :class="classeBadgeAlerte(jour)"
            :aria-label="`Voir les alertes du jour ${jour.jour}`"
            :aria-expanded="alertesOuvertes?.jour === jour.jour"
            aria-haspopup="dialog"
            @click.stop="ouvrirAlertes(jour)"
            @keydown.enter.stop
          >
            !
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="survol"
      class="pointer-events-none absolute z-30 w-64 -translate-x-1/2 -translate-y-full rounded-lg border border-edf-blue-deep bg-edf-blue p-3 text-left text-xs text-blue-50 shadow-xl"
      :style="{
        left: `${survol.x}px`,
        top: `${survol.y - 8}px`,
      }"
      aria-hidden="true"
    >
      <p class="font-semibold text-white">Jour {{ survol.jour.jour }}</p>
      <dl class="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
        <dt class="text-blue-100/75">Production</dt>
        <dd>{{ formaterPourcentage(survol.jour.facteurProduction) }}</dd>
        <dt class="text-blue-100/75">Énergie</dt>
        <dd>{{ formaterEnergie(survol.jour.energieMwh) }}</dd>
        <dt class="text-blue-100/75">JEPP restant</dt>
        <dd>
          {{ formaterNombre(survol.jour.jeppRestant) }} /
          {{ formaterNombre(survol.jour.jeppInitial) }}
        </dd>
        <template
          v-if="survol.jour.estMaintenance && survol.jour.arret"
        >
          <dt class="text-blue-100/75">Arrêt</dt>
          <dd>{{ libelleTypeArret(survol.jour.arret.type_arret) }}</dd>
        </template>
        <template v-if="survol.jour.modulation">
          <dt class="text-blue-100/75">Modulation</dt>
          <dd>
            {{ formaterPourcentage(survol.jour.modulation.facteur) }}
          </dd>
        </template>
      </dl>
    </div>

    <AlertPopover
      v-if="alertesOuvertes"
      :alertes="alertesOuvertes.alertes"
      :jour="alertesOuvertes.jour"
      :position-pct="positionAlertes"
      @fermer="alertesOuvertes = null"
    />

    <div
      class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-slate-600"
    >
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
          class="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-gradient-to-br from-red-600 via-edf-orange to-edf-cyan text-[8px] font-black text-white"
          aria-hidden="true"
        >
          !
        </span>
        alerte de tranche, couleur selon le type
      </span>
    </div>
  </div>
</template>
