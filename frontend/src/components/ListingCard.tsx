"use client";
import Image from "next/image";
import { Listing } from "@/lib/types";
import { DealBadge } from "./DealBadge";
import { formatPrice, formatMileage, timeAgo, titleStatusColor, cn } from "@/lib/utils";

interface Props {
  listing: Listing;
  selected?: boolean;
  onClick: () => void;
}

export function ListingCard({ listing, selected, onClick }: Props) {
  const photo = listing.photos?.[0];
  const carName = [listing.year, listing.make, listing.model, listing.generation]
    .filter(Boolean).join(" ");

  return (
    <div
      onClick={onClick}
      className={cn(
        "flex gap-3 p-3 cursor-pointer transition-colors border-b border-zinc-800 hover:bg-zinc-800/60",
        selected && "bg-zinc-800 border-l-2 border-l-blue-500"
      )}
    >
      {/* Photo */}
      <div className="relative w-24 h-18 rounded overflow-hidden bg-zinc-800 shrink-0" style={{ height: 72 }}>
        {photo ? (
          <Image
            src={photo}
            alt={carName}
            fill
            className="object-cover"
            unoptimized
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-zinc-600 text-xs">No photo</div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="font-semibold text-sm text-white truncate">{carName || listing.title || "Unknown"}</div>
          <DealBadge score={listing.deal_rating} confidence={listing.deal_confidence} size="sm" />
        </div>

        <div className="flex items-center gap-2 mt-1 text-sm">
          <span className="text-white font-medium">{formatPrice(listing.price)}</span>
          <span className="text-zinc-500">·</span>
          <span className="text-zinc-400">{formatMileage(listing.mileage)}</span>
          {listing.transmission === "manual" && (
            <>
              <span className="text-zinc-500">·</span>
              <span className="text-emerald-400 text-xs font-medium">Manual</span>
            </>
          )}
        </div>

        <div className="flex flex-wrap gap-1 mt-1.5">
          {listing.title_status && listing.title_status !== "clean" && (
            <span className={cn("text-xs px-1.5 py-0.5 rounded bg-zinc-700", titleStatusColor(listing.title_status))}>
              {listing.title_status} title
            </span>
          )}
          {listing.city && (
            <span className="text-xs text-zinc-500">{listing.city}</span>
          )}
          {listing.posted_at && (
            <span className="text-xs text-zinc-600 ml-auto">{timeAgo(listing.posted_at)}</span>
          )}
        </div>

        {/* Red flags */}
        {listing.red_flags && listing.red_flags.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {listing.red_flags.slice(0, 2).map((flag, i) => (
              <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-red-950 text-red-400 border border-red-900">
                ⚠ {flag}
              </span>
            ))}
            {listing.red_flags.length > 2 && (
              <span className="text-xs text-zinc-500">+{listing.red_flags.length - 2} more</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
