# QuantDecoder

A small neural network that decodes the distance-3 surface code. The goal is to compare it with
PyMatching, the standard matching decoder, on Google's public Sycamore experiment data.

Status: setting up. There are no results yet.

## Setup

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.12 and every dependency into a
local `.venv` folder.

```sh
git clone https://github.com/mahyar-jbr/QuantDecoder.git
cd QuantDecoder
uv sync
uv run pytest
uv run python scripts/check_env.py
```

The last command prints the tool versions and which compute devices work: `cpu` always, `mps` on
Apple silicon, `cuda` on an NVIDIA GPU.

## Data

The experiments use Google Quantum AI's public surface code data:

> Google Quantum AI Team. Data for "Suppressing quantum errors by scaling a surface code logical
> qubit". Zenodo, 2022. https://doi.org/10.5281/zenodo.6804040. License: CC BY 4.0.

Download it with:

```sh
uv run python scripts/download_data.py
```

This fetches the 315 MB zip into `data/`, checks its size and md5 checksum, and unpacks it. A
second run does nothing. The data is never committed to this repository.

## License

MIT. See [LICENSE](LICENSE).
