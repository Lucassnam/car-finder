"use client";
import { useState, useCallback, useEffect } from "react";
import { useQuery, useInfiniteQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { RefreshCw, Car } from "lucide-react";

import { FilterBar } from "@/components/FilterBar";
import { ListingList } from "@/components/ListingList";
import { ListingDetail } from "@/components/ListingDetail";
import { fetchListings, fetchMapPoints, triggerSweep } from "@/lib/api";
import type { FilterState, Listing } from "@/lib/types";

// MapLibre uses browser APIs — must be client-only
const Map = dynamic(() => import("@/components/Map").then(m => m.Map), { ssr: false });

const DEFAULT_FILTERS: FilterState = {
  make: "",
  model: "",
  min_year: "",
  max_year: "",
  min_price: "",
  max_price: "30000",
  min_score: "5",
  transmission: "",
  title_status: "",
  private_only: true,
  sort_by: "deal_rating",
};

export default function HomePage() {
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [allListings, setAllListings] = useState<Listing[]>([]);
  const [sweeping, setSweeping] = useState(false);

  // Listings (paginated, accumulated for infinite scroll)
  const { data, isFetching, isLoading } = useQuery({
    queryKey: ["listings", filters, page],
    queryFn: () => fetchListings(filters, page),
    placeholderData: (prev) => prev,
  });

  // Accumulate pages for infinite scroll
  useEffect(() => {
    if (!data) return;
    if (page === 1) {
      setAllListings(data.items);
    } else {
      setAllListings(prev => {
        const existingIds = new Set(prev.map(l => l.id));
        const newItems = data.items.filter(l => !existingIds.has(l.id));
        return [...prev, ...newItems];
      });
    }
  }, [data, page]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
    setSelectedId(null);
  }, [filters]);

  // Map points (lightweight, separate query)
  const { data: mapPoints = [] } = useQuery({
    queryKey: ["mapPoints", filters],
    queryFn: () => fetchMapPoints({
      make: filters.make,
      max_price: filters.max_price,
      min_score: filters.min_score,
      private_only: filters.private_only,
    }),
    staleTime: 120_000,
  });

  const handleLoadMore = useCallback(() => {
    if (data && page < data.pages && !isFetching) {
      setPage(p => p + 1);
    }
  }, [data, page, isFetching]);

  const handleSweep = async () => {
    setSweeping(true);
    await triggerSweep();
    setTimeout(() => setSweeping(false), 3000);
  };

  const hasMore = data ? page < data.pages : false;

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-zinc-950">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-2 bg-zinc-950 border-b border-zinc-800 shrink-0">
        <div className="flex items-center gap-2 text-white font-bold">
          <Car size={20} className="text-blue-400" />
          Car Finder
        </div>
        <span className="text-zinc-600 text-xs">Bay Area + NorCal · Sports & Project Cars</span>
        <div className="ml-auto">
          <button
            onClick={handleSweep}
            disabled={sweeping}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded border border-zinc-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={12} className={sweeping ? "animate-spin" : ""} />
            {sweeping ? "Sweeping…" : "Refresh"}
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="shrink-0">
        <FilterBar filters={filters} onChange={setFilters} total={data?.total} />
      </div>

      {/* Main content: map left + list+detail right */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map */}
        <div className="w-[45%] shrink-0 relative border-r border-zinc-800">
          <Map
            points={mapPoints}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
          <div className="absolute bottom-2 left-2 bg-zinc-900/80 text-zinc-400 text-xs px-2 py-1 rounded backdrop-blur-sm">
            {mapPoints.length} local pins
          </div>
        </div>

        {/* Right panel: list OR detail */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {selectedId ? (
            <ListingDetail
              listingId={selectedId}
              onClose={() => setSelectedId(null)}
            />
          ) : (
            <ListingList
              listings={allListings}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onLoadMore={handleLoadMore}
              hasMore={hasMore}
              isLoading={isLoading || isFetching}
            />
          )}
        </div>
      </div>
    </div>
  );
}
