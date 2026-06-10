"use client";
import { FilterState } from "@/lib/types";

interface Props {
  filters: FilterState;
  onChange: (f: FilterState) => void;
  total?: number;
}

const MAKES = ["Any", "BMW", "Mazda", "Porsche", "Toyota", "Honda", "Nissan", "Subaru", "Volkswagen", "Mitsubishi", "Ford", "Chevrolet", "Dodge"];
const TRANSMISSIONS = ["Any", "manual", "automatic"];
const TITLE_STATUSES = ["Any", "clean", "salvage", "rebuilt"];
const SORT_OPTIONS = [
  { value: "deal_rating", label: "Best deal" },
  { value: "price",       label: "Price: low" },
  { value: "posted_at",   label: "Newest" },
  { value: "mileage",     label: "Low mileage" },
];

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-zinc-400 uppercase tracking-wide">{label}</label>
      {children}
    </div>
  );
}

const inputCls = "bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500 w-full";

export function FilterBar({ filters, onChange, total }: Props) {
  const set = (key: keyof FilterState, val: string | boolean) =>
    onChange({ ...filters, [key]: val });

  return (
    <div className="bg-zinc-900 border-b border-zinc-800 px-4 py-3">
      <div className="flex flex-wrap items-end gap-3">

        {/* Make */}
        <Field label="Make">
          <select className={inputCls} value={filters.make} onChange={e => set("make", e.target.value === "Any" ? "" : e.target.value)}>
            {MAKES.map(m => <option key={m}>{m}</option>)}
          </select>
        </Field>

        {/* Model free-text */}
        <Field label="Model">
          <input className={inputCls} placeholder="e.g. Miata, M3…" value={filters.model} onChange={e => set("model", e.target.value)} />
        </Field>

        {/* Year range */}
        <Field label="Year">
          <div className="flex gap-1 items-center">
            <input className={`${inputCls} w-20`} placeholder="1990" value={filters.min_year} onChange={e => set("min_year", e.target.value)} />
            <span className="text-zinc-500">–</span>
            <input className={`${inputCls} w-20`} placeholder="2020" value={filters.max_year} onChange={e => set("max_year", e.target.value)} />
          </div>
        </Field>

        {/* Price range */}
        <Field label="Price">
          <div className="flex gap-1 items-center">
            <input className={`${inputCls} w-24`} placeholder="$0" value={filters.min_price} onChange={e => set("min_price", e.target.value)} />
            <span className="text-zinc-500">–</span>
            <input className={`${inputCls} w-24`} placeholder="$50k" value={filters.max_price} onChange={e => set("max_price", e.target.value)} />
          </div>
        </Field>

        {/* Min score */}
        <Field label="Min score">
          <select className={inputCls} value={filters.min_score} onChange={e => set("min_score", e.target.value)}>
            <option value="">Any</option>
            {[5,6,7,8,9].map(n => <option key={n} value={n}>{n}+</option>)}
          </select>
        </Field>

        {/* Transmission */}
        <Field label="Trans">
          <select className={inputCls} value={filters.transmission} onChange={e => set("transmission", e.target.value === "Any" ? "" : e.target.value)}>
            {TRANSMISSIONS.map(t => <option key={t}>{t}</option>)}
          </select>
        </Field>

        {/* Title */}
        <Field label="Title">
          <select className={inputCls} value={filters.title_status} onChange={e => set("title_status", e.target.value === "Any" ? "" : e.target.value)}>
            {TITLE_STATUSES.map(t => <option key={t}>{t}</option>)}
          </select>
        </Field>

        {/* Sort */}
        <Field label="Sort">
          <select className={inputCls} value={filters.sort_by} onChange={e => set("sort_by", e.target.value)}>
            {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </Field>

        {/* Private-only toggle */}
        <Field label="Private only">
          <button
            onClick={() => set("private_only", !filters.private_only)}
            className={`px-3 py-1.5 rounded text-sm font-medium border transition-colors ${
              filters.private_only
                ? "bg-blue-600 border-blue-500 text-white"
                : "bg-zinc-800 border-zinc-700 text-zinc-400"
            }`}
          >
            {filters.private_only ? "On" : "Off"}
          </button>
        </Field>

        {/* Result count */}
        {total !== undefined && (
          <div className="ml-auto text-sm text-zinc-400 self-end pb-1.5">
            {total.toLocaleString()} listings
          </div>
        )}
      </div>
    </div>
  );
}
