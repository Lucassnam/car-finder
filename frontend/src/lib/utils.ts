import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number | null): string {
  if (!price) return "—";
  return `$${price.toLocaleString()}`;
}

export function formatMileage(mileage: number | null): string {
  if (!mileage) return "—";
  return `${mileage.toLocaleString()} mi`;
}

export function scoreColor(score: number | null): string {
  if (!score) return "bg-zinc-700 text-zinc-300";
  if (score >= 9) return "bg-emerald-500 text-white";
  if (score >= 7) return "bg-green-500 text-white";
  if (score >= 5) return "bg-amber-500 text-black";
  if (score >= 3) return "bg-orange-500 text-white";
  return "bg-red-500 text-white";
}

export function scoreLabel(score: number | null): string {
  if (!score) return "?";
  if (score >= 9) return "🔥 Great deal";
  if (score >= 7) return "Good deal";
  if (score >= 5) return "Fair";
  if (score >= 3) return "Overpriced";
  return "Pass";
}

export function titleStatusColor(status: string | null): string {
  if (!status || status === "clean") return "";
  if (status === "salvage") return "text-red-400";
  if (status === "rebuilt") return "text-amber-400";
  return "text-zinc-400";
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// Score → map pin hex color
export function pinColor(score: number | null): string {
  if (!score) return "#71717a";
  if (score >= 9) return "#10b981";
  if (score >= 7) return "#22c55e";
  if (score >= 5) return "#f59e0b";
  if (score >= 3) return "#f97316";
  return "#ef4444";
}
