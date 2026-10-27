<script setup lang="ts">
import { computed, ref } from 'vue'

import type { Alerte, TypeAlerte } from '../api/types'
import {
  classesBordureTypeAlerte,
  classesTypeAlerte,
} from '../lib/couleurs'
import {
  filtrerAlertesNationales,
  libelleTypeAlerte,
  TYPES_ALERTES_NATIONALES,
  type FiltresAlertes,
} from '../lib/timeline'

const props = defineProps<{
  alertes: Alerte[]
}>()

const ouvert = ref(true)
const typeFiltre = ref<TypeAlerte | 'tous'>('tous')
const jourDebut = ref<number | ''>('')
const jourFin = ref<number | ''>('')

const alertesNationales = computed(() =>
  filtrerAlertesNationales(props.alertes),
)

function nombreJour(valeur: number | ''): number | null {
  if (valeur === '') return null
  const nombre = Number(valeur)
  return Number.isFinite(nombre) ? nombre : null
}

const filtres = computed<FiltresAlertes>(() => {
  const debut = nombreJour(jourDebut.value)
  const fin = nombreJour(jourFin.value)

  return {
    type: typeFiltre.value === 'tous' ? null : typeFiltre.value,
    jourDebut:
      debut !== null && fin !== null ? Math.min(debut, fin) : debut,
    jourFin: debut !== null && fin !== null ? Math.max(debut, fin) : fin,
  }
})

const alertesFiltrees = computed(() =>
  filtrerAlertesNationales(props.alertes, filtres.value),
)

const filtresActifs = computed(
  () =>
    filtres.value.type !== null ||
    filtres.value.jourDebut !== null ||
    filtres.value.jourFin !== null,
)

function reinitialiserFiltres() {
  typeFiltre.value = 'tous'
  jourDebut.value = ''
  jourFin.value = ''
}
</script>

<template>
  <aside
    class="flex max-h-[calc(100vh-9rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
    aria-labelledby="alertes-nationales-titre"
  >
    <header class="border-b border-slate-200 px-5 py-4">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Vision nationale
          </p>
          <h2 id="alertes-nationales-titre" class="mt-0.5 text-base font-semibold text-slate-950">
            Alertes nationales
          </h2>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <span
            class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700"
            :aria-label="
              filtresActifs
                ? `${alertesFiltrees.length} alertes affichées sur ${alertesNationales.length}`
                : `${alertesNationales.length} alertes nationales`
            "
          >
            <template v-if="filtresActifs">
              {{ alertesFiltrees.length }} / {{ alertesNationales.length }}
            </template>
            <template v-else>
              {{ alertesNationales.length }}
            </template>
          </span>
          <button
            type="button"
            class="bouton-discret px-2"
            :aria-expanded="ouvert"
            aria-controls="alertes-nationales-contenu"
            @click="ouvert = !ouvert"
          >
            {{ ouvert ? 'Masquer' : 'Afficher' }}
          </button>
        </div>
      </div>
    </header>

    <div
      v-show="ouvert"
      id="alertes-nationales-contenu"
      class="flex min-h-0 flex-1 flex-col"
    >
      <div class="space-y-3 border-b border-slate-200 p-4">
        <div class="flex items-center justify-between gap-2">
          <p class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
            Filtres
          </p>
          <button
            v-if="filtresActifs"
            type="button"
            class="text-xs font-semibold text-edf-blue transition hover:text-edf-blue-deep"
            @click="reinitialiserFiltres"
          >
            Réinitialiser
          </button>
        </div>

        <div>
          <label for="filtre-alerte-type" class="etiquette">
            Type d’alerte
          </label>
          <select
            id="filtre-alerte-type"
            v-model="typeFiltre"
            class="champ"
          >
            <option value="tous">Tous les types</option>
            <option
              v-for="type in TYPES_ALERTES_NATIONALES"
              :key="type"
              :value="type"
            >
              {{ libelleTypeAlerte(type) }}
            </option>
          </select>
        </div>

        <div>
          <p class="etiquette">Plage de jours</p>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label
                for="filtre-jour-debut"
                class="mb-1 block text-[11px] text-slate-500"
              >
                Du jour
              </label>
              <input
                id="filtre-jour-debut"
                v-model.number="jourDebut"
                class="champ"
                type="number"
                min="0"
                step="1"
                placeholder="Tous"
              />
            </div>
            <div>
              <label
                for="filtre-jour-fin"
                class="mb-1 block text-[11px] text-slate-500"
              >
                Au jour
              </label>
              <input
                id="filtre-jour-fin"
                v-model.number="jourFin"
                class="champ"
                type="number"
                min="0"
                step="1"
                placeholder="Tous"
              />
            </div>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4">
        <div
          v-if="alertesNationales.length === 0"
          class="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center"
        >
          <p class="text-sm font-semibold text-slate-700">
            Aucune alerte nationale
          </p>
          <p class="mt-1 text-xs leading-relaxed text-slate-500">
            L’offre couvre la demande et le prix spot reste au-dessus de la
            valeur d’usage sur tout l’horizon.
          </p>
        </div>

        <div
          v-else-if="alertesFiltrees.length === 0"
          class="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center"
        >
          <p class="text-sm font-semibold text-slate-700">
            Aucune alerte ne correspond aux filtres
          </p>
          <button
            type="button"
            class="mt-3 text-xs font-semibold text-edf-blue transition hover:text-edf-blue-deep"
            @click="reinitialiserFiltres"
          >
            Effacer les filtres
          </button>
        </div>

        <ul v-else class="space-y-3">
          <li
            v-for="(alerte, index) in alertesFiltrees"
            :key="`${alerte.type_alerte}-${alerte.jour ?? 'sans-jour'}-${index}`"
            class="rounded-xl border border-l-4 border-slate-200 bg-white p-3.5 shadow-sm"
            :class="classesBordureTypeAlerte[alerte.type_alerte]"
          >
            <div class="flex flex-wrap items-center gap-2">
              <span
                class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset"
                :class="classesTypeAlerte[alerte.type_alerte]"
              >
                {{ libelleTypeAlerte(alerte.type_alerte) }}
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

            <p class="mt-2 text-xs leading-relaxed text-slate-600">
              {{ alerte.message }}
            </p>
          </li>
        </ul>
      </div>
    </div>
  </aside>
</template>
