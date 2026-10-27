<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { messageErreur } from '../api/client'
import type { Simulation } from '../api/types'
import {
  analyserSerie,
  formaterSerie,
  redimensionnerSerie,
} from '../lib/format'
import { useSimulationsStore } from '../stores/simulations'
import BaseDialog from './BaseDialog.vue'

const props = defineProps<{
  simulationId: string
  simulation: Simulation
}>()

const emit = defineEmits<{
  fermer: []
  enregistre: []
}>()

const store = useSimulationsStore()

const formulaire = reactive({
  nom: props.simulation.nom,
  horizon_jours: props.simulation.horizon_jours,
})
const series = reactive({
  prix_spot_eur_mwh: formaterSerie(props.simulation.prix_spot_eur_mwh),
  demande_nationale_mwh: formaterSerie(
    props.simulation.demande_nationale_mwh,
  ),
  valeur_usage_eur_mwh: formaterSerie(
    props.simulation.valeur_usage_eur_mwh,
  ),
})
const erreurs = ref<string[]>([])
const erreurApi = ref<string | null>(null)
const avertissement = ref<string | null>(null)

const horizonValide = computed(() => {
  const horizon = Number(formulaire.horizon_jours)
  return Number.isInteger(horizon) && horizon >= 1 && horizon <= 7305
})

function nombreDeValeurs(texte: string): number {
  return texte
    .split(/\r?\n/)
    .map((ligne) => ligne.trim())
    .filter((ligne) => ligne.length > 0).length
}

function redimensionnerSeries() {
  avertissement.value = null
  if (!horizonValide.value) return

  const horizon = Number(formulaire.horizon_jours)
  const champs = [
    'prix_spot_eur_mwh',
    'demande_nationale_mwh',
    'valeur_usage_eur_mwh',
  ] as const

  const analyse = champs.map((champ) => analyserSerie(series[champ]))
  const premiereErreur = analyse.find((resultat) => resultat.erreur)?.erreur
  if (premiereErreur) {
    erreurs.value = [premiereErreur]
    return
  }

  champs.forEach((champ, index) => {
    series[champ] = formaterSerie(
      redimensionnerSerie(analyse[index].valeurs, horizon),
    )
  })

  erreurs.value = []
  avertissement.value =
    'Les séries ont été redimensionnées. Vérifiez leurs valeurs avant d’enregistrer.'
}

function valider(): {
  prix: number[]
  demande: number[]
  valeurUsage: number[]
} | null {
  const messages: string[] = []
  const horizon = Number(formulaire.horizon_jours)

  if (formulaire.nom.trim().length === 0) {
    messages.push('Le nom de la simulation est obligatoire.')
  }
  if (!horizonValide.value) {
    messages.push(
      'L’horizon doit être un nombre entier compris entre 1 et 7305 jours.',
    )
  }

  const prix = analyserSerie(series.prix_spot_eur_mwh)
  const demande = analyserSerie(series.demande_nationale_mwh)
  const valeurUsage = analyserSerie(series.valeur_usage_eur_mwh)

  if (prix.erreur) messages.push(`Prix spot : ${prix.erreur}`)
  if (demande.erreur) messages.push(`Demande nationale : ${demande.erreur}`)
  if (valeurUsage.erreur) {
    messages.push(`Valeur d’usage : ${valeurUsage.erreur}`)
  }

  const seriesAValider = [
    ['Prix spot', prix.valeurs, prix.erreur],
    ['Demande nationale', demande.valeurs, demande.erreur],
    ['Valeur d’usage', valeurUsage.valeurs, valeurUsage.erreur],
  ] as const

  if (horizonValide.value) {
    for (const [libelle, valeurs, erreur] of seriesAValider) {
      if (!erreur && valeurs.length !== horizon) {
        messages.push(
          `${libelle} : ${valeurs.length} valeur${valeurs.length > 1 ? 's' : ''} saisie${valeurs.length > 1 ? 's' : ''}, ${horizon} attendue${horizon > 1 ? 's' : ''}.`,
        )
      }
    }
  }

  if (demande.valeurs.some((valeur) => valeur < 0)) {
    messages.push('La demande nationale ne doit pas être négative.')
  }

  erreurs.value = messages
  if (messages.length > 0) return null

  return {
    prix: prix.valeurs,
    demande: demande.valeurs,
    valeurUsage: valeurUsage.valeurs,
  }
}

