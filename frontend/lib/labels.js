// Shared display labels and lucide icon maps for facility types, services,
// and route maneuver steps.

import {
  Accessibility,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  Baby,
  Bed,
  Brain,
  CalendarDays,
  Droplets,
  Eye,
  FlaskConical,
  Flag,
  HeartHandshake,
  HeartPulse,
  Pill,
  Ribbon,
  RotateCw,
  ScanLine,
  Scissors,
  Siren,
  Smile,
  Stethoscope,
  Syringe,
  Truck,
  Undo2,
  Virus,
  Waves,
  Video,
} from "lucide-react";

export const TYPE_LABELS = {
  hospital: "Hospital",
  clinic: "Clinic",
  health_centre: "Health centre",
  dispensary: "Dispensary",
  pharmacy: "Pharmacy",
  dentist: "Dentist",
  laboratory: "Laboratory",
  maternity: "Maternity",
  eye_clinic: "Eye clinic",
};

export const INSURANCE_KIND_LABELS = {
  public: "Public / NHIF·SHA",
  private: "Private insurers",
  self: "Self pay",
};

// Icon slugs used by the seed data, with safe fallbacks for renamed icons.
export const SERVICE_ICONS = {
  stethoscope: Stethoscope,
  bed: Bed,
  siren: Siren,
  baby: Baby,
  scissors: Scissors,
  pill: Pill,
  "flask-conical": FlaskConical,
  "scan-line": ScanLine,
  waves: Waves,
  "heart-pulse": HeartPulse,
  smile: Smile,
  eye: Eye,
  "baby-face": Baby,
  "calendar-heart": CalendarDays,
  syringe: Syringe,
  accessibility: Accessibility,
  droplets: Droplets,
  ribbon: Ribbon,
  brain: Brain,
  virus: Virus,
  "activity-heartbeat": HeartPulse,
  "heart-handshake": HeartHandshake,
  truck: Truck,
  video: Video,
};

export function serviceIcon(slug) {
  return SERVICE_ICONS[slug] || Stethoscope;
}

export const STEP_ICONS = {
  left: ArrowLeft,
  right: ArrowRight,
  straight: ArrowUp,
  roundabout: RotateCw,
  uturn: Undo2,
  arrive: Flag,
};

export function stepIcon(icon) {
  return STEP_ICONS[icon] || ArrowUp;
}

export function titleCase(slug) {
  if (!slug) return "";
  return String(slug)
    .split(/[_\s-]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
