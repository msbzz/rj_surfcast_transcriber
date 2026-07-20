
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

## 📡 Configuração do Arquivo `.env`

Crie um arquivo `.env` na raiz do projeto contendo as seguintes definições:

```env
# Modelo do Faster-Whisper a ser utilizado (ex: tiny, base, small, medium, large-v3)
TRANSCRIBER_MODEL=small

# Idioma padrão para transcrição (ex: pt, en)
TRANSCRIBER_LANGUAGE=pt

# Dispositivo de hardware para execução (cpu ou cuda)
TRANSCRIBER_DEVICE=cpu

# Tipo de computação de precisão (ex: int8, float16)
TRANSCRIBER_COMPUTE_TYPE=int8

# Parâmetro beam_size para o decodificador Whisper
TRANSCRIBER_BEAM_SIZE=5

# Diretório local para salvar/carregar os modelos do Faster-Whisper
TRANSCRIBER_MODEL_DIR=./models

# Limite máximo do tamanho do arquivo de áudio em bytes (padrão: 10MB)
TRANSCRIBER_MAX_SIZE_BYTES=10485760

# Token Bearer de segurança exigido no header Authorization para chamadas à API (opcional)
TRANSCRIBER_API_TOKEN=

# Nível do logger da aplicação (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

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
# Copia o arquivo de configuração do serviço systemd
sudo cp rj-surfcast-transcriber.service /etc/systemd/system/

# Garante permissões de escrita/leitura para o usuário www-data (responsável pela execução do serviço)
# Evita o erro 'Permission denied (os error 13)' ao baixar modelos e criar arquivos temporários
sudo chown -R www-data:www-data /opt/rj_surfcast_transcriber

# Habilita e inicializa o serviço
sudo systemctl daemon-reload
sudo systemctl enable rj-surfcast-transcriber
sudo systemctl start rj-surfcast-transcriber
```

> [!IMPORTANT]
> **Permissões de Diretório e Cache do Hugging Face:**
> Como o serviço é executado sob o usuário `www-data`, a pasta apontada na variável `TRANSCRIBER_MODEL_DIR` no arquivo `.env` (ex: `./models`) deve possuir permissão total de escrita para este usuário. Executar o `chown` acima resolve o problema de `Permission denied (os error 13)` que pode ocorrer na inicialização e carregamento de modelos do Hugging Face.

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

