# pyright: reportUnreachable=information
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from getpass import getpass
import hashlib
import json
import sys
import tomllib as toml
from typing import Callable, NotRequired, TypedDict, cast

EXIT_INPUT = "qq"
type ChoiceCommand = Callable[[], object]


class Node:
    default_fromtext: str
    title: str
    choices: list[Choice]

    def __init__(
        self,
        title: str = "",
        *choices: Choice,
        default_fromtext: str = "",
    ):
        self.title = title
        self.choices = list(choices)
        self.default_fromtext = default_fromtext

    def choice(self, text: str = "", command: ChoiceCommand = lambda: None) -> Choice:
        return Choice(text or self.default_fromtext, self, command)

    def run(
        self,
        /,
        *,
        exit_input: str | None = None,
        nodes: dict[str, Node] | None = None,
    ) -> bool:
        if exit_input is None:
            exit_input = EXIT_INPUT
        if nodes is None:
            nodes = {}

        retry = True
        while retry:
            print(self.title)

            if len(self.choices) > 1:
                for n, choice in enumerate(self.choices):
                    print(f"{n + 1}) {choice.text}")
                while True:
                    inp = input(f"Number ({exit_input} to exit): ")
                    if inp == exit_input:
                        return False
                    if inp.lower() == "xyzzy":
                        return debug_console(nodes)
                    if inp.isnumeric() and 1 <= int(inp) <= len(self.choices):
                        node = self.choices[int(inp) - 1].node
                        if node is None:
                            return True
                        else:
                            if not (retry := node.run(exit_input=exit_input)):
                                return False
                    print(end="Invalid input. ")

            elif len(self.choices):
                inp = input(self.choices[0].text)
                if inp == "xyzzy":
                    return debug_console(nodes)
                node = self.choices[0].node
                if node is None:
                    return True
                else:
                    if not (retry := node.run(exit_input=exit_input)):
                        return False

            else:
                print("No choices found. Exiting...")
                return False

        return False


@dataclass
class Choice:
    text: str = ""
    node: Node | None = None
    command: ChoiceCommand = lambda: None


class ChoiceData(TypedDict):
    command: NotRequired[str]
    node: NotRequired[str]
    text: NotRequired[str]


class NodeData(TypedDict):
    choices: Iterable[ChoiceData]
    default_fromtext: NotRequired[str]
    title: NotRequired[str]


class CyoaTOML_info(TypedDict):
    name: str
    title: NotRequired[str]


class CyoaTOML_runtime(TypedDict):
    exit_input: NotRequired[str]
    start_node: str


class CyoaTOML(TypedDict):
    file: str
    info: CyoaTOML_info
    runtime: CyoaTOML_runtime


def parse_node_data(json_data: dict[str, NodeData]) -> dict[str, Node]:
    nodes: dict[str, Node] = {}
    callbacks: list[Callable[..., None]] = []

    for k, v in json_data.items():
        node = Node()
        node.title = v.get("title", node.title)
        node.default_fromtext = v.get("default_fromtext", node.default_fromtext)

        for choice in v["choices"]:
            node.choices.append(
                Choice(
                    choice.get("text", ""),
                    None,
                    cast(
                        ChoiceCommand,
                        eval(f"lambda: ({choice.get('command')})"),
                    ),
                )
            )

            n = len(node.choices) - 1

            def _cb(
                node: Node = node,
                n: int = n,
                choice: ChoiceData = choice,
            ):
                c = node.choices[n]
                to_node = choice.get("node", None)
                if to_node == "$exit":
                    c.node = None
                elif to_node is not None:
                    c.node = nodes.get(to_node)

                if c.text == "" and c.node is not None:
                    c.text = c.node.default_fromtext

            callbacks.append(_cb)

        nodes[k] = node

    for cb in callbacks:
        cb()

    return nodes


def debug_console(nodes: dict[str, Node], password: str = "") -> bool:
    while True:
        if (
            hashlib.sha3_512(bytes(password, "utf-8")).hexdigest()
            == "c8db9c143a167043713faf016febd72a9e9f20637175d6faff22ef057440e8113bbc0999bbccd2b8e56a730ab249cb21721e65026810c747edd43ae5b37b078d"
        ):
            break

        try:
            if sys.version_info >= (3, 14):
                password = getpass(
                    "Debug console password: ",
                    echo_char="*",
                )
            else:
                password = getpass("Debug console password: ")
        except KeyboardInterrupt:
            return True

    while True:
        print("Debug console options:")
        print("1) Go to node...")
        print("-) exit")

        inp = input("Option: ")
        if inp == "-":
            break
        elif inp.isnumeric():
            match int(inp):
                case 1:
                    name = input("Node: ")
                    node = nodes.get(name)
                    if node is not None:
                        _ = node.run()
                case _:
                    print("Invalid option")
    return True


def __main__():
    while True:
        try:
            packname = input("Pack name (e.g. ONE): ")
            with open(f"CYOAs/{packname}.toml", "rb") as th:
                toml_data: CyoaTOML = toml.load(th)  # pyright: ignore[reportAssignmentType]
            with open(f"CYOAs/{toml_data['file']}") as jh:
                json_data: dict[str, NodeData] = json.load(jh)  # pyright: ignore[reportAny]
        except FileNotFoundError:
            print("Please try again")
        else:
            break
    nodes = parse_node_data(json_data)

    print(toml_data["info"].get("title", toml_data["info"]["name"]))

    return nodes[toml_data["runtime"]["start_node"]].run(
        exit_input=toml_data["runtime"].get("exit_input"), nodes=nodes
    )


if __name__ == "__main__":
    while __main__():
        pass
