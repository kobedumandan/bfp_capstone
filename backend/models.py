from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime, timezone
import enum

from database import Base


class SeverityLevel(str, enum.Enum):
    critical  = "critical"
    moderate  = "moderate"
    contained = "contained"


class PersonnelStatus(str, enum.Enum):
    standby    = "standby"
    dispatched = "dispatched"
    on_scene   = "on_scene"
    off_duty   = "off_duty"


class FireStation(Base):
    __tablename__ = "fire_stations"

    id         = Column(Integer, primary_key=True)
    name       = Column(String(120), nullable=False)
    address    = Column(String(255))
    # WGS84 point: POINT(longitude latitude)
    location   = Column(Geometry("POINT", srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    personnel  = relationship("Personnel", back_populates="station")
    incidents  = relationship("Incident", back_populates="nearest_station")


class Incident(Base):
    __tablename__ = "incidents"

    id               = Column(Integer, primary_key=True)
    code             = Column(String(30), unique=True, nullable=False)   # e.g. INC-2026-084
    address          = Column(String(255))
    structure_type   = Column(String(100))
    severity         = Column(Enum(SeverityLevel), nullable=False, default=SeverityLevel.moderate)
    alarm_level      = Column(Integer, default=1)
    casualties       = Column(String(50), default="None reported")
    reported_by      = Column(String(120))
    # WGS84 point
    location         = Column(Geometry("POINT", srid=4326), nullable=False)
    reported_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at      = Column(DateTime(timezone=True), nullable=True)

    nearest_station_id = Column(Integer, ForeignKey("fire_stations.id"), nullable=True)
    nearest_station    = relationship("FireStation", back_populates="incidents")
    dispatches         = relationship("Dispatch", back_populates="incident")


class Personnel(Base):
    __tablename__ = "personnel"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(120), nullable=False)
    initials    = Column(String(4),   nullable=False)
    status      = Column(Enum(PersonnelStatus), default=PersonnelStatus.standby)
    iot_active  = Column(Boolean, default=True)
    # Live GPS position updated by IoT device
    location    = Column(Geometry("POINT", srid=4326), nullable=True)
    updated_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    station_id  = Column(Integer, ForeignKey("fire_stations.id"), nullable=True)
    station     = relationship("FireStation", back_populates="personnel")
    dispatches  = relationship("Dispatch", back_populates="personnel")


class Dispatch(Base):
    """Links a personnel member to an incident response."""
    __tablename__ = "dispatches"

    id            = Column(Integer, primary_key=True)
    incident_id   = Column(Integer, ForeignKey("incidents.id"),  nullable=False)
    personnel_id  = Column(Integer, ForeignKey("personnel.id"),  nullable=False)
    dispatched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    arrived_at    = Column(DateTime(timezone=True), nullable=True)
    # Snapshot of the GNN-computed route at dispatch time (LineString)
    route         = Column(Geometry("LINESTRING", srid=4326), nullable=True)
    eta_seconds   = Column(Integer, nullable=True)
    gnn_confidence = Column(Integer, nullable=True)  # stored as integer 0–100

    incident  = relationship("Incident",  back_populates="dispatches")
    personnel = relationship("Personnel", back_populates="dispatches")