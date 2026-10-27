<script setup lang="ts">
import { computed } from 'vue'

import { formaterNombre, formaterSerie } from '../lib/format'
import {
  construireSerie,
  creerGraine,
  echantillonnerPoints,
  resumerSerie,
  type EtatSerie,
  type ModeSerie,
} from '../lib/series'
import SerieDistributionChart from './SerieDistributionChart.vue'

const props = withDefaults(
  defineProps<{
    libelle: string
    unite: string
    horizonJours: number
    etat: EtatSerie
    plancher?: number | null
  }>(),
  {
    plancher: null,
  },
)

const modes: Array<{ valeur: ModeSerie; libelle: string }> = [
  { valeur: 'constante', libelle: 'Constante' },
  { valeur: 'uniforme', libelle: 'Uniforme' },
  { valeur: 'normale', libelle: 'Normale aléatoire' },
  { valeur: 'gaussienne', libelle: 'Profil gaussien' },
  { valeur: 'courbe', libelle: 'Courbe personnalisée' },
  { valeur: 'manuelle', libelle: 'Manuelle' },
]

const resultat = computed(() =>
  construireSerie(props.etat, props.horizonJours, {
    plancher: props.plancher,
  }),
)

const resume = computed(() => resumerSerie(resultat.value.valeurs))

function changerMode(event: Event) {
  const nouveau = (event.target as HTMLSelectElement).value as ModeSerie
  if (nouveau === props.etat.mode) return

  const valeursActuelles = resultat.value.valeurs

  if (nouveau === 'courbe') {
    props.etat.courbe = echantillonnerPoints(
      valeursActuelles,
      props.horizonJours,
    )
  }

  if (nouveau === 'manuelle') {
    props.etat.manuelle = formaterSerie(valeursActuelles)
  }

  props.etat.mode = nouveau
}

function majPoint(index: number, valeur: number) {
  const points = [...props.etat.courbe]
  points[index] = valeur
  props.etat.courbe = points
}

function nouvelleGraine() {
  props.etat.graine = creerGraine()
}

function nombreDeValeursManuelles(texte: string): number {
  return texte
    .split(/\r?\n/)
    .map((ligne) => ligne.trim())
    .filter((ligne) => ligne.length > 0).length
}
</script>

