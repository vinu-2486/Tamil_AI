export async function analyzePronunciation(audioBlob: Blob) {
  const formData = new FormData();

  formData.append(
    "audio",
    audioBlob,
    "recording.wav"
  );

  const response = await fetch(
    "http://127.0.0.1:8000/pronunciation/analyze",
    {
      method: "POST",
      body: formData,
    }
  );

  return response.json();
}