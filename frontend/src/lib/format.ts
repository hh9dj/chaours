const formateurDate = new Intl.DateTimeFormat('fr-FR', {
  day: '2-digit',
  month: 'long',
  year: 'numeric',
})

const formateurNombre = new Intl.NumberFormat('fr-FR', {
  maximumFractionDigits: 1,
})

const formateurEntier = new Intl.NumberFormat('fr-FR', {
  maximumFractionDigits: 0,
})

export function formaterDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return 'Date inconnue'
  return formateurDate.format(date)
}

export function formaterNombre(valeur: number): string {
  if (!Number.isFinite(valeur)) return '—'
  return formateurNombre.format(valeur)
}

export function formaterEntier(valeur: number): string {
  if (!Number.isFinite(valeur)) return '—'
  return formateurEntier.format(valeur)
}

export function formaterEuros(valeur: number): string {
  return `${formaterNombre(valeur)} €`
}

export function formaterEnergie(valeur: number): string {
  return `${formaterNombre(valeur)} MWh`
}

export function formaterPourcentage(ratio: number): string {
  if (!Number.isFinite(ratio)) return '—'
  return `${formaterNombre(ratio * 100)} %`
}

export function formaterJour(jour: number): string {
  return `Jour ${jour}`
}

export function analyserSerie(texte: string): {
  valeurs: number[]
  erreur: string | null
} {
  const lignes = texte
    .split(/\r?\n/)
    .map((ligne) => ligne.trim())
    .filter((ligne) => ligne.length > 0)

  const valeurs: number[] = []
  for (const [index, ligne] of lignes.entries()) {
    const normalisee = ligne.replace(/\s+/g, '').replace(',', '.')
    const valeur = Number(normalisee)
    if (!Number.isFinite(valeur)) {
      return {
        valeurs: [],
        erreur: `La valeur ligne ${index + 1} (« ${ligne} ») n’est pas un nombre valide.`,
      }
    }
    valeurs.push(valeur)
  }

  return { valeurs, erreur: null }
}

export function formaterSerie(valeurs: number[]): string {
  return valeurs.map((valeur) => String(valeur)).join('\n')
}

export function redimensionnerSerie(
  valeurs: number[],
  horizonJours: number,
): number[] {
  const horizon = Math.max(0, Math.floor(horizonJours))
  if (horizon === 0) return []
  if (valeurs.length >= horizon) return valeurs.slice(0, horizon)

  const derniereValeur = valeurs.length > 0 ? valeurs[valeurs.length - 1] : 0
  return [
    ...valeurs,
    ...Array.from({ length: horizon - valeurs.length }, () => derniereValeur),
  ]
}
