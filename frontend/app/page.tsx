"use client";
import { useEffect, useRef, useState } from "react";

const ISSUES = [
  { id:1, severity:"error",   file:"auth.py", line:7,  title:"MD5 is not safe for password hashing",  category:"security",   suggestion:"Use bcrypt or argon2 instead",              diff:`-    return hashlib.md5(password.encode()).hexdigest()\n+    import bcrypt\n+    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())` },
  { id:2, severity:"error",   file:"auth.py", line:11, title:"SQL injection vulnerability detected",   category:"security",   suggestion:"Use parameterized queries",                 diff:`-    query = "SELECT * FROM users WHERE username = '" + username\n+    query = "SELECT * FROM users WHERE username = ?"\n+    cursor.execute(query, (username,))` },
  { id:3, severity:"warning", file:"auth.py", line:4,  title:"Hardcoded secret key in source code",    category:"style",      suggestion:"Move to environment variables",             diff:`-SECRET_KEY = "mysecret123"\n+import os\n+SECRET_KEY = os.environ.get("SECRET_KEY")` },
  { id:4, severity:"warning", file:"auth.py", line:15, title:"No input validation on user_id",         category:"logic",      suggestion:"Validate and sanitize all inputs",          diff:`-    os.system("cat /etc/passwd/" + user_id)\n+    if not user_id.isalnum():\n+        raise ValueError("Invalid user_id")\n+    subprocess.run(["cat", f"/etc/passwd/{user_id}"], check=True)` },
  { id:5, severity:"nit",     file:"auth.py", line:19, title:"Missing zero-division check",            category:"bug",        suggestion:"Add if b == 0 guard",                       diff:`-    return a / b\n+    if b == 0:\n+        raise ValueError("Cannot divide by zero")\n+    return a / b` },
];

const FEED = [
  { time:"00:00", msg:"Webhook received from GitHub" },
  { time:"00:01", msg:"PR #1 — Add authentication module" },
  { time:"00:02", msg:"Fetching raw diff from GitHub API..." },
  { time:"00:03", msg:"Parsed 1 hunk across 1 file" },
  { time:"00:04", msg:"Running AST analysis on auth.py" },
  { time:"00:05", msg:"Extracted function: hash_password, login, get_user_data" },
  { time:"00:06", msg:"Calling Llama 3.1 via Groq API..." },
  { time:"00:07", msg:"LLM response received — 5 issues found" },
  { time:"00:08", msg:"Posting inline comments to GitHub PR..." },
  { time:"00:09", msg:"Review complete ✓" },
];

const SEV_STYLE: Record<string, {color:string;bg:string;border:string;dot:string;label:string}> = {
  error:   { color:"#f87171", bg:"rgba(239,68,68,0.08)",   border:"rgba(239,68,68,0.2)",   dot:"#ef4444", label:"ERROR" },
  warning: { color:"#fbbf24", bg:"rgba(251,191,36,0.08)",  border:"rgba(251,191,36,0.2)",  dot:"#f59e0b", label:"WARN" },
  nit:     { color:"#60a5fa", bg:"rgba(96,165,250,0.08)",  border:"rgba(96,165,250,0.2)",  dot:"#3b82f6", label:"NIT" },
};

function Particle({ x, y, size, opacity, speed }: { x:number;y:number;size:number;opacity:number;speed:number }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let pos = y;
    const move = () => {
      pos -= speed;
      if (pos < -10) pos = 110;
      if (ref.current) ref.current.style.top = pos + "%";
      requestAnimationFrame(move);
    };
    const id = requestAnimationFrame(move);
    return () => cancelAnimationFrame(id);
  }, [y, speed]);
  return (
    <div ref={ref} style={{
      position:"absolute", left:`${x}%`, top:`${y}%`,
      width:size, height:size, borderRadius:"50%",
      background:`rgba(139,92,246,${opacity})`,
      pointerEvents:"none",
    }} />
  );
}

function Donut({ errors, warnings, nits }: { errors:number;warnings:number;nits:number }) {
  const total = errors + warnings + nits;
  const r = 54; const cx = 64; const cy = 64;
  const circ = 2 * Math.PI * r;
  const errPct = errors / total;
  const warnPct = warnings / total;
  const nitPct = nits / total;
  const errDash = errPct * circ;
  const warnDash = warnPct * circ;
  const nitDash = nitPct * circ;
  const warnOffset = -(errDash);
  const nitOffset = -(errDash + warnDash);
  return (
    <svg width="128" height="128" viewBox="0 0 128 128">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="14" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#ef4444" strokeWidth="14"
        strokeDasharray={`${errDash} ${circ - errDash}`} strokeDashoffset={circ/4} strokeLinecap="round" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#f59e0b" strokeWidth="14"
        strokeDasharray={`${warnDash} ${circ - warnDash}`} strokeDashoffset={circ/4 + warnOffset} strokeLinecap="round" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#3b82f6" strokeWidth="14"
        strokeDasharray={`${nitDash} ${circ - nitDash}`} strokeDashoffset={circ/4 + nitOffset} strokeLinecap="round" />
      <text x={cx} y={cy-8} textAnchor="middle" fill="white" fontSize="22" fontWeight="600">{total}</text>
      <text x={cx} y={cy+10} textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="10">issues</text>
    </svg>
  );
}

