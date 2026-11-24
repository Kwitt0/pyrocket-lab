(function(){
  "use strict";

  const MAX_LINE_EVENTS = 20000;
  const EXEC_LIMIT_MS = 4000;
  const MAX_ROBOT_CMDS = 3000;
  const MAX_PRINTS = 200;
  const MAX_PRINT_CHARS = 100000;
  const LIMIT_MSG = "โค้ดรันคำสั่งมากเกินไป (อาจมีลูปไม่สิ้นสุด) — โปรแกรมถูกหยุดเพื่อความปลอดภัย";

  class RobotCrash extends Error{ constructor(info){ super("crash"); this.info = info; } }
  class RobotLimit extends Error{ constructor(){ super(LIMIT_MSG); } }

  const BASE = new URL(".", document.currentScript.src).href;

  const PREAMBLE = "import robot\n";
  const PREAMBLE_LINES = 1;

  let ctx = null;

  const BLOCK_KW = /^(for|while|if|elif|else|try|except|finally|with|def|class|import|from)\b/;

  function instrumentCode(code){
    if(/'''|"""/.test(code)) return code;
    let depth = 0, cont = false;
    return code.split("\n").map((line, i) => {
      const bare = line.replace(/'[^']*'|"[^"]*"/g, '""').replace(/#.*$/, "");
      const trimmed = bare.trim();
      let res = line;
      if(!cont && depth === 0 && trimmed !== "" && !/:$/.test(trimmed) && !BLOCK_KW.test(trimmed)){
        const ind = (line.match(/^[ \t]*/) || [""])[0];
        res = ind + "robot._line(" + (i + 1) + "); " + line.slice(ind.length);
      }
      for(const ch of bare){
        if(ch === "(" || ch === "[" || ch === "{") depth++;
        else if(ch === ")" || ch === "]" || ch === "}") depth = Math.max(0, depth - 1);
      }
      cont = depth > 0 || /\\$/.test(bare.replace(/\s+$/, ""));
      return res;
    }).join("\n");
  }

  function emitOutput(final){
    const text = ctx.out.join("");
    if(!text) return;
    const cut = final ? text.length : text.lastIndexOf("\n");
    if(cut < 0) return;
    let shown = text.slice(0, cut);
    const rest = text.slice(cut + 1);
    if(final && shown.endsWith("\n")) shown = shown.slice(0, -1);
    ctx.out = rest ? [rest] : [];
    shown.split("\n").forEach(t => ctx.events.push({ t:"print", text:t, line:ctx.line }));
  }

  function onOutput(s){
    ctx.chars += s.length;
    ctx.prints += (s.match(/\n/g) || []).length;
    if(ctx.chars > MAX_PRINT_CHARS || ctx.prints > MAX_PRINTS) throw new RobotLimit();
    ctx.out.push(s);
    emitOutput(false);
  }

  const jsRound = (v) => Math.floor(v + 0.5);
  const clamp = (v) => Math.min(Math.max(v, 0), ctx.N - 1);
  const inBounds = (x, y) => { const e = 1e-9; return -e <= x && x <= ctx.N - 1 + e && -e <= y && y <= ctx.N - 1 + e; };
  const blocked = (cx, cy) => !(cx === ctx.goal.x && cy === ctx.goal.y) && ctx.obstacles.has(cx + "," + cy);

  function robotCmd(){
    emitOutput(true);
    if(++ctx.cmds > MAX_ROBOT_CMDS) throw new RobotLimit();
  }

  function straight(cells){
    if(cells === undefined) cells = 0;
    robotCmd();
    const b = ctx.bot;
    const steps = Math.max(1, Math.ceil(Math.abs(cells) * 12));
    const sign = cells >= 0 ? 1 : -1;
    const rad = b.h * Math.PI / 180;
    const fx = b.x, fy = b.y;
    for(let i = 0; i < steps; i++){
      const step = sign * (Math.abs(cells) / steps);
      const nx = b.x + Math.sin(rad) * step;
      const ny = b.y - Math.cos(rad) * step;
      let crash = null;
      if(!inBounds(nx, ny)){
        crash = { type:"edge", at:[jsRound(clamp(nx)), jsRound(clamp(ny))] };
      }else{
        const cx = jsRound(b.x), cy = jsRound(b.y), tx = jsRound(nx), ty = jsRound(ny);
        if((tx !== cx || ty !== cy) && blocked(tx, ty)) crash = { type:"obstacle", at:[tx, ty] };
      }
      if(crash){
        Object.assign(crash, { from:[fx, fy], heading:b.h, cells, line:ctx.line });
        ctx.events.push({ t:"move", from:[fx, fy], to:[b.x, b.y], cells, line:ctx.line, crash });
        throw new RobotCrash(crash);
      }
      b.x = clamp(nx);
      b.y = clamp(ny);
    }
    ctx.events.push({ t:"move", from:[fx, fy], to:[b.x, b.y], cells, line:ctx.line });
  }

  function turn(deg){
    if(deg === undefined) deg = 0;
    robotCmd();
    ctx.bot.h = (((ctx.bot.h + deg) % 360) + 360) % 360;
    ctx.events.push({ t:"turn", deg, heading:ctx.bot.h, line:ctx.line });
  }

  function line(n){
    if(++ctx.lines > MAX_LINE_EVENTS) throw new RobotLimit();
    emitOutput(false);
    ctx.line = n;
    ctx.events.push({ t:"line", n });
  }

  window.__robotSk = { straight, turn, line };

  function registerRobotModule(){
    Sk.builtinFiles.files["src/lib/robot/__init__.js"] = [
      "var $builtinmodule = function(name){",
      "  var mod = {}, none = Sk.builtin.none.none$, js = Sk.ffi.remapToJs;",
      "  function num(fn, v){",
      "    if(v === undefined) return undefined;",
      "    if(!Sk.builtin.checkNumber(v) || Sk.builtin.checkBool(v))",
      "      throw new Sk.builtin.TypeError('robot.' + fn + '() ต้องการตัวเลข แต่ได้รับ ' + Sk.abstr.typeName(v) + ': ' + Sk.builtin.repr(v).v);",
      "    return js(v);",
      "  }",
      "  mod.straight = new Sk.builtin.func(function(cells){ window.__robotSk.straight(num('straight', cells)); return none; });",
      "  mod.turn = new Sk.builtin.func(function(deg){ window.__robotSk.turn(num('turn', deg)); return none; });",
      "  mod._line = new Sk.builtin.func(function(n){ window.__robotSk.line(js(n)); return none; });",
      "  return mod;",
      "};",
    ].join("\n");
  }

  let loading = null;
  function load(){
    if(loading) return loading;
    const add = (src) => new Promise((res, rej) => {
      const s = document.createElement("script");
      s.src = src; s.onload = res; s.onerror = () => rej(new Error("โหลด " + src + " ไม่สำเร็จ"));
      document.head.appendChild(s);
    });
    loading = (window.Sk ? Promise.resolve() : add(BASE + "vendor/skulpt/skulpt.min.js").then(() => add(BASE + "vendor/skulpt/skulpt-stdlib.js")))
      .then(registerRobotModule);
    loading.catch(() => { loading = null; });
    return loading;
  }

  function describeError(e){
    const name = (e && e.tp$name) || "Error";
    let msg = "";
    try{ msg = e.args && e.args.v && e.args.v[0] ? Sk.ffi.remapToJs(e.args.v[0]) : String(e); }catch(_){ msg = String(e); }
    let lineNo = null;
    try{ if(e.traceback && e.traceback.length) lineNo = e.traceback[0].lineno - PREAMBLE_LINES; }catch(_){}
    return { status:"error", name, msg:String(msg), line:(lineNo > 0 ? lineNo : null) || ctx.line, full:name + ": " + msg };
  }

  async function run(code, level){
    await load();
    const st = level.start;
    const heading = "heading" in st ? st.heading : (st.dir || 0) * 90;
    const c = ctx = {
      N: level.N, goal: level.goal,
      obstacles: new Set((level.obs || []).map(o => o.x + "," + o.y)),
      bot: { x:+st.x, y:+st.y, h:((heading % 360) + 360) % 360 },
      events: [], line: null, lines: 0, cmds: 0,
      out: [], chars: 0, prints: 0,
    };
    const t0 = performance.now();
    Sk.configure({
      output: onOutput,
      read: (f) => {
        if(Sk.builtinFiles === undefined || Sk.builtinFiles.files[f] === undefined) throw "File not found: '" + f + "'";
        return Sk.builtinFiles.files[f];
      },
      __future__: Sk.python3,
      execLimit: EXEC_LIMIT_MS,
    });
    Sk.execStart = Date.now();
    let outcome = { status:"ok" };
    try{
      await Sk.misceval.asyncToPromise(() => Sk.importMainWithBody("<student>", false, PREAMBLE + instrumentCode(code), true));
    }catch(e){
      const native = (e && e.nativeError) ? e.nativeError : e;
      if(native instanceof RobotCrash) outcome = { status:"crash", crash:native.info, line:c.line };
      else if(native instanceof RobotLimit || (e && e.tp$name === "TimeLimitError"))
        outcome = { status:"limit", name:"RuntimeError", msg:LIMIT_MSG, line:c.line };
      else outcome = describeError(e);
    }
    try{ emitOutput(true); }catch(_){}
    return {
      outcome, events: c.events,
      final: { x:c.bot.x, y:c.bot.y, h:c.bot.h },
      stats: { lines:c.lines, cmds:c.cmds, py_ms: Math.round((performance.now() - t0) * 100) / 100 },
    };
  }

  window.SkulptEngine = { load, run };
})();
