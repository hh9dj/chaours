<script setup lang="ts">
const emit = defineEmits<{ creer: [] }>()
</script>

<template>
  <button
    type="button"
    class="group flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-slate-300 bg-white/60 p-5 text-slate-500 transition hover:border-edf-blue hover:bg-edf-paper hover:text-edf-blue"
    @click="emit('creer')"
  >
    <span
      class="flex h-12 w-12 items-center justify-center rounded-full border border-slate-300 bg-white text-2xl font-light transition group-hover:border-edf-orange group-hover:text-edf-orange"
      aria-hidden="true"
    >
      +
    </span>
    <span class="text-sm font-semibold">Nouvelle simulation</span>
    <span class="text-xs text-slate-400">
      Définir un scénario de production
    </span>
  </button>
</template>
