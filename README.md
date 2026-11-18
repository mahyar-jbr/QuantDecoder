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
```

## Data

The experiments use Google Quantum AI's public surface code data, Zenodo record
[6804040](https://zenodo.org/records/6804040), licensed CC BY 4.0. The data is never committed to
this repository.

## License

MIT. See [LICENSE](LICENSE).
