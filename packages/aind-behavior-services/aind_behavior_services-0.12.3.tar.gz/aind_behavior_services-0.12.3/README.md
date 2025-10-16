# aind-behavior-services

![CI](https://github.com/AllenNeuralDynamics/Aind.Behavior.Services/actions/workflows/aind-behavior-services-cicd.yml/badge.svg)
[![PyPI - Version](https://img.shields.io/pypi/v/aind-behavior-services)](https://pypi.org/project/aind-behavior-services/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

A library for defining and maintaining behavior tasks.

---

## Installation

The python package can be installed from pypi using the following command:

```bash
pip install aind-behavior-services
```

However, to use all the tasks and hardware that this package supports, you should over over the [prerequisites](#prerequisites) and [deployment](#deployment) sections.

## Prerequisites

These should only need to be installed once on a fresh new system, and are not required if simply refreshing the install or deploying to a new folder.

- Windows 10 or 11
- Run `./scripts/install_dependencies.ps1` to automatically install dependencies
- The following dependencies should be manually installed:
  - [Spinnaker SDK 1.29.0.5](https://www.flir.co.uk/support/products/spinnaker-sdk/#Downloads) (device drivers for FLIR cameras)

    - On FLIR website: `Download > archive > 1.29.0.5 > SpinnakerSDK_FULL_1.29.0.5_x64.exe`

---

## Deployment

Install the [prerequisites](#prerequisites) mentioned below.
From the root of the repository, run `./scripts/deploy.ps1` to bootstrap both python and bonsai environments.

---

## Generating valid JSON input files

One of the core principles of this repository is the strict adherence to [json-schemas](https://json-schema.org/). We use [Pydantic](https://pydantic.dev/) as a way to write and compile our schemas, but also to generate valid JSON input files. These files can be used by Bonsai (powered by [Bonsai.SGen](https://github.com/bonsai-rx/sgen) code generation tool) or to simply record metadata. Examples of how to interact with the library can be found in the `./examples` folder.

---

## Regenerating schemas

Once a Pydantic model is updated, updates to all downstream dependencies must be made to ensure that the ground-truth data schemas (and all dependent interoperability tools) are also updated. This can be achieved by running `uv run ./src/_generators/<__init__.py>` from the root of the repository.
This script will regenerate all `json-schemas` along with `C#` code (`./scr/Extensions`) used by the Bonsai environment.

---

## Contributors

Contributions to this repository are welcome! However, please ensure that your code adheres to the recommended DevOps practices below:

### Linting

We use [ruff](https://docs.astral.sh/ruff/) as our primary linting tool.

### Testing

Attempt to add tests when new features are added.
To run the currently available tests, run `python -m unittest` from the root of the repository.

### Lock files

We use [uv](https://docs.astral.sh/uv/) to manage our lock files.

### Versioning

Where possible, adhere to [Semantic Versioning](https://semver.org/).

---

## Project dependency tree


```mermaid
classDiagram
    class aind_behavior_curriculum {
        +Task
        +Curriculum
    }

    class aind_behavior_services {
        +Task (Subclasses)
        +Rig (maintains hardware library)
        +Session
        +Calibration (maintains device/calibration library)
        +Deployment instructions
        +Ecosystem documentation
    }

    class clabe {
        +Launch experiment
        +Interfaces with external applications (e.g. Bonsai)
        +Interfaces with aind-services
    }

    class aind_behavior_some_task {
        +Concrete implementation of a task
        +Rig (Subclasses for some task)
        +Session
        +Task Logic (Subclasses for some task)
        +Maintains a task data-schema
        +Saves data in standard format
    }

    class aind_behavior_some_task_analysis {
        +Analysis code for some task
    }

    class contraqctor {
        +Data ingestion
        +Data contract definition
        +Core analysis primitives
        +QC
    }

    aind_behavior_curriculum --|> aind_behavior_services : Subclasses Task
    aind_behavior_services --|> aind_behavior_some_task 
    aind_behavior_some_task --|> aind_behavior_some_task_analysis : Analysis
    contraqctor --|> aind_behavior_some_task_analysis : Imports core analysis methods
    aind_behavior_some_task_analysis --|> aind_behavior_curriculum : Metrics[Task]
    
    clabe --|> aind_behavior_some_task : Launches

```

