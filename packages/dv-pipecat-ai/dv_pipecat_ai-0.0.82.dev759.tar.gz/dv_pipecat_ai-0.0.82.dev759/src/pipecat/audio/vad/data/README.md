This directory contains packaged VAD model files used by Pipecat.

- `silero_vad.onnx`: Default Silero VAD model shipped with the package.
- `silero_vad_v2.onnx`: Alternate model used when Arabic (codes starting with `ar`) is present
  in the call configuration (primary `language` or any `add_langs`). This file is optional.

If `silero_vad_v2.onnx` is not present or fails to load, Pipecat will automatically fall back
to `silero_vad.onnx` and log a warning. To enable the Arabic-optimized model, place a valid
ONNX file at this path with the exact filename.

