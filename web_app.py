import pyaudio
import wave
import io
from google.cloud import speech
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import uvicorn

app = FastAPI()

# Serve static files (HTML, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/record_audio")
async def record_audio(duration: int = 8, sample_rate: int = 44100):
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=1024)

        frames = []
        for i in range(0, int(sample_rate / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        audio_data = b''.join(frames)
        return Response(content=audio_data, media_type="audio/wav")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio recording failed: {str(e)}")

@app.post("/transcribe_audio")
async def transcribe_audio(audio: UploadFile = File(...), sample_rate_hertz: int = Form(44100)):
    try:
        # Initialize Google Cloud Speech-to-Text client
        client = speech.SpeechClient()

        # Read the uploaded audio file
        audio_content = await audio.read()

        # Set up the audio and config for transcription
        recognition_audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate_hertz,
            language_code="en-US",
        )

        # Perform transcription
        response = client.recognize(config=config, audio=recognition_audio)
        transcription = ""
        for result in response.results:
            transcription += result.alternatives[0].transcript

        return {"transcription": transcription}

    except Exception as e:
        # Log error and return an error response
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
