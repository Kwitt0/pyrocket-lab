const PYODIDE_URL = new URL("vendor/pyodide/", self.location.href).href;

const HARNESS = String.raw`
import sys, io, builtins, time, math, types, json, traceback

STUDENT = "<student>"
MAX_LINE_EVENTS = 20000
MAX_SECONDS = 4.0
MAX_ROBOT_CMDS = 3000
MAX_PRINTS = 200
MAX_PRINT_CHARS = 100000
LIMIT_MSG = "โค้ดรันคำสั่งมากเกินไป (อาจมีลูปไม่สิ้นสุด) — โปรแกรมถูกหยุดเพื่อความปลอดภัย"

class RobotCrash(Exception):
    pass

class RobotLimit(BaseException):
    pass

def _round(v):
    return int(math.floor(v + 0.5))

def run_student(code, level_json):
    level = json.loads(level_json)
    N = level["N"]
    goal = (level["goal"]["x"], level["goal"]["y"])
    obstacles = {(o["x"], o["y"]) for o in level["obs"]}
    st = level["start"]
    heading = st["heading"] if "heading" in st else st.get("dir", 0) * 90
    bot = {"x": float(st["x"]), "y": float(st["y"]), "h": float(heading) % 360}

    events = []
    cur = {"line": None}
    count = {"lines": 0, "cmds": 0}
    t0 = time.perf_counter()

    def blocked(cx, cy):
        return (cx, cy) != goal and (cx, cy) in obstacles

    def in_bounds(x, y):
        e = 1e-9
        return -e <= x <= N - 1 + e and -e <= y <= N - 1 + e

    def robot_cmd():
        emit_output(final=True)
        count["cmds"] += 1
        if count["cmds"] > MAX_ROBOT_CMDS:
            raise RobotLimit(LIMIT_MSG)

    def need_number(fn, v):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise TypeError(f"robot.{fn}() ต้องการตัวเลข แต่ได้รับ {type(v).__name__}: {v!r}")

    def straight(cells=0):
        need_number("straight", cells)
        robot_cmd()
        steps = max(1, math.ceil(abs(cells) * 12))
        sign = 1 if cells >= 0 else -1
        rad = math.radians(bot["h"])
        fx, fy = bot["x"], bot["y"]
        for _ in range(steps):
            step = sign * (abs(cells) / steps)
            nx = bot["x"] + math.sin(rad) * step
            ny = bot["y"] - math.cos(rad) * step
            crash = None
            if not in_bounds(nx, ny):
                crash = {"type": "edge",
                         "at": [_round(min(max(nx, 0), N - 1)), _round(min(max(ny, 0), N - 1))]}
            else:
                c, n = (_round(bot["x"]), _round(bot["y"])), (_round(nx), _round(ny))
                if n != c and blocked(*n):
                    crash = {"type": "obstacle", "at": list(n)}
            if crash:
                crash.update({"from": [fx, fy], "heading": bot["h"], "cells": cells, "line": cur["line"]})
                events.append({"t": "move", "from": [fx, fy], "to": [bot["x"], bot["y"]],
                               "cells": cells, "line": cur["line"], "crash": crash})
                raise RobotCrash(crash)
            bot["x"] = min(max(nx, 0), N - 1)
            bot["y"] = min(max(ny, 0), N - 1)
        events.append({"t": "move", "from": [fx, fy], "to": [bot["x"], bot["y"]],
                       "cells": cells, "line": cur["line"]})

    def turn(deg=0):
        need_number("turn", deg)
        robot_cmd()
        bot["h"] = (bot["h"] + deg) % 360
        events.append({"t": "turn", "deg": deg, "heading": bot["h"], "line": cur["line"]})

    out = {"buf": [], "chars": 0, "lines": 0}

    class StudentOutput(io.TextIOBase):
        encoding = "utf-8"
        def writable(self):
            return True
        def write(self, s):
            if not isinstance(s, str):
                raise TypeError(f"write() argument must be str, not {type(s).__name__}")
            out["chars"] += len(s)
            out["lines"] += s.count("\n")
            if out["chars"] > MAX_PRINT_CHARS or out["lines"] > MAX_PRINTS:
                raise RobotLimit(LIMIT_MSG)
            out["buf"].append(s)
            return len(s)

    def emit_output(final=False):
        text = "".join(out["buf"])
        if not text:
            return
        cut = len(text) if final else text.rfind("\n")
        if cut < 0:
            return
        shown, rest = text[:cut], text[cut + 1:]
        if final and shown.endswith("\n"):
            shown = shown[:-1]
        out["buf"] = [rest] if rest else []
        events.append({"t": "print", "text": shown, "line": cur["line"]})

    real_print = builtins.print
    def print_watch(frame, event, arg):
        if event == "c_return" and arg is real_print and frame.f_code.co_filename == STUDENT:
            emit_output()

    robot = types.ModuleType("robot", "หุ่นยนต์นักบินอวกาศบนสนามจำลอง")
    robot.straight = straight
    robot.turn = turn
    sys.modules["robot"] = robot

    def local_trace(frame, event, arg):
        if event == "line":
            count["lines"] += 1
            if count["lines"] > MAX_LINE_EVENTS or time.perf_counter() - t0 > MAX_SECONDS:
                raise RobotLimit(LIMIT_MSG)
            emit_output()
            cur["line"] = frame.f_lineno
            events.append({"t": "line", "n": frame.f_lineno})
        return local_trace

    def global_trace(frame, event, arg):
        return local_trace if frame.f_code.co_filename == STUDENT else None

    def finish(outcome):
        emit_output(final=True)
        return json.dumps({
            "outcome": outcome, "events": events,
            "final": {"x": bot["x"], "y": bot["y"], "h": bot["h"]},
            "stats": {"lines": count["lines"], "cmds": count["cmds"],
                      "py_ms": round((time.perf_counter() - t0) * 1000, 2)},
        }, ensure_ascii=False)

    try:
        compiled = compile(code, STUDENT, "exec")
    except SyntaxError as e:
        return finish({"status": "error", "name": type(e).__name__, "msg": e.msg,
                       "line": e.lineno, "full": f"{type(e).__name__}: {e.msg}"})

    g = {"__name__": "__main__", "__builtins__": __builtins__, "robot": robot}
    outcome = {"status": "ok"}
    saved_out, saved_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = StudentOutput()
    sys.setprofile(print_watch)
    sys.settrace(global_trace)
    try:
        exec(compiled, g)
    except RobotCrash as e:
        outcome = {"status": "crash", "crash": e.args[0], "line": cur["line"]}
    except RobotLimit as e:
        outcome = {"status": "limit", "name": "RuntimeError", "msg": str(e), "line": cur["line"]}
    except BaseException as e:
        line = None
        tb = e.__traceback__
        while tb is not None:
            if tb.tb_frame.f_code.co_filename == STUDENT:
                line = tb.tb_lineno
            tb = tb.tb_next
        full = traceback.format_exception(e)[-1].strip()
        outcome = {"status": "error", "name": type(e).__name__, "msg": str(e),
                   "line": line or cur["line"], "full": full}
    finally:
        sys.settrace(None)
        sys.setprofile(None)
        sys.stdout, sys.stderr = saved_out, saved_err
    return finish(outcome)
`;