async function enregistrer() {
  erreurApi.value = null
  const donnees = valider()
  if (!donnees) return

  try {
    await store.enregistrerParametres(props.simulationId, {
      nom: formulaire.nom.trim(),
      horizon_jours: Number(formulaire.horizon_jours),
      prix_spot_eur_mwh: donnees.prix,
      demande_nationale_mwh: donnees.demande,
      valeur_usage_eur_mwh: donnees.valeurUsage,
    })
    emit('enregistre')
  } catch (error) {
    erreurApi.value = messageErreur(error)
  }
}
</script>

<template>
  <BaseDialog
    titre="Paramètres de la simulation"
    description="Modifiez le nom, l’horizon et les séries nationales journalières."
    taille="large"
    :closeable="!store.saving"
    @fermer="emit('fermer')"
  >
    <div
      v-if="erreurs.length > 0 || erreurApi"
      role="alert"
      class="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <p v-if="erreurApi">{{ erreurApi }}</p>
      <ul v-if="erreurs.length > 0" class="list-inside list-disc space-y-1">
        <li v-for="erreur in erreurs" :key="erreur">{{ erreur }}</li>
      </ul>
    </div>

    <div
      v-if="avertissement"
      role="status"
      class="mb-5 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
    >
      {{ avertissement }}
    </div>

    <form class="space-y-5" novalidate @submit.prevent="enregistrer">
      <div class="grid gap-4 md:grid-cols-[1fr_14rem]">
        <div>
          <label for="parametres-nom" class="etiquette">Nom</label>
          <input
            id="parametres-nom"
            v-model="formulaire.nom"
            class="champ"
            type="text"
            maxlength="200"
            autocomplete="off"
          />
        </div>
        <div>
          <label for="parametres-horizon" class="etiquette">
            Horizon en jours
          </label>
          <input
            id="parametres-horizon"
            v-model.number="formulaire.horizon_jours"
            class="champ"
            type="number"
            min="1"
            max="7305"
            step="1"
            @change="redimensionnerSeries"
          />
        </div>
      </div>

      <p class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
        Chaque série doit contenir exactement
        <strong>{{ horizonValide ? formulaire.horizon_jours : '—' }}</strong>
        valeur{{ Number(formulaire.horizon_jours) > 1 ? 's' : '' }}, une par
        ligne. Le copier-coller de séries est autorisé.
      </p>

      <div class="grid gap-4 lg:grid-cols-3">
        <div>
          <label for="parametres-prix" class="etiquette">
            Prix spot (€/MWh)
          </label>
          <textarea
            id="parametres-prix"
            v-model="series.prix_spot_eur_mwh"
            class="champ min-h-44 font-mono text-xs leading-relaxed"
            spellcheck="false"
          />
          <p class="mt-1 text-[11px] text-slate-500">
            {{ nombreDeValeurs(series.prix_spot_eur_mwh) }} valeur(s) saisie(s)
          </p>
        </div>

        <div>
          <label for="parametres-demande" class="etiquette">
            Demande nationale (MWh)
          </label>
          <textarea
            id="parametres-demande"
            v-model="series.demande_nationale_mwh"
            class="champ min-h-44 font-mono text-xs leading-relaxed"
            spellcheck="false"
          />
          <p class="mt-1 text-[11px] text-slate-500">
            {{ nombreDeValeurs(series.demande_nationale_mwh) }} valeur(s)
            saisie(s)
          </p>
        </div>

        <div>
          <label for="parametres-valeur-usage" class="etiquette">
            Valeur d’usage (€/MWh)
          </label>
          <textarea
            id="parametres-valeur-usage"
            v-model="series.valeur_usage_eur_mwh"
            class="champ min-h-44 font-mono text-xs leading-relaxed"
            spellcheck="false"
          />
          <p class="mt-1 text-[11px] text-slate-500">
            {{ nombreDeValeurs(series.valeur_usage_eur_mwh) }} valeur(s)
            saisie(s)
          </p>
        </div>
      </div>

      <p class="text-xs text-slate-500">
        Un changement d’horizon tronque les séries ou les étend avec leur
        dernière valeur. Vérifiez le résultat avant l’enregistrement.
      </p>
    </form>

    <template #pied>
      <button
        type="button"
        class="bouton-secondaire"
        :disabled="store.saving"
        @click="emit('fermer')"
      >
        Annuler
      </button>
      <button
        type="button"
        class="bouton-primaire"
        :disabled="store.saving"
        @click="enregistrer"
      >
        {{ store.saving ? 'Enregistrement…' : 'Enregistrer et recalculer' }}
      </button>
    </template>
  </BaseDialog>
</template>
