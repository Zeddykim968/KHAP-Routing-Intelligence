"use client";

import {
  Accessibility,
  ArrowLeft,
  Clock,
  Globe,
  Landmark,
  MapPin,
  Phone,
  Siren,
  Share2,
  Shield,
  Wallet,
} from "lucide-react";
import { formatDistance, openState } from "@/lib/format";
import { INSURANCE_KIND_LABELS, TYPE_LABELS, serviceIcon, titleCase } from "@/lib/labels";
import styles from "./FacilityDetail.module.css";

const KIND_ICON = { public: Landmark, private: Shield, self: Wallet };

export default function FacilityDetail({
  facility,
  status,
  error,
  onBack,
  onDirections,
  onToast,
}) {
  if (status === "loading" || !facility) {
    return (
      <div className={`${styles.wrap} khap-scroll`}>
        <div className={styles.skTitle} />
        <div className={styles.skMeta} />
        <div className={styles.actions}>
          <div className={`${styles.skBtn} ${styles.skPrimary}`} />
          <div className={styles.skBtn} />
          <div className={styles.skBtn} />
          <div className={styles.skBtn} />
        </div>
        <div className={styles.section}>
          <div className={`${styles.skLine} ${styles.skWide}`} />
          <div className={styles.skChips}>
            {[0, 1, 2, 3, 4].map((i) => (
              <span key={i} className={styles.skChip} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.fail}>
        <p>{error}</p>
        <button className={styles.backBtn} onClick={onBack}>
          <ArrowLeft size={16} /> Back
        </button>
      </div>
    );
  }

  const st = openState(facility.is_open);

  // Group services by their seed category, preserving a stable order.
  const groups = {};
  for (const s of facility.services || []) {
    const key = s.category || "general";
    (groups[key] ||= []).push(s);
  }

  const insGroups = {};
  for (const i of facility.insurances || []) {
    const key = i.kind || "private";
    (insGroups[key] ||= []).push(i);
  }

  const tel = (facility.phone || "").replace(/\s+/g, "");

  const share = async () => {
    const text = `${facility.name} — ${facility.address || ""}${facility.county ? ", " + facility.county : ""}`.trim();
    try {
      if (navigator.share) {
        await navigator.share({ title: facility.name, text });
        return;
      }
      await navigator.clipboard.writeText(text);
      onToast?.("Facility details copied");
    } catch {
      /* user dismissed the share sheet */
    }
  };

  return (
    <div className={`${styles.wrap} khap-scroll`}>
      <div className={styles.headRow}>
        <button className={styles.backBtn} onClick={onBack} aria-label="Back to list">
          <ArrowLeft size={20} />
        </button>
        <div className={styles.headMain}>
          <h1 className={styles.title}>{facility.name}</h1>
          <div className={styles.meta}>
            <span className={styles.type}>{TYPE_LABELS[facility.facility_type] || facility.facility_type}</span>
            {facility.distance_m != null && (
              <>
                <span className={styles.dot} />
                <span className={styles.dist}>{formatDistance(facility.distance_m)} away</span>
              </>
            )}
            <span className={styles.dot} />
            <span className={st.tone === "closed" ? styles.closed : st.tone === "open" ? styles.open : styles.unknown}>
              {st.label}
            </span>
          </div>
        </div>
      </div>

      <div className={styles.badges}>
        {facility.is_emergency && (
          <span className={`${styles.badge} ${styles.badgeEmg}`}>
            <Siren size={14} /> 24/7 Emergency
          </span>
        )}
        {facility.wheelchair_accessible && (
          <span className={styles.badge}>
            <Accessibility size={14} /> Wheelchair accessible
          </span>
        )}
        {facility.open_24_7 && (
          <span className={styles.badge}>
            <Clock size={14} /> Open 24 hours
          </span>
        )}
      </div>

      <div className={styles.actions}>
        <button className={styles.primary} onClick={() => onDirections(facility)}>
          Directions
        </button>
        {tel && (
          <a className={styles.circle} href={`tel:${tel}`} aria-label="Call" title="Call">
            <Phone size={18} />
          </a>
        )}
        {facility.website && (
          <a
            className={styles.circle}
            href={facility.website}
            target="_blank"
            rel="noreferrer noopener"
            aria-label="Website"
            title="Website"
          >
            <Globe size={18} />
          </a>
        )}
        <button className={styles.circle} onClick={share} aria-label="Share" title="Share">
          <Share2 size={18} />
        </button>
      </div>

      {facility.address && (
        <div className={styles.section}>
          <div className={styles.addr}>
            <MapPin size={16} />
            <span>
              {facility.address}
              {facility.county ? `, ${facility.county}` : ""}
            </span>
          </div>
        </div>
      )}

      {facility.services?.length > 0 && (
        <div className={styles.section}>
          <h2 className={styles.h2}>Services</h2>
          {Object.entries(groups).map(([cat, list]) => (
            <div key={cat} className={styles.group}>
              <div className={styles.groupLabel}>{titleCase(cat)}</div>
              <div className={styles.chips}>
                {list.map((s) => {
                  const Icon = serviceIcon(s.icon);
                  return (
                    <span key={s.slug} className={styles.chip}>
                      <Icon size={14} />
                      {s.name}
                    </span>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {facility.insurances?.length > 0 && (
        <div className={styles.section}>
          <h2 className={styles.h2}>Insurance accepted</h2>
          {Object.entries(insGroups).map(([kind, list]) => {
            const Icon = KIND_ICON[kind] || Shield;
            return (
              <div key={kind} className={styles.group}>
                <div className={styles.groupLabel}>
                  <Icon size={14} /> {INSURANCE_KIND_LABELS[kind] || titleCase(kind)}
                </div>
                <div className={styles.chips}>
                  {list.map((i) => (
                    <span key={i.slug} className={`${styles.chip} ${styles.chipIns}`}>
                      {i.name}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