let py = null;

(async function boot(){
  try {
    if (typeof WebAssembly !== "object") throw new Error("เบราว์เซอร์นี้ไม่รองรับ WebAssembly");
    const t0 = performance.now();
    importScripts(PYODIDE_URL + "pyodide.js");
    py = await loadPyodide({ indexURL: PYODIDE_URL });
    py.runPython(HARNESS);
    const info = JSON.parse(py.runPython(
      "import sys, platform, json; json.dumps([sys.version.split()[0], platform.python_implementation()])"));
    self.postMessage({ type: "ready", ms: Math.round(performance.now() - t0), version: info[0], impl: info[1] });
  } catch (e) {
    self.postMessage({ type: "fatal", msg: String((e && e.message) || e) });
  }
})();

self.onmessage = (ev) => {
  const msg = ev.data;
  if (msg.type !== "run" || !py) return;
  const t0 = performance.now();
  try {
    const out = py.globals.get("run_student")(msg.code, msg.level);
    self.postMessage({ type: "result", id: msg.id, data: JSON.parse(out), wall: performance.now() - t0 });
  } catch (e) {
    self.postMessage({ type: "result", id: msg.id, wall: performance.now() - t0,
      data: { outcome: { status: "error", name: "InternalError", msg: String((e && e.message) || e),
                         full: "InternalError: " + String((e && e.message) || e) },
              events: [], stats: {} } });
  }
};
