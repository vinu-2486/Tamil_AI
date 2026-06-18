import { useEffect, useState } from "react";
import { ReactMediaRecorder } from "react-media-recorder";
import {
  analyzePronunciation,
  type FeedbackLanguage,
} from "../services/api";

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
  return sentence ? [sentence, sentence, sentence].join(". ") : "";
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
  onStatus: (status: PlaybackStatus) => void
) {
  if (!url.trim()) {
    onStatus({
      message: "Tamil audio is still being generated. Please try again.",
      tone: "warning",
    });
    return;
  }

  const audio = new Audio(resolveAudioUrl(url));
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

  return (
    <div style={{ padding: "20px" }}>
      <h1>Tamil Pronunciation Coach AI</h1>

      <div style={{ marginBottom: "20px" }}>
        <label htmlFor="feedback-language">Feedback language</label>
        <select
          id="feedback-language"
          value={feedbackLanguage}
          onChange={(event) =>
            setFeedbackLanguage(event.target.value as FeedbackLanguage)
          }
          style={{ marginLeft: "10px", padding: "8px" }}
        >
          <option value="english">English</option>
          <option value="tamil">Tamil</option>
        </select>
      </div>

      <ReactMediaRecorder
        audio
        onStop={(blobUrl) => {
          sendAudio(blobUrl);
        }}
        render={({
          startRecording,
          stopRecording,
          mediaBlobUrl,
          status,
        }) => (
          <div>
            <p>Status: {status}</p>

            <button
              onClick={() => {
                window.speechSynthesis.cancel();
                setPlaybackStatus(null);
                startRecording();
              }}
            >
              Start Recording
            </button>

            <button onClick={stopRecording}>
              Stop Recording
            </button>

            {mediaBlobUrl && (
              <div style={{ marginTop: "10px" }}>
                <audio src={mediaBlobUrl} controls />
              </div>
            )}
          </div>
        )}
      />

      {loading && <h3>Analyzing...</h3>}

      {transcript && (
        <div style={{ marginTop: "20px" }}>
          <h3>Transcript</h3>
          <p>{transcript}</p>
        </div>
      )}

      {score !== null && (
        <div style={{ marginTop: "20px" }}>
          <h3>Pronunciation Score</h3>
          <p>{score}/100</p>
        </div>
      )}

      {feedback && (
        <div style={{ marginTop: "20px" }}>
          <h3>Feedback</h3>
          <p>{feedback}</p>
        </div>
      )}

      {improvements.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <h3>Improvements</h3>

          <ul
            style={{
              textAlign: "left",
              maxWidth: "800px",
              margin: "0 auto",
              lineHeight: "1.8",
            }}
          >
            {improvements.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {(coachAudioText || correctionAudioText) && (
        <div style={{ marginTop: "20px" }}>
          <button
            disabled={
              feedbackLanguage === "tamil"
                ? !coachAudioUrl && !coachAudioText
                : !coachAudioText
            }
            onClick={() => {
              if (feedbackLanguage === "tamil") {
                playBackendAudio(coachAudioUrl, setPlaybackStatus);
                return;
              }

              speakText(
                coachAudioText,
                coachVoiceLanguage,
                voices,
                setPlaybackStatus
              );
            }}
          >
            Play Coach Feedback
          </button>

          <button
            disabled={!correctionAudioUrl && !correctionAudioText}
            onClick={() =>
              playBackendAudio(correctionAudioUrl, setPlaybackStatus)
            }
            style={{ marginLeft: "10px" }}
          >
            Play Correct Pronunciation
          </button>

          {playbackStatus && (
            <p
              style={{
                marginTop: "10px",
                color:
                  playbackStatus.tone === "error"
                    ? "#b91c1c"
                    : playbackStatus.tone === "warning"
                      ? "#a16207"
                      : "inherit",
              }}
            >
              {playbackStatus.message}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
