# Chunked Spleeter

This script provides a memory-friendly way to run Spleeter on large audio files. It processes the audio in chunks, separates the vocals and accompaniment, and then concatenates the results.

It also includes a feature to automatically activate a specified Python virtual environment before running, ensuring all dependencies are correctly managed.

## Features

- **Memory-Efficient:** Processes large audio files in smaller, manageable chunks to avoid memory issues.
- **Virtual Environment Integration:** Can automatically re-execute itself within a specified Python virtual environment.
- **Stem Separation:** Separates audio files into vocals and accompaniment using the Spleeter library.
- **Lossless Concatenation:** Uses FFmpeg to losslessly concatenate the separated audio chunks.

## Prerequisites

- **Python 3.7+**
- **FFmpeg:** You must have FFmpeg installed on your system and available in your PATH.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/chunked-spleeter.git
    cd chunked-spleeter
    ```

2.  Create and activate a Python virtual environment (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The script is run from the command line, with the input audio file as the main argument.

### Basic Usage

```bash
python chunked_spleeter.py path/to/your/audio.wav
```

This will process the audio file with the default settings (10-minute chunks) and save the output to an `output` directory.

### Advanced Usage

- **Specify Chunk Size:** Use the `-c` or `--chunk` option to set the chunk size in seconds.
  ```bash
  python chunked_spleeter.py audio.wav -c 300  # 5-minute chunks
  ```

- **Specify Output Directory:** Use the `-o` or `--output-dir` option to set a custom output directory.
  ```bash
  python chunked_spleeter.py audio.wav -o /path/to/output
  ```

- **Use a Virtual Environment:** Use the `-V` or `--venv` option to specify the path to a Python virtual environment. The script will automatically re-launch itself within this environment.
  ```bash
  python chunked_spleeter.py audio.wav -V /path/to/your/venv
  ```

- **Keep Temporary Files:** Use the `--keep-temp` flag to prevent the script from deleting the temporary chunk directories.
  ```bash
  python chunked_spleeter.py audio.wav --keep-temp
  ```

## Pre-trained Models

This project uses Spleeter's pre-trained models. The default model is `spleeter:2stems`, which separates audio into vocals and accompaniment. You can specify other models using the `--model` argument.

The necessary model files should be placed in the `pretrained_models` directory. This repository includes the `2stems` model.

## Dependencies

The Python dependencies are listed in the `requirements.txt` file. The core dependencies are:

- `spleeter`
- `numpy`
- `pandas`
- `tensorflow`
- `ffmpeg-python`

## Credits

This project is a wrapper around the original Spleeter library by Deezer. All credit for the core separation technology goes to them.

- **Spleeter on GitHub:** [https://github.com/deezer/spleeter](https://github.com/deezer/spleeter)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
