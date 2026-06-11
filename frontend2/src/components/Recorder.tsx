import { useState } from "react";
import { ReactMediaRecorder } from "react-media-recorder";
import { analyzePronunciation } from "../services/api";

export default function Recorder() {
  const [score, setScore] = useState<number | null>(null);
  const [feedback, setFeedback] = useState("");
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(false);
  const [improvements, setImprovements] = useState<string[]>([]);

  const sendAudio = async (blobUrl: string) => {
    try {
      setLoading(true);

      const blob = await fetch(blobUrl).then((r) => r.blob());

      const result = await analyzePronunciation(blob);

      console.log("FULL RESULT:", result);

      setTranscript(result.transcript || "");

      let analysis = result.analysis;

      // Handle stringified JSON
      if (typeof analysis === "string") {
        try {
          analysis = JSON.parse(analysis);
        } catch (e) {
          console.error("JSON Parse Error:", e);
          return;
        }
      }

      if (analysis) {
        setScore(Number(analysis.score));
        setFeedback(analysis.feedback || "");
        setImprovements(analysis.improvements || []);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to analyze audio");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>கற்பது தமிழ் கற்பிப்பது AI</h1>

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

            <button onClick={startRecording}>
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
    </div>
  );
}