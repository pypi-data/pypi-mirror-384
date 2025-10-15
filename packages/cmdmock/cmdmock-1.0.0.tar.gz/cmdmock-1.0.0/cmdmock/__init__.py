#!/usr/bin/env python3

import argparse
import dataclasses
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Type, TypeVar

HOME_DIR = Path(os.getenv("HOME"))
MOCKS_BASE_DIR = Path(os.getenv("CMDMOCK_BASE_DIR", HOME_DIR / ".cmdmock"))
MOCKS_DEF_FILE = MOCKS_BASE_DIR / "mocks.json"
MOCKS_BIN_DIR = MOCKS_BASE_DIR / "bin"
MOCKS_EXEC_FILE = MOCKS_BASE_DIR / "exec.json"

JSON_INDENT = None
DFLT_ARG = "/dflt/"

COLORED_OUTPUT = os.getenv("COLORED_OUTPUT", "").lower() not in ["false", "no", "0"]


class Color:
    """Output Colouring helper class.

    See: https://notes.burke.libbey.me/ansi-escape-codes/"""

    _ESC_CALL = "\033["
    """Function call escape sequence"""
    _ESC_SGR = "m"
    """Select Graphics Rendition function"""
    BOLD = 1
    """Style: bold"""
    UNDERLINE = 2
    """Style: underline"""
    ITALIC = 4
    """Style: italic"""
    BACKGROUND = 8
    """Style: background color"""
    BRIGHT = 16
    """Style: bright color"""

    # constructor with one argument
    def __init__(self, color: str):
        self.color = color

    # colorize function
    def __call__(
        self,
        txt: str,
        style: int = 0,
    ):
        if COLORED_OUTPUT:
            if style & Color.BACKGROUND:
                tens = "10" if style & Color.BRIGHT else "4"
            else:
                tens = "9" if style & Color.BRIGHT else "3"
            return (
                Color._ESC_CALL
                + ("1;" if style & Color.BOLD else "")
                + ("3;" if style & Color.ITALIC else "")
                + ("4;" if style & Color.UNDERLINE else "")
                + tens
                + self.color
                + Color._ESC_SGR
                + str(txt)
                + Color._ESC_CALL
                + "0"
                + Color._ESC_SGR
            )
        return txt


BLACK = Color("0")
RED = Color("1")
GREEN = Color("2")
YELLOW = Color("3")
BLUE = Color("4")
PURPLE = Color("5")
CYAN = Color("6")
WHITE = Color("7")

T = TypeVar("T")  # Needed for type inference


@dataclass
class BaseJson:
    def to_json(self, include_null=False) -> dict:
        """Converts this to json.

        Args:
            include_null (bool, optional): Whether null values are included. Defaults to False.

        Returns:
            dict: Json dictionary
        """
        return dataclasses.asdict(
            self,
            dict_factory=lambda fields: {
                key: value
                for (key, value) in fields
                if value is not None or include_null
            },
        )

    @classmethod
    def from_json(cls: Type[T], json: dict) -> T:
        """Constructs `this` from given json.

        Args:
            json (dict): Json dictionary

        Raises:
            ValueError: When `this` isn't a dataclass

        Returns:
            T: New instance
        """
        if not dataclasses.is_dataclass(cls):
            raise ValueError(f"{cls.__name__} must be a dataclass")
        field_names = {field.name for field in dataclasses.fields(cls)}
        kwargs = {key: value for key, value in json.items() if key in field_names}
        return cls(**kwargs)


# create Python enum of 'stub', 'spy' and 'fake'
class MockKind(str, Enum):
    """3 kinds of mock objects."""

    stub = "stub"
    spy = "spy"
    fake = "fake"


class MockChange(str, Enum):
    update = "update"
    delete = "delete"


