<script setup lang="ts">
const emit = defineEmits<{ creer: [] }>()
</script>

<template>
  <button
    type="button"
    class="group flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-slate-300 bg-white/60 p-5 text-slate-500 transition hover:border-sky-400 hover:bg-sky-50 hover:text-sky-800"
    @click="emit('creer')"
  >
    <span
      class="flex h-12 w-12 items-center justify-center rounded-full border border-slate-300 bg-white text-2xl font-light transition group-hover:border-sky-300 group-hover:text-sky-600"
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