function LiveFeed() {
  const [lines, setLines] = useState<string[]>([]);
  const [idx, setIdx] = useState(0);
  const [running, setRunning] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const start = () => { setLines([]); setIdx(0); setRunning(true); };
  useEffect(() => {
    if (!running) return;
    if (idx >= FEED.length) { setRunning(false); return; }
    const t = setTimeout(() => {
      setLines(l => [...l, `[${FEED[idx].time}] ${FEED[idx].msg}`]);
      setIdx(i => i + 1);
    }, 600);
    return () => clearTimeout(t);
  }, [running, idx]);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines]);
  return (
    <div style={{ background:"rgba(0,0,0,0.4)", border:"1px solid rgba(139,92,246,0.2)", borderRadius:16, padding:20, height:240 }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:12 }}>
        <span style={{ color:"rgba(255,255,255,0.5)", fontSize:11, textTransform:"uppercase", letterSpacing:"0.1em" }}>Live pipeline log</span>
        <button onClick={start} style={{ background:"rgba(139,92,246,0.2)", border:"1px solid rgba(139,92,246,0.4)", borderRadius:8, color:"#a78bfa", fontSize:11, padding:"4px 12px", cursor:"pointer" }}>
          {running ? "Running..." : "Replay ▶"}
        </button>
      </div>
      <div ref={ref} style={{ fontFamily:"monospace", fontSize:12, color:"#4ade80", overflowY:"auto", height:170 }}>
        {lines.map((l,i) => (
          <div key={i} style={{ marginBottom:4, opacity: i === lines.length-1 ? 1 : 0.7 }}>
            <span style={{ color:"rgba(139,92,246,0.7)" }}>&gt; </span>{l}
            {i === lines.length-1 && running && <span style={{ animation:"blink 1s infinite" }}>█</span>}
          </div>
        ))}
        {lines.length === 0 && <span style={{ color:"rgba(255,255,255,0.2)" }}>Click replay to simulate a PR review...</span>}
      </div>
    </div>
  );
}

