// Base map (MapLibre, OpenFreeMap's free "liberty" style), plus:
//  - a distinct, DRAGGABLE marker for the search origin ("you") --
//    drag it to fine-tune after any search; drop it and the parent
//    re-searches from the new spot
//  - clicking anywhere on the map also sets a new origin, for when
//    the person doesn't know the road/neighbourhood name at all
//  - facility markers, colored to show which one is selected, each
//    with a popup that has its own "Get directions" button
//  - the actual road route as a line, with the view auto-fit to it
import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const ROUTE_SOURCE_ID = "route";
const ROUTE_LAYER_ID = "route-line";

export default function MapView({ route, facilities, origin, selectedFacilityId, onSelectFacility, onMapClick, center }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const originMarkerRef = useRef(null);
  const facilityMarkersRef = useRef([]);

  // Keep a ref to the latest onMapClick so the click listener --
  // registered once, below -- never closes over a stale callback.
  const onMapClickRef = useRef(onMapClick);
  useEffect(() => {
    onMapClickRef.current = onMapClick;
  }, [onMapClick]);

  // Init the map once, and wire up click-to-set-origin.
  useEffect(() => {
    mapRef.current = new maplibregl.Map({
      container: containerRef.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [center[1], center[0]], // MapLibre wants [lon, lat]
      zoom: 13,
    });
    mapRef.current.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current.on("click", (e) => {
      onMapClickRef.current({ lon: e.lngLat.lng, lat: e.lngLat.lat });
    });

    return () => mapRef.current?.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Origin marker ("you") -- draggable, so it can be fine-tuned after
  // any search without having to re-click the map from scratch.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (originMarkerRef.current) originMarkerRef.current.remove();
    if (origin) {
      const label = origin.accuracy
        ? `Your location (±${Math.round(origin.accuracy)}m) -- drag to adjust`
        : "Your location -- drag to adjust";
      const marker = new maplibregl.Marker({ color: "#10b981", draggable: true })
        .setLngLat([origin.lon, origin.lat])
        .setPopup(new maplibregl.Popup().setText(label))
        .addTo(map);
      marker.on("dragend", () => {
        const { lng, lat } = marker.getLngLat();
        onMapClickRef.current({ lon: lng, lat });
      });
      originMarkerRef.current = marker;
    }
  }, [origin]);

  // Facility markers, each with a popup + "Get directions" button.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    facilityMarkersRef.current.forEach((m) => m.remove());
    facilityMarkersRef.current = facilities.map((f) => {
      const node = document.createElement("div");
      node.innerHTML = `<strong>${f.name}</strong><br/>${f.facility_type}<br/>${(f.distance_m / 1000).toFixed(1)} km away`;
      const button = document.createElement("button");
      button.textContent = "Get directions";
      button.style.marginTop = "6px";
      button.onclick = () => onSelectFacility(f);
      node.appendChild(button);

      const isSelected = f.facility_id === selectedFacilityId;
      return new maplibregl.Marker({ color: isSelected ? "#2563eb" : "#ef4444" })
        .setLngLat([f.lon, f.lat])
        .setPopup(new maplibregl.Popup().setDOMContent(node))
        .addTo(map);
    });
  }, [facilities, selectedFacilityId, onSelectFacility]);

  // Route line, fit the view to it once it's drawn.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const draw = () => {
      if (!route) {
        if (map.getLayer(ROUTE_LAYER_ID)) map.removeLayer(ROUTE_LAYER_ID);
        if (map.getSource(ROUTE_SOURCE_ID)) map.removeSource(ROUTE_SOURCE_ID);
        return;
      }
      const geojson = { type: "Feature", geometry: route, properties: {} };
      if (map.getSource(ROUTE_SOURCE_ID)) {
        map.getSource(ROUTE_SOURCE_ID).setData(geojson);
      } else {
        map.addSource(ROUTE_SOURCE_ID, { type: "geojson", data: geojson });
        map.addLayer({
          id: ROUTE_LAYER_ID,
          type: "line",
          source: ROUTE_SOURCE_ID,
          paint: { "line-color": "#2563eb", "line-width": 5 },
        });
      }
      const bounds = route.coordinates.reduce(
        (b, coord) => b.extend(coord),
        new maplibregl.LngLatBounds(route.coordinates[0], route.coordinates[0])
      );
      map.fitBounds(bounds, { padding: 60, maxZoom: 15 });
    };

    if (map.isStyleLoaded()) draw();
    else map.once("load", draw);
  }, [route]);

  return <div ref={containerRef} style={{ height: "100%", width: "100%" }} />;
}
