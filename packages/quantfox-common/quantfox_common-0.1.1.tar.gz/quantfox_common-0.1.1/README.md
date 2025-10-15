# qf-common

Common utilities pour QuantFox.

## Setup Instructions

### Prerequisites

- - Python 3.x
  - pipx (for Poetry installation)

### Installation Steps

- 1. Install dependencies using Poetry:
     `bash
 poetry install
`
- 2. Verify Poetry installation:
     `bash
 pipx run poetry --version
`
- 3. Activate Poetry environment:
     `bash
     poetry shell

## Install

Privé via GitHub Packages:

```toml
[tool.poetry.dependencies]
qf-common = { version = "^0.1.0", source = "github" }

[[tool.poetry.source]]
name = "github"
url = "https://maven.pkg.github.com/QuantFox/qf-common"
default = false

```
