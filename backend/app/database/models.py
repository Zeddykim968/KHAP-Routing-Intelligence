from sqlalchemy import Column, BigInteger, Integer, String
from geoalchemy2 import Geometry
from app.database.session import Base


class HealthFacility(Base):
    """
    Schema: gis
    Table:  health_facilities

    Stores every healthcare facility imported from OpenStreetMap.
    The `geom` column is a PostGIS Point (SRID 4326).
    The `vertex_id` links to routing.edges_vertices_pgr for pgRouting.
    """
    __tablename__ = "health_facilities"
    __table_args__ = {"schema": "gis"}

    id            = Column(Integer,    primary_key=True, index=True)
    name          = Column(String)
    facility_type = Column(String)
    operator      = Column(String)
    phone         = Column(String)
    website       = Column(String)
    emergency     = Column(String)
    opening_hours = Column(String)
    wheelchair    = Column(String)
    geom          = Column(Geometry("POINT", srid=4326))
    vertex_id     = Column(BigInteger)


class Edge(Base):
    """
    Schema: routing
    Table:  edges

    Road network imported from OpenStreetMap via osm2pgrouting.
    Used by pgRouting for graph-based shortest-path calculations.
    """
    __tablename__ = "edges"
    __table_args__ = {"schema": "routing"}

    id           = Column(BigInteger, primary_key=True, index=True)
    source       = Column(BigInteger)
    target       = Column(BigInteger)
    cost         = Column(String)        # DOUBLE PRECISION in DB
    reverse_cost = Column(String)
    highway      = Column(String)
    way          = Column(Geometry("LINESTRING", srid=4326))
