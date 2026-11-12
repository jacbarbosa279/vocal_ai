"""Executa o Demucs usando soundfile no lugar do TorchCodec.

Substitui torchaudio.load e torchaudio.save por versões baseadas em
soundfile, evitando a dependência do TorchCodec (e das DLLs do FFmpeg).
Uso: python demucs_runner.py [argumentos do demucs]
"""

import sys

import soundfile as sf
import torch
import torchaudio


def _load(uri, *args, **kwargs):
    data, sample_rate = sf.read(str(uri), dtype="float32", always_2d=True)
    return torch.from_numpy(data.T.copy()), sample_rate


def _save(uri, src, sample_rate, **kwargs):
    encoding = kwargs.get("encoding")
    bits = kwargs.get("bits_per_sample")
    if encoding == "PCM_F" or bits == 32 and encoding == "PCM_F":
        subtype = "FLOAT"
    elif bits == 32:
        subtype = "PCM_32"
    elif bits == 24:
        subtype = "PCM_24"
    else:
        subtype = "PCM_16"
    data = src.detach().cpu().numpy().T
    sf.write(str(uri), data, sample_rate, subtype=subtype)


torchaudio.load = _load
torchaudio.save = _save

from demucs.separate import main  # noqa: E402

if __name__ == "__main__":
    main(sys.argv[1:])