@dataclass
class Mock(BaseJson):
    kind: MockKind
    # field for stub
    returncode: int = None
    stdout: str = None
    times: int = None
    # field for fake
    impl: str = None

    def exec(self, command: str, args: str, arg_match: re.Match[str]) -> dict[str, Any]:
        if self.kind == MockKind.stub:
            ret = {"returncode": self.returncode or 0}
            if self.times:
                self.times -= 1
                ret["change"] = (
                    MockChange.delete if self.times == 0 else MockChange.update
                )
            if self.stdout:
                # print specified stdout (support capture group replacement from args)
                print(arg_match.expand(self.stdout))
            return ret

        if self.kind == MockKind.spy:
            # execute command, redirect stdout and stderr and retrieve return returncode
            cmd_path = _resolve_cmd(command)
            if not cmd_path:
                print(f"{RED('✗ command not found')}: {command}", file=sys.stderr)
                return {"returncode": 127}
            # print(f"{GREEN('✓')} command found: {str(cmd_path)}", file=sys.stderr)
            callargs = sys.argv.copy()
            callargs[0] = str(cmd_path)
            return {"returncode": subprocess.run(callargs).returncode}

        if self.kind == MockKind.fake:
            # execute impl, redirect stdout and stderr and retrieve return returncode
            os.putenv("CMDMOCK_CMD", command)
            callargs = sys.argv.copy()
            callargs[0] = self.impl
            return {"returncode": subprocess.run(callargs).returncode}

    def pretty(self, args: str):
        if self.kind == MockKind.stub:
            return f"{BLUE(args) if args else CYAN(DFLT_ARG)} ❯ {PURPLE('stub')} {RED('rc=' + str(self.returncode)) if self.returncode else GREEN('rc=0')}{', stdout' if self.stdout else ''}{', ' + YELLOW('⏲ ' + str(self.times)) if self.times else ''}"
        if self.kind == MockKind.spy:
            return f"{BLUE(args) if args else CYAN(DFLT_ARG)} ❯ {PURPLE('spy')}"
        if self.kind == MockKind.fake:
            return f"{BLUE(args) if args else CYAN(DFLT_ARG)} ❯ {PURPLE('fake')} {BLACK('impl=' + self.impl, Color.BRIGHT)}"


def cli_reset(args):
    # delete execution logs
    if MOCKS_EXEC_FILE.exists():
        MOCKS_EXEC_FILE.unlink()
    print(f"{GREEN('✓')} execution logs reset", file=sys.stderr)

    if args.all:
        # delete mocks definition file if exists
        if MOCKS_DEF_FILE.exists():
            MOCKS_DEF_FILE.unlink()
        # delete mocks bin dir if exists
        if MOCKS_BIN_DIR.exists():
            shutil.rmtree(MOCKS_BIN_DIR, ignore_errors=True)
        print(f"{GREEN('✓')} mocked commands reset", file=sys.stderr)


def cli_import(args):
    # create mocks base dir if not exists
    MOCKS_BASE_DIR.mkdir(parents=True, exist_ok=True)
    # copy file to mocks base dir
    with args.input as src:
        mocks_json = src.read()
        try:
            mocks_def = json.loads(mocks_json)
            if not isinstance(mocks_def, dict):
                raise ValueError("root must be a key-value object")
            for cmd in mocks_def.keys():
                if not isinstance(mocks_def[cmd], dict):
                    raise ValueError(f"'{cmd}' must be a key-value object")
                for mock_args in mocks_def[cmd].keys():
                    if not isinstance(mocks_def[cmd][mock_args], dict):
                        raise ValueError(
                            f"'{cmd}.{mock_args}' must be a key-value object"
                        )
                    try:
                        Mock.from_json(mocks_def[cmd][mock_args])
                    except (AttributeError, TypeError) as e:
                        raise ValueError(
                            f"'{cmd}.{mock_args}' is an invalid mock ({e})"
                        )

        except (json.JSONDecodeError, ValueError) as e:
            print(f"{RED('✗ invalid json')}: {e}", file=sys.stderr)
            exit(1)
            return

    # finally save input JSON
    with open(MOCKS_DEF_FILE, "w") as dst:
        dst.write(mocks_json)

    # delete mocks bin dir if exists
    if MOCKS_BIN_DIR.exists():
        shutil.rmtree(MOCKS_BIN_DIR, ignore_errors=True)

    # install all proxy commands
    for cmd in mocks_def.keys():
        _install_proxy(cmd)

    print(f"{GREEN('✓')} mocks configuration imported", file=sys.stderr)


def cli_export(args):
    if MOCKS_DEF_FILE.exists():
        # copy file to mocks base dir
        with open(MOCKS_DEF_FILE, "r") as src, args.output as dst:
            while True:
                buff = src.read(512)
                if not buff:
                    break
                dst.write(buff)
            dst.write("\n")

    print(f"{GREEN('✓')} mocks configuration exported", file=sys.stderr)


