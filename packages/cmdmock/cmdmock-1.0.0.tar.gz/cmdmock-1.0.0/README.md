<img alt="cmdmock logo" width="128px" src="https://raw.githubusercontent.com/pismy/cmdmock/refs/heads/main/logo.png">

[![pypi](https://img.shields.io/pypi/v/cmdmock.svg)](https://pypi.org/project/cmdmock/)
[![python](https://img.shields.io/pypi/pyversions/cmdmock.svg)](https://pypi.org/project/cmdmock/)

# cmdmock

> a simplistic mocking framework for CLI commands

`cmdmock` is a basic CLI program that allows you to install and configure command mocks.

It may be used in conjunction with shell unit testing frameworks such as [bats](https://bats-core.readthedocs.io/) or [shUnit2](https://github.com/kward/shunit2).

It serves exactly the same purpose as other unit testing mocking frameworks but dedicated to mocking CLI programs/commands:

- intercepts CLI programs to behave the way you want,
- capture all invocations of the mocked commands,
- support basic assertions (to verify - for instance - a given command has been called exactly twice, with some expected parameters),
- simple setup (configuration can be exported/imported).

`cmdmock` manages 3 kinds of **Test Doubles** (see [Martin Fowler's terminology](https://martinfowler.com/articles/mocksArentStubs.html)):

- **Stubs** implement a **predefined behavior** (return code and stdout).
- **Spies** intercept and **record every call** to the spied command (the original command is still executed).
- **Fakes** provide an **alternate impementation** of the original command.

## Install

`cmdmock` can be installed using pip package manager:

```bash
pip install cmdmock
```

It can also be installed as a standalone script (only uses Standard Python Library):

```bash
# download
sudo curl -s https://raw.githubusercontent.com/pismy/cmdmock/refs/heads/main/cmdmock/__init__.py --output /usr/local/bin/cmdmock
# make executable
sudo chmod +x /usr/local/bin/cmdmock
```

## Usage

### General Usage

```
usage: cmdmock [-h] [--no-color] {stub,spy,fake,del,show,import,export,logs,reset} ...

This tool can be used to mock commands and check their execution details afterwards.

options:
  -h, --help            show this help message and exit
  --no-color            Disable colored output

subcommands:
  valid subcommands

  {stub,spy,fake,del,show,import,export,logs,reset}
                        Manage mocks, configuration and execution logs...

examples:
  cmdmock stub systemctl
                        Install a stub for 'systemctl ...'
  cmdmock stub -t=2 -rc=15 systemctl 'restart'
                        Install a stub for 'systemctl restart ...'
                        Exists with return code 15 and will be uninstalled after 2 invocations
  cmdmock spy curl      Install a spy for 'curl ...'
  cmdmock fake -i='./my-keygen.sh' ssh-keygen
                        Install a fake for 'ssh-keygen' and use './my-keygen.sh' implementation
  cmdmock show          Display the actual mocks configuration
  cmdmock import < mocks.json
                        Import the mocks configuration from mocks.json
  cmdmock export        Export the actual mocks configuration to stdout
  cmdmock logs          Display all execution logs (textual format)
  cmdmock logs -f=json systemctl
                        Display execution logs from 'systemctl' commands in JSON format
  cmdmock reset         Reset execution logs
  cmdmock reset --all   Reset execution logs and mocks configuration
```

`cmdmock` supports the following subcommands:

- [`stub`](#install-a-stub): Installs a stub
- [`spy`](#install-a-spy): Installs a spy
- [`fake`](#install-a-fake): Installs a fake
- [`del`](#uninstall-a-mock): Uninstalls a mocked command
- [`show`](#show-installed-mocks): Shows installed mocks
- [`export`](#export-the-mock-configuration): Exports the mocks configuration file (JSON)
- [`import`](#import-the-mocks-configuration): Imports the mocks configuration from a (JSON) file
- [`logs`](#print-the-execution-logs): Prints the execution logs
- [`reset`](#reset-the-execution-logs): Resets the execution logs

### Install a stub

```
usage: cmdmock stub [-h] [-f] [-t TIMES] [-rc RETURNCODE] [-o STDOUT] command [args]

Installs a stub for the specified command signature.

positional arguments:
  command               Command name
  args                  Arguments pattern (regular expression)

options:
  -h, --help            show this help message and exit
  -f, --force           Force registration even when another mock is installed (overwritten)
  -t TIMES, --times TIMES
                        Number of times the mock will be executed
  -rc RETURNCODE, --returncode RETURNCODE
                        Return code of the mocked command
  -o STDOUT, --stdout STDOUT
                        Standard output of the mocked command (capture group references supported)

Every call to the specified command signature will be intercepted and replaced with the stub implementation.
```

> `--stdout` supports [Python group reference substitutions](https://learnbyexample.github.io/py_regular_expressions/groupings-and-backreferences.html) captured from the arguments regular expression.
>
> Example:
>
> ```bash
> cmdmock stub --stdout 'hostname set: \1' hostnamectl 'set-hostname (.*)'
> ```
>
> will capture the value passed in argument and return it in the console output.

### Install a spy

```
usage: cmdmock spy [-h] [-f] command [args]

Installs a spy for the specified command signature.

positional arguments:
  command      Command name
  args         Arguments pattern (regular expression)

options:
  -h, --help   show this help message and exit
  -f, --force  Force registration even when another mock is installed (overwritten)

Every call to the specified command signature will be intercepted and recorded by the tool. The original command will still be called.
```

### Install a fake

```
usage: cmdmock fake [-h] [-f] -i IMPL command [args]

Installs a fake for the specified command signature.

positional arguments:
  command               Command name
  args                  Arguments pattern (regular expression)

options:
  -h, --help            show this help message and exit
  -f, --force           Force registration even when another mock is installed (overwritten)
  -i IMPL, --impl IMPL  Alternate (fake) implementation of the original command

Every call to the specified command signature will be intercepted and replaced with the provided alternate (fake) implementation.
```

### Uninstall a mock

```
usage: cmdmock del [-h] command [args]

Uninstalls the mock associated to the specified command signature.

positional arguments:
  command     Command name
  args        Arguments pattern (regular expression)

options:
  -h, --help  show this help message and exit
```

### Show installed mocks

```
usage: cmdmock show [-h]

Shows installed mocks.

options:
  -h, --help  show this help message and exit
```

### Export the mock configuration

```
usage: cmdmock export [-h] [-o OUTPUT]

Exports the mocks configuration.

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file (default: stdout)
```

### Import the mocks configuration

```
usage: cmdmock import [-h] [-i INPUT]

Imports the mocks configuration.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input file (default: stdin)
```

### Print the execution logs

```
usage: cmdmock logs [-h] [-f {text,json}] [-F] [command] [args]

Prints the execution logs.

positional arguments:
  command               Command name
  args                  Arguments pattern (regular expression)

options:
  -h, --help            show this help message and exit
  -f {text,json}, --format {text,json}
                        Output format
  -F, --fail            Fail if no log matching command and args

examples:
  cmdmock logs          Display all execution logs (textual format)
  cmdmock logs -f=json systemctl
                        Display execution logs from 'systemctl' commands in JSON format
  cmdmock logs systemctl 'show .*' | wc -l
                        Count the number of times 'systemctl show .*' was call (used with wc)
  cmdmock logs -f=json systemctl | jq -r '.args'
                        Extracts the arguments of each 'systemctl' invocation (used with jq)
```

### Reset the execution logs

```
usage: cmdmock reset [-h] [-a]

Resets the execution logs.

options:
  -h, --help  show this help message and exit
  -a, --all   Also resets mocked commands
```

## Developers

```bash
# install dependencies
poetry install

# run tool
poetry run cmdmock ...
```
