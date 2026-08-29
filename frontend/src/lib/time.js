// Days from now until `dateStr` (can be negative if overdue).
export function daysUntil(dateStr) {
  const target = new Date(dateStr).getTime();
  const now = Date.now();
  return (target - now) / (1000 * 60 * 60 * 24);
}

export function isDue(dateStr) {
  return daysUntil(dateStr) <= 0;
}

// Friendly, kid-readable label used across the trail / card lists.
export function horizonLabel(dateStr) {
  const d = daysUntil(dateStr);
  if (d <= 0) return "Ready now!";
  if (d < 1) return "Later today";
  const days = Math.round(d);
  if (days === 1) return "Tomorrow";
  if (days < 7) return `In ${days} days`;
  if (days < 30) return `In ${Math.round(days / 7)} weeks`;
  if (days < 365) return `In ${Math.round(days / 30)} months`;
  return `In ${(days / 365).toFixed(1)} years`;
}

export function formatDateTime(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
