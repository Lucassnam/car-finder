"use client";
import { useEffect, useRef } from "react";
import type { Map as MapLibreMap, Marker, Popup } from "maplibre-gl";
import { MapPoint } from "@/lib/types";
import { formatPrice, pinColor } from "@/lib/utils";

interface Props {
  points: MapPoint[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

// Bay Area center
const DEFAULT_CENTER: [number, number] = [-122.05, 37.5];
const DEFAULT_ZOOM = 8.5;

export function Map({ points, selectedId, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markersRef = useRef<globalThis.Map<string, Marker>>(new globalThis.Map());
  const popupRef = useRef<Popup | null>(null);

  // Init map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    // Dynamic import — MapLibre uses browser APIs, can't run on server
    import("maplibre-gl").then(({ Map, Popup }) => {
      const map = new Map({
        container: containerRef.current!,
        style: {
          version: 8,
          sources: {
            "osm-tiles": {
              type: "raster",
              tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
              tileSize: 256,
              attribution: "© OpenStreetMap contributors",
            },
          },
          layers: [{ id: "osm", type: "raster", source: "osm-tiles" }],
        },
        center: DEFAULT_CENTER,
        zoom: DEFAULT_ZOOM,
        attributionControl: false,
      });

      mapRef.current = map;

      // Dark-tint overlay so pins pop
      map.on("style.load", () => {
        if (!map.getLayer("osm")) return;
        map.setPaintProperty("osm", "raster-brightness-max", 0.45);
        map.setPaintProperty("osm", "raster-saturation", -0.5);
      });
    });

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  // Sync markers when points change
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    import("maplibre-gl").then(({ Marker, Popup }) => {
      const incoming = new Set(points.map(p => p.id));

      // Remove stale markers
      markersRef.current.forEach((marker, id) => {
        if (!incoming.has(id)) {
          marker.remove();
          markersRef.current.delete(id);
        }
      });

      // Add new markers
      points.forEach((point) => {
        if (markersRef.current.has(point.id)) return;

        const el = document.createElement("div");
        const color = pinColor(point.score);
        const score = point.score ?? "?";
        el.innerHTML = `
          <div style="
            background:${color};
            color:white;
            border-radius:50%;
            width:28px;height:28px;
            display:flex;align-items:center;justify-content:center;
            font-size:11px;font-weight:700;
            border:2px solid rgba(255,255,255,0.3);
            cursor:pointer;
            box-shadow:0 2px 8px rgba(0,0,0,0.6);
            transition:transform 0.1s;
          ">${score}</div>`;

        const marker = new Marker({ element: el })
          .setLngLat([point.lng, point.lat])
          .addTo(map);

        el.addEventListener("mouseenter", () => {
          if (popupRef.current) popupRef.current.remove();
          const popup = new Popup({ closeButton: false, offset: 20 })
            .setLngLat([point.lng, point.lat])
            .setHTML(`
              <strong>${point.year ?? ""} ${point.make ?? ""} ${point.model ?? ""}</strong><br/>
              ${formatPrice(point.price)} · Score ${point.score ?? "?"}
              ${point.title_status && point.title_status !== "clean" ? `<br/><span style="color:#f87171">${point.title_status} title</span>` : ""}
            `)
            .addTo(map);
          popupRef.current = popup;
        });

        el.addEventListener("mouseleave", () => {
          setTimeout(() => popupRef.current?.remove(), 300);
        });

        el.addEventListener("click", () => {
          onSelect(point.id);
        });

        markersRef.current.set(point.id, marker);
      });
    });
  }, [points, onSelect]);

  // Highlight selected marker
  useEffect(() => {
    markersRef.current.forEach((marker, id) => {
      const el = marker.getElement().firstElementChild as HTMLElement | null;
      if (!el) return;
      el.style.transform = id === selectedId ? "scale(1.4)" : "scale(1)";
      el.style.zIndex = id === selectedId ? "10" : "1";
    });
  }, [selectedId]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full"
      style={{ minHeight: 300 }}
    />
  );
}
