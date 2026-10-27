<script setup lang="ts">
import { reactive, ref } from 'vue'

import { messageErreur } from '../api/client'
import type { Simulation } from '../api/types'
import { useSimulationsStore } from '../stores/simulations'
import BaseDialog from './BaseDialog.vue'

const emit = defineEmits<{
  fermer: []
  cree: [simulation: Simulation]
}>()

const store = useSimulationsStore()

const formulaire = reactive({
  nom: '',
  horizon_jours: 365,
  identifiant: '',
  code_eic: '',
  puissance_nominale_mw: 0,
  jepp_initial: 0,
})

const erreurs = ref<Record<string, string>>({})
const erreurApi = ref<string | null>(null)

function valider(): boolean {
  const prochainesErreurs: Record<string, string> = {}
  const horizon = Number(formulaire.horizon_jours)

  if (formulaire.nom.trim().length === 0) {
    prochainesErreurs.nom = 'Le nom de la simulation est obligatoire.'
  }
  if (!Number.isInteger(horizon) || horizon < 1 || horizon > 7305) {
    prochainesErreurs.horizon_jours =
      'L’horizon doit être un nombre entier compris entre 1 et 7305 jours.'
  }
  if (formulaire.identifiant.trim().length === 0) {
    prochainesErreurs.identifiant = 'L’identifiant de la tranche est obligatoire.'
  }
  if (formulaire.code_eic.trim().length === 0) {
    prochainesErreurs.code_eic = 'Le code EIC est obligatoire.'
  }
  if (
    !Number.isFinite(Number(formulaire.puissance_nominale_mw)) ||
    Number(formulaire.puissance_nominale_mw) <= 0
  ) {
    prochainesErreurs.puissance_nominale_mw =
      'La puissance nominale doit être supérieure à 0 MW.'
  }
  if (
    !Number.isFinite(Number(formulaire.jepp_initial)) ||
    Number(formulaire.jepp_initial) < 0
  ) {
    prochainesErreurs.jepp_initial = 'Le JEPP initial doit être positif ou nul.'
  }

  erreurs.value = prochainesErreurs
  return Object.keys(prochainesErreurs).length === 0
}

async function soumettre() {
  erreurApi.value = null
  if (!valider()) return

  const horizon = Number(formulaire.horizon_jours)
  const serie = (valeur: number) =>
    Array.from({ length: horizon }, () => valeur)

  try {
    const simulation = await store.creerSimulation({
      nom: formulaire.nom.trim(),
      horizon_jours: horizon,
      prix_spot_eur_mwh: serie(80),
      demande_nationale_mwh: serie(0),
      valeur_usage_eur_mwh: serie(60),
      tranches: [
        {
          tranche: {
            identifiant: formulaire.identifiant.trim(),
            code_eic: formulaire.code_eic.trim(),
            puissance_nominale_mw: Number(formulaire.puissance_nominale_mw),
            jepp_initial: Number(formulaire.jepp_initial),
          },
          arrets: [],
          modulations: [],
        },
      ],
    })
    emit('cree', simulation)
  } catch (error) {
    erreurApi.value = messageErreur(error)
  }
}
</script>

<template>
  <BaseDialog
    titre="Créer une simulation"
    description="Le scénario démarre avec une tranche et des séries nationales plates."
    :closeable="!store.saving"
    @fermer="emit('fermer')"
  >
    <form class="space-y-6" novalidate @submit.prevent="soumettre">
      <div
        v-if="erreurApi"
        role="alert"
        class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      >
        {{ erreurApi }}
      </div>

      <fieldset class="space-y-4">
        <legend class="mb-1 text-sm font-semibold text-slate-950">
          Simulation
        </legend>

        <div>
          <label for="creation-nom" class="etiquette">Nom</label>
          <input
            id="creation-nom"
            v-model="formulaire.nom"
            class="champ"
            type="text"
            maxlength="200"
            autocomplete="off"
            required
            :aria-invalid="Boolean(erreurs.nom)"
          />
          <p v-if="erreurs.nom" class="mt-1 text-xs text-red-700">
            {{ erreurs.nom }}
          </p>
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label for="creation-horizon" class="etiquette">
              Horizon en jours
            </label>
            <input
              id="creation-horizon"
              v-model.number="formulaire.horizon_jours"
              class="champ"
              type="number"
              min="1"
              max="7305"
              step="1"
              required
              :aria-invalid="Boolean(erreurs.horizon_jours)"
            />
            <p v-if="erreurs.horizon_jours" class="mt-1 text-xs text-red-700">
              {{ erreurs.horizon_jours }}
            </p>
          </div>
        </div>

        <p class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
          Valeurs initiales : prix spot 80 €/MWh, demande nationale 0 MWh et
          valeur d’usage 60 €/MWh sur tout l’horizon.
        </p>
      </fieldset>

      <fieldset class="space-y-4">
        <legend class="mb-1 text-sm font-semibold text-slate-950">
          Première tranche
        </legend>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label for="creation-identifiant" class="etiquette">
              Identifiant
            </label>
            <input
              id="creation-identifiant"
              v-model="formulaire.identifiant"
              class="champ"
              type="text"
              autocomplete="off"
              required
              :aria-invalid="Boolean(erreurs.identifiant)"
            />
            <p v-if="erreurs.identifiant" class="mt-1 text-xs text-red-700">
              {{ erreurs.identifiant }}
            </p>
          </div>

          <div>
            <label for="creation-code-eic" class="etiquette">Code EIC</label>
            <input
              id="creation-code-eic"
              v-model="formulaire.code_eic"
              class="champ"
              type="text"
              autocomplete="off"
              required
              :aria-invalid="Boolean(erreurs.code_eic)"
            />
            <p v-if="erreurs.code_eic" class="mt-1 text-xs text-red-700">
              {{ erreurs.code_eic }}
            </p>
          </div>

          <div>
            <label for="creation-puissance" class="etiquette">
              Puissance nominale (MW)
            </label>
            <input
              id="creation-puissance"
              v-model.number="formulaire.puissance_nominale_mw"
              class="champ"
              type="number"
              min="0"
              step="any"
              required
              :aria-invalid="Boolean(erreurs.puissance_nominale_mw)"
            />
            <p
              v-if="erreurs.puissance_nominale_mw"
              class="mt-1 text-xs text-red-700"
            >
              {{ erreurs.puissance_nominale_mw }}
            </p>
          </div>

          <div>
            <label for="creation-jepp" class="etiquette">
              JEPP initial
            </label>
            <input
              id="creation-jepp"
              v-model.number="formulaire.jepp_initial"
              class="champ"
              type="number"
              min="0"
              step="any"
              required
              :aria-invalid="Boolean(erreurs.jepp_initial)"
            />
            <p v-if="erreurs.jepp_initial" class="mt-1 text-xs text-red-700">
              {{ erreurs.jepp_initial }}
            </p>
          </div>
        </div>
      </fieldset>

      <div class="flex flex-wrap items-center justify-end gap-3 border-t border-slate-100 pt-4">
        <button
          type="button"
          class="bouton-secondaire"
          :disabled="store.saving"
          @click="emit('fermer')"
        >
          Annuler
        </button>
        <button type="submit" class="bouton-primaire" :disabled="store.saving">
          {{ store.saving ? 'Création…' : 'Créer la simulation' }}
        </button>
      </div>
    </form>
  </BaseDialog>
</template>
