<!-- SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>

SPDX-License-Identifier: Apache-2.0 -->

[![PyPI version](https://badge.fury.io/py/amirispy.svg)](https://badge.fury.io/py/amirispy)
[![PyPI license](https://img.shields.io/pypi/l/amirispy.svg)](https://badge.fury.io/py/amirispy)
[![pipeline status](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/badges/main/pipeline.svg)](https://gitlab.com/dlr-ve/esy/amiris/amiris-py/commits/main)

# AMIRIS-Py

Python tools for the electricity market model [AMIRIS](https://dlr-ve.gitlab.io/esy/amiris/home/).

## Installation

    pip install amirispy

You may also use `pipx`. For detailed information please refer to the
official `pipx` [documentation](https://github.com/pypa/pipx).

    pipx install amirispy

### Further Requirements

In order to execute all commands provided by `amirispy`, you also require a Java Development Kit (JDK).
JDK must be installed and accessible via your console in which you run `amirispy`.

To test, run `java --version` which should show your JDK version (required: 11 or above).
If `java` command is not found or relates to a Java Runtime Environment (JRE), please download and install JDK (e.g. from [Adoptium](https://adoptium.net/de/temurin/releases/?version=17))

## Usage

Currently, there are three distinct commands available:

- `amiris download`: download the latest versions of [AMIRIS](https://gitlab.com/dlr-ve/esy/amiris/amiris) and [examples](https://gitlab.com/dlr-ve/esy/amiris/examples) files
- `amiris run`: perform a full workflow by compiling the `.pb` file from your `scenario.yaml`, executing AMIRIS, and extracting the results
- `amiris batch`: perform multiple runs, each with scenario compilation, AMIRIS execution, and results extraction
- `amiris comparison`: compare the results of two different AMIRIS runs to check their equivalence

You may also use the arguments as a list of strings in your script directly, e.g.

```python
from amirispy.scripts import amiris_cli

amiris_cli(["download", "-m", "model"])
```

### `amiris download`

Downloads and extracts the latest open access AMIRIS instance and accompanying examples.

| Option             | Provides                                                                                                                                                     |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `-u` or `--url`    | URL to download AMIRIS from (default: latest AMIRIS artifact from [https://gitlab.com/dlr-ve/esy/amiris/amiris](https://gitlab.com/dlr-ve/esy/amiris/amiris) |
| `-t` or `--target` | Folder to download `amiris-core_<version>-jar-with-dependencies.jar` to (default: `./`)                                                                      |
| `-f` or `--force`  | Force download which may overwrites existing AMIRIS installation of same version and existing examples (default: False)                                      |
| `-m` or `--mode`   | Option to download model and examples `all` (default), only `model`, or only `examples`                                                                      |

### `amiris run`

Compile scenario, execute AMIRIS, and extract results.

| Option                      | Provides                                                                                                                                                          |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `-s` or `--scenario`        | Path to a scenario yaml-file                                                                                                                                      |
| `-j` or `--jar`             | Path to `amiris-core_<version>-jar-with-dependencies.jar`, defaults to a single "amiris*.jar"-file in current working directory                                   |
| `-o` or `--output`          | Directory to write output to, defaults to "./result"                                                                                                              |
| `-oo` or `--output-options` | Optional arguments to override default output [conversion arguments of fameio](https://gitlab.com/fame-framework/fame-io/-/blob/main/README.md#read-fame-results) |
| `-nc` or `--no-checks`      | Skip checks for Java installation and correct version to increase speed                                                                                           |

#### Bug in argparse

:warning: If you provide but a single flag to `--output-option`, you may get a crash as there is a [bug](https://bugs.python.org/issue9334) in the `argparse` library which will not be fixed.
We recommend these workarounds:

* provide additional parameters, e.g. for the log level: change `-oo "-m"` to `-oo "-m -l critical"`, or
* add a space after the single flag: change `-oo "-m"` to `-oo "-m "`

#### Calling AMIRIS from your own script using `amiris_cli`

If you happen to run AMIRIS in your own script by importing `amiris_cli`, this is an example of how to use it.

```python
from amirispy.scripts import amiris_cli

commands = [
    "-l", "critical",
    "run",
    "-j", "amiris-core_3.4.0-jar-with-dependencies.jar",
    "-s", "examples/Germany2019/scenario.yaml",
    "-oo", "-m ",
]

amiris_cli(commands)
```

:warning: Similar to the command-line call you need to work around the argparse bug when using `--output-option` with a single flag only.
Thus, the extra space in statement `"-oo", "-m "` is intended - see explanation above.

### `amiris batch`

Perform multiple runs - each with scenario compilation, AMIRIS execution, and results extraction

| Option                      | Provides                                                                                                                                                          |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `-s` or `--scenarios`       | Path to single or list of: scenario yaml-files or their enclosing directories                                                                                     |
| `-j` or `--jar`             | Path to `amiris-core_<version>-jar-with-dependencies.jar`, defaults to a single "amiris*.jar"-file in current working directory                                   |
| `-o` or `--output`          | Directory to write output to "./result"                                                                                                                           |
| `-r` or `--recursive`       | Option to recursively search in provided Path for scenario (default: False)                                                                                       |
| `-p` or `--pattern`         | Optional name pattern that scenario files searched for must match                                                                                                 |
| `-oo` or `--output-options` | Optional arguments to override default output [conversion arguments of fameio](https://gitlab.com/fame-framework/fame-io/-/blob/main/README.md#read-fame-results) |
| `-nc` or `--no-checks`      | Skip checks for Java installation and correct version to increase speed                                                                                           |

See description of `amiris run` for details on the issues with the  `-oo` option.

### `amiris compare`

Compare if results of two AMIRIS runs and equivalent.

| Option               | Provides                                                           |
|----------------------|--------------------------------------------------------------------|
| `-e` or `--expected` | Path to folder with expected result .csv files                     |
| `-t` or `--test`     | Path to folder with results files (.csv) to test  for equivalence  |
| `-i` or `--ignore`   | Optional list of file names not to be compared                     |

### Help

You reach the help menu at any point using `-h` or `--help` which gives you a list of all available options, e.g.:

`amiris --help`

### Logging

You may define a logging level or optional log file as **first** arguments in your workflow using any of the following
arguments:

| Option               | Provides                                                                                                 |
|----------------------|----------------------------------------------------------------------------------------------------------|
| `-l` or `--log`      | logging level, defaults to `error`; options are `debug`, `info`, `warning`, `warn`, `error`, `critical`. |
| `-lf` or `--logfile` | path to log file, defaults to `None`; if `None` is provided, all logs get only printed to the console.   |

Example: `amiris --log debug --logfile my/log/file.txt download`

## Cite AMIRIS-Py

If you use AMIRIS-Py for academic work, please cite:

Christoph Schimeczek, Kristina Nienhaus, Ulrich Frey, Evelyn Sperber, Seyedfarzad Sarfarazi, Felix Nitsch, Johannes Kochems & A. Achraf El Ghazi (2023).
AMIRIS: Agent-based Market model for the Investigation of Renewable and Integrated energy Systems.
Journal of Open Source Software. doi: [10.21105/joss.05041](https://doi.org/10.21105/joss.05041)

## Contributing

Please see [CONTRIBUTING](CONTRIBUTING.md).

## Available Support

This is a purely scientific project by (at the moment) one research group.
Thus, there is no paid technical support available.

If you experience any trouble with AMIRIS, you may contact the developers at the [openMod-Forum](https://forum.openmod.org/tag/amiris) or via [amiris@dlr.de](mailto:amiris@dlr.de).
Please report bugs and make feature requests by filing issues following the provided templates (see also [CONTRIBUTING](CONTRIBUTING.md)).
For substantial enhancements, we recommend that you contact us via [amiris@dlr.de](mailto:amiris@dlr.de) for working together on the code in common projects or towards common publications and thus further develop AMIRIS.

## Acknowledgement

Work on AMIRIS-Py was financed by the Helmholtz Association's Energy System Design research programme.
