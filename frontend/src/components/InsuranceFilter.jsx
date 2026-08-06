// Checkbox list of insurance providers, loaded from the backend so
// the options always match app/constants.py without a frontend redeploy.
import { useEffect, useState } from "react";
import { fetchInsuranceProviders } from "../api/client";

export default function InsuranceFilter({ selected, onChange }) {
  const [providers, setProviders] = useState([]);

  useEffect(() => {
    fetchInsuranceProviders().then(setProviders).catch(() => setProviders([]));
  }, []);

  function toggle(provider) {
    const next = selected.includes(provider)
      ? selected.filter((p) => p !== provider)
      : [...selected, provider];
    onChange(next);
  }

  return (
    <div>
      <p>Filter by insurance:</p>
      {providers.map((p) => (
        <label key={p} style={{ marginRight: 8 }}>
          <input
            type="checkbox"
            checked={selected.includes(p)}
            onChange={() => toggle(p)}
          />
          {p}
        </label>
      ))}
    </div>
  );
}
