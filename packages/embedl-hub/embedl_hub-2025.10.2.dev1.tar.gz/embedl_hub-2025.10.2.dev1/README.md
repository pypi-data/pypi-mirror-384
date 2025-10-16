# Embedl Hub Python library

Optimize and deploy your model on any edge device with the Embedl Hub Python library:

- **Quantize** your model for lower latency and memory usage.
- **Compile** your model for execution on CPU, GPU, NPU or other AI accelerators on your target devices.
- **Benchmark** your model's latency and memory usage on real edge devices in the cloud.

The library logs your metrics, parameters, and benchmarks on the [Embedl Hub](https://hub.embedl.com)
website, allowing you to inspect, compare, and reproduce your results.

[Create a free Embedl Hub account](https://hub.embedl.com/docs/setup)
to get started with the `embedl-hub` library.

## Installation

The simplest way to install `embedl-hub` is through `pip`:

```shell
pip install embedl-hub
```

## Quickstart

We recommend using our end-to-end workflow CLI to quickly get started building your edge AI application:

```shell
 Usage: embedl-hub [OPTIONS] COMMAND [ARGS]...

 embedl-hub end-to-end Edge-AI workflow CLI


╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version             -V               Print embedl-hub version and exit.                                                                                           │
│ --verbose             -v      INTEGER  Increase verbosity (-v, -vv, -vvv).                                                                                          │
│ --install-completion                   Install completion for the current shell.                                                                                    │
│ --show-completion                      Show completion for the current shell, to copy it or customize the installation.                                             │
│ --help                                 Show this message and exit.                                                                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ auth           Store the API key for embedl-hub CLI.                                                                                                                │
│ init           Configure persistent CLI context.                                                                                                                    │
│ show           Print active project/experiment IDs and names.                                                                                                       │
│ compile        Compile a model into a device ready binary using Qualcomm AI Hub.                                                                                    │
│                Qualcomm AI Hub may return a zip file containing multiple files.                                                                                     │
│ quantize       Quantize an ONNX model using Qualcomm AI Hub.                                                                                                        │
│                Qualcomm AI Hub may return a zip file containing multiple files.                                                                                     │
│ benchmark      Benchmark compiled model on device and measure it's performance.                                                                                     │
│ list-devices   List all available target devices.                                                                                                                   │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## License

Copyright (C) 2025 Embedl AB

This software is subject to the [Embedl Hub Software License Agreement](https://hub.embedl.com/embedl-hub-sla.txt).

<!-- Copyright (C) 2025 Embedl AB -->