def cli_show(args):
    if MOCKS_DEF_FILE.exists():
        with open(MOCKS_DEF_FILE, "r") as reader:
            mocks_def = json.load(reader)

        for cmd in mocks_def.keys():
            print(BLUE(cmd, Color.BOLD | Color.UNDERLINE))
            cmd_mocks: dict[str, dict[str, Any]] = mocks_def[cmd]
            for mock_args in cmd_mocks.keys():
                if mock_args == DFLT_ARG:
                    continue
                mock = Mock.from_json(cmd_mocks[mock_args])
                print(f"  {mock.pretty(mock_args)}")
            if DFLT_ARG in cmd_mocks:
                mock = Mock.from_json(cmd_mocks[DFLT_ARG])
                print(f"  {mock.pretty(None)}")
            print()


def cli_logs(args):
    # open execution logs file and print it
    if not MOCKS_EXEC_FILE.exists():
        return
    logs_count = 0
    with open(MOCKS_EXEC_FILE, "r") as reader:
        for line in reader:
            if args.command:
                log = json.loads(line)
                if log["cmd"] != args.command:
                    continue
                if args.args and not re.match(args.args, log["args"]):
                    continue
            if args.format == "text":
                log = json.loads(line)
                mock = log.get("mock")
                print(
                    f"{BLACK(log['time'], Color.BRIGHT)} {PURPLE(mock.get('kind') if mock else 'none')} {YELLOW(log['returncode'])} {BLUE(log['cmd'], Color.BOLD | Color.UNDERLINE)} {BLUE(log['args'])}",
                )
            elif args.format == "json":
                print(line, end="")
            logs_count += 1
    if args.fail and logs_count == 0:
        exit(1)


def _resolve_cmd(cmd) -> Path:
    # check wheter cmd is already a path
    cmd_path = Path(cmd)
    if cmd_path.is_file() and os.access(cmd_path, os.X_OK):
        return cmd_path.resolve()
    # else look into $PATH
    path = os.getenv("PATH")
    for path_dir in path.split(os.pathsep):
        if Path(path_dir) == MOCKS_BIN_DIR:
            # skip cmdmock proxies dir
            continue
        cmd_path: Path = Path(path_dir) / cmd
        # if path exists, is a file and is executable: return
        if cmd_path.is_file() and os.access(cmd_path, os.X_OK):
            return cmd_path.resolve()
    # command not found
    return None


def _add_log(time, cmd, args, returncode, mock):
    # append execution to file
    with open(MOCKS_EXEC_FILE, "a") as writer:
        writer.write(
            json.dumps(
                {
                    "time": time.isoformat().split(".")[0] + "Z",
                    "cmd": cmd,
                    "args": args,
                    "returncode": returncode,
                    "mock": mock,
                }
            )
        )
        writer.write("\n")


def _install_proxy(cmd):
    # install proxy if not done yet
    if not MOCKS_BIN_DIR.exists():
        MOCKS_BIN_DIR.mkdir(parents=True, exist_ok=True)
        print(
            f"{YELLOW('⚠')}  don't forget to prepend cmdmock bin dir to your PATH:",
            file=sys.stderr,
        )
        print(f"  export PATH={MOCKS_BIN_DIR}:$PATH", file=sys.stderr)

    proxy_cmd = MOCKS_BIN_DIR / cmd
    if not proxy_cmd.exists():
        proxy_cmd.symlink_to(sys.argv[0])
        print(
            f"{GREEN('✓')} proxy command {BLUE(cmd, Color.BOLD | Color.UNDERLINE)} installed",
            file=sys.stderr,
        )


def _uninstall_proxy(cmd):
    proxy_cmd = MOCKS_BIN_DIR / cmd
    if proxy_cmd.exists():
        proxy_cmd.unlink()
        print(
            f"{GREEN('✓')} proxy command {BLUE(cmd, Color.BOLD | Color.UNDERLINE)} uninstalled",
            file=sys.stderr,
        )


