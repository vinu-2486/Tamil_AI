import { useEffect, useState } from "react";
import { ReactMediaRecorder } from "react-media-recorder";
import {
  analyzePronunciation,
  type FeedbackLanguage,
} from "../services/api";
import ScoreCard from "./ScoreCard";
import FeedbackCard from "./FeedbackCard";

type AnalysisResult = {
  score?: number | string;
  feedback?: string;
  improvements?: string[];
  coach_audio_text?: string;
  correction_audio_text?: string;
  coach_audio_url?: string | null;
  correction_audio_url?: string | null;
};

type PlaybackStatus = {
  message: string;
  tone: "info" | "warning" | "error";
};

function normalizeVoiceLang(value: string) {
  return value.toLowerCase().replace("_", "-");
}

function findVoice(
  voices: SpeechSynthesisVoice[],
  language: string
): SpeechSynthesisVoice | undefined {
  const requested = normalizeVoiceLang(language);
  const baseLanguage = requested.split("-")[0];

  return (
    voices.find((voice) => normalizeVoiceLang(voice.lang) === requested) ||
    voices.find((voice) =>
      normalizeVoiceLang(voice.lang).startsWith(`${baseLanguage}-`)
    ) ||
    voices.find((voice) => normalizeVoiceLang(voice.lang) === baseLanguage) ||
    voices.find((voice) =>
      voice.name.toLowerCase().includes(baseLanguage === "ta" ? "tamil" : "english")
    )
  );
}

function splitSpeechText(text: string): string[] {
  const sentences = text
    .replace(/([.!?।])\s+/g, "$1|")
    .split("|")
    .map((item) => item.trim())
    .filter(Boolean);

  if (sentences.length > 0) {
    return sentences;
  }

  return text
    .match(/.{1,180}(\s|$)/g)
    ?.map((item) => item.trim())
    .filter(Boolean) || [text];
}

function repeatPracticeSentence(text: string): string {
  const sentence = text.trim();
  return sentence;
}

const BACKEND_ORIGIN = "http://127.0.0.1:8000";

function resolveAudioUrl(url: string): string {
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }

  return `${BACKEND_ORIGIN}${url.startsWith("/") ? url : `/${url}`}`;
}

function playBackendAudio(
  url: string,
  onStatus: (status: PlaybackStatus) => void,
  playbackRate = 1
) {
  if (!url.trim()) {
    onStatus({
      message: "Tamil audio is still being generated. Please try again.",
      tone: "warning",
    });
    return;
  }

  const audio = new Audio(resolveAudioUrl(url));
  audio.playbackRate = playbackRate;
  onStatus({ message: "Playing audio...", tone: "info" });
  audio.onended = () => {
    onStatus({ message: "Audio playback finished.", tone: "info" });
  };
  audio.onerror = () => {
    onStatus({
      message: "Unable to play generated Tamil audio. Please try recording again.",
      tone: "error",
    });
  };
  audio.play().catch(() => {
    onStatus({
      message: "Audio playback was blocked. Click the button again.",
      tone: "warning",
    });
  });
}

function speakText(
  text: string,
  language: string,
  voices: SpeechSynthesisVoice[],
  onStatus: (status: PlaybackStatus) => void
) {
  if (!("speechSynthesis" in window)) {
    onStatus({
      message: "Speech playback is not supported in this browser.",
      tone: "error",
    });
    return;
  }

  const trimmedText = text.trim();
  if (!trimmedText) {
    onStatus({ message: "No audio text is available yet.", tone: "warning" });
    return;
  }

  const matchingVoice = findVoice(voices, language);
  if (!matchingVoice && language === "ta-IN") {
    onStatus({
      message:
        "Tamil voice is not installed in this browser. Trying browser fallback voice.",
      tone: "warning",
    });
  } else {
    onStatus({ message: "Playing audio...", tone: "info" });
  }

  window.speechSynthesis.cancel();

  const chunks = splitSpeechText(trimmedText);
  chunks.forEach((chunk, index) => {
    const utterance = new SpeechSynthesisUtterance(chunk);
    utterance.lang = language;
    utterance.rate = language === "ta-IN" ? 0.82 : 0.95;
    utterance.pitch = 1;

    if (matchingVoice) {
      utterance.voice = matchingVoice;
    }

    utterance.onerror = () => {
      onStatus({
        message:
          language === "ta-IN"
            ? "Tamil playback failed. Install or enable a Tamil voice in your browser/OS."
            : "Audio playback failed. Please try again.",
        tone: "error",
      });
    };

    utterance.onend = () => {
      if (index === chunks.length - 1) {
        onStatus({ message: "Audio playback finished.", tone: "info" });
      }
    };

    window.speechSynthesis.speak(utterance);
  });

  window.speechSynthesis.resume();
}