<template>
  <div class="space-y-4">
    <div class="grid gap-3 sm:grid-cols-[minmax(0,1fr)_16rem]">
      <div>
        <p class="text-sm font-semibold text-slate-950">
          {{ libelle }}
          <span class="font-normal text-slate-500">({{ unite }})</span>
        </p>
        <p class="mt-1 text-xs text-slate-500">
          Choisissez une distribution, puis ajustez ses paramètres.
        </p>
      </div>

      <div>
        <label for="serie-mode" class="etiquette">Distribution</label>
        <select
          id="serie-mode"
          class="champ"
          :value="etat.mode"
          @change="changerMode"
        >
          <option
            v-for="mode in modes"
            :key="mode.valeur"
            :value="mode.valeur"
          >
            {{ mode.libelle }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="etat.mode === 'constante'">
      <label for="serie-constante" class="etiquette">
        Valeur constante ({{ unite }})
      </label>
      <input
        id="serie-constante"
        v-model.number="etat.constante"
        class="champ max-w-xs"
        type="number"
        step="any"
      />
    </div>

    <div
      v-else-if="etat.mode === 'uniforme'"
      class="grid gap-3 sm:grid-cols-2"
    >
      <div>
        <label for="serie-uniforme-min" class="etiquette">
          Minimum ({{ unite }})
        </label>
        <input
          id="serie-uniforme-min"
          v-model.number="etat.uniformeMinimum"
          class="champ"
          type="number"
          step="any"
        />
      </div>
      <div>
        <label for="serie-uniforme-max" class="etiquette">
          Maximum ({{ unite }})
        </label>
        <input
          id="serie-uniforme-max"
          v-model.number="etat.uniformeMaximum"
          class="champ"
          type="number"
          step="any"
        />
      </div>
    </div>

    <div
      v-else-if="etat.mode === 'normale'"
      class="grid gap-3 sm:grid-cols-2"
    >
      <div>
        <label for="serie-normale-moyenne" class="etiquette">
          Valeur moyenne ({{ unite }})
        </label>
        <input
          id="serie-normale-moyenne"
          v-model.number="etat.normaleMoyenne"
          class="champ"
          type="number"
          step="any"
        />
      </div>
      <div>
        <label for="serie-normale-ecart" class="etiquette">
          Écart-type ({{ unite }})
        </label>
        <input
          id="serie-normale-ecart"
          v-model.number="etat.normaleEcartType"
          class="champ"
          type="number"
          min="0"
          step="any"
        />
      </div>
    </div>

    <div
      v-else-if="etat.mode === 'gaussienne'"
      class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
    >
      <div>
        <label for="serie-gaussienne-base" class="etiquette">
          Valeur de base ({{ unite }})
        </label>
        <input
          id="serie-gaussienne-base"
          v-model.number="etat.gaussienneBase"
          class="champ"
          type="number"
          step="any"
        />
      </div>
      <div>
        <label for="serie-gaussienne-pic" class="etiquette">
          Valeur au pic ({{ unite }})
        </label>
        <input
          id="serie-gaussienne-pic"
          v-model.number="etat.gaussiennePic"
          class="champ"
          type="number"
          step="any"
        />
      </div>
      <div>
        <label for="serie-gaussienne-jour" class="etiquette">
          Jour du pic
        </label>
        <input
          id="serie-gaussienne-jour"
          v-model.number="etat.gaussienneJourPic"
          class="champ"
          type="number"
          min="0"
          :max="Math.max(0, Math.floor(horizonJours) - 1)"
          step="1"
        />
      </div>
      <div>
        <label for="serie-gaussienne-largeur" class="etiquette">
          Largeur (jours)
        </label>
        <input
          id="serie-gaussienne-largeur"
          v-model.number="etat.gaussienneLargeur"
          class="champ"
          type="number"
          min="1"
          step="any"
        />
      </div>
    </div>

    <div v-else-if="etat.mode === 'manuelle'">
      <label for="serie-manuelle" class="etiquette">
        Valeurs journalières (une par ligne)
      </label>
      <textarea
        id="serie-manuelle"
        v-model="etat.manuelle"
        class="champ min-h-44 font-mono text-xs leading-relaxed"
        spellcheck="false"
      />
      <p class="mt-1 text-[11px] text-slate-500">
        {{ nombreDeValeursManuelles(etat.manuelle) }} valeur(s) saisie(s).
        Le copier-coller est autorisé.
      </p>
    </div>

    <p v-else class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
      La courbe est interpolée entre les points de contrôle. Les valeurs
      finales sont enregistrées jour par jour.
    </p>

    <div
      v-if="
        etat.mode === 'uniforme' || etat.mode === 'normale'
      "
      class="flex flex-wrap items-end gap-3 rounded-lg bg-slate-50 px-3 py-2"
    >
      <div class="w-40">
        <label for="serie-graine" class="etiquette">Graine</label>
        <input
          id="serie-graine"
          v-model.number="etat.graine"
          class="champ"
          type="number"
          min="0"
          step="1"
        />
      </div>
      <button
        type="button"
        class="bouton-secondaire"
        @click="nouvelleGraine"
      >
        Nouveau tirage
      </button>
      <p class="text-[11px] text-slate-500">
        La même graine produit la même série.
      </p>
    </div>

    <p
      v-if="resultat.erreur"
      role="alert"
      class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800"
    >
      {{ resultat.erreur }}
    </p>

    <SerieDistributionChart
      :valeurs="resultat.valeurs"
      :horizon-jours="horizonJours"
      :points="etat.mode === 'courbe' ? etat.courbe : null"
      :unite="unite"
      :plancher="plancher"
      @deplacer-point="majPoint"
    />

    <div
      class="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-slate-600"
    >
      <span>
        Min
        <strong class="font-semibold text-slate-800">
          {{ formaterNombre(resume.minimum) }} {{ unite }}
        </strong>
      </span>
      <span>
        Moyenne
        <strong class="font-semibold text-slate-800">
          {{ formaterNombre(resume.moyenne) }} {{ unite }}
        </strong>
      </span>
      <span>
        Max
        <strong class="font-semibold text-slate-800">
          {{ formaterNombre(resume.maximum) }} {{ unite }}
        </strong>
      </span>
      <span v-if="plancher !== null" class="text-slate-500">
        Valeurs générées bornées à {{ formaterNombre(plancher) }} {{ unite }}.
      </span>
    </div>
  </div>
</template>
