<script setup lang="ts">
import BaseDialog from './BaseDialog.vue'

withDefaults(
  defineProps<{
    titre: string
    message: string
    libelleConfirmation?: string
    occupe?: boolean
  }>(),
  {
    libelleConfirmation: 'Supprimer',
    occupe: false,
  },
)

const emit = defineEmits<{
  confirmer: []
  fermer: []
}>()
</script>

<template>
  <BaseDialog
    :titre="titre"
    :closeable="!occupe"
    @fermer="emit('fermer')"
  >
    <p class="text-sm leading-relaxed text-slate-600">
      {{ message }}
    </p>

    <template #pied>
      <button
        type="button"
        class="bouton-secondaire"
        :disabled="occupe"
        @click="emit('fermer')"
      >
        Annuler
      </button>
      <button
        type="button"
        class="inline-flex items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="occupe"
        @click="emit('confirmer')"
      >
        {{ occupe ? 'Suppression…' : libelleConfirmation }}
      </button>
    </template>
  </BaseDialog>
</template>
