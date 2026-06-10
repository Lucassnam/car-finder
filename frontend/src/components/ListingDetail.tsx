"use client";
import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import { X, ExternalLink, Copy, Check } from "lucide-react";
import { useState } from "react";
import { fetchListing } from "@/lib/api";
import { DealBadge } from "./DealBadge";
import { formatPrice, formatMileage, timeAgo, titleStatusColor, cn } from "@/lib/utils";

interface Props {
  listingId: string;
  onClose: () => void;
}

export function ListingDetail({ listingId, onClose }: Props) {
  const [photoIdx, setPhotoIdx] = useState(0);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const { data: listing, isLoading } = useQuery({
    queryKey: ["listing", listingId],
    queryFn: () => fetchListing(listingId),
  });

  const copyQuestion = async (q: string, i: number) => {
    await navigator.clipboard.writeText(q);
    setCopiedIdx(i);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  if (isLoading || !listing) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-500 text-sm">
        Loading…
      </div>
    );
  }

  const carName = [listing.year, listing.make, listing.model, listing.generation, listing.trim]
    .filter(Boolean).join(" ");
  const photos = listing.photos ?? [];

  return (
    <div className="flex flex-col h-full overflow-y-auto scrollbar-hide bg-zinc-900">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-zinc-900 border-b border-zinc-800 px-4 py-3 flex items-center gap-3">
        <button onClick={onClose} className="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white">
          <X size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <h2 className="font-bold text-white truncate">{carName || listing.title}</h2>
          <div className="text-xs text-zinc-400">{listing.city}{listing.state ? `, ${listing.state}` : ""}</div>
        </div>
        <DealBadge score={listing.deal_rating} confidence={listing.deal_confidence} />
      </div>

      {/* Photo gallery */}
      {photos.length > 0 && (
        <div className="relative aspect-video bg-zinc-800">
          <Image
            src={photos[photoIdx]}
            alt={carName}
            fill
            className="object-cover"
            unoptimized
          />
          {photos.length > 1 && (
            <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-1">
              {photos.slice(0, 12).map((_, i) => (
                <button
                  key={i}
                  onClick={() => setPhotoIdx(i)}
                  className={cn("w-1.5 h-1.5 rounded-full transition-colors", i === photoIdx ? "bg-white" : "bg-white/40")}
                />
              ))}
            </div>
          )}
          {photoIdx > 0 && (
            <button onClick={() => setPhotoIdx(i => i - 1)} className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 text-white px-2 py-1 rounded">‹</button>
          )}
          {photoIdx < photos.length - 1 && (
            <button onClick={() => setPhotoIdx(i => i + 1)} className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 text-white px-2 py-1 rounded">›</button>
          )}
        </div>
      )}

      <div className="p-4 flex flex-col gap-5">
        {/* Price + link */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-white">{formatPrice(listing.price)}</div>
            {listing.fair_value_estimate && (
              <div className="text-sm text-zinc-400">
                Fair value ~{formatPrice(listing.fair_value_estimate)}
                {listing.fair_value_delta != null && (
                  <span className={listing.fair_value_delta < 0 ? "text-green-400 ml-1" : "text-red-400 ml-1"}>
                    ({listing.fair_value_delta < 0 ? "−" : "+"}{formatPrice(Math.abs(listing.fair_value_delta))})
                  </span>
                )}
                {listing.comp_count > 0 && (
                  <span className="text-zinc-600 ml-1">· {listing.comp_count} comps</span>
                )}
                {listing.deal_confidence === "low" && (
                  <span className="text-zinc-600 ml-1">· AI estimate</span>
                )}
              </div>
            )}
          </div>
          <a
            href={listing.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded font-medium transition-colors"
          >
            View listing <ExternalLink size={14} />
          </a>
        </div>

        {/* Specs grid */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <Spec label="Mileage" value={formatMileage(listing.mileage)} />
          <Spec label="Transmission" value={listing.transmission ?? "—"} highlight={listing.transmission === "manual"} />
          <Spec label="Title" value={listing.title_status ?? "—"} className={titleStatusColor(listing.title_status)} />
          <Spec label="Drivetrain" value={listing.drivetrain ?? "—"} />
          <Spec label="VIN" value={listing.vin ?? "—"} mono />
          <Spec label="Listed" value={timeAgo(listing.posted_at)} />
          {listing.modifications && listing.modifications.length > 0 && (
            <div className="col-span-2">
              <div className="text-xs text-zinc-400 mb-1">Modifications</div>
              <div className="flex flex-wrap gap-1">
                {listing.modifications.map((m, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 bg-zinc-800 text-zinc-300 rounded-full">{m}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Deal rationale */}
        {listing.deal_rationale && (
          <Section title="Deal assessment">
            <p className="text-sm text-zinc-300 leading-relaxed">{listing.deal_rationale}</p>
          </Section>
        )}

        {/* Red flags */}
        {listing.red_flags && listing.red_flags.length > 0 && (
          <Section title="⚠ Red flags">
            <ul className="flex flex-col gap-1.5">
              {listing.red_flags.map((f, i) => (
                <li key={i} className="text-sm text-red-300 flex items-start gap-2">
                  <span className="text-red-500 mt-0.5">•</span>{f}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Known quirks */}
        {listing.known_quirks && listing.known_quirks.length > 0 && (
          <Section title="🔧 Known quirks to inspect">
            <ul className="flex flex-col gap-1.5">
              {listing.known_quirks.map((q, i) => (
                <li key={i} className="text-sm text-amber-200 flex items-start gap-2">
                  <span className="text-amber-500 mt-0.5">•</span>{q}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Questions to ask */}
        {listing.questions_to_ask && listing.questions_to_ask.length > 0 && (
          <Section title="💬 Questions to ask the seller">
            <ul className="flex flex-col gap-2">
              {listing.questions_to_ask.map((q, i) => (
                <li key={i} className="flex items-start justify-between gap-2 group">
                  <span className="text-sm text-zinc-300 flex items-start gap-2">
                    <span className="text-zinc-500 mt-0.5">{i + 1}.</span>{q}
                  </span>
                  <button
                    onClick={() => copyQuestion(q, i)}
                    className="shrink-0 p-1 rounded text-zinc-600 hover:text-zinc-300 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Copy question"
                  >
                    {copiedIdx === i ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                  </button>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Raw description */}
        {listing.raw_text && (
          <Section title="Original listing">
            <p className="text-xs text-zinc-500 leading-relaxed whitespace-pre-wrap">{listing.raw_text.slice(0, 1500)}</p>
          </Section>
        )}
      </div>
    </div>
  );
}

function Spec({ label, value, highlight, mono, className }: {
  label: string; value: string; highlight?: boolean; mono?: boolean; className?: string;
}) {
  return (
    <div>
      <div className="text-xs text-zinc-400">{label}</div>
      <div className={cn("text-sm font-medium mt-0.5", highlight ? "text-emerald-400" : "text-white", mono && "font-mono", className)}>
        {value}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wide mb-2">{title}</div>
      {children}
    </div>
  );
}
