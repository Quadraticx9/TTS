# Bark Small TTS API

A FastAPI server for running the Suno Bark small model. 

It exposes a simple REST API to convert text to speech in multiple languages.

## API Endpoints
- `GET /health` : Returns readiness status (model is lazy-loaded on the first request).
- `POST /generate` : Generates text-to-speech audio.

### Example Request
```json
{
  "text": "Hello, world",
  "voice_preset": "v2/en_speaker_6"
}
```

## How to make an API call from Make.com (Integromat)

You can easily trigger this API from a Make.com scenario using the standard **HTTP module**.

1. Add the **HTTP / Make a request** module in Make.com.
2. Configure it with the following settings:
   - **URL**: `https://<YOUR_DEPLOYED_APP_URL>/generate`
   - **Method**: `POST`
   - **Headers**:
     - `Content-Type` : `application/json`
   - **Body type**: `Raw`
   - **Content type**: `JSON (application/json)`
   - **Request content**:
     ```json
     {
       "text": "The text you want spoken",
       "voice_preset": "v2/en_speaker_6"
     }
     ```
   - **Parse response**: `Yes`
3. Since the response is a raw binary `.wav` file, Make.com will receive it as buffer data.
4. You can then map the `Data` buffer from the HTTP module to any other module that accepts files (like "Google Drive - Upload a File", "Email - Send an Email with Attachment", etc.). Map the file name as `response.wav`.
