# PyRocket Lab

Code and data for the paper "Development and Evaluation of a CPython-Based In-Browser Python Execution Engine for an Educational Robot Simulation System".

PyRocket Lab runs CPython 3.13 in the browser through Pyodide inside a Web Worker. The learner's program runs to completion first, every executed line and robot command is recorded, and the page then replays that record to move the robot. Skulpt is kept as a fallback interpreter that produces records in the same format.

## Contents

```
index.html, style.css, assets/   the robot simulation page
pyodide_worker.js                Web Worker that loads Pyodide and runs the trace recorder (HARNESS)
skulpt_engine.js                 fallback interpreter using Skulpt
vendor/pyodide/                  Pyodide 0.28.3 (CPython 3.13.2), unmodified
vendor/skulpt/                   Skulpt build 2c08b3e8973b28d572cc3ad5d4fd87358b7843a7 (2026-03-05), unmodified
tests/cases.json                 the 93 test programs (45 language, 27 error, 21 robot)
tests/levels.json                field layouts of the four levels
tests/reference.json             reference results from CPython 3.13.2 on macOS
tests/make_reference.py          script that builds cases.json and reference.json
tests/index.html                 test harness (correctness and performance)
results/devices/                 results downloaded from the harness on the six devices
```

## Running

The pages need to be served over HTTP. Any static server works, for example:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000/` for the simulation page or `http://localhost:8000/tests/index.html` for the test harness. Add `?engine=skulpt` to the simulation page to force the fallback interpreter. The harness can download its results as JSON or CSV.

## Rebuilding the reference results

```
python3.13 tests/make_reference.py
```

This must be run with CPython 3.13.x, the same minor version that Pyodide 0.28.3 ships. The script reads the trace recorder directly from `pyodide_worker.js`, so the browser and the reference run use the same recording code. Because of this, the comparison shows agreement between the in-browser interpreter and a locally installed CPython; it does not independently check the robot movement rules.

## Device results

| Folder | Device | Browser |
|---|---|---|
| desktop-i9-12900k | Gigabyte Z690 AORUS ELITE AX DDR4 desktop, Intel Core i9-12900K, 64 GB, Windows 11 Pro | Microsoft Edge 155 |
| macbook-pro-13-m2 | MacBook Pro 13-inch (2022), Apple M2, 16 GB, macOS 26.3.1 | Google Chrome 155 |
| hp-255-g9 | HP 255 G9, AMD Ryzen 5 5625U, 16 GB, Windows 11 Home | Google Chrome 154 |
| asus-x412fl | ASUS VivoBook X412FL, Intel Core i5-8265U, 8 GB, Windows 11 Home | Microsoft Edge 155 |
| ipad-air-3 | iPad Air (3rd generation), Apple A12 Bionic, iPadOS 18.0.1 | Safari 18.0.1 |
| iphone-12-pro-max | iPhone 12 Pro Max, Apple A14 Bionic, iOS 26.6.1 | Safari 26.6.1 |

All devices were tested over the same home Wi-Fi network. The `url` field in each `results.json` was shortened to remove the host name of the test server; nothing else in the result files was changed.

## Licenses

Pyodide is distributed under the Mozilla Public License 2.0 (see `vendor/pyodide/LICENSE`). Skulpt is distributed under the MIT License (https://github.com/skulpt/skulpt).
