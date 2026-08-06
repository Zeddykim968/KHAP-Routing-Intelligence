# OSRM

OSRM (Open Source Routing Machine) provides high-performance road routing.

It is responsible **only** for routing — it returns distance, duration, and geometry.
All facility data lives in PostgreSQL.

## Directory layout

```
osrm/
├── data/       ← Kenya OSM extract (.osm.pbf) and processed OSRM files
└── profiles/   ← Lua routing profiles (car.lua, etc.)
```

## Setup (WSL Ubuntu)

### 1. Download Kenya OSM extract

```bash
cd osrm/data
wget https://download.geofabrik.de/africa/kenya-latest.osm.pbf
```

### 2. Pre-process with OSRM Docker

```bash
docker run -t -v $(pwd)/osrm/data:/data osrm/osrm-backend \
    osrm-extract -p /opt/car.lua /data/kenya-latest.osm.pbf

docker run -t -v $(pwd)/osrm/data:/data osrm/osrm-backend \
    osrm-partition /data/kenya-latest.osrm

docker run -t -v $(pwd)/osrm/data:/data osrm/osrm-backend \
    osrm-customize /data/kenya-latest.osrm
```

### 3. Run the OSRM server

```bash
docker run -t -i -p 5000:5000 -v $(pwd)/osrm/data:/data osrm/osrm-backend \
    osrm-routed --algorithm mld /data/kenya-latest.osrm
```

Server is now available at `http://localhost:5000`.

Set `OSRM_URL=http://localhost:5000` in `.env`.

## API used by KHAP

```
GET /route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson
```

Returns `distance` (metres), `duration` (seconds), and a GeoJSON `LineString` geometry.
