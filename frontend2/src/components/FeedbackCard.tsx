type PlaybackStatus = {
  message: string;
  tone: "info" | "warning" | "error";
};

type FeedbackCardProps = {
  feedback: string;
  improvements: string[];
  onPlayCoach: () => void;
  onPlayCorrection: () => void;
  coachDisabled: boolean;
  correctionDisabled: boolean;
  playbackStatus: PlaybackStatus | null;
};

export default function FeedbackCard({
  feedback,
  improvements,
  onPlayCoach,
  onPlayCorrection,
  coachDisabled,
  correctionDisabled,
  playbackStatus,
}: FeedbackCardProps) {
  return (
    <div className="card">
      {feedback && (
        <>
          <p className="label">Feedback</p>
          <p className="feedback-text">{feedback}</p>
        </>
      )}

      {improvements.length > 0 && (
        <>
          <p className="label" style={{ marginTop: feedback ? 18 : 0 }}>
            Improvements
          </p>
          <ul className="improvements">
            {improvements.map((item, index) => (
              <li key={index}>
                <span className="pulli"></span>
                {item}
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="action-row">
        <button className="btn" disabled={coachDisabled} onClick={onPlayCoach}>
          Play coach feedback
        </button>
        <button className="btn" disabled={correctionDisabled} onClick={onPlayCorrection}>
          Play correct pronunciation
        </button>
      </div>

      {playbackStatus && (
        <p className={`playback-status tone-${playbackStatus.tone}`}>
          {playbackStatus.message}
        </p>
      )}
    </div>
  );
}