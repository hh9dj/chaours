<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { messageErreur } from '../api/client'
import type { Simulation } from '../api/types'
import {
  analyserSerie,
  formaterSerie,
  redimensionnerSerie,
} from '../lib/format'
import {
  adapterPointsCourbe,
  construireSerie,
  etatInitial,
  type EtatSerie,
} from '../lib/series'
import { useSimulationsStore } from '../stores/simulations'
import BaseDialog from './BaseDialog.vue'
import SerieDistributionEditor from './SerieDistributionEditor.vue'

const props = defineProps<{
  simulationId: string
  simulation: Simulation
}>()

const emit = defineEmits<{
  fermer: []
  enregistre: []
}>()

type ChampSerie =
  | 'prix_spot_eur_mwh'
  | 'demande_nationale_mwh'
  | 'valeur_usage_eur_mwh'

interface DefinitionSerie {
  cle: ChampSerie
  libelle: string
  unite: string
  plancher: number | null
}

const store = useSimulationsStore()

const champs: DefinitionSerie[] = [
  {
    cle: 'prix_spot_eur_mwh',
    libelle: 'Prix spot',
    unite: '€/MWh',
    plancher: null,
  },
  {
    cle: 'demande_nationale_mwh',
    libelle: 'Demande nationale',
    unite: 'MWh',
    plancher: 0,
  },
  {
    cle: 'valeur_usage_eur_mwh',
    libelle: 'Valeur d’usage',
    unite: '€/MWh',
    plancher: null,
  },
]

const formulaire = reactive({
  nom: props.simulation.nom,
  horizon_jours: props.simulation.horizon_jours,
})

const series = reactive<Record<ChampSerie, EtatSerie>>({
  prix_spot_eur_mwh: etatInitial(
    props.simulation.prix_spot_eur_mwh,
    props.simulation.horizon_jours,
  ),
  demande_nationale_mwh: etatInitial(
    props.simulation.demande_nationale_mwh,
    props.simulation.horizon_jours,
  ),
  valeur_usage_eur_mwh: etatInitial(
    props.simulation.valeur_usage_eur_mwh,
    props.simulation.horizon_jours,
  ),
})

const ongletActif = ref<ChampSerie>('prix_spot_eur_mwh')
const erreurs = ref<string[]>([])
const erreurApi = ref<string | null>(null)
const avertissement = ref<string | null>(null)

const horizonValide = computed(() => {
  const horizon = Number(formulaire.horizon_jours)
  return Number.isInteger(horizon) && horizon >= 1 && horizon <= 7305
})

const horizonEffectif = computed(() =>
  horizonValide.value ? Number(formulaire.horizon_jours) : 0,
)

const resultatsSeries = computed(() => ({
  prix_spot_eur_mwh: construireSerie(
    series.prix_spot_eur_mwh,
    horizonEffectif.value,
  ),
  demande_nationale_mwh: construireSerie(
    series.demande_nationale_mwh,
    horizonEffectif.value,
    { plancher: 0 },
  ),
  valeur_usage_eur_mwh: construireSerie(
    series.valeur_usage_eur_mwh,
    horizonEffectif.value,
  ),
}))

function redimensionnerSeries() {
  avertissement.value = null
  if (!horizonValide.value) return

  const horizon = Number(formulaire.horizon_jours)
  for (const champ of champs) {
    const etat = series[champ.cle]

    if (etat.mode === 'manuelle') {
      const analyse = analyserSerie(etat.manuelle)
      if (!analyse.erreur) {
        etat.manuelle = formaterSerie(
          redimensionnerSerie(analyse.valeurs, horizon),
        )
      }
    }

    etat.courbe = adapterPointsCourbe(etat.courbe, horizon)
    etat.gaussienneJourPic = Math.min(
      Math.max(0, Math.round(etat.gaussienneJourPic)),
      Math.max(0, horizon - 1),
    )
  }

  erreurs.value = []
  avertissement.value =
    'Les séries ont été mises à jour pour le nouvel horizon. Vérifiez leurs valeurs avant d’enregistrer.'
}

function valider(): {
  prix: number[]
  demande: number[]
  valeurUsage: number[]
} | null {
  const messages: string[] = []

  if (formulaire.nom.trim().length === 0) {
    messages.push('Le nom de la simulation est obligatoire.')
  }
  if (!horizonValide.value) {
    messages.push(
      'L’horizon doit être un nombre entier compris entre 1 et 7305 jours.',
    )
  }

  for (const champ of champs) {
    const resultat = resultatsSeries.value[champ.cle]
    if (resultat.erreur) {
      messages.push(`${champ.libelle} : ${resultat.erreur}`)
    }
  }

  const demande = resultatsSeries.value.demande_nationale_mwh
  if (!demande.erreur && demande.valeurs.some((valeur) => valeur < 0)) {
    messages.push('La demande nationale ne doit pas être négative.')
  }

  erreurs.value = messages
  if (messages.length > 0) {
    const premiereSerieEnErreur = champs.find(
      (champ) => resultatsSeries.value[champ.cle].erreur !== null,
    )
    if (premiereSerieEnErreur) {
      ongletActif.value = premiereSerieEnErreur.cle
    }
    return null
  }

  return {
    prix: resultatsSeries.value.prix_spot_eur_mwh.valeurs,
    demande: resultatsSeries.value.demande_nationale_mwh.valeurs,
    valeurUsage: resultatsSeries.value.valeur_usage_eur_mwh.valeurs,
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
    description="Modifiez le nom, l’horizon et les séries nationales générées."
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
        Chaque série est générée sur
        <strong>{{ horizonValide ? formulaire.horizon_jours : '—' }}</strong>
        jour{{ Number(formulaire.horizon_jours) > 1 ? 's' : '' }}. Les valeurs
        sont converties en une valeur par jour avant l’enregistrement.
      </p>

      <div
        class="flex flex-wrap gap-1 border-b border-slate-200"
        role="tablist"
        aria-label="Séries nationales"
      >
        <button
          v-for="champ in champs"
          :id="`onglet-${champ.cle}`"
          :key="champ.cle"
          type="button"
          role="tab"
          :aria-selected="ongletActif === champ.cle"
          :aria-controls="`panneau-${champ.cle}`"
          :tabindex="ongletActif === champ.cle ? 0 : -1"
          class="-mb-px inline-flex items-center gap-2 border-b-2 px-3 py-2 text-sm font-semibold transition"
          :class="
            ongletActif === champ.cle
              ? 'border-edf-blue text-edf-blue'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          "
          @click="ongletActif = champ.cle"
        >
          {{ champ.libelle }}
          <span
            v-if="resultatsSeries[champ.cle].erreur"
            class="flex h-4 w-4 items-center justify-center rounded-full bg-red-100 text-[10px] font-black text-red-700"
            aria-label="Cette série contient une erreur"
          >
            !
          </span>
        </button>
      </div>

      <template v-for="champ in champs" :key="champ.cle">
        <div
          v-if="ongletActif === champ.cle"
          :id="`panneau-${champ.cle}`"
          role="tabpanel"
          :aria-labelledby="`onglet-${champ.cle}`"
        >
          <SerieDistributionEditor
            :libelle="champ.libelle"
            :unite="champ.unite"
            :horizon-jours="horizonEffectif"
            :etat="series[champ.cle]"
            :plancher="champ.plancher"
          />
        </div>
      </template>

      <p class="text-xs text-slate-500">
        Les réglages de distribution ne sont pas conservés après la fermeture :
        seules les valeurs journalières générées sont enregistrées. Un
        changement d’horizon met à jour les séries.
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