def _add_mock(command: str, args: str, mock: Mock, force: bool = False):
    # maybe create base dir
    MOCKS_BASE_DIR.mkdir(parents=True, exist_ok=True)

    _install_proxy(command)

    # read mocks definition file if exists
    mocks_def = {}
    if MOCKS_DEF_FILE.exists():
        with open(MOCKS_DEF_FILE, "r") as reader:
            mocks_def = json.load(reader)

    mocks_for_cmd: dict[str, dict[str, Any]] = mocks_def.get(command)
    if mocks_for_cmd is None:
        mocks_for_cmd = {}
        mocks_def[command] = mocks_for_cmd

    # look for existing entry (args)
    existing_mock = mocks_for_cmd.get(args or DFLT_ARG)
    if existing_mock and not force:
        print(
            f"{RED('✗ mock already installed')}: {Mock.from_json(existing_mock).pretty(args)}",
            file=sys.stderr,
        )
        print(
            RED("  use --force to overwrite"),
            file=sys.stderr,
        )
        exit(1)

    # add new mock
    mocks_for_cmd[args or DFLT_ARG] = mock.to_json()

    # write mocks definition file
    with open(MOCKS_DEF_FILE, "w") as writer:
        json.dump(mocks_def, indent=JSON_INDENT, fp=writer)

    if existing_mock:
        print(
            f"{GREEN('✓')} mock updated: {BLUE(command, Color.BOLD | Color.UNDERLINE)} {mock.pretty(args)}",
            file=sys.stderr,
        )
    else:
        print(
            f"{GREEN('✓')} mock added: {BLUE(command, Color.BOLD | Color.UNDERLINE)} {mock.pretty(args)}",
            file=sys.stderr,
        )


def _delete_mock(command: str, args: str):
    # read mocks definition file if exists
    mocks_def = {}
    if MOCKS_DEF_FILE.exists():
        with open(MOCKS_DEF_FILE, "r") as reader:
            mocks_def = json.load(reader)

    # look for existing entry (args)
    mocks_for_cmd: dict[str, dict[str, Any]] = mocks_def.get(command, {})
    existing_mock = mocks_for_cmd.get(args or DFLT_ARG)
    if not existing_mock:
        print(
            f"{YELLOW('✗ no mock installed')}: {BLUE(command, Color.BOLD | Color.UNDERLINE)} {BLUE(args)}",
            file=sys.stderr,
        )
        exit(0)

    # delete mock entry
    del mocks_for_cmd[args or DFLT_ARG]
    # maybe delete command entry if no more mocks
    if len(mocks_for_cmd) == 0:
        del mocks_def[command]
        _uninstall_proxy(command)

    # write mocks definition file
    with open(MOCKS_DEF_FILE, "w") as writer:
        json.dump(mocks_def, indent=JSON_INDENT, fp=writer)

    print(
        f"{GREEN('✓')} mock deleted: {BLUE(command, Color.BOLD | Color.UNDERLINE)} {Mock.from_json(existing_mock).pretty(args)}",
        file=sys.stderr,
    )


def cli_add_stub(args):
    _add_mock(
        args.command,
        args.args,
        Mock(kind=MockKind.stub, returncode=args.returncode, stdout=args.stdout),
        args.force,
    )


def cli_add_spy(args):
    cmd_path = _resolve_cmd(args.command)
    if not cmd_path:
        print(
            f"{RED('✗ command not found')}: {BLUE(args.command, Color.BOLD | Color.UNDERLINE)}",
            file=sys.stderr,
        )
        exit(1)
    print(f"command found: {cmd_path}")
    _add_mock(args.command, args.args, Mock(kind=MockKind.spy), args.force)


def cli_add_fake(args):
    impl_path = _resolve_cmd(args.impl)
    if not impl_path:
        print(
            f"{RED('✗ command not found')}: {BLUE(args.impl, Color.BOLD | Color.UNDERLINE)}",
            file=sys.stderr,
        )
        exit(1)
    _add_mock(
        args.command,
        args.args,
        Mock(kind=MockKind.fake, impl=str(impl_path)),
        args.force,
    )


def cli_delete_mock(args):
    _delete_mock(args.command, args.args)


def _esc_arg_char(char):
    """Escape a character from a command argument."""
    if char == "\t":
        return "\\t"
    elif char == "\n":
        return "\\n"
    elif char == "\r":
        return "\\r"
    elif char in ["\\", '"', "'", " ", "<", ">", "|", "&", ";", "$"]:
        # word delimiter: needs to be escaped
        return "\\" + char
    else:
        return char


def _esc_arg(arg: str) -> str:
    """Escape a command argument."""
    return "".join(map(_esc_arg_char, arg))


