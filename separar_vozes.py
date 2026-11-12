"""Baixa áudio do YouTube e separa voz e instrumental com Demucs.

Instale as dependências com
``.venv\\Scripts\\python.exe -m pip install -r requirements.txt``.
Exemplo: ``.venv\\Scripts\\python.exe separar_vozes.py``

Observação: use torch/torchaudio 2.8.x (veja requirements.txt) para que o
Demucs consiga ler o áudio sem depender do TorchCodec.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


YOUTUBE_HOSTS = {
    "youtu.be",
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Separa voz e instrumental de um vídeo do YouTube."
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Link do vídeo do YouTube (se omitido, será solicitado)",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("separacoes"),
        help="Pasta para salvar as faixas (padrão: ./separacoes)",
    )
    parser.add_argument(
        "--dispositivo",
        choices=("cpu", "cuda"),
        help="Dispositivo de processamento (por padrão, escolha do Demucs)",
    )
    return parser.parse_args()


def validate_youtube_url(url: str) -> None:
    clean_url = url.strip()
    if not clean_url:
        raise ValueError("Informe um link válido de vídeo do YouTube.")

    if "://" not in clean_url:
        clean_url = f"https://{clean_url}"

    parsed_url = urlsplit(clean_url)
    hostname = (parsed_url.hostname or "").lower()
    if (
        parsed_url.scheme not in {"http", "https"}
        or not hostname
        or hostname not in YOUTUBE_HOSTS
    ):
        raise ValueError("Informe um link válido de vídeo do YouTube.")


def convert_to_wav(ffmpeg_path: str, source: Path, target_dir: Path) -> Path:
    """Converte o áudio baixado para WAV estéreo de 44,1 kHz."""
    wav_path = target_dir / f"{source.stem}.wav"
    result = subprocess.run(
        [
            ffmpeg_path,
            "-y",
            "-i",
            str(source),
            "-ar",
            "44100",
            "-ac",
            "2",
            str(wav_path),
        ],
        capture_output=True,
        text=True,
        errors="replace",
    )
    if result.returncode != 0:
        details = (result.stderr or "").strip().splitlines()[-5:]
        raise RuntimeError(
            "Falha ao converter o áudio para WAV com o FFmpeg: "
            + " | ".join(details)
        )
    if not wav_path.is_file():
        raise FileNotFoundError(
            f"O arquivo WAV convertido não foi encontrado: {wav_path}"
        )
    return wav_path


def main() -> int:
    args = parse_args()
    try:
        url = args.url or input(
            "Cole o link do YouTube aqui e pressione Enter: "
        ).strip()
    except EOFError:
        print("Nenhum link foi informado.", file=sys.stderr)
        return 2
    if not url:
        print("Nenhum link foi informado.", file=sys.stderr)
        return 2

    try:
        validate_youtube_url(url)
    except ValueError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2

    missing_packages = [
        package
        for package in ("yt_dlp", "demucs", "imageio_ffmpeg")
        if importlib.util.find_spec(package) is None
    ]
    if missing_packages:
        print(
            "Dependências ausentes: "
            f"{', '.join(missing_packages)}. Instale com: "
            ".venv\\Scripts\\python.exe -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    import imageio_ffmpeg
    import yt_dlp

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        try:
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        except RuntimeError as error:
            print(f"FFmpeg não encontrado: {error}", file=sys.stderr)
            return 1
    if not Path(ffmpeg_path).is_file():
        print(
            f"Executável do FFmpeg não encontrado: {ffmpeg_path}",
            file=sys.stderr,
        )
        return 1

    args.saida.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory(prefix="separar_vozes_") as temp_dir:
            download_dir = Path(temp_dir)
            download_options = {
                "format": "bestaudio/best",
                "noplaylist": True,
                "outtmpl": str(download_dir / "%(id)s.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(download_options) as downloader:
                info = downloader.extract_info(url, download=True)
                audio_path = Path(downloader.prepare_filename(info))

            if not audio_path.is_file():
                raise FileNotFoundError(
                    f"O arquivo de áudio baixado não foi encontrado: {audio_path}"
                )

            # Converte para WAV para evitar problemas de decodificação
            # de formatos como .webm/.m4a no Demucs.
            audio_path = convert_to_wav(ffmpeg_path, audio_path, download_dir)

            command = [
                sys.executable,
                "-m",
                "demucs_runner",
                "--two-stems=vocals",
                "--mp3",
                "--out",
                str(args.saida.resolve()),
            ]
            if args.dispositivo:
                command.extend(("--device", args.dispositivo))
            command.append(str(audio_path))
            environment = os.environ.copy()
            ffmpeg_dir = str(Path(ffmpeg_path).parent)
            environment["PATH"] = ffmpeg_dir + os.pathsep + environment.get(
                "PATH", ""
            )
            subprocess.run(command, check=True, env=environment)
    except yt_dlp.utils.DownloadError as error:
        print(f"Falha ao baixar o vídeo: {error}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(
            f"Demucs falhou com código de saída {error.returncode}.",
            file=sys.stderr,
        )
        return 1
    except (FileNotFoundError, RuntimeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    print(f"Separação concluída. Confira as faixas na pasta: {args.saida.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())