const KOLAM_DOTS = [
  [80, 10], [115, 20], [140, 45], [150, 80], [140, 115], [115, 140],
  [80, 150], [45, 140], [20, 115], [10, 80], [20, 45], [45, 20],
];

function KolamDots() {
  return (
    <>
      {KOLAM_DOTS.map(([cx, cy], i) => (
        <circle key={i} className="dot" cx={cx} cy={cy} r="4" />
      ))}
    </>
  );
}

export default function Recorder() {
  const [feedbackLanguage, setFeedbackLanguage] =
    useState<FeedbackLanguage>("english");
  const [score, setScore] = useState<number | null>(null);
  const [feedback, setFeedback] = useState("");
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(false);
  const [improvements, setImprovements] = useState<string[]>([]);
  const [coachAudioText, setCoachAudioText] = useState("");
  const [correctionAudioText, setCorrectionAudioText] = useState("");
  const [coachAudioUrl, setCoachAudioUrl] = useState("");
  const [correctionAudioUrl, setCorrectionAudioUrl] = useState("");
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [playbackStatus, setPlaybackStatus] = useState<PlaybackStatus | null>(
    null
  );

  useEffect(() => {
    if (!("speechSynthesis" in window)) {
      return;
    }

    const loadVoices = () => {
      setVoices(window.speechSynthesis.getVoices());
    };

    loadVoices();
    window.speechSynthesis.addEventListener("voiceschanged", loadVoices);

    const fallbackTimer = window.setTimeout(loadVoices, 500);

    return () => {
      window.clearTimeout(fallbackTimer);
      window.speechSynthesis.removeEventListener("voiceschanged", loadVoices);
      window.speechSynthesis.cancel();
    };
  }, []);

  const sendAudio = async (blobUrl: string) => {
    try {
      setLoading(true);
      setScore(null);
      setFeedback("");
      setTranscript("");
      setImprovements([]);
      setCoachAudioText("");
      setCorrectionAudioText("");
      setCoachAudioUrl("");
      setCorrectionAudioUrl("");
      setPlaybackStatus(null);

      const blob = await fetch(blobUrl).then((r) => r.blob());

      const result = await analyzePronunciation(blob, feedbackLanguage);

      console.log("FULL RESULT:", result);

      const transcriptText = result.transcript || "";
      setTranscript(transcriptText);

      let analysis: AnalysisResult | null = result.analysis;

      if (typeof analysis === "string") {
        try {
          analysis = JSON.parse(analysis);
        } catch (e) {
          console.error("JSON Parse Error:", e);
          analysis = null;
          return;
        }
      }

      if (analysis) {
        const nextFeedback = analysis.feedback || "";
        const nextImprovements = analysis.improvements || [];
        const fallbackCoachText = [nextFeedback, ...nextImprovements]
          .join(" ")
          .trim();

        setScore(Number(analysis.score));
        setFeedback(nextFeedback);
        setImprovements(nextImprovements);
        setCoachAudioText(analysis.coach_audio_text || fallbackCoachText);
        setCorrectionAudioText(
          analysis.correction_audio_text || repeatPracticeSentence(transcriptText)
        );
        setCoachAudioUrl(analysis.coach_audio_url || "");
        setCorrectionAudioUrl(analysis.correction_audio_url || "");
      }
    } catch (err) {
      console.error(err);
      alert("Failed to analyze audio");
    } finally {
      setLoading(false);
    }
  };

  const coachVoiceLanguage =
    feedbackLanguage === "tamil" ? "ta-IN" : "en-US";

  const handlePlayCoach = () => {
    if (feedbackLanguage === "tamil") {
      playBackendAudio(coachAudioUrl, setPlaybackStatus, 1.08);
      return;
    }

    speakText(coachAudioText, coachVoiceLanguage, voices, setPlaybackStatus);
  };

  const handlePlayCorrection = () => {
    playBackendAudio(correctionAudioUrl, setPlaybackStatus);
  };

  const coachDisabled =
    feedbackLanguage === "tamil"
      ? !coachAudioUrl && !coachAudioText
      : !coachAudioText;

  const correctionDisabled = !correctionAudioUrl && !correctionAudioText;

  return (
    <div className="page">
      <div className="kolam-divider">
        {Array.from({ length: 7 }).map((_, i) => (
          <span key={i}></span>
        ))}
      </div>

      <header>
        <h1>கற்பது தமிழ், கற்பிப்பது AI</h1>
        <p className="subtitle">Tamil pronunciation coach</p>
      </header>

      <div className="lang-toggle">
        <label htmlFor="feedback-language" style={{ display: "none" }}>
          Feedback language
        </label>
        <select
          id="feedback-language"
          value={feedbackLanguage}
          onChange={(event) =>
            setFeedbackLanguage(event.target.value as FeedbackLanguage)
          }
        >
          <option value="english">Feedback language: English</option>
          <option value="tamil">Feedback language: தமிழ்</option>
        </select>
      </div>

      <ReactMediaRecorder
        audio
        onStop={(blobUrl) => {
          sendAudio(blobUrl);
        }}
        render={({ startRecording, stopRecording, mediaBlobUrl, status }) => (
          <div className="card record-card">
            <div className={`status-row ${status === "recording" ? "active" : ""}`}>
              <span className="status-dot"></span> Status: {status}
            </div>

            <div className={`kolam-ring ${status === "recording" ? "recording" : ""}`}>
              <svg viewBox="0 0 160 160">
                <KolamDots />
              </svg>
              <button
                className="mic-btn"
                aria-label="Start recording"
                onClick={() => {
                  window.speechSynthesis.cancel();
                  setPlaybackStatus(null);
                  startRecording();
                }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                  <line x1="12" y1="19" x2="12" y2="23"></line>
                </svg>
              </button>
            </div>

            <div className="rec-controls">
              <button className="btn primary" onClick={startRecording}>
                Start recording
              </button>
              <button className="btn outline" onClick={stopRecording}>
                Stop recording
              </button>
            </div>

            {mediaBlobUrl && (
              <audio className="audio-player" src={mediaBlobUrl} controls />
            )}
          </div>
        )}
      />

      {loading && <p className="loading-text">Analyzing...</p>}

      {transcript && (
        <div className="card">
          <p className="label">Transcript</p>
          <p className="transcript-text">{transcript}</p>
        </div>
      )}

      {(score !== null || feedback || improvements.length > 0) && (
        <div className="grid-2">
          <ScoreCard score={score} />
          <FeedbackCard
            feedback={feedback}
            improvements={improvements}
            onPlayCoach={handlePlayCoach}
            onPlayCorrection={handlePlayCorrection}
            coachDisabled={coachDisabled}
            correctionDisabled={correctionDisabled}
            playbackStatus={playbackStatus}
          />
        </div>
      )}

      <div className="kolam-divider" style={{ marginTop: 32 }}>
        {Array.from({ length: 7 }).map((_, i) => (
          <span key={i}></span>
        ))}
      </div>
    </div>
  );
}