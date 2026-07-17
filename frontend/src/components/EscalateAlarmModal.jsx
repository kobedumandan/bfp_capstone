import { useEffect, useMemo, useState } from "react";
import AppModal from "./AppModal";
import {
  fetchDispatchRecommendations,
  fetchTeams,
  createDispatch,
  updateIncident,
} from "../api";
import "../styles/AppModal.css";

// Alarm levels the dashboard exposes (mirrors Log/Edit incident modals). The
// backend also knows "General Alarm", but the rest of the UI caps at 3rd, so
// escalation does too — a dispatcher never escalates past what they can log.
const ALARM_LEVELS = ["1st Alarm", "2nd Alarm", "3rd Alarm"];

// Human copy for the diagnostic `reason` codes when nothing eligible remains.
const REASON_COPY = {
  incident_missing_coordinates:
    "The incident has no map coordinates, so routes can't be computed.",
  no_teams_configured: "No response teams are configured in the system.",
  all_teams_active: "Every other team is already active on an incident.",
  no_team_on_shift: "No additional team is assigned to the current shift.",
  no_available_truck: "No remaining eligible team has an available truck.",
  no_team_on_standby: "No additional team is fully on standby.",
};

function formatEta(minutes) {
  if (minutes == null) return "—";
  if (minutes < 1) return "< 1 min";
  return `${Math.round(minutes)} min`;
}

/**
 * Propose-and-confirm alarm escalation.
 *
 * Raises the incident's alarm level and lets the dispatcher review a ranked
 * shortlist of additional units before committing. Nothing is dispatched until
 * the dispatcher confirms — the system recommends, the human authorizes.
 *
 * Props:
 *   incident      – selected incident (needs fire_id, alarm, id, loc, sev)
 *   onClose       – dismiss the modal
 *   onDispatched  – called once per team actually dispatched, with
 *                   { team, dispatchId, routes } (same shape DispatchModal uses)
 */
export default function EscalateAlarmModal({ incident, onClose, onDispatched }) {
  const currentLevel = incident?.alarm || "1st Alarm";
  const currentIdx = Math.max(0, ALARM_LEVELS.indexOf(currentLevel));
  const nextLevel = ALARM_LEVELS[currentIdx + 1] || null;
  const atMax = !nextLevel;

  // Only fetch (and thus start in a loading state) when there's a level to
  // escalate to and a real incident to fetch for.
  const willFetch = !atMax && !!incident?.fire_id;
  const [loading, setLoading] = useState(willFetch);
  const [loadError, setLoadError] = useState(null);
  const [recs, setRecs] = useState([]);
  const [teams, setTeams] = useState([]);
  const [alreadyActive, setAlreadyActive] = useState(0);
  const [targetUnits, setTargetUnits] = useState(null);
  const [reason, setReason] = useState(null);
  const [selected, setSelected] = useState(() => new Set());

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  useEffect(() => {
    if (!willFetch) return;
    let cancelled = false;
    Promise.all([
      fetchDispatchRecommendations(incident.fire_id, {
        limit: 8,
        targetLevel: nextLevel,
      }),
      fetchTeams().catch(() => []),
    ])
      .then(([data, teamList]) => {
        if (cancelled) return;
        const recommended = data.recommended || [];
        const active = data.already_active || 0;
        const target = data.target_units ?? currentIdx + 2;
        setRecs(recommended);
        setTeams(teamList || []);
        setAlreadyActive(active);
        setTargetUnits(target);
        setReason(data.reason || null);
        // Pre-select the top (target − already responding) recommended units.
        const additional = Math.max(target - active, 0);
        setSelected(
          new Set(recommended.slice(0, additional).map((r) => r.team_id))
        );
      })
      .catch((ex) => {
        if (!cancelled) setLoadError(ex.message || "Failed to load recommendations.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [willFetch, incident?.fire_id, nextLevel, currentIdx]);

  const recommendedCount = useMemo(
    () => Math.max((targetUnits ?? 0) - alreadyActive, 0),
    [targetUnits, alreadyActive]
  );
  const shortfall = Math.max(recommendedCount - recs.length, 0);

  function toggle(teamId) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(teamId)) next.delete(teamId);
      else next.add(teamId);
      return next;
    });
  }

  async function handleConfirm() {
    if (!incident?.fire_id || !nextLevel) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      // 1. Raise the alarm level (broadcasts incident_updated → sidebar refreshes).
      await updateIncident(incident.fire_id, { fire_alarm_level: nextLevel });

      // 2. Dispatch each chosen team in ranked order. Reuses the same dispatch
      //    endpoint as manual dispatch, so routes/websocket behave identically.
      const chosen = recs.filter((r) => selected.has(r.team_id));
      for (const rec of chosen) {
        const result = await createDispatch({
          fire_id: incident.fire_id,
          team_id: rec.team_id,
        });
        const full = teams.find((t) => t.team_id === rec.team_id);
        onDispatched?.({
          team: full || {
            team_id: rec.team_id,
            team_name: rec.team_name,
            station_name: rec.station_name,
            members: [],
          },
          dispatchId: result.dispatch_id,
          routes: result.routes ?? [],
        });
      }
      onClose();
    } catch (ex) {
      setSubmitError(ex.message || "Escalation failed.");
      setSubmitting(false);
    }
  }

  const selectedCount = selected.size;

  return (
    <AppModal
      eyebrow="ESCALATE ALARM"
      title={atMax ? "Highest Alarm Level" : "Escalate Alarm"}
      width={480}
      onClose={onClose}
    >
      <div className="apm-scroll">
        <div className="apm-body">
          {/* Incident summary strip */}
          <div className="dpm-incident-strip">
            <div className="dpm-strip-wrap">
              <div className="dpm-strip-id">{incident?.id}</div>
              <div className="dpm-strip-loc">{incident?.loc}</div>
            </div>
            <div
              className={`dpm-strip-sev dpm-sev-${(incident?.sev || "").toLowerCase()}`}
            >
              {incident?.sev}
            </div>
          </div>

          {atMax ? (
            <div className="adm-banner adm-banner-warn" role="status">
              This incident is already at the highest alarm level
              ({currentLevel}). No further escalation is available.
            </div>
          ) : loading ? (
            <div className="dpm-empty">Loading recommended units…</div>
          ) : loadError ? (
            <div className="apm-error">{loadError}</div>
          ) : (
            <>
              <div className="adm-banner adm-banner-ok" role="status">
                Escalating <strong>{currentLevel}</strong> →{" "}
                <strong>{nextLevel}</strong>. This level calls for{" "}
                <strong>{targetUnits}</strong> unit
                {targetUnits === 1 ? "" : "s"}; <strong>{alreadyActive}</strong>{" "}
                already responding.
              </div>

              {recs.length === 0 ? (
                <div className="adm-reason">
                  {REASON_COPY[reason] ||
                    "No additional units are available to dispatch right now. The alarm level will still be raised."}
                </div>
              ) : (
                <>
                  <div className="apm-section-label">
                    Recommended Units — dispatching {selectedCount}
                  </div>

                  {shortfall > 0 && (
                    <div className="adm-reason">
                      Only {recs.length} of the {recommendedCount} recommended
                      units are available.
                    </div>
                  )}

                  <div className="adm-cand-list">
                    {recs.map((c, i) => {
                      const isSel = selected.has(c.team_id);
                      return (
                        <button
                          type="button"
                          key={c.team_id}
                          className={`adm-cand-row${isSel ? " adm-cand-winner" : ""}`}
                          onClick={() => toggle(c.team_id)}
                          aria-pressed={isSel}
                          style={{ cursor: "pointer", textAlign: "left" }}
                        >
                          <div className="adm-cand-rank" aria-hidden="true">
                            {isSel ? "✓" : i + 1}
                          </div>
                          <div className="adm-cand-info">
                            <div className="adm-cand-name">{c.team_name}</div>
                            <div className="adm-cand-meta">
                              {c.station_name ? `${c.station_name} · ` : ""}
                              {(c.haversine_m / 1000).toFixed(1)} km
                              {c.eta_source === "haversine_fallback" && (
                                <span className="adm-cand-flag">
                                  {" "}
                                  · est. (routing offline)
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="adm-cand-eta">
                            {formatEta(c.eta_minutes)}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </>
              )}

              {submitError && <div className="apm-error">{submitError}</div>}
            </>
          )}
        </div>
      </div>

      <div className="apm-actions">
        {atMax ? (
          <button className="apm-btn-submit" onClick={onClose}>
            Close
          </button>
        ) : (
          <>
            <button
              className="apm-btn-cancel"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              className="apm-btn-submit"
              onClick={handleConfirm}
              disabled={loading || submitting}
            >
              {submitting ? (
                <span className="apm-spinner" />
              ) : selectedCount > 0 ? (
                `Escalate & Dispatch (${selectedCount})`
              ) : (
                "Escalate Alarm"
              )}
            </button>
          </>
        )}
      </div>
    </AppModal>
  );
}
