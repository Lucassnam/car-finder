import type { PaginatedListings, ListingDetail, MapPoint, FilterState } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

function buildParams(filters: Partial<FilterState> & Record<string, unknown>): string {
  const p = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== "" && v !== undefined && v !== null) {
      p.set(k, String(v));
    }
  });
  return p.toString();
}

export async function fetchListings(
  filters: Partial<FilterState>,
  page = 1,
  per_page = 40
): Promise<PaginatedListings> {
  const qs = buildParams({ ...filters, page, per_page });
  const res = await fetch(`${BASE}/listings?${qs}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch listings: ${res.status}`);
  return res.json();
}

export async function fetchListing(id: string): Promise<ListingDetail> {
  const res = await fetch(`${BASE}/listings/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch listing ${id}: ${res.status}`);
  return res.json();
}

export async function fetchMapPoints(filters: Partial<FilterState>): Promise<MapPoint[]> {
  const qs = buildParams(filters);
  const res = await fetch(`${BASE}/listings/map/points?${qs}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch map points: ${res.status}`);
  return res.json();
}

export async function triggerSweep(): Promise<void> {
  await fetch(`${BASE}/pipeline/run/craigslist`, { method: "POST" });
}
