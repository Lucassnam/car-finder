"use client";
import { useRef, useEffect } from "react";
import { Listing } from "@/lib/types";
import { ListingCard } from "./ListingCard";

interface Props {
  listings: Listing[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
  isLoading?: boolean;
}

export function ListingList({ listings, selectedId, onSelect, onLoadMore, hasMore, isLoading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Infinite scroll sentinel
  useEffect(() => {
    if (!onLoadMore || !hasMore) return;
    const observer = new IntersectionObserver(
      (entries) => { if (entries[0].isIntersecting) onLoadMore(); },
      { threshold: 0.1 }
    );
    const el = bottomRef.current;
    if (el) observer.observe(el);
    return () => { if (el) observer.unobserve(el); };
  }, [onLoadMore, hasMore]);

  if (!isLoading && listings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-zinc-500 gap-2">
        <span className="text-4xl">🏁</span>
        <span className="text-sm">No listings match your filters</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col overflow-y-auto scrollbar-hide h-full">
      {listings.map((l) => (
        <ListingCard
          key={l.id}
          listing={l}
          selected={l.id === selectedId}
          onClick={() => onSelect(l.id)}
        />
      ))}
      {/* Load more sentinel */}
      <div ref={bottomRef} className="h-4" />
      {isLoading && (
        <div className="py-4 text-center text-zinc-500 text-sm">Loading…</div>
      )}
      {!hasMore && listings.length > 0 && (
        <div className="py-4 text-center text-zinc-600 text-xs">All caught up</div>
      )}
    </div>
  );
}