function IssueCard({ issue }: { issue: typeof ISSUES[0] }) {
  const [open, setOpen] = useState(false);
  const s = SEV_STYLE[issue.severity];
  return (
    <div onClick={() => setOpen(o => !o)} style={{
      background: open ? s.bg : "rgba(255,255,255,0.03)",
      border:`1px solid ${open ? s.border : "rgba(255,255,255,0.08)"}`,
      borderRadius:12, padding:"14px 16px", cursor:"pointer",
      transition:"all 0.2s ease", marginBottom:8,
    }}>
      <div style={{ display:"flex", alignItems:"center", gap:10 }}>
        <div style={{ width:8, height:8, borderRadius:"50%", background:s.dot, flexShrink:0 }} />
        <span style={{ fontSize:10, fontWeight:600, color:s.color, background:s.bg, border:`1px solid ${s.border}`, borderRadius:6, padding:"2px 6px" }}>{s.label}</span>
        <span style={{ fontFamily:"monospace", fontSize:12, color:"rgba(255,255,255,0.4)" }}>{issue.file}:{issue.line}</span>
        <span style={{ fontSize:13, color:"rgba(255,255,255,0.8)", flex:1 }}>{issue.title}</span>
        <span style={{ fontSize:10, color:"rgba(255,255,255,0.25)", background:"rgba(255,255,255,0.05)", borderRadius:6, padding:"2px 8px" }}>{issue.category}</span>
        <span style={{ color:"rgba(255,255,255,0.3)", fontSize:12, transform: open ? "rotate(180deg)" : "rotate(0deg)", transition:"transform 0.2s" }}>▼</span>
      </div>
      {open && (
        <div style={{ marginTop:14, paddingTop:14, borderTop:"1px solid rgba(255,255,255,0.06)" }}>
          <p style={{ fontSize:12, color:"rgba(255,255,255,0.5)", marginBottom:10 }}>💡 {issue.suggestion}</p>
          <div style={{ background:"rgba(0,0,0,0.5)", borderRadius:8, padding:14, fontFamily:"monospace", fontSize:12, lineHeight:1.8 }}>
            {issue.diff.split("\n").map((line, i) => (
              <div key={i} style={{
                color: line.startsWith("+") ? "#4ade80" : line.startsWith("-") ? "#f87171" : "rgba(255,255,255,0.4)",
                background: line.startsWith("+") ? "rgba(74,222,128,0.06)" : line.startsWith("-") ? "rgba(248,113,113,0.06)" : "transparent",
                padding:"1px 4px", borderRadius:3,
              }}>{line}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [mounted, setMounted] = useState(false);
  const particles = useRef(Array.from({length:30}, () => ({
    x: Math.random()*100, y: Math.random()*100,
    size: Math.random()*2+1, opacity: Math.random()*0.15+0.05,
    speed: Math.random()*0.03+0.01,
  }))).current;

  useEffect(() => { setMounted(true); }, []);

  return (
    <div style={{ minHeight:"100vh", background:"#08060f", color:"white", fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif", padding:"32px 24px", position:"relative", overflow:"hidden" }}>
      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        .fade-up { animation: fadeUp 0.6s ease forwards; }
        .pulse { animation: pulse 2s infinite; }
        ::-webkit-scrollbar { width:4px; }
        ::-webkit-scrollbar-track { background:transparent; }
        ::-webkit-scrollbar-thumb { background:rgba(139,92,246,0.3); border-radius:2px; }
      `}</style>

      {mounted && particles.map((p,i) => <Particle key={i} {...p} />)}

      <div style={{ maxWidth:1100, margin:"0 auto", position:"relative" }}>

        {/* Header */}
        <div className="fade-up" style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:40 }}>
          <div style={{ display:"flex", alignItems:"center", gap:14 }}>
            <div style={{ width:44, height:44, borderRadius:14, background:"linear-gradient(135deg,#7c3aed,#4f46e5)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:22 }}>🤖</div>
            <div>
              <h1 style={{ fontSize:20, fontWeight:700, margin:0, letterSpacing:"-0.3px" }}>AI Code Reviewer</h1>
              <p style={{ fontSize:12, color:"rgba(255,255,255,0.35)", margin:0, fontFamily:"monospace" }}>HamzzaFareed/ai-code-reviewer</p>
            </div>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:8, background:"rgba(16,185,129,0.1)", border:"1px solid rgba(16,185,129,0.25)", borderRadius:99, padding:"6px 14px" }}>
            <div className="pulse" style={{ width:7, height:7, borderRadius:"50%", background:"#10b981" }} />
            <span style={{ fontSize:12, color:"#34d399", fontWeight:500 }}>Agent online</span>
          </div>
        </div>

        {/* Metrics */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:14, marginBottom:24 }}>
          {[
            { label:"PRs reviewed",    value:"1",  sub:"all time",        accent:"#7c3aed" },
            { label:"Issues found",    value:"5",  sub:"in this PR",      accent:"#f59e0b" },
            { label:"Bugs caught",     value:"2",  sub:"critical errors", accent:"#ef4444" },
            { label:"Avg review time", value:"8s", sub:"per PR",          accent:"#06b6d4" },
          ].map((m,i) => (
            <div key={i} className="fade-up" style={{ animationDelay:`${i*80}ms`, background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:16, padding:"20px 18px", position:"relative", overflow:"hidden" }}>
              <div style={{ position:"absolute", top:0, left:0, right:0, height:2, background:m.accent, borderRadius:"16px 16px 0 0" }} />
              <p style={{ fontSize:11, color:"rgba(255,255,255,0.4)", margin:"0 0 10px", textTransform:"uppercase", letterSpacing:"0.08em" }}>{m.label}</p>
              <p style={{ fontSize:32, fontWeight:700, margin:"0 0 4px", color:"white" }}>{m.value}</p>
              <p style={{ fontSize:11, color:"rgba(255,255,255,0.25)", margin:0 }}>{m.sub}</p>
            </div>
          ))}
        </div>

        {/* Main grid */}
        <div style={{ display:"grid", gridTemplateColumns:"1fr 340px", gap:20, marginBottom:20 }}>

          {/* Left — PR Card */}
          <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:20, padding:24 }}>
            <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:20 }}>
              <span style={{ fontSize:18 }}>🔀</span>
              <div>
                <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                  <span style={{ fontWeight:600, fontSize:15 }}>PR #1 — Add authentication module</span>
                  <span style={{ fontSize:11, background:"rgba(16,185,129,0.15)", color:"#34d399", border:"1px solid rgba(16,185,129,0.3)", borderRadius:99, padding:"2px 8px" }}>open</span>
                </div>
                <p style={{ fontSize:12, color:"rgba(255,255,255,0.35)", fontFamily:"monospace", margin:"4px 0 0" }}>auth.py · 1 file · 16 additions</p>
              </div>
              <span style={{ marginLeft:"auto", fontSize:12, color:"rgba(255,255,255,0.25)" }}>just now</span>
            </div>

            <div style={{ background:"rgba(0,0,0,0.3)", borderRadius:12, padding:16, fontFamily:"monospace", fontSize:12, lineHeight:2, marginBottom:20 }}>
              {ISSUES.map((issue,i) => {
                const s = SEV_STYLE[issue.severity];
                return (
                  <div key={i} style={{ display:"flex", alignItems:"center", gap:8 }}>
                    <span>{issue.severity==="error"?"🔴":issue.severity==="warning"?"🟡":"🔵"}</span>
                    <span style={{ color:s.color, minWidth:52 }}>{s.label}</span>
                    <span style={{ color:"rgba(255,255,255,0.3)" }}>·</span>
                    <span style={{ color:"rgba(255,255,255,0.4)", minWidth:56 }}>line {issue.line}</span>
                    <span style={{ color:"rgba(255,255,255,0.3)" }}>·</span>
                    <span style={{ color:"rgba(255,255,255,0.75)" }}>{issue.title}</span>
                  </div>
                );
              })}
            </div>

            <div style={{ display:"flex", gap:10 }}>
              <button style={{ background:"linear-gradient(135deg,#7c3aed,#4f46e5)", border:"none", borderRadius:10, color:"white", fontSize:13, fontWeight:600, padding:"10px 20px", cursor:"pointer" }}>
                View on GitHub →
              </button>
              <button style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, color:"rgba(255,255,255,0.6)", fontSize:13, padding:"10px 20px", cursor:"pointer" }}>
                Redeliver webhook
              </button>
            </div>
          </div>

          {/* Right — Donut + breakdown */}
          <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
            <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:20, padding:20, display:"flex", flexDirection:"column", alignItems:"center" }}>
              <p style={{ fontSize:11, color:"rgba(255,255,255,0.4)", textTransform:"uppercase", letterSpacing:"0.1em", margin:"0 0 16px" }}>Issues breakdown</p>
              <Donut errors={2} warnings={2} nits={1} />
              <div style={{ display:"flex", gap:16, marginTop:16 }}>
                {[{color:"#ef4444",label:"Errors",val:2},{color:"#f59e0b",label:"Warnings",val:2},{color:"#3b82f6",label:"Nits",val:1}].map((d,i) => (
                  <div key={i} style={{ textAlign:"center" }}>
                    <div style={{ width:8, height:8, borderRadius:"50%", background:d.color, margin:"0 auto 4px" }} />
                    <p style={{ fontSize:10, color:"rgba(255,255,255,0.35)", margin:0 }}>{d.label}</p>
                    <p style={{ fontSize:16, fontWeight:600, margin:0 }}>{d.val}</p>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:20, padding:20, flex:1 }}>
              <p style={{ fontSize:11, color:"rgba(255,255,255,0.4)", textTransform:"uppercase", letterSpacing:"0.1em", margin:"0 0 14px" }}>By category</p>
              {[
                {label:"Security", val:2, pct:80, color:"#ef4444"},
                {label:"Logic",    val:1, pct:40, color:"#a78bfa"},
                {label:"Style",    val:1, pct:40, color:"#60a5fa"},
                {label:"Bug",      val:1, pct:40, color:"#f59e0b"},
              ].map((b,i) => (
                <div key={i} style={{ marginBottom:12 }}>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:4 }}>
                    <span style={{ fontSize:12, color:"rgba(255,255,255,0.5)" }}>{b.label}</span>
                    <span style={{ fontSize:12, color:"rgba(255,255,255,0.3)" }}>{b.val}</span>
                  </div>
                  <div style={{ height:4, background:"rgba(255,255,255,0.06)", borderRadius:99, overflow:"hidden" }}>
                    <div style={{ height:"100%", width:`${b.pct}%`, background:b.color, borderRadius:99, transition:"width 1s ease" }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Live Feed */}
        <div style={{ marginBottom:20 }}>
          <LiveFeed />
        </div>

        {/* Issues list */}
        <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:20, padding:24 }}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:16 }}>
            <p style={{ fontSize:11, color:"rgba(255,255,255,0.4)", textTransform:"uppercase", letterSpacing:"0.1em", margin:0 }}>Issues found — click to expand</p>
            <span style={{ fontSize:12, color:"rgba(255,255,255,0.25)" }}>5 total</span>
          </div>
          {ISSUES.map(issue => <IssueCard key={issue.id} issue={issue} />)}
        </div>

      </div>
    </div>
  );
}