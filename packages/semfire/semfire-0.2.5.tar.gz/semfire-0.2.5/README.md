# SemFire 

[![CI](https://github.com/josephedward/SemFire/actions/workflows/ci.yml/badge.svg)](https://github.com/josephedward/SemFire/actions/workflows/ci.yml)

 ## AI Deception Detection Toolkit

**SemFire (Semantic Firewall) is an open-source toolkit for detecting advanced AI deception, with a primary focus on "in-context scheming" and multi-turn manipulative attacks.** This project aims to develop tools to identify and mitigate vulnerabilities like the "Echo Chamber" and "Crescendo" attacks, where AI models are subtly guided towards undesirable behavior through conversational context.

### Project Vision: A Toolkit for AI Deception Detection

*see* [/docs/context.md](./docs/context.md)

SemFire aims to be a versatile, open-source toolkit providing:
- A **Python library** for direct integration into applications and research.
- A **Command Line Interface (CLI)** for quick analysis and scripting.
- A **REST API service** (via FastAPI) for broader accessibility and enterprise use cases.
- Core components that can be integrated into broader semantic-firewall-like systems to monitor and analyze AI interactions in real-time.

## Features

 - Rule-based detector (`EchoChamberDetector`) for identifying cues related to "in-context scheming," context poisoning, semantic steering, and other multi-turn manipulative attack patterns (e.g., "Echo Chamber", "Crescendo").
 - Analyzes both current text input and conversation history to detect evolving deceptive narratives.
 - Heuristic-based detector (`HeuristicDetector`) for signals like text complexity and keyword usage.
 - ML-based classifiers to enhance detection of complex scheming behaviors over extended dialogues (Future Work).
 
 *API Instructions forthcoming.* 
 - ~~Python API for programmatic access.~~
 - ~~REST service (FastAPI) for network-based access.~~
 

## Installation
The project can be installed from PyPI:
```bash
pip install semfire
```

- **LLM Providers for ai-as-judge features :** [/docs/providers.md](./docs/providers.md)
- **Quickstart :**[/docs/quickstart.md](./docs/quickstart.md)
- **Usage :** [/docs/usage.md](./docs/usage.md)

# Demo

*see* [Examples](./docs/examples.md)

**Quick Start**  
[![Quick Start](https://asciinema.org/a/vyMQ9gpnEgyBEDF5q8ifmZ1Mz.svg)](https://asciinema.org/a/vyMQ9gpnEgyBEDF5q8ifmZ1Mz)

**Individual Detectors**  
[![Individual Detectors](https://asciinema.org/a/pNPjV3rJJ4kH1L3A4R6Pytm1O.svg)](https://asciinema.org/a/pNPjV3rJJ4kH1L3A4R6Pytm1O)

**Python API**  
[![Python API](https://asciinema.org/a/RhrolgA23FxQbcjLtB6RhE9Ww.svg)](https://asciinema.org/a/RhrolgA23FxQbcjLtB6RhE9Ww)

**Complete Workflow**  
[![Complete Workflow](https://asciinema.org/a/lJPq57UMvBQ5RX2UWS2B6dl19.svg)](https://asciinema.org/a/lJPq57UMvBQ5RX2UWS2B6dl19)

<!-- **Library — Basic Usage**  
[![Library — Basic Usage](https://asciinema.org/a/Mtk3RcSxwF66REU6ymdPKlFrd.svg)](https://asciinema.org/a/Mtk3RcSxwF66REU6ymdPKlFrd)

**Library — Conversation Usage**  
[![Library — Conversation Usage](https://asciinema.org/a/BiQD6IxghsAQuRn684uRbiNdK.svg)](https://asciinema.org/a/BiQD6IxghsAQuRn684uRbiNdK)

**Transformers — Env Config**  
[![Transformers — Env Config](https://asciinema.org/a/aPTMLqFhpiOQraWxcR2DtkrUM.svg)](https://asciinema.org/a/aPTMLqFhpiOQraWxcR2DtkrUM)

**Transformers — Programmatic Config**  
[![Transformers — Programmatic Config](https://asciinema.org/a/8uGbIpHrnU4cKuJm8hSPyYepf.svg)](https://asciinema.org/a/8uGbIpHrnU4cKuJm8hSPyYepf)

 -->


## Contributing
Contributions are welcome! Please open an issue or submit a pull request.Library — Basic Usage
