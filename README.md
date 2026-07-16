
# RJ SurfCast Transcriber

Serviço HTTP independente responsável exclusivamente pela transcrição de áudio utilizando Faster-Whisper.

---

# Por que existe este serviço?

Inicialmente a transcrição era executada diretamente pela API Django do RJ SurfCast. Isso fazia com que a API tivesse dependências de IA (Faster-Whisper, modelos, FFmpeg etc.), aumentando sua complexidade.

Com a separação:

- A API Django continua responsável apenas pelas regras de negócio.
- O Ollama continua responsável apenas pela IA conversacional.
- O Transcriber fica responsável apenas por converter áudio em texto.

Arquitetura:

```text
Flutter
   │
   ▼
API Django
   │
   ├── PostgreSQL
   ├── Ollama (IA)
   └── Transcriber (Áudio → Texto)
```

Vantagens:

- Isolamento das dependências de IA.
- Atualização do transcritor sem alterar a API.
- Reutilização do serviço por outros projetos.
- Melhor manutenção e escalabilidade.

---

# Instalação - Windows 11

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app:app --host 127.0.0.1 --port 9001 --workers 1 --env-file .env
```

Teste:

http://127.0.0.1:9001/health

---

# Instalação - Linux (Hostinger / Interserver)

```bash
cd /opt
git clone <repositorio>
mv rj_surfcast_transcriber /opt/rj_surfcast_transcriber
cd /opt/rj_surfcast_transcriber

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env

uvicorn app:app --host 127.0.0.1 --port 9001 --workers 1 --env-file .env
```

Na primeira execução o modelo Faster-Whisper será baixado automaticamente caso ainda não exista.

Instalação como serviço:

```bash
sudo cp rj-surfcast-transcriber.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rj-surfcast-transcriber
sudo systemctl start rj-surfcast-transcriber
```

Logs:

```bash
sudo journalctl -u rj-surfcast-transcriber -f
```

---

# Endpoints

GET /health

POST /v1/transcribe

Campo multipart:

audio

---

# Fluxo de funcionamento

1. Flutter envia o áudio para a API.
2. A API salva o áudio e encaminha ao Transcriber.
3. O Transcriber converte o áudio em texto.
4. A API grava a transcrição.
5. O Ollama utiliza apenas o texto transcrito.

