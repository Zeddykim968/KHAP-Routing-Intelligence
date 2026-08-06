import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet's default icon paths when bundled with Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const originIcon = new L.Icon({
  iconUrl:    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
  shadowUrl:  "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize:   [25, 41],
  iconAnchor: [12, 41],
});

const selectedIcon = new L.Icon({
  iconUrl:    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
  shadowUrl:  "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize:   [25, 41],
  iconAnchor: [12, 41],
});

/** Auto-fit the map view to the route geometry when it changes. */
function FitRoute({ route }) {
  const map = useMap();
  useEffect(() => {
    if (route && route.length > 1) {
      const bounds = L.latLngBounds(route.map(([lon, lat]) => [lat, lon]));
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [route, map]);
  return null;
}

/**
 * Map component (Leaflet + react-leaflet).
 *
 * Props
 * -----
 * facilities       — array of facility objects with lat/lon
 * origin           — { lat, lon } search origin
 * selectedFacility — the currently selected facility object
 * route            — [[lon, lat], ...] GeoJSON coordinate array from OSRM
 * onSelectFacility — callback(facility) when a marker is clicked
 * onMapClick       — callback({ lat, lon }) on plain map click
 * center           — [lat, lon] initial map center
 */
export default function Map({
  facilities = [],
  origin,
  selectedFacility,
  route,
  onSelectFacility,
  onMapClick,
  center = [-1.2921, 36.8219],
}) {
  // Convert OSRM [lon, lat] pairs to Leaflet [lat, lon] pairs
  const routePositions = route ? route.map(([lon, lat]) => [lat, lon]) : [];

  return (
    <MapContainer
      center={center}
      zoom={13}
      style={{ height: "100%", width: "100%" }}
      onClick={(e) => onMapClick && onMapClick({ lat: e.latlng.lat, lon: e.latlng.lng })}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* Origin marker */}
      {origin && (
        <Marker position={[origin.lat, origin.lon]} icon={originIcon}>
          <Popup>Your location</Popup>
        </Marker>
      )}

      {/* Facility markers */}
      {facilities.map((f) => (
        <Marker
          key={f.id}
          position={[f.lat, f.lon]}
          icon={selectedFacility?.id === f.id ? selectedIcon : new L.Icon.Default()}
          eventHandlers={{ click: () => onSelectFacility && onSelectFacility(f) }}
        >
          <Popup>
            <strong>{f.name}</strong>
            <br />
            {f.facility_type}
            {f.distance_m != null && (
              <>
                <br />
                {(f.distance_m / 1000).toFixed(1)} km away
              </>
            )}
            <br />
            <button onClick={() => onSelectFacility && onSelectFacility(f)}>
              Get directions
            </button>
          </Popup>
        </Marker>
      ))}

      {/* Route polyline */}
      {routePositions.length > 1 && (
        <Polyline positions={routePositions} color="#2563eb" weight={4} opacity={0.8} />
      )}

      <FitRoute route={route} />
    </MapContainer>
  );
}