def proxy_call():
    cmd = sys.argv[0].split(os.sep)[-1]
    args = " ".join(map(_esc_arg, sys.argv[1:]))
    time = datetime.datetime.now(tz=datetime.timezone.utc)
    print(
        f"{GREEN('▶')} proxy call: {BLUE(cmd, Color.BOLD | Color.UNDERLINE)} {BLUE(args)}",
        file=sys.stderr,
    )

    if MOCKS_DEF_FILE.exists():
        # load mockd def and look for matching mock
        with open(MOCKS_DEF_FILE, "r") as reader:
            mocks_def = json.load(reader)

        # look for mocks definition for the command
        cmd_mocks: dict[str, dict[str, Any]] = mocks_def.get(cmd)
        mock, args_pattern, match = None, None, None
        if cmd_mocks:
            # select default mock if defined as a fallback
            if cmd_mocks.get(DFLT_ARG):
                args_pattern = None
                mock = Mock.from_json(cmd_mocks[DFLT_ARG])
                match = re.match(".*", args)
            # look for a mock that matches the args pattern
            for mock_args in cmd_mocks.keys():
                if mock_args == DFLT_ARG:
                    continue
                match = re.match(mock_args, args)
                if match:
                    mock = Mock.from_json(cmd_mocks[mock_args])
                    args_pattern = mock_args
                    break

            if mock:
                print(
                    f"{GREEN('✓')} best match found: {mock.pretty(args_pattern)}",
                    file=sys.stderr,
                )
                exec = mock.exec(cmd, args, match)
                if exec.get("change") == MockChange.delete:
                    _delete_mock(cmd, args_pattern or DFLT_ARG)
                elif exec.get("change") == MockChange.update:
                    _add_mock(cmd, args_pattern or DFLT_ARG, mock, force=True)

                # log execution
                _add_log(time, cmd, args, exec["returncode"], mock.to_json())

                # return code
                sys.exit(exec["returncode"])

    print(
        YELLOW("✗ no match found ❯ rc=0"),
        file=sys.stderr,
    )
    _add_log(time, cmd, args, 0, None)
    sys.exit(0)


