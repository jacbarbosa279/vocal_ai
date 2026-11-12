# Vocal AI

Vocal AI downloads an audio track from YouTube and separates the vocal and instrumental stems using Demucs. It is designed for local experimentation, audio cleanup, remix preparation, and voice-isolation workflows without requiring a cloud service.

## What this project does

The project provides a Python script, `separar_vozes.py`, that:

- accepts a YouTube URL
- validates that the URL points to a supported YouTube host
- checks whether the required Python packages are installed
- downloads the best available audio stream with `yt-dlp`
- runs Demucs separation with a two-stem configuration (`vocals` + accompaniment)
- saves the generated outputs to a local folder

The resulting output is useful for:

- isolating vocals from a track
- preparing instrumental versions
- creating stems for editing or remix work
- experimenting with source separation locally

## Architecture

The script follows a straightforward pipeline:

1. CLI input
   - receives a YouTube URL from the command line or interactive prompt
   - optional output directory override via `--saida`
   - optional device selection via `--dispositivo`

2. URL validation
   - checks whether the provided URL uses a supported YouTube hostname
   - rejects non-YouTube URLs

3. Dependency validation
   - ensures `yt_dlp`, `demucs`, and `imageio_ffmpeg` are installed
   - if missing, the script exits with a clear installation instruction

4. FFmpeg detection
   - uses `ffmpeg` from the environment when available
   - otherwise falls back to the `imageio_ffmpeg` binary path

5. Download
   - downloads the best audio-only stream into a temporary folder using `yt_dlp`

6. Separation
   - invokes Demucs with:
     - `--two-stems=vocals`
     - target output directory
     - optional device selection (`cpu` or `cuda`)

7. Output persistence
   - writes the separated files under the configured output folder

## Project structure

```text
vocal_ai/
├── README.md
├── requirements.txt
├── separar_vozes.py
├── separacoes/
│   └── ... generated output files ...
└── .venv/                 # optional local virtual environment
```

## Installation

The project expects a Python environment with the dependencies listed in `requirements.txt`.

### 1) Create and activate a virtual environment

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The required packages are:

- `yt-dlp`
- `demucs==4.0.1`
- `imageio-ffmpeg`

## Usage

Run the script with a YouTube URL:

```powershell
.venv\Scripts\python.exe separar_vozes.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

You can also provide the URL interactively if you omit it:

```powershell
.venv\Scripts\python.exe separar_vozes.py
```

### Command-line options

```powershell
.venv\Scripts\python.exe separar_vozes.py --help
```

Available options:

- positional `url`: YouTube video URL
- `--saida PATH`: output folder for generated stems (default: `./separacoes`)
- `--dispositivo {cpu,cuda}`: processing device to pass to Demucs

Example:

```powershell
.venv\Scripts\python.exe separar_vozes.py "https://youtu.be/VIDEO_ID" --saida .\separacoes\musica --dispositivo cpu
```

## Output structure

The script saves generated stems to the directory configured by `--saida` (default: `./separacoes`).

Typical structure:

```text
separacoes/
├── <video_id>/
│   ├── vocals.wav
│   ├── accompaniment.wav
│   ├── no_vocals.wav
│   └── ...
└── ...
```

Depending on the underlying Demucs output format and version, the exact filenames may vary, but the main separation results are usually organized by a generated output folder corresponding to the downloaded media.

Important notes:

- the script creates the destination directory automatically
- intermediate media is stored in a temporary folder during processing
- output files remain in the configured output directory after the separation completes

## Troubleshooting

### Missing dependencies

If you see output like:

```text
Dependências ausentes: yt_dlp, demucs, imageio_ffmpeg
```

run:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### FFmpeg not found

Common error:

```text
FFmpeg não encontrado
```

Make sure FFmpeg is installed and available in the PATH, or ensure `imageio-ffmpeg` is installed. The script will try both methods automatically.

### Invalid YouTube URL

The script validates supported YouTube hosts such as:

- `youtube.com`
- `www.youtube.com`
- `youtu.be`
- `m.youtube.com`
- `music.youtube.com`

If the URL is malformed or points to a non-YouTube site, it exits with a validation error.

### Demucs fails during processing

If Demucs exits with a non-zero status, check:

- the video URL is valid
- the audio file was downloaded successfully
- the system has enough disk space and memory
- the selected device (`cpu` or `cuda`) is compatible with your machine

The script prints the Demucs exit code when the process fails.

### Output folder issues

If the script cannot create or write to the target folder:

- check whether the path already exists and is writable
- ensure you have write access to the parent directory
- avoid protected folders such as system directories unless you intentionally choose them

## Notes and limitations

- This project is intended for local use and requires a working Python environment.
- Source separation is computationally intensive, especially for longer media and higher-quality models.
- GPU support depends on the machine's CUDA compatibility and the installed Demucs/PyTorch environment.
- The tool is for media processing only and should be used in compliance with the rights and permissions of the source material.

## License and usage policy

This project does not enforce licensing or legal compliance checks. You are responsible for ensuring that the sources you download and process are authorized for your intended use.
