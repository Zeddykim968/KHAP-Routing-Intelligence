"use client";

import { useEffect, useRef, useState } from "react";
import styles from "./BottomSheet.module.css";

const SNAPS = { peek: 0.14, half: 0.52, full: 0.87 };
const MIN_PEEK = 104;

export default function BottomSheet({ snapTo, snapTick, onHeight, label, children }) {
  const [height, setHeight] = useState(0); // 0 until mount → slides up cleanly
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef(null);

  const snapPx = (name) => {
    const h = Math.round(window.innerHeight * SNAPS[name]);
    return name === "peek" ? Math.max(MIN_PEEK, h) : h;
  };

  // Slide in to the half position on first mount.
  useEffect(() => {
    const target = snapPx("half");
    setHeight(target);
    onHeight?.(target);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Forced snap from the page (mode changes: list/detail/route/nav).
  useEffect(() => {
    if (!snapTo || height === 0) return;
    setHeight(snapPx(snapTo));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [snapTick]);

  // Report height so the page can pad the map / offset controls.
  useEffect(() => {
    if (height > 0) onHeight?.(height);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [height]);

  const onPointerDown = (e) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    dragRef.current = {
      startY: e.clientY,
      startH: height,
      lastY: e.clientY,
      lastT: performance.now(),
      v: 0,
      moved: 0,
    };
    setDragging(true);
  };

  const onPointerMove = (e) => {
    const d = dragRef.current;
    if (!d) return;
    const now = performance.now();
    const dt = Math.max(1, now - d.lastT);
    d.v = (d.lastY - e.clientY) / dt; // px/ms, positive = dragging up
    d.moved += Math.abs(e.clientY - d.lastY);
    d.lastY = e.clientY;
    d.lastT = now;
    const max = window.innerHeight * SNAPS.full + 48;
    const next = Math.min(max, Math.max(MIN_PEEK, d.startH + (d.startY - e.clientY)));
    setHeight(next);
  };

  const onPointerUp = () => {
    const d = dragRef.current;
    dragRef.current = null;
    setDragging(false);

    // A plain tap on the grip toggles half ↔ full.
    if (d && d.moved < 4) {
      setHeight((h) => (h < window.innerHeight * SNAPS.half ? snapPx("full") : snapPx("half")));
      return;
    }

    const pts = ["peek", "half", "full"].map(snapPx);
    const v = d?.v || 0;
    let target;
    if (Math.abs(v) > 0.45) {
      if (v > 0) target = pts.find((p) => p > height + 6) ?? pts[pts.length - 1];
      else target = [...pts].reverse().find((p) => p < height - 6) ?? pts[0];
    } else {
      target = pts.reduce((best, p) => (Math.abs(p - height) < Math.abs(best - height) ? p : best));
    }
    setHeight(target);
  };

  return (
    <section
      className={`${styles.root} ${dragging ? styles.dragging : ""}`}
      style={height ? { height: `${height}px` } : { height: 0, pointerEvents: "none" }}
      aria-label={label}
    >
      <div
        className={styles.grab}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        role="separator"
        aria-label="Drag to resize"
        title="Drag to resize"
      >
        <span className={styles.grip} />
      </div>
      <div className={styles.body}>{children}</div>
    </section>
  );
}
