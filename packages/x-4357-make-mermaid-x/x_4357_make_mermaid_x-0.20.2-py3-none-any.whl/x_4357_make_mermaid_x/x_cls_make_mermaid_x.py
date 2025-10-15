"""Mermaid diagram builder.

Builds Mermaid source for many diagram types with a concise, fluent API.
Output is a plain string suitable for Markdown or Mermaid CLI.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys as _sys
from collections.abc import Iterable, Mapping
from collections.abc import Iterable as _Iterable
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self


class CommandError(RuntimeError):
    def __init__(
        self,
        argv: tuple[str, ...],
        returncode: int,
        stdout: str,
        stderr: str,
    ) -> None:
        message = (
            "Command "
            + " ".join(argv)
            + f" failed with exit code {returncode}: {stderr or stdout}"
        )
        super().__init__(message)
        self.argv = argv
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_command(
    args: _Iterable[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    argv = tuple(args)
    completed = subprocess.run(  # noqa: S603
        list(argv),
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise CommandError(
            argv,
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )
    return completed


_LOGGER = logging.getLogger("x_make")


def _info(*args: object) -> None:
    msg = " ".join(str(a) for a in args)
    with suppress(Exception):
        _LOGGER.info("%s", msg)
    printed = False
    with suppress(Exception):
        print(msg)
        printed = True
    if not printed:
        with suppress(Exception):
            _sys.stdout.write(msg + "\n")


# Diagram kinds supported (primary headers)
_FLOW = "flowchart"
_SEQ = "sequenceDiagram"
_CLASS = "classDiagram"
_STATE = "stateDiagram-v2"
_ER = "erDiagram"
_GANTT = "gantt"
_JOURNEY = "journey"
_PIE = "pie"
_TIMELINE = "timeline"
_GIT = "gitGraph"
_MINDMAP = "mindmap"
_REQ = "requirementDiagram"
_QUAD = "quadrantChart"
_SANKEY = "sankey-beta"
_XY = "xychart-beta"
_BLOCK = "block-beta"

FlowDir = tuple[str, ...]
AttrValue = str | int | float | bool | None
DirectivePayload = Mapping[str, object]


def _new_str_list() -> list[str]:
    return []


def _esc(s: str) -> str:
    return s.replace("\n", "\\n")


@dataclass
class MermaidDoc:
    kind: str
    header: str
    lines: list[str] = field(default_factory=_new_str_list)
    directives: list[str] = field(
        default_factory=_new_str_list
    )  # e.g., %%{init: {...}}%%
    comments: list[str] = field(default_factory=_new_str_list)


class MermaidBuilder:
    """Flexible Mermaid builder covering many diagram kinds.

    Typical usage:
      m = x_cls_make_mermaid_x().flowchart("LR").node("A","Start").edge("A","B","go")
      m.sequence().participant("A","Alice").message("A","B","Hi")
      src = m.source()
    """

    def __init__(self, direction: str = "LR", ctx: object | None = None) -> None:
        self._ctx = ctx
        self._doc = MermaidDoc(kind=_FLOW, header=f"{_FLOW} {direction}")

    def _is_verbose(self) -> bool:
        value: object = getattr(self._ctx, "verbose", False)
        if isinstance(value, bool):
            return value
        return bool(value)

    # Core controls

    def set_directive(self, directive_json: str | DirectivePayload) -> Self:
        """Add a directive block like %%{init: { 'theme':'dark' }}%%."""
        if isinstance(directive_json, dict):
            # minimal serializer without imports
            txt = json.dumps(directive_json, separators=(",", ":"))
            self._doc.directives.append(f"%%{{init: {txt}}}%%")
        else:
            self._doc.directives.append(str(directive_json))
        return self

    def add_comment(self, text: str) -> Self:
        self._doc.comments.append(f"%% {_esc(text)} %%")
        return self

    # Kind switches

    def flowchart(self, direction: str = "LR") -> Self:
        self._doc = MermaidDoc(kind=_FLOW, header=f"{_FLOW} {direction}")
        return self

    def sequence(self, title: str | None = None) -> Self:
        self._doc = MermaidDoc(kind=_SEQ, header=_SEQ)
        if title:
            self._doc.lines.append(f"title {_esc(title)}")
        return self

    def class_diagram(self) -> Self:
        self._doc = MermaidDoc(kind=_CLASS, header=_CLASS)
        return self

    def state(self) -> Self:
        self._doc = MermaidDoc(kind=_STATE, header=_STATE)
        return self

    def er(self) -> Self:
        self._doc = MermaidDoc(kind=_ER, header=_ER)
        return self

    def gantt(self, title: str | None = None, date_format: str = "YYYY-MM-DD") -> Self:
        self._doc = MermaidDoc(kind=_GANTT, header=_GANTT)
        self._doc.lines.append(f"dateFormat {date_format}")
        if title:
            self._doc.lines.append(f"title {_esc(title)}")
        return self

    def journey(self, title: str | None = None) -> Self:
        self._doc = MermaidDoc(kind=_JOURNEY, header=_JOURNEY)
        if title:
            self._doc.lines.append(f"title {_esc(title)}")
        return self

    def pie(self, title: str | None = None) -> Self:
        self._doc = MermaidDoc(kind=_PIE, header=_PIE)
        if title:
            self._doc.lines.append(f"title {_esc(title)}")
        return self

    def timeline(self, title: str | None = None) -> Self:
        self._doc = MermaidDoc(kind=_TIMELINE, header=_TIMELINE)
        if title:
            self._doc.lines.append(f"title {_esc(title)}")
        return self

    def gitgraph(self) -> Self:
        self._doc = MermaidDoc(kind=_GIT, header=_GIT)
        return self

    def mindmap(self) -> Self:
        self._doc = MermaidDoc(kind=_MINDMAP, header=_MINDMAP)
        return self

    def requirement(self) -> Self:
        self._doc = MermaidDoc(kind=_REQ, header=_REQ)
        return self

    def quadrants(
        self,
        title: str | None = None,
        x_left: str = "Low",
        x_right: str = "High",
        y_bottom: str = "Low",
        y_top: str = "High",
    ) -> Self:
        self._doc = MermaidDoc(kind=_QUAD, header=_QUAD)
        if title:
            self._doc.lines.append(f"title {_esc(title)}")
        self._doc.lines.append(f'x-axis "{_esc(x_left)}" "{_esc(x_right)}"')
        self._doc.lines.append(f'y-axis "{_esc(y_bottom)}" "{_esc(y_top)}"')
        return self

    # Flowchart API

    def node(
        self, node_id: str, label: str | None = None, shape: str | None = None
    ) -> Self:
        """Add a node; shape can be: [], (), (()) , {} , [[]], >, etc."""
        if self._doc.kind != _FLOW:
            return self
        if label is None:
            self._doc.lines.append(f"{node_id}")
            return self
        shape_map = {
            "rect": ("[", "]"),
            "round": ("(", ")"),
            "stadium": ("((", "))"),
            "subroutine": ("[[", "]]"),
            "cylinder": ("[(", ")]"),
            "circle": ("((", "))"),
            "asym": (">", "]"),
        }
        if shape and shape in shape_map:
            left_delim, right_delim = shape_map[shape]
            self._doc.lines.append(f"{node_id}{left_delim}{_esc(label)}{right_delim}")
        else:
            self._doc.lines.append(f'{node_id}["{_esc(label)}"]')
        return self

    def edge(
        self,
        src: str,
        dst: str,
        label: str | None = None,
        arrow: str = "-->",
        style: str | None = None,
    ) -> Self:
        if self._doc.kind != _FLOW:
            return self
        mid = f"|{_esc(label)}|" if label else ""
        sfx = f" {style}" if style else ""
        self._doc.lines.append(f"{src} {arrow}{mid} {dst}{sfx}")
        return self

    def subgraph(self, title: str, body: Iterable[str] | None = None) -> Self:
        if self._doc.kind != _FLOW:
            return self
        self._doc.lines.append(f"subgraph {_esc(title)}")
        if body:
            for ln in body:
                self._doc.lines.append(ln)
        self._doc.lines.append("end")
        return self

    def style_node(self, node_id: str, css: str) -> Self:
        if self._doc.kind == _FLOW:
            self._doc.lines.append(f"style {node_id} {_esc(css)}")
        return self

    def link_style(self, idx: int, css: str) -> Self:
        if self._doc.kind == _FLOW:
            self._doc.lines.append(f"linkStyle {idx} {_esc(css)}")
        return self

    def click(self, node_id: str, url: str, tooltip: str | None = None) -> Self:
        if self._doc.kind == _FLOW:
            if tooltip:
                self._doc.lines.append(
                    f'click {node_id} "{_esc(url)}" "{_esc(tooltip)}"'
                )
            else:
                self._doc.lines.append(f'click {node_id} "{_esc(url)}"')
        return self

    # Sequence API

    def participant(self, pid: str, label: str | None = None) -> Self:
        if self._doc.kind == _SEQ:
            if label:
                self._doc.lines.append(f'participant {pid} as "{_esc(label)}"')
            else:
                self._doc.lines.append(f"participant {pid}")
        return self

    def message(self, src: str, dst: str, text: str, kind: str = "->>") -> Self:
        if self._doc.kind == _SEQ:
            self._doc.lines.append(f"{src} {kind} {dst}: {_esc(text)}")
        return self

    def note_over(self, who: str | tuple[str, str], text: str) -> Self:
        if self._doc.kind == _SEQ:
            if isinstance(who, tuple):
                self._doc.lines.append(f"Note over {who[0]},{who[1]}: {_esc(text)}")
            else:
                self._doc.lines.append(f"Note over {who}: {_esc(text)}")
        return self

    def activate(self, pid: str) -> Self:
        if self._doc.kind == _SEQ:
            self._doc.lines.append(f"activate {pid}")
        return self

    def deactivate(self, pid: str) -> Self:
        if self._doc.kind == _SEQ:
            self._doc.lines.append(f"deactivate {pid}")
        return self

    def block(self, kind: str, title: str, body: Iterable[str]) -> Self:
        """Generic sequence block: kind in ('loop','alt','opt','par','rect')."""
        if self._doc.kind == _SEQ:
            self._doc.lines.append(f"{kind} {_esc(title)}")
            for ln in body:
                self._doc.lines.append(ln)
            self._doc.lines.append("end")
        return self

    # Class API

    def class_(
        self,
        name: str,
        fields: list[str] | None = None,
        methods: list[str] | None = None,
    ) -> Self:
        if self._doc.kind == _CLASS:
            self._doc.lines.append(f"class {name} {{")
            for f in fields or []:
                self._doc.lines.append(f"  {f}")
            for m in methods or []:
                self._doc.lines.append(f"  {m}()")
            self._doc.lines.append("}")
        return self

    def class_rel(self, a: str, op: str, b: str, label: str | None = None) -> Self:
        """op: '<|--', '*--', 'o--', '--', '<..', etc."""
        if self._doc.kind == _CLASS:
            lab = f" : {_esc(label)}" if label else ""
            self._doc.lines.append(f"{a} {op} {b}{lab}")
        return self

    # State API

    def state_node(self, name: str, alias: str | None = None) -> Self:
        if self._doc.kind == _STATE:
            if alias:
                self._doc.lines.append(f'state "{_esc(name)}" as {alias}')
            else:
                self._doc.lines.append(f'state "{_esc(name)}"')
        return self

    def state_trans(self, src: str, dst: str, event: str | None = None) -> Self:
        if self._doc.kind == _STATE:
            ev = f" : {_esc(event)}" if event else ""
            self._doc.lines.append(f"{src} --> {dst}{ev}")
        return self

    def state_start(self, to: str) -> Self:
        return self.state_trans("[*]", to)

    def state_end(self, frm: str) -> Self:
        return self.state_trans(frm, "[*]")

    def state_subgraph(self, name: str, body: Iterable[str]) -> Self:
        if self._doc.kind == _STATE:
            self._doc.lines.append(f"state {_esc(name)} {{")
            for ln in body:
                self._doc.lines.append(ln)
            self._doc.lines.append("}")
        return self

    # ER API

    def er_entity(self, name: str, *fields: str) -> Self:
        if self._doc.kind == _ER:
            if fields:
                self._doc.lines.append(
                    f"{name} {{ {'; '.join(_esc(f) for f in fields)} }}"
                )
            else:
                self._doc.lines.append(f"{name}")
        return self

    def er_rel(self, left: str, card: str, right: str, label: str = "") -> Self:
        """card like '||--o{' etc."""
        if self._doc.kind == _ER:
            lab = f" : {_esc(label)}" if label else ""
            self._doc.lines.append(f"{left} {card} {right}{lab}")
        return self

    # Gantt API

    def gantt_section(self, title: str) -> Self:
        if self._doc.kind == _GANTT:
            self._doc.lines.append(f"section {_esc(title)}")
        return self

    def gantt_task(
        self,
        title: str,
        task_id: str | None = None,
        start_or_rel: str | None = None,
        duration: str | None = None,
        depends_on: str | None = None,
    ) -> Self:
        """Examples:
        Task :t1, 2025-01-01, 3d
        Task :t2, after t1, 5d
        Task :t3, 2025-01-02, 1d
        """
        if self._doc.kind == _GANTT:
            parts: list[str] = []
            if task_id:
                parts.append(task_id)
            if start_or_rel:
                parts.append(start_or_rel)
            if duration:
                parts.append(duration)
            if depends_on:
                parts.append(f"after {depends_on}")
            meta = ", ".join(parts) if parts else ""
            self._doc.lines.append(f"{_esc(title)} : {meta}".rstrip())
        return self

    # Journey

    def journey_section(self, title: str) -> Self:
        if self._doc.kind == _JOURNEY:
            self._doc.lines.append(f"section {_esc(title)}")
        return self

    def journey_step(self, actor: str, score: int, text: str) -> Self:
        if self._doc.kind == _JOURNEY:
            self._doc.lines.append(f"{_esc(actor)}: {score}: {_esc(text)}")
        return self

    # Pie

    def pie_slice(self, label: str, value: float) -> Self:
        if self._doc.kind == _PIE:
            self._doc.lines.append(f'"{_esc(label)}" : {value}')
        return self

    # Timeline

    def timeline_entry(self, when: str, *items: str) -> Self:
        if self._doc.kind == _TIMELINE:
            self._doc.lines.append(
                f'{_esc(when)} : {", ".join(_esc(i) for i in items)}'
            )
        return self

    # GitGraph

    def git_commit(self, msg: str | None = None) -> Self:
        if self._doc.kind == _GIT:
            tag_part = f'tag: "{_esc(msg)}"' if msg else ""
            entry = f"commit {tag_part}".rstrip()
            self._doc.lines.append(entry)
        return self

    def git_branch(self, name: str) -> Self:
        if self._doc.kind == _GIT:
            self._doc.lines.append(f"branch {name}")
        return self

    def git_checkout(self, name: str) -> Self:
        if self._doc.kind == _GIT:
            self._doc.lines.append(f"checkout {name}")
        return self

    def git_merge(self, name: str) -> Self:
        if self._doc.kind == _GIT:
            self._doc.lines.append(f"merge {name}")
        return self

    # Mindmap

    def mindmap_node(self, path: list[str]) -> Self:
        """Add a node by path; indent with 2 spaces per level."""
        if self._doc.kind == _MINDMAP and path:
            for i, part in enumerate(path):
                indent = "  " * i
                self._doc.lines.append(f"{indent}{_esc(part)}")
        return self

    # Requirement

    def req(self, kind: str, ident: str, attrs: dict[str, str]) -> Self:
        """kind in ('requirement','functionalRequirement','test','risk',...)."""
        if self._doc.kind == _REQ:
            self._doc.lines.append(f"{kind} {ident} {{")
            for k, v in attrs.items():
                self._doc.lines.append(f"  {k}: {_esc(v)}")
            self._doc.lines.append("}")
        return self

    def req_link(self, a: str, op: str, b: str, label: str | None = None) -> Self:
        if self._doc.kind == _REQ:
            lab = f" : {_esc(label)}" if label else ""
            self._doc.lines.append(f"{a} {op} {b}{lab}")
        return self

    # Quadrant chart

    def quadrant(self, idx: int, name: str) -> Self:
        if self._doc.kind == _QUAD:
            self._doc.lines.append(f'quadrant-{idx} "{_esc(name)}"')
        return self

    def quad_point(self, label: str, x: float, y: float) -> Self:
        if self._doc.kind == _QUAD:
            self._doc.lines.append(f'point "{_esc(label)}" : {x}, {y}')
        return self

    # Beta charts (stubs: let callers write lines)

    def raw(self, line: str) -> Self:
        """Append a raw Mermaid line (escape yourself if needed)."""
        self._doc.lines.append(line)
        return self

    # Output

    def source(self) -> str:
        parts: list[str] = []
        parts.extend(self._doc.directives)
        parts.extend(self._doc.comments)
        parts.append(self._doc.header)
        parts.extend(self._doc.lines)
        return "\n".join(parts) + "\n"

    def save(self, path: str = "diagram.mmd") -> str:
        src = self.source()
        path_obj = Path(path)
        path_obj.write_text(src, encoding="utf-8")
        if self._is_verbose():
            _info(f"[mermaid] saved mermaid source to {path}")
        return str(path_obj)

    def to_svg(
        self,
        mmd_path: str | None = None,
        svg_path: str | None = None,
        mmdc_cmd: str | None = None,
        extra_args: list[str] | None = None,
    ) -> str | None:
        """Convert Mermaid to SVG via mermaid-cli (mmdc) if available.

        Returns SVG path on success, or None if CLI not found or conversion failed.
        """
        # Ensure .mmd exists
        mmd_path_obj = Path(mmd_path or "diagram.mmd")
        needs_write = True
        with suppress(Exception):
            needs_write = not mmd_path_obj.exists()
        if needs_write:
            self.save(str(mmd_path_obj))
        # Decide svg output
        svg_path_obj = Path(svg_path) if svg_path else mmd_path_obj.with_suffix(".svg")
        # Resolve CLI
        cmd = mmdc_cmd or os.environ.get("MMDC", "mmdc")
        exe = shutil.which(cmd)
        if not exe:
            if self._is_verbose():
                missing_msg = (
                    f"[mermaid] mermaid-cli '{cmd}' not found in PATH; "
                    f"left .mmd at {mmd_path_obj}"
                )
                _info(missing_msg)
            return None
        args = [
            exe,
            "-i",
            str(mmd_path_obj),
            "-o",
            str(svg_path_obj),
            "-b",
            "transparent",
        ]
        if extra_args:
            args.extend(extra_args)
        try:
            res = run_command(args, check=False)
        except OSError as exc:
            if self._is_verbose():
                _info(f"[mermaid] failed to invoke mermaid-cli: {exc}")
            return None
        if res.stdout:
            _info(res.stdout.strip())
        if res.returncode == 0:
            return str(svg_path_obj)
        if res.stderr:
            _info(res.stderr.strip())
        return None


def main() -> str:
    # Tiny demo
    m = (
        MermaidBuilder()
        .flowchart("LR")
        .node("A", "Start")
        .node("B", "End")
        .edge("A", "B", "next")
    )
    m.save("example.mmd")
    svg = m.to_svg("example.mmd", "example.svg")
    return svg or "example.mmd"


if __name__ == "__main__":
    _info(main())


class MermaidMake(MermaidBuilder):
    """Backward-compatible alias for legacy consumers."""


x_cls_make_mermaid_x = MermaidMake


__all__ = ["MermaidBuilder", "MermaidMake", "x_cls_make_mermaid_x"]