def cli():
    parser = argparse.ArgumentParser(
        description="This tool can be used to mock commands and check their execution details afterwards.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""examples:
  %(prog)s stub systemctl
                        Install a stub for 'systemctl ...'
  %(prog)s stub -t=2 -rc=15 systemctl 'restart'
                        Install a stub for 'systemctl restart ...'
                        Exists with return code 15 and will be uninstalled after 2 invocations
  %(prog)s spy curl     Install a spy for 'curl ...'
  %(prog)s fake -i='./my-keygen.sh' ssh-keygen
                        Install a fake for 'ssh-keygen' and use './my-keygen.sh' implementation
  %(prog)s show          Display the actual mocks configuration
  %(prog)s import < mocks.json
                        Import the mocks configuration from mocks.json
  %(prog)s export        Export the actual mocks configuration to stdout
  %(prog)s logs          Display all execution logs (textual format)
  %(prog)s logs -f=json systemctl
                        Display execution logs from 'systemctl' commands in JSON format
  %(prog)s reset         Reset execution logs
  %(prog)s reset --all   Reset execution logs and mocks configuration
""",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="valid subcommands",
        help="Manage mocks, configuration and execution logs...",
    )

    # 'add stub' sub-command
    add_stub_parser = subparsers.add_parser(
        "stub",
        description="Installs a stub for the specified command signature.",
        epilog="Every call to the specified command signature will be intercepted and replaced with the stub implementation.",
    )
    add_stub_parser.set_defaults(func=cli_add_stub)
    add_stub_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force registration even when another mock is installed (overwritten)",
    )
    add_stub_parser.add_argument(
        "-t",
        "--times",
        type=int,
        default=0,
        help="Number of times the mock will be executed",
    )
    add_stub_parser.add_argument(
        "-rc",
        "--returncode",
        type=int,
        default=0,
        help="Return code of the mocked command",
    )
    add_stub_parser.add_argument(
        "-o",
        "--stdout",
        help="Standard output of the mocked command (capture group references supported)",
    )
    add_stub_parser.add_argument(
        "command",
        help="Command name",
    )
    add_stub_parser.add_argument(
        "args",
        nargs="?",
        help="Arguments pattern (regular expression)",
    )
    # 'add spy' sub-command
    add_spy_parser = subparsers.add_parser(
        "spy",
        description="Installs a spy for the specified command signature.",
        epilog="Every call to the specified command signature will be intercepted and recorded by the tool. The original command will still be called.",
    )
    add_spy_parser.set_defaults(func=cli_add_spy)
    add_spy_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force registration even when another mock is installed (overwritten)",
    )
    add_spy_parser.add_argument(
        "command",
        help="Command name",
    )
    add_spy_parser.add_argument(
        "args",
        nargs="?",
        help="Arguments pattern (regular expression)",
    )
    # 'add fake' sub-command
    add_fake_parser = subparsers.add_parser(
        "fake",
        description="Installs a fake for the specified command signature.",
        epilog="Every call to the specified command signature will be intercepted and replaced with the provided alternate (fake) implementation.",
    )
    add_fake_parser.set_defaults(func=cli_add_fake)
    add_fake_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force registration even when another mock is installed (overwritten)",
    )
    add_fake_parser.add_argument(
        "command",
        help="Command name",
    )
    add_fake_parser.add_argument(
        "args",
        nargs="?",
        help="Arguments pattern (regular expression)",
    )
    add_fake_parser.add_argument(
        "-i",
        "--impl",
        required=True,
        help="Alternate (fake) implementation of the original command",
    )
    # 'del' sub-command
    delete_parser = subparsers.add_parser(
        "del",
        description="Uninstalls the mock associated to the specified command signature.",
    )
    delete_parser.set_defaults(func=cli_delete_mock)
    delete_parser.add_argument(
        "command",
        help="Command name",
    )
    delete_parser.add_argument(
        "args",
        nargs="?",
        help="Arguments pattern (regular expression)",
    )
    # show sub-command
    show_parser = subparsers.add_parser(
        "show",
        description="Shows installed mocks.",
    )
    show_parser.set_defaults(func=cli_show)
    # import sub-command
    import_parser = subparsers.add_parser(
        "import",
        description="Imports the mocks configuration.",
    )
    import_parser.set_defaults(func=cli_import)
    import_parser.add_argument(
        "-i",
        "--input",
        help="Input file (default: stdin)",
        type=argparse.FileType("r"),
        default=sys.stdin,
    )
    # export sub-command
    export_parser = subparsers.add_parser(
        "export",
        description="Exports the mocks configuration.",
    )
    export_parser.set_defaults(func=cli_export)
    export_parser.add_argument(
        "-o",
        "--output",
        help="Output file (default: stdout)",
        type=argparse.FileType("w"),
        default=sys.stdout,
    )
    # logs sub-command
    logs_parser = subparsers.add_parser(
        "logs",
        description="Prints the execution logs.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""examples:
  %(prog)s          Display all execution logs (textual format)
  %(prog)s -f=json systemctl
                        Display execution logs from 'systemctl' commands in JSON format
  %(prog)s systemctl 'show .*' | wc -l
                        Count the number of times 'systemctl show .*' was call (used with wc)
  %(prog)s -f=json systemctl | jq -r '.args'
                        Extracts the arguments of each 'systemctl' invocation (used with jq)
""",
    )
    logs_parser.set_defaults(func=cli_logs)
    logs_parser.add_argument(
        "-f",
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    logs_parser.add_argument(
        "-F",
        "--fail",
        action="store_true",
        help="Fail if no log matching command and args",
    )
    logs_parser.add_argument(
        "command",
        nargs="?",
        help="Command name",
    )
    logs_parser.add_argument(
        "args",
        nargs="?",
        help="Arguments pattern (regular expression)",
    )
    # reset sub-command
    reset_parser = subparsers.add_parser(
        "reset",
        description="Resets the execution logs.",
    )
    reset_parser.set_defaults(func=cli_reset)
    reset_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Also resets mocked commands",
    )

    # parse command and args
    args = parser.parse_args()
    # disable colouring on flag '--no-color'
    if args.no_color:
        global COLORED_OUTPUT
        COLORED_OUTPUT = False
    # finally execute command
    if vars(args).get("func") is None:
        print(
            YELLOW("⚠ a subcommand is expected!", Color.BOLD),
            file=sys.stderr,
        )
        parser.print_help(sys.stderr)
        sys.exit(1)
    args.func(args)


def main():
    if sys.argv[0].split(os.sep)[-1] == "cmdmock":
        cli()
    else:
        proxy_call()


if __name__ == "__main__":
    main()
