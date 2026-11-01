"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import CategoryChips from "@/components/CategoryChips";
import FacilityDetail from "@/components/FacilityDetail";
import FacilityList from "@/components/FacilityList";
import BottomSheet from "@/components/BottomSheet";
import MapView from "@/components/MapView";
import NavigationBanner from "@/components/NavigationBanner";
import RouteHud from "@/components/RouteHud";
import SearchBar from "@/components/SearchBar";
import { fetchFacility, fetchNearest, fetchRoute } from "@/lib/api";
import { useTheme } from "@/lib/theme";
import styles from "./page.module.css";

const NAIROBI = { lat: -1.2921, lon: 36.8219 };
const SIM_SPEED = 66; // m/s along the route (~8× real driving time)
const REROUTE_TRIGGER_M = 80;
const REROUTE_THROTTLE_MS = 20_000;

const MODE_SNAP = { list: "half", detail: "half", route: "half", nav: "peek" };

/* ── small geo helpers ──────────────────────────────────────────────────── */
function distM(a, b) {
  const R = 6371000;
  const toR = Math.PI / 180;
  const dLat = (b[1] - a[1]) * toR;
  const dLon = (b[0] - a[0]) * toR;
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(a[1] * toR) * Math.cos(b[1] * toR) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

function bearingDeg(a, b) {
  const toR = Math.PI / 180;
  const y = Math.sin((b[0] - a[0]) * toR) * Math.cos(b[1] * toR);
  const x =
    Math.cos(a[1] * toR) * Math.sin(b[1] * toR) -
    Math.sin(a[1] * toR) * Math.cos(b[1] * toR) * Math.cos((b[0] - a[0]) * toR);
  return (Math.atan2(y, x) / toR + 360) % 360;
}

export default function Page() {
  const [theme, toggleTheme] = useTheme();

  // Location
  const [origin, setOrigin] = useState(null); // {lat, lon, source: gps|manual}
  const [puck, setPuck] = useState(null);
  const [locating, setLocating] = useState(false);

  // Filters
  const [typeFilter, setTypeFilter] = useState("all");
  const [openNow, setOpenNow] = useState(false);
  const [emergency, setEmergency] = useState(false);

  // Nearby list
  const [facilities, setFacilities] = useState([]);
  const [listStatus, setListStatus] = useState("loading");
  const [listError, setListError] = useState(null);
  const [listNonce, setListNonce] = useState(0);

  // Modes & selection
  const [mode, setMode] = useState("list"); // list | detail | route | nav
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailStatus, setDetailStatus] = useState("idle");
  const [detailError, setDetailError] = useState(null);

  // Route & navigation
  const [route, setRoute] = useState(null);
  const [routeDest, setRouteDest] = useState(null);
  const [routeStatus, setRouteStatus] = useState("idle");
  const [navActive, setNavActive] = useState(false);
  const [simActive, setSimActive] = useState(false);
  const [progress, setProgress] = useState(null);

  // Sheet + toast
  const [sheetHeight, setSheetHeight] = useState(null);
  const [snapTo, setSnapTo] = useState("half");
  const [snapTick, setSnapTick] = useState(0);
  const [toast, setToast] = useState(null);

  // refs
  const mapRef = useRef(null);
  const watchIdRef = useRef(null);
  const simRafRef = useRef(null);
  const simDistRef = useRef(0);
  const lastTsRef = useRef(null);
  const cumRef = useRef(null);
  const stepVertsRef = useRef(null);
  const routeRef = useRef(null);
  const destRef = useRef(null);
  const navActiveRef = useRef(false);
  const simActiveRef = useRef(false);
  const speedRef = useRef(null);
  const lastFixRef = useRef(null);
  const lastRerouteRef = useRef(0);
  const toastTimerRef = useRef(null);
  const sheetHRef = useRef(null);

  routeRef.current = route;
  navActiveRef.current = navActive;
  simActiveRef.current = simActive;
  destRef.current = routeDest || destRef.current;
  sheetHRef.current = sheetHeight;

  /* ── toast ─────────────────────────────────────────────────────────────── */
  const showToast = useCallback((msg) => {
    setToast(msg);
    clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToast(null), 3400);
  }, []);

  /* ── snap helper (mode-driven) ─────────────────────────────────────────── */
  useEffect(() => {
    setSnapTo(MODE_SNAP[mode] || "half");
    setSnapTick((t) => t + 1);
  }, [mode]);

  /* ── location ──────────────────────────────────────────────────────────── */
  const applyFix = useCallback((pos, { isInit = false } = {}) => {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const prev = lastFixRef.current;
    const t = pos.timestamp || Date.now();

    let heading = Number.isFinite(pos.coords.heading) && pos.coords.heading >= 0
      ? pos.coords.heading
      : -1;
    if (heading < 0 && prev) {
      const dt = (t - prev.t) / 1000;
      if (dt > 0.2 && distM([prev.lon, prev.lat], [lon, lat]) > 3) {
        heading = bearingDeg([prev.lon, prev.lat], [lon, lat]);
        if (Number.isFinite(pos.coords.speed)) speedRef.current = pos.coords.speed;
        else speedRef.current = distM([prev.lon, prev.lat], [lon, lat]) / dt;
      } else {
        heading = prev.heading;
      }
    }
    lastFixRef.current = { lat, lon, heading, t };
    setPuck({ lat, lon, heading, accuracy: pos.coords.accuracy, t });

    if (!simActiveRef.current) {
      setOrigin((prevO) => {
        if (
          prevO &&
          prevO.source === "gps" &&
          distM([prevO.lon, prevO.lat], [lon, lat]) < 15
        ) {
          return prevO;
        }
        return { lat, lon, source: "gps" };
      });
    }

    // Live progress + off-route detection while navigating with GPS.
    if (navActiveRef.current && !simActiveRef.current && routeRef.current) {
      const p = computeProgress([lon, lat]);
      if (p) setProgress(p);
      if (p && p.offRoute > REROUTE_TRIGGER_M && Date.now() - lastRerouteRef.current > REROUTE_THROTTLE_MS) {
        lastRerouteRef.current = Date.now();
        const dest = destRef.current;
        if (dest) {
          planRoute({ lat, lon }, dest, { keepMode: true });
          showToast("Rerouting — you left the route");
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startWatch = useCallback(() => {
    if (watchIdRef.current != null || !navigator.geolocation) return;
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => applyFix(pos),
      () => {
        /* interim watch errors are expected when permission is off */
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 3000 }
    );
  }, [applyFix]);

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setOrigin((o) => o || { ...NAIROBI, source: "manual" });
      showToast("Location not supported — right-click the map to set your start.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        applyFix(pos, { isInit: true });
        startWatch();
      },
      (err) => {
        setLocating(false);
        setOrigin((o) => o || { ...NAIROBI, source: "manual" });
        setPuck(null);
        showToast(
          err.code === 1
            ? "Location permission denied — right-click the map to set your start."
            : "Location unavailable — showing Nairobi CBD. Right-click the map to set your start."
        );
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
    );
  }, [applyFix, startWatch, showToast]);

  useEffect(() => {
    requestLocation();
    return () => {
      if (watchIdRef.current != null) navigator.geolocation?.clearWatch(watchIdRef.current);
      if (simRafRef.current) cancelAnimationFrame(simRafRef.current);
      clearTimeout(toastTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ── nearby list ───────────────────────────────────────────────────────── */
  useEffect(() => {
    if (!origin) return;
    let stale = false;
    setListStatus("loading");
    fetchNearest(origin.lat, origin.lon, { type: typeFilter, openNow, emergency })
      .then((res) => {
        if (stale) return;
        setFacilities(Array.isArray(res) ? res : res?.results || []);
        setListStatus("ready");
      })
      .catch((e) => {
        if (stale) return;
        setListError(e.message);
        setListStatus("error");
      });
    return () => {
      stale = true;
    };
  }, [origin, typeFilter, openNow, emergency, listNonce]);

  /* ── route geometry precompute (cumulative distances + step vertices) ──── */
  useEffect(() => {
    if (!route?.route?.length) {
      cumRef.current = null;
      stepVertsRef.current = null;
      return;
    }
    const cum = [0];
    let acc = 0;
    for (let i = 1; i < route.route.length; i++) {
      acc += distM(route.route[i - 1], route.route[i]);
      cum.push(acc);
    }
    cumRef.current = cum;
    stepVertsRef.current = (route.steps || []).map((s) => s.index ?? 0);
  }, [route]);

  /* ── progress from a route vertex index ────────────────────────────────── */
  function progressFromIdx(idx, offRoute, speed) {
    const cum = cumRef.current;
    if (!cum) return null;
    const total = cum[cum.length - 1] || 1;
    const sv = stepVertsRef.current || [];
    let stepIndex = sv.findIndex((v) => v > idx);
    if (stepIndex < 0) stepIndex = Math.max(0, sv.length - 1);
    const maneuverV = sv[stepIndex] ?? cum.length - 1;
    const remaining = Math.max(0, total - cum[idx]);
    const effSpeed = speed || 8.3;
    return {
      stepIndex,
      distToManeuver: Math.max(0, cum[maneuverV] - cum[idx]),
      remaining_m: remaining,
      remaining_s: remaining / Math.max(2, effSpeed),
      frac: cum[idx] / total,
      offRoute,
      speed: speed ?? null,
    };
  }

  function computeProgress(target) {
    const r = routeRef.current;
    const cum = cumRef.current;
    if (!r || !cum) return null;
    let idx = 0;
    let best = Infinity;
    for (let i = 0; i < r.route.length; i++) {
      const d = distM(r.route[i], target);
      if (d < best) {
        best = d;
        idx = i;
      }
    }
    return progressFromIdx(idx, best, speedRef.current);
  }

  /* ── facility selection ────────────────────────────────────────────────── */
  const selectFacility = useCallback(
    (f) => {
      const same = f.id === selectedId;
      setSelectedId(f.id);
      setDetail(null);
      setDetailError(null);
      setDetailStatus("loading");
      setMode("detail");

      if (!same) {
        // A different destination invalidates the current route.
        if (simActiveRef.current) stopSim();
        setNavActive(false);
        setRoute(null);
        setRouteDest(null);
        setRouteStatus("idle");
        setProgress(null);
      }

      fetchFacility(f.id)
        .then((d) => {
          setDetail(d);
          setDetailStatus("ready");
          const map = mapRef.current;
          if (map) {
            if (f.latitude != null) {
              map.flyTo({
                center: [f.longitude, f.latitude],
                zoom: Math.max(map.getZoom(), 14.6),
                duration: 900,
                essential: true,
              });
            } else if (d.latitude != null) {
              map.flyTo({
                center: [d.longitude, d.latitude],
                zoom: Math.max(map.getZoom(), 14.6),
                duration: 900,
                essential: true,
              });
            }
          }
        })
        .catch((e) => {
          setDetailError(e.message);
          setDetailStatus("error");
        });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selectedId]
  );

  const backFromDetail = useCallback(() => {
    setMode(routeRef.current ? "route" : "list");
    setDetail(null);
    setDetailStatus("idle");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ── routing ───────────────────────────────────────────────────────────── */
  const fitRoute = useCallback((r) => {
    const map = mapRef.current;
    if (!map || !r?.route?.length) return;
    let w = Infinity;
    let s = Infinity;
    let e = -Infinity;
    let n = -Infinity;
    for (const [lon, lat] of r.route) {
      w = Math.min(w, lon);
      e = Math.max(e, lon);
      s = Math.min(s, lat);
      n = Math.max(n, lat);
    }
    map.fitBounds(
      [
        [w, s],
        [e, n],
      ],
      {
        padding: { top: 120, bottom: (sheetHRef.current || 160) + 30, left: 48, right: 48 },
        duration: 1100,
        maxZoom: 16.5,
        essential: true,
      }
    );
  }, []);

  const planRoute = useCallback(
    async (start, dest, { keepMode = false } = {}) => {
      setRouteStatus("loading");
      try {
        const r = await fetchRoute(start, { lat: dest.latitude, lon: dest.longitude });
        setRoute(r);
        setRouteDest(dest);
        setRouteStatus("ready");
        lastRerouteRef.current = Date.now();
        if (!keepMode) setMode("route");
        setProgress(null);
        fitRoute(r);
        return r;
      } catch (e) {
        setRouteStatus("error");
        showToast(e.message);
        return null;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [fitRoute, showToast]
  );

  const directions = useCallback(
    async (f) => {
      const dest = f || detail;
      if (!dest) return;
      if (!origin) {
        showToast("Set your starting point first — right-click the map.");
        return;
      }
      if (simActiveRef.current) stopSim();
      setNavActive(false);
      setProgress(null);
      await planRoute(origin, dest, {});
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [origin, detail, planRoute, showToast]
  );

  /* ── navigation mode ───────────────────────────────────────────────────── */
  const enterNav = useCallback(() => {
    if (!routeRef.current) return;
    setNavActive(true);
    setMode("nav");
    startWatch();
    if (lastFixRef.current && !simActiveRef.current) {
      const p = computeProgress([lastFixRef.current.lon, lastFixRef.current.lat]);
      if (p) setProgress(p);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startWatch]);

  const exitNav = useCallback(() => {
    stopSim();
    setNavActive(false);
    setProgress(null);
    setMode("route");
  }, []);

  /* ── simulation ────────────────────────────────────────────────────────── */
  function stopSim() {
    simActiveRef.current = false;
    if (simRafRef.current) {
      cancelAnimationFrame(simRafRef.current);
      simRafRef.current = null;
    }
    lastTsRef.current = null;
    setSimActive(false);
  }

  function posAlongRoute(d) {
    const cum = cumRef.current;
    const pts = routeRef.current?.route;
    if (!cum || !pts?.length) return null;
    let i = 0;
    while (i < cum.length - 2 && cum[i + 1] < d) i++;
    const span = cum[i + 1] - cum[i] || 1;
    const t = Math.min(1, Math.max(0, (d - cum[i]) / span));
    const a = pts[i];
    const b = pts[Math.min(i + 1, pts.length - 1)];
    return {
      lon: a[0] + (b[0] - a[0]) * t,
      lat: a[1] + (b[1] - a[1]) * t,
      heading: bearingDeg(a, b),
      idx: i,
    };
  }

  const toggleSim = useCallback(() => {
    if (simActiveRef.current) {
      stopSim();
      return;
    }
    const r = routeRef.current;
    if (!r || !cumRef.current) return;
    if (!navActiveRef.current) {
      setNavActive(true);
      setMode("nav");
    }

    // Resume from the current progress if we already drove part-way.
    const total = cumRef.current[cumRef.current.length - 1];
    const startFrac = progress?.frac || 0;
    simDistRef.current = startFrac * total;
    simActiveRef.current = true;
    setSimActive(true);
    lastTsRef.current = null;

    const tick = (ts) => {
      if (!simActiveRef.current) return;
      const last = lastTsRef.current ?? ts;
      const dt = Math.min(0.1, (ts - last) / 1000);
      lastTsRef.current = ts;
      simDistRef.current += dt * SIM_SPEED;

      const totalNow = cumRef.current?.[cumRef.current.length - 1] || 0;
      if (simDistRef.current >= totalNow) {
        // Arrived.
        stopSim();
        setNavActive(false);
        setProgress(null);
        setMode("route");
        showToast(`You have arrived at ${routeDest?.name || "your destination"}`);
        return;
      }

      const pos = posAlongRoute(simDistRef.current);
      if (pos) {
        const { idx } = pos;
        lastFixRef.current = { lat: pos.lat, lon: pos.lon, heading: pos.heading, t: ts };
        setPuck({ lat: pos.lat, lon: pos.lon, heading: pos.heading, accuracy: 0, t: ts });
        const p = progressFromIdx(idx, 0, null);
        if (p) setProgress(p);
      }
      simRafRef.current = requestAnimationFrame(tick);
    };
    simRafRef.current = requestAnimationFrame(tick);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [progress, routeDest, showToast]);

  /* ── map interactions ──────────────────────────────────────────────────── */
  const handleMapReady = useCallback((map) => {
    mapRef.current = map;
  }, []);

  const dropPin = useCallback(
    ({ lat, lon }) => {
      setOrigin({ lat, lon, source: "manual" });
      showToast("Start point set to this location");
    },
    [showToast]
  );

  const handleLocate = useCallback(() => {
    if (puck && mapRef.current) {
      mapRef.current.flyTo({ center: [puck.lon, puck.lat], zoom: 15, duration: 800 });
      return;
    }
    requestLocation();
  }, [puck, requestLocation]);

  const clearFilters = useCallback(() => {
    setTypeFilter("all");
    setOpenNow(false);
    setEmergency(false);
  }, []);

  /* ── render ────────────────────────────────────────────────────────────── */
  const filtered = typeFilter !== "all" || openNow || emergency;
  const currentStep =
    route?.steps?.length
      ? route.steps[Math.max(0, Math.min(progress?.stepIndex ?? 0, route.steps.length - 1))]
      : null;

  let sheetBody;
  if (mode === "detail") {
    sheetBody = (
      <FacilityDetail
        facility={detail}
        status={detailStatus}
        error={detailError}
        onBack={backFromDetail}
        onDirections={(f) => directions(f)}
        onToast={showToast}
      />
    );
  } else if (mode === "route" || mode === "nav") {
    sheetBody = route ? (
      <RouteHud
        route={route}
        facility={routeDest}
        progress={progress}
        navActive={navActive}
        simActive={simActive}
        onBack={() => {
          setMode(detail ? "detail" : "list");
        }}
        onStart={enterNav}
        onSimulate={toggleSim}
        onExitNav={exitNav}
      />
    ) : (
      <div className={styles.routeMsg}>
        {routeStatus === "loading" ? "Routing…" : "No route found."}
      </div>
    );
  } else {
    sheetBody = (
      <FacilityList
        items={facilities}
        status={listStatus}
        error={listError}
        selectedId={selectedId}
        onSelect={selectFacility}
        onRetry={() => setListNonce((n) => n + 1)}
        hasOrigin={!!origin}
        filtered={filtered}
        onClearFilters={clearFilters}
      />
    );
  }

  return (
    <div className={styles.app}>
      {!navActive && (
        <div className={styles.topBar}>
          <SearchBar
            origin={origin}
            theme={theme}
            onToggleTheme={toggleTheme}
            onSelect={selectFacility}
            onLocate={handleLocate}
            locating={locating}
          />
          <CategoryChips
            value={typeFilter}
            onChange={setTypeFilter}
            openNow={openNow}
            emergency={emergency}
            onToggleOpenNow={() => setOpenNow((v) => !v)}
            onToggleEmergency={() => setEmergency((v) => !v)}
          />
        </div>
      )}

      <MapView
        theme={theme}
        origin={origin}
        facilities={facilities}
        selectedId={selectedId}
        route={route}
        puck={puck}
        navActive={navActive}
        bottomOffset={sheetHeight || 0}
        onSelectFacility={selectFacility}
        onDropPin={dropPin}
        onReady={handleMapReady}
      />

      {navActive && route && (
        <NavigationBanner
          step={currentStep}
          distToManeuver={progress?.distToManeuver}
          remaining_m={progress?.remaining_m ?? route.distance_m}
          remaining_s={progress?.remaining_s ?? route.duration_s}
          onExit={exitNav}
        />
      )}

      <BottomSheet snapTo={snapTo} snapTick={snapTick} onHeight={setSheetHeight} label="Results">
        {sheetBody}
      </BottomSheet>

      {toast && (
        <div
          className={styles.toast}
          style={{ bottom: `${(sheetHeight || 0) + 14}px` }}
          role="status"
        >
          {toast}
        </div>
      )}
    </div>
  );
}
