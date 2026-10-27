export type CouleurJepp = 'vert' | 'jaune' | 'orange' | 'rouge'

export const SEUILS_JEPP = {
  vert: 0.5,
  jaune: 0.2,
  orange: 0.05,
} as const

export function ratioJepp(jeppRestant: number, jeppInitial: number): number {
  if (!Number.isFinite(jeppRestant) || jeppInitial <= 0) return 0
  return jeppRestant / jeppInitial
}

export function couleurJepp(
  jeppRestant: number,
  jeppInitial: number,
): CouleurJepp {
  if (jeppInitial <= 0) return 'rouge'

  const ratio = ratioJepp(jeppRestant, jeppInitial)
  if (ratio >= SEUILS_JEPP.vert) return 'vert'
  if (ratio >= SEUILS_JEPP.jaune) return 'jaune'
  if (ratio >= SEUILS_JEPP.orange) return 'orange'
  return 'rouge'
}

export const classesCouleurJepp: Record<CouleurJepp, string> = {
  vert: 'bg-emerald-500',
  jaune: 'bg-amber-400',
  orange: 'bg-orange-500',
  rouge: 'bg-red-600',
}

export const classesBordureJepp: Record<CouleurJepp, string> = {
  vert: 'border-emerald-500',
  jaune: 'border-amber-400',
  orange: 'border-orange-500',
  rouge: 'border-red-600',
}

export const libellesCouleurJepp: Record<CouleurJepp, string> = {
  vert: 'JEPP supérieur ou égal à 50 %',
  jaune: 'JEPP entre 20 % et 50 %',
  orange: 'JEPP entre 5 % et 20 %',
  rouge: 'JEPP inférieur à 5 %',
}

export const classesGravite: Record<'INFO' | 'WARNING' | 'CRITICAL', string> = {
  INFO: 'bg-slate-100 text-slate-700 ring-slate-300',
  WARNING: 'bg-amber-50 text-amber-800 ring-amber-300',
  CRITICAL: 'bg-red-50 text-red-800 ring-red-300',
}

export const libellesGravite: Record<'INFO' | 'WARNING' | 'CRITICAL', string> = {
  INFO: 'Information',
  WARNING: 'Avertissement',
  CRITICAL: 'Critique',
}
