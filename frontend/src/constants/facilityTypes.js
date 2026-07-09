// Central source of truth for facility-type colors and groupings.
// Kept in sync with the distinct `type` values in the Supabase `facilities`
// table (see GET /recommendations/types). Grouped by care category so visual
// disparities on the map/legend/search are meaningful, not arbitrary.

export const FACILITY_CATEGORIES = [
  {
    id: "hospitals",
    label: "Hospitals",
    types: {
      "National Referral Hospital":  "#7f1d1d",
      "Provincial General Hospital": "#b91c1c",
      "District Hospital":           "#ef4444",
      "Sub-District Hospital":       "#f97316",
      "Other Hospital":              "#fb923c",
    },
  },
  {
    id: "primary_care",
    label: "Primary & Outpatient Care",
    types: {
      "Health Centre":               "#3b82f6",
      "Medical Centre":              "#2563eb",
      "Medical Clinic":              "#06b6d4",
      "Dispensary":                  "#10b981",
      "Rural Health Training Centre":"#0ea5e9",
    },
  },
  {
    id: "maternity_nursing",
    label: "Maternity & Nursing",
    types: {
      "Maternity Home":              "#ec4899",
      "Nursing Home":                "#8b5cf6",
    },
  },
  {
    id: "specialized",
    label: "Specialized & Diagnostic",
    types: {
      "Laboratory (Stand-alone)":            "#d946ef",
      "Radiology Unit":                      "#a78bfa",
      "Blood Bank":                          "#c026d3",
      "Regional Blood Transfusion Centre":   "#e879f9",
      "Eye Centre":                          "#7c3aed",
      "Eye Clinic":                          "#a855f7",
      "Dental Clinic":                       "#84cc16",
      "VCT Centre (Stand-Alone)":            "#eab308",
    },
  },
  {
    id: "admin_other",
    label: "Admin, Training & Other",
    types: {
      "District Health Office":                          "#64748b",
      "Health Programme":                                "#78716c",
      "Health Project":                                  "#a8a29e",
      "Training Institution in Health (Stand-alone)":    "#57534e",
      "Funeral Home (Stand-alone)":                       "#44403c",
      "Not in List":                                      "#9ca3af",
    },
  },
];

// Flat lookup: type -> color, plus a default fallback.
export const FACILITY_COLORS = FACILITY_CATEGORIES.reduce((acc, cat) => {
  Object.assign(acc, cat.types);
  return acc;
}, { default: "#6b7280" });

// Flat lookup: type -> category label (for badges/analysis grouping).
export const FACILITY_TYPE_CATEGORY = FACILITY_CATEGORIES.reduce((acc, cat) => {
  Object.keys(cat.types).forEach((t) => { acc[t] = cat.label; });
  return acc;
}, {});
