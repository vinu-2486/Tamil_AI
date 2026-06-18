export type FeedbackLanguage = "english" | "tamil";

export async function analyzePronunciation(
  audioBlob: Blob,
  feedbackLanguage: FeedbackLanguage
) {
  const formData = new FormData();

  formData.append(
    "audio",
    audioBlob,
    "recording.wav"
  );
  formData.append("feedback_language", feedbackLanguage);

  const response = await fetch(
    "http://127.0.0.1:8000/pronunciation/analyze",
    {
      method: "POST",
      body: formData,
    }
  );

  return response.json();
}
