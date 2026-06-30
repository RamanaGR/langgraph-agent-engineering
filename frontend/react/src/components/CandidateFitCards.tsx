import type { RankedCandidate } from "../api/client";

export function CandidateFitCards({ candidates }: { candidates: RankedCandidate[] }) {
  if (!candidates.length) return null;

  return (
    <div className="candidate-cards">
      {candidates.map((cand, i) => (
        <div key={cand.name ?? i} className="candidate-card">
          <div className="candidate-card-header">
            <strong>{cand.name}</strong>
            <span className="fit-badge">{Math.round((cand.fit_score ?? 0) * 100)}% fit</span>
          </div>
          {cand.years_experience != null && (
            <p className="candidate-meta">{cand.years_experience} years experience</p>
          )}
          {cand.skills?.length ? (
            <div className="skill-tags">
              {cand.skills.map((s) => (
                <span key={s} className="skill-tag">
                  {s}
                </span>
              ))}
            </div>
          ) : null}
          <p className="candidate-detail">
            <span className="label-ok">Matched:</span>{" "}
            {(cand.matched_skills ?? []).join(", ") || "none"}
          </p>
          <p className="candidate-detail">
            <span className="label-gap">Gaps:</span> {(cand.gaps ?? []).join(", ") || "none"}
          </p>
        </div>
      ))}
    </div>
  );
}
