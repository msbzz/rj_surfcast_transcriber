import logging
import os
import tempfile
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from faster_whisper import WhisperModel

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("rj_surfcast_transcriber")
app = FastAPI(title="RJ SurfCast Transcriber", version="1.0.0")

_model = None
_model_lock = Lock()
ALLOWED_EXTENSIONS = {".m4a", ".aac", ".mp3"}


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                model_name = os.getenv("TRANSCRIBER_MODEL", "small")
                logger.info("Carregando modelo Faster-Whisper: %s", model_name)
                _model = WhisperModel(
                    model_name,
                    device=os.getenv("TRANSCRIBER_DEVICE", "cpu"),
                    compute_type=os.getenv("TRANSCRIBER_COMPUTE_TYPE", "int8"),
                    download_root=os.getenv("TRANSCRIBER_MODEL_DIR") or None,
                )
    return _model


def validate_token(authorization: str | None) -> None:
    expected = os.getenv("TRANSCRIBER_API_TOKEN", "").strip()
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Token de acesso inválido.")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "ready": True,
        "model": os.getenv("TRANSCRIBER_MODEL", "small"),
        "provider": "faster_whisper",
    }


@app.post("/v1/transcribe")
async def transcribe(audio: UploadFile = File(...), authorization: str | None = Header(default=None)):
    validate_token(authorization)
    suffix = Path(audio.filename or "audio").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Formato não permitido: {suffix}")

    max_size = int(os.getenv("TRANSCRIBER_MAX_SIZE_BYTES", str(10 * 1024 * 1024)))
    content = await audio.read()
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="Arquivo maior que o limite configurado.")

    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(content)
        segments, info = get_model().transcribe(
            temp_path,
            language=os.getenv("TRANSCRIBER_LANGUAGE", "pt"),
            beam_size=max(1, int(os.getenv("TRANSCRIBER_BEAM_SIZE", "5"))),
            vad_filter=True,
        )
        text = " ".join(str(segment.text or "").strip() for segment in segments if str(segment.text or "").strip()).strip()
        if not text:
            raise HTTPException(status_code=422, detail="A transcrição retornou texto vazio.")
        duration = getattr(info, "duration", None)
        return {
            "success": True,
            "text": text,
            "duration_seconds": float(duration) if duration is not None else None,
            "provider": "faster_whisper_http",
            "model": os.getenv("TRANSCRIBER_MODEL", "small"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Falha na transcrição de %s", audio.filename)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
