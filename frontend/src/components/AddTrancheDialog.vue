<script setup lang="ts">
import { reactive, ref } from 'vue'

import { messageErreur } from '../api/client'
import { useSimulationsStore } from '../stores/simulations'
import BaseDialog from './BaseDialog.vue'

const props = defineProps<{
  simulationId: string
}>()

const emit = defineEmits<{
  fermer: []
  ajoute: []
}>()

const store = useSimulationsStore()

const formulaire = reactive({
  identifiant: '',
  code_eic: '',
  puissance_nominale_mw: 0,
  jepp_initial: 0,
})

const erreurs = ref<Record<string, string>>({})
const erreurApi = ref<string | null>(null)

function valider(): boolean {
  const prochainesErreurs: Record<string, string> = {}

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

  try {
    await store.ajouterTranche(props.simulationId, {
      tranche: {
        identifiant: formulaire.identifiant.trim(),
        code_eic: formulaire.code_eic.trim(),
        puissance_nominale_mw: Number(formulaire.puissance_nominale_mw),
        jepp_initial: Number(formulaire.jepp_initial),
      },
      arrets: [],
      modulations: [],
    })
    emit('ajoute')
  } catch (error) {
    erreurApi.value = messageErreur(error)
  }
}
</script>

<template>
  <BaseDialog
    titre="Ajouter une tranche"
    description="Renseignez les caractéristiques de la nouvelle tranche nucléaire."
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

      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label for="tranche-identifiant" class="etiquette">
            Identifiant
          </label>
          <input
            id="tranche-identifiant"
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
          <label for="tranche-code-eic" class="etiquette">Code EIC</label>
          <input
            id="tranche-code-eic"
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
          <label for="tranche-puissance" class="etiquette">
            Puissance nominale (MW)
          </label>
          <input
            id="tranche-puissance"
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
          <label for="tranche-jepp" class="etiquette">JEPP initial</label>
          <input
            id="tranche-jepp"
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

      <div
        class="flex flex-wrap items-center justify-end gap-3 border-t border-slate-100 pt-4"
      >
        <button
          type="button"
          class="bouton-secondaire"
          :disabled="store.saving"
          @click="emit('fermer')"
        >
          Annuler
        </button>
        <button type="submit" class="bouton-primaire" :disabled="store.saving">
          {{ store.saving ? 'Ajout…' : 'Ajouter la tranche' }}
        </button>
      </div>
    </form>
  </BaseDialog>
</template>
