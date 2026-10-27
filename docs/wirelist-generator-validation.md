# Validating the SysML v2 Wirelist Generator

**How we check the parser against the official SysML v2 reference implementation**

## Purpose

The Wirelist (signal list) generator reads `.sysml` source files and produces a
spreadsheet of parts, ports, and connections. We need confidence that its parser
actually understands the model it is given — that it is not silently dropping
elements it does not recognise.

Rather than hand-audit the output, we validate it differentially against a parser
we can trust: the **SysML v2 reference implementation**. Both tools read the *same*
`.sysml` files, but the reference implementation uses the official OMG parser, which
understands the entire language. If our generator and the reference agree on the
numbers, our parser handled that construct correctly. Where they disagree, the
reference is authoritative, and the gap tells us exactly what to fix.

## The principle

> Same input, two parsers, compare the outputs. Where they disagree, the official
> parser is authoritative, and the difference tells us what to fix in the signal
> list generator's parser.

That is the whole idea. Everything below is the mechanics of putting it into
practice.

## What you need

| Component | Role |
| --- | --- |
| SysML v2 reference implementation (Docker) | The authoritative parser — understands the full language |
| Jupyter notebook | Where the model is pasted and the parse is triggered |
| API server (ships with the reference impl) | Serves the parsed model for querying |
| Python query library | Small helper to ask the API server for counts |
| Wirelist generator spreadsheet | The output under test |
| A model to test with | The Lunar Lander `.sysml` source, used as the reference example |

## Procedure

### 1. Spin up the reference implementation

Start the reference implementation with Docker. It is a single command:

```sh
make spin-up
```

This brings up both the official parser (reachable from a Jupyter notebook) and the
API server that sits alongside it.

### 2. Feed the model into the official parser

Paste the Lunar Lander `.sysml` source code into a cell in the Jupyter notebook and
run it. The official parser processes the entire model and **publishes the result to
the API server** running next to it. From this point the parsed model is available to
query.

### 3. Query the reference counts, subsystem by subsystem

Using the small Python query library, ask the API server for the counts that matter,
one subsystem at a time:

- how many **parts** are in the subsystem,
- how many **ports**,
- how many **connections**.

Repeat for each subsystem — Thermal Control, EPS (Electrical Power System), and so on
through the model. These are the authoritative numbers.

### 4. Compare against the generator's spreadsheet

Take the counts the wirelist generator reported in its spreadsheet and line them up
against the reference counts, per subsystem.

## Interpreting the results

- **Numbers match** — e.g. the spreadsheet says EPS has 10 elements and the reference
  also says 10. That part of the parser is working correctly.
- **Numbers disagree** — e.g. the spreadsheet says 10 but the reference says 12. The
  generator's parser missed 2 elements.

When they disagree, go back to the API and ask *which specific elements* the reference
counted. The two it found that the spreadsheet did not reveal exactly which SysML v2
construct the generator's parser does not yet handle — which is precisely the thing to
fix next.

## Why this works

The reference implementation is built on the official parser, so it is the ground
truth for what the language actually says. Our generator only has to match it. Each
mismatch is self-describing: it names the subsystem, the count, and — after one more
query — the exact construct responsible. The validation loop is therefore also a
to-do list for the parser.

## Summary

1. `make spin-up` to start the reference implementation.
2. Paste the model into Jupyter; the official parser publishes it to the API server.
3. Query parts / ports / connections per subsystem with the Python library.
4. Compare against the generator's spreadsheet.
5. Where they differ, the reference is authoritative — ask it which elements are
   missing, and fix the parser to handle that construct.
