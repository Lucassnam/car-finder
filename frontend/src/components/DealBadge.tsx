import { cn, scoreColor, scoreLabel } from "@/lib/utils";

interface Props {
  score: number | null;
  confidence?: string | null;
  size?: "sm" | "md";
}

export function DealBadge({ score, confidence, size = "md" }: Props) {
  const label = size === "sm" ? (score ?? "?") : scoreLabel(score);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-bold rounded",
        size === "sm" ? "px-2 py-0.5 text-sm" : "px-3 py-1 text-base",
        scoreColor(score)
      )}
      title={confidence === "low" ? "AI estimate (no comp data yet)" : undefined}
    >
      {label}
      {confidence === "low" && (
        <span className="opacity-60 text-xs font-normal">~</span>
      )}
    </span>
  );
}
