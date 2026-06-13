

import type { VersionEntry } from '../types';

interface VersionTimelineProps {
  versionHistory: VersionEntry[];
  currentVersion: string;
}

export default function VersionTimeline({ versionHistory, currentVersion }: VersionTimelineProps) {
  if (!versionHistory || versionHistory.length === 0) return null;

  return (
    <div className="version-timeline" id="version-timeline">
      <div className="version-timeline__track">
        {versionHistory.map((entry, idx) => {
          const isActive = entry.version === currentVersion;
          const isFuture = idx > versionHistory.findIndex((v) => v.version === currentVersion);

          return (
            <div
              key={entry.version}
              className={`version-timeline__node ${
                isActive ? 'version-timeline__node--active' : ''
              } ${isFuture ? 'version-timeline__node--future' : ''}`}
            >
              {/* Connector line */}
              {idx > 0 && (
                <div
                  className={`version-timeline__connector ${
                    !isFuture ? 'version-timeline__connector--filled' : ''
                  }`}
                />
              )}

              {/* Node dot */}
              <div className="version-timeline__dot">
                {isActive && <div className="version-timeline__dot-pulse" />}
              </div>

              {/* Label */}
              <div className="version-timeline__label">
                <span className="version-timeline__version">v{entry.version}</span>
                {entry.eval_score !== null && entry.eval_score !== undefined && (
                  <span className="version-timeline__score">{entry.eval_score}pts</span>
                )}
                {entry.promoted_at && (
                  <span className="version-timeline__time">
                    {new Date(entry.promoted_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
