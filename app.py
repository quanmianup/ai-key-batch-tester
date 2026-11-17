#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Key 批量测试 · 多厂商分 Tab（终端感控制台）
支持：OpenAI / Claude / DeepSeek / Gemini / xAI / 通用(OpenAI兼容)
特性：主题(系统/深/浅) · 按结论筛选 · 拉取模型列表 · 导出
"""
import json
import re
import urllib.parse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VENDORS = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-5.6-sol",
        "models": ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5-pro", "gpt-5.5",
                   "gpt-5.4", "gpt-5.2", "gpt-5", "gpt-4o", "gpt-4.1", "o3", "o4-mini"],
        "auth": "bearer", "kind": "openai",
        "hint": "Bearer 鉴权；列模型 GET /models，对话 POST /chat/completions",
    },
    "claude": {
        "label": "Claude (Anthropic)",
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-opus-5",
        "models": ["claude-opus-5", "claude-sonnet-5", "claude-fable-5", "claude-mythos-5",
                   "claude-haiku-4-5", "claude-opus-4-5"],
        "auth": "x-api-key", "kind": "claude",
        "hint": "x-api-key + anthropic-version 鉴权；列模型 GET /models，对话 POST /messages",
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-v4-pro",
        "models": ["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-v4-flash-vision-exp",
                   "deepseek-reasoner", "deepseek-chat"],
        "auth": "bearer", "kind": "openai",
        "hint": "Bearer 鉴权（OpenAI 兼容）；官方模型 deepseek-v4-pro / deepseek-v4-flash",
    },
    "gemini": {
        "label": "Gemini (Google)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "gemini-3.5",
        "models": ["gemini-3.5", "gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.6-flash",
                   "gemini-3.1-pro", "gemini-3-pro", "gemini-2.5-pro"],
        "auth": "x-goog-api-key", "kind": "gemini",
        "hint": "x-goog-api-key 鉴权；列模型 GET /models，对话 POST /models/{m}:generateContent",
    },
    "generic": {
        "label": "通用 (OpenAI兼容)",
        "base_url": "",
        "default_model": "gpt-4o",
        "models": ["gpt-4o", "gpt-5.6-sol", "claude-opus-5", "deepseek-v4-pro", "gemini-3.5", "grok-4.6"],
        "auth": "bearer", "kind": "openai",
        "hint": "任意 OpenAI 兼容中转站/网关，Bearer 鉴权，自填基地址",
    },
    "xai": {
        "label": "xAI (Grok)",
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-4.6",
        "models": ["grok-4.6", "grok-4.5", "grok-4.3", "grok-4.20", "grok-4.20-beta-latest"],
        "auth": "bearer", "kind": "openai",
        "hint": "Bearer 鉴权（OpenAI 兼容）；列模型 GET /models，对话 POST /chat/completions",
    },
}

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Key 批量测试 · 控制台</title>
<style>
:root{
  --bg:#0b0d12; --surface:#12161f; --surface-2:#171c27;
  --border:#222a37; --border-strong:#2d3748;
  --ink:#e8edf5; --muted:#8a94a6; --faint:#5b6472;
  --accent:#2dd4bf; --accent-ink:#06231f; --accent-dim:rgba(45,212,191,.14);
  --ok:#34d399; --ok-dim:rgba(52,211,153,.14);
  --warn:#f5b041; --warn-dim:rgba(245,176,65,.14);
  --bad:#f4605f; --bad-dim:rgba(244,96,95,.14);
  --input-bg:#0d1117;
  --grid:rgba(255,255,255,.018);
  --glow1:rgba(45,212,191,.07); --glow2:rgba(245,176,65,.045);
  --mono:"JetBrains Mono","DejaVu Sans Mono",monospace;
  --sans:"Noto Sans CJK SC","DejaVu Sans",sans-serif;
}
:root[data-theme="light"]{
  --bg:#f4f6f9; --surface:#ffffff; --surface-2:#f1f3f7;
  --border:#e4e8ef; --border-strong:#d3dae4;
  --ink:#1a2230; --muted:#5c6675; --faint:#94a0b0;
  --accent:#0e9f8e; --accent-ink:#ffffff; --accent-dim:rgba(14,159,142,.13);
  --ok:#0b9f62; --ok-dim:rgba(11,159,98,.13);
  --warn:#b7791f; --warn-dim:rgba(183,121,31,.14);
  --bad:#d64545; --bad-dim:rgba(214,69,69,.13);
  --input-bg:#ffffff;
  --grid:rgba(15,23,42,.04);
  --glow1:rgba(14,159,142,.05); --glow2:rgba(183,121,31,.04);
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{font-family:var(--sans);background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(1200px 500px at 18% -10%,var(--glow1),transparent 60%),
  radial-gradient(900px 500px at 90% 0%,var(--glow2),transparent 55%),
  repeating-linear-gradient(0deg,var(--grid) 0 1px,transparent 1px 32px),
  repeating-linear-gradient(90deg,var(--grid) 0 1px,transparent 1px 32px)}
.app{position:relative;z-index:1;max-width:1400px;margin:0 auto;padding:22px 30px 60px}

header{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;gap:16px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:12px}
.logo-link{display:block;width:34px;height:34px;border-radius:9px;overflow:hidden;border:1px solid var(--border-strong)}
.logo{display:block;width:34px;height:34px;object-fit:cover;border-radius:8px;
  background:linear-gradient(135deg,var(--accent-dim),transparent);display:grid;place-items:center;
  font-family:var(--mono);font-weight:700;color:var(--accent);font-size:13px}
.wordmark{font-family:var(--mono);font-size:17px;font-weight:700;letter-spacing:.04em}
.wordmark .dim{color:var(--faint);font-weight:400}
.sub{color:var(--muted);font-size:12.5px;margin-top:2px}
.hdr-right{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.chip{font-family:var(--mono);font-size:11px;color:var(--muted);border:1px solid var(--border);
  border-radius:20px;padding:5px 11px;display:flex;align-items:center;gap:7px}
.chip .led{width:7px;height:7px;border-radius:50%;background:var(--ok);box-shadow:0 0 8px var(--ok)}
.theme-bar{display:flex;align-items:center;gap:8px}
.theme-bar .lbl{font-size:12px;color:var(--muted)}
.theme-seg{display:flex;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:2px;gap:2px}
.theme-btn{font-family:var(--mono);font-size:11.5px;color:var(--muted);background:none;border:none;
  padding:5px 10px;border-radius:6px;cursor:pointer}
.theme-btn.on{background:var(--accent);color:var(--accent-ink);font-weight:700}

.tabs{display:flex;gap:4px;border-bottom:1px solid var(--border);margin-bottom:20px;padding:0 2px;flex-wrap:wrap}
.tab{font-family:var(--mono);font-size:13px;color:var(--muted);background:none;border:none;
  padding:11px 16px 12px;cursor:pointer;position:relative;white-space:nowrap}
.tab:hover{color:var(--ink)}
.tab.active{color:var(--ink)}
.tab.active::after{content:"";position:absolute;left:12px;right:12px;bottom:-1px;height:2px;background:var(--accent);border-radius:2px 2px 0 0}
.tab .k{font-size:10px;color:var(--faint);margin-left:6px}

.layout{display:grid;grid-template-columns:376px 1fr;gap:20px;align-items:start}
@media(max-width:980px){.layout{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden}
.card-h{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--border)}
.card-h .t{font-family:var(--mono);font-size:11px;letter-spacing:.1em;color:var(--faint);text-transform:uppercase}
.card-b{padding:16px}

.field{margin-bottom:14px}
.field label{display:block;font-size:12px;color:var(--muted);margin-bottom:7px}
.field label .req{color:var(--faint)}
.input{display:flex;align-items:center;gap:8px;background:var(--input-bg);border:1px solid var(--border);
  border-radius:8px;padding:9px 12px}
.input:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-dim)}
.input input{flex:1;background:none;border:none;outline:none;color:var(--ink);font-family:var(--mono);font-size:12.5px}
.input .chev{color:var(--faint);font-size:11px}
.combo{position:relative;display:flex;align-items:center;background:var(--input-bg);border:1px solid var(--border);border-radius:8px}
.combo:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-dim)}
.combo input{flex:1;background:none;border:none;outline:none;color:var(--ink);font-family:var(--mono);font-size:12.5px;padding:9px 12px;min-width:0}
.combo-btn{background:none;border:none;color:var(--muted);padding:9px 12px;cursor:pointer;font-size:11px}
.combo-btn:hover{color:var(--accent)}
.combo-menu{position:absolute;top:calc(100% + 4px);left:0;right:0;background:var(--surface-2);border:1px solid var(--border-strong);border-radius:8px;max-height:260px;overflow-y:auto;display:none;z-index:50;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.combo-menu.open{display:block}
.combo-item{font-family:var(--mono);font-size:12px;padding:8px 12px;cursor:pointer;color:var(--ink)}
.combo-item:hover,.combo-item.sel{background:var(--accent-dim);color:var(--accent)}
.combo-menu .empty{padding:10px 12px;color:var(--faint);font-size:12px}
.probe{display:inline-block;font-family:var(--mono);font-size:11px;padding:2px 6px;border-radius:5px;margin:1px 3px 1px 0;border:1px solid var(--border)}
.probe.ok{color:var(--ok);border-color:var(--ok-dim);background:var(--ok-dim)}
.probe.warn{color:var(--warn);border-color:var(--warn-dim);background:var(--warn-dim)}
.probe.bad{color:var(--bad);border-color:var(--bad-dim);background:var(--bad-dim)}
textarea{width:100%;min-height:128px;background:var(--input-bg);border:1px solid var(--border);border-radius:8px;
  color:var(--ink);font-family:var(--mono);font-size:12px;line-height:1.75;padding:11px 12px;resize:vertical;outline:none}
textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-dim)}
.hint{font-size:11px;color:var(--faint);margin-top:6px}

.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.btn{font-family:var(--mono);font-size:12px;border-radius:8px;padding:9px 14px;cursor:pointer;
  border:1px solid transparent;display:inline-flex;align-items:center;gap:7px}
.btn.primary{background:var(--accent);color:var(--accent-ink);font-weight:700}
.btn.primary:hover{filter:brightness(1.08)}
.btn.ghost{background:transparent;border-color:var(--border-strong);color:var(--muted)}
.btn.ghost:hover{color:var(--ink);border-color:var(--accent)}
.btn.ghost:disabled{opacity:.45;cursor:not-allowed}
.toggle{display:flex;align-items:center;gap:9px;margin-top:16px;font-size:12.5px;color:var(--muted);cursor:pointer}
.switch{width:34px;height:19px;border-radius:20px;background:var(--border-strong);position:relative;flex:none}
.switch::after{content:"";position:absolute;top:2px;left:2px;width:15px;height:15px;border-radius:50%;background:var(--muted);transition:.15s}
.switch.on{background:var(--accent-dim)}
.switch.on::after{left:17px;background:var(--accent)}
.spin{display:none;margin-left:6px;color:var(--muted);font-family:var(--mono);font-size:12px}

.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:14px}
.stat{background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:12px 14px}
.stat .n{font-family:var(--mono);font-size:24px;font-weight:700;line-height:1.1}
.stat .l{font-size:11px;color:var(--faint);margin-top:4px}
.stat .n.ok{color:var(--ok)}.stat .n.warn{color:var(--warn)}.stat .n.bad{color:var(--bad)}.stat .n.plain{color:var(--ink)}

.filters{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:12px}
.filter-chip{font-family:var(--mono);font-size:11.5px;color:var(--muted);background:var(--surface-2);
  border:1px solid var(--border);border-radius:20px;padding:5px 12px;cursor:pointer}
.filter-chip.on{background:var(--accent-dim);color:var(--accent);border-color:var(--accent);font-weight:700}
.filter-chip .cnt{opacity:.6;margin-left:5px}

.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
thead th{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);
  font-weight:600;text-align:left;padding:11px 14px;border-bottom:1px solid var(--border);background:var(--surface-2);white-space:nowrap}
tbody td{padding:11px 14px;border-bottom:1px solid var(--border);vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:var(--accent-dim)}
.mono{font-family:var(--mono);font-size:12px}
.muted{color:var(--muted)}.faint{color:var(--faint)}
.key{color:var(--muted)}
.tag{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;border-radius:6px;padding:3px 8px;white-space:nowrap}
.tag .d{width:6px;height:6px;border-radius:50%}
.tag.ok{background:var(--ok-dim);color:var(--ok)}.tag.ok .d{background:var(--ok)}
.tag.warn{background:var(--warn-dim);color:var(--warn)}.tag.warn .d{background:var(--warn)}
.tag.bad{background:var(--bad-dim);color:var(--bad)}.tag.bad .d{background:var(--bad)}
.reply{color:var(--ink);font-size:12.5px}
.reply.dim{color:var(--muted)}
.empty{color:var(--faint);padding:26px;text-align:center;font-size:13px}
</style>
</head>
<body>
<div class="app">
  <header>
    <div class="brand">
      <a class="logo-link" href="https://jianlong.it/" aria-label="建龍网络官网"><img class="logo" src="/jianlong-logo-mark.png" alt="建龍网络"></a>
      <div>
        <div class="wordmark">KEY <span class="dim">TESTER</span></div>
        <div class="sub">多厂商 API Key 批量测试 · 控制台</div>
      </div>
    </div>
    <div class="hdr-right">
      <div class="theme-bar">
        <span class="lbl">主题</span>
        <div class="theme-seg" id="themeSeg">
          <button class="theme-btn" data-m="system">系统</button>
          <button class="theme-btn" data-m="dark">深色</button>
          <button class="theme-btn" data-m="light">浅色</button>
        </div>
      </div>
      <div class="chip"><span class="led"></span> 6 厂商 + 识别</div>
    </div>
  </header>

  <div class="tabs" id="tabs"></div>

  <div class="layout">
    <div class="card">
      <div class="card-h"><span class="t">配置 · CONFIG</span></div>
      <div class="card-b">
        <div class="field" id="urlField">
          <label>API 基地址</label>
          <div class="input"><input id="url"></div>
        </div>
        <div class="field" id="modelField">
          <label>模型</label>
          <div class="combo" id="combo">
            <input id="model" autocomplete="off">
            <button class="combo-btn" id="modelBtn" type="button">▾</button>
            <div class="combo-menu" id="modelMenu"></div>
          </div>
        </div>
        <div class="field">
          <label>Keys <span class="req">· 每行一个</span></label>
          <textarea id="keys" placeholder="sk-proj-...&#10;sk-ant-...&#10;AIza..."></textarea>
          <div class="hint" id="hint"></div>
        </div>
        <div class="actions">
          <button class="btn primary" id="btnRun">▶ 一键测试</button>
          <button class="btn ghost" id="btnFetchModels">拉取模型列表</button>
        </div>
        <div class="actions" style="margin-top:8px">
          <button class="btn ghost" id="btnExportCsv" disabled>导出 CSV</button>
          <button class="btn ghost" id="btnExportGood" disabled>导出可用 Key</button>
          <span class="spin" id="spin">测试中…</span>
        </div>
        <div class="toggle"><span class="switch" id="showFullSwitch"></span> 显示完整 Key</div>
      </div>
    </div>

    <div>
      <div class="stats" id="stats" style="display:none"></div>
      <div class="filters" id="filters"></div>
      <div class="card" id="resultCard" style="display:none">
        <div class="card-h"><span class="t">结果 · RESULTS</span><span class="t" id="resultMeta"></span></div>
        <div class="tbl-wrap">
          <table>
            <thead><tr><th>#</th><th>Key</th><th>认证</th><th>对话</th><th>详情 / 回复</th><th>结论</th></tr></thead>
            <tbody id="tbody"></tbody>
          </table>
        </div>
      </div>
      <div class="card" id="detectCard" style="display:none">
        <div class="card-h"><span class="t">未知 Key 检测 · DETECT</span><span class="t" id="detectMeta"></span></div>
        <div class="tbl-wrap">
          <table>
            <thead><tr><th>#</th><th>Key</th><th>归属厂商</th><th>官方接口 URL</th><th>对话</th><th>探测明细</th></tr></thead>
            <tbody id="detectBody"></tbody>
          </table>
        </div>
      </div>
      <div class="card" id="emptyCard"><div class="empty">粘贴 Key 后点「一键测试」，结果会显示在这里</div></div>
    </div>
  </div>
</div>

<script>
let VENDORS=[], activeV='', state={}, resultStore={}, cur=null, filter='全部', modelOptions=[];
const THEME_KEY='keytester_theme';
const CONCL_STYLE={'可用':'ok','无余额/配额':'warn','无权限':'bad','模型不存在':'warn','限流':'warn','认证失败':'bad','连接失败':'bad','不可用':'bad'};
const CONCL_ORDER=['可用','无余额/配额','无权限','模型不存在','限流','认证失败','连接失败','不可用'];
const STATE_STYLE={'通过':'ok','有效':'warn','失效':'bad'};

function themeMode(){return localStorage.getItem(THEME_KEY)||'system';}
function applyTheme(mode){
  localStorage.setItem(THEME_KEY,mode);
  const dark = mode==='system' ? window.matchMedia('(prefers-color-scheme: dark)').matches : (mode==='dark');
  document.documentElement.setAttribute('data-theme', dark?'dark':'light');
  document.querySelectorAll('.theme-btn').forEach(b=>b.classList.toggle('on', b.dataset.m===mode));
}

function maskKey(k){return k.length<=10?k.slice(0,3)+'***':k.slice(0,13)+'...'+k.slice(-4);}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function trunc(s,n){s=String(s==null?'':s);return s.length>n?s.slice(0,n)+'…':s;}
function parseKeys(raw){const seen=new Set(),o=[];for(const l of raw.split(/\r?\n/)){const k=l.trim();if(k&&!seen.has(k)){seen.add(k);o.push(k);}}return o;}

function switchTab(id){
  const isDetect=(id==='detect');
  activeV=id;
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.id==='tab-'+id));
  if(isDetect){
    if(!state[id])state[id]={url:'',model:'',keys:''};
    document.getElementById('keys').value=state[id].keys;
    document.getElementById('url').value=state[id].url;
    document.getElementById('urlField').style.display='';
    document.getElementById('modelField').style.display='none';
    document.getElementById('btnRun').textContent='⚡ 一键检测';
    document.getElementById('btnFetchModels').style.display='none';
    document.getElementById('btnExportCsv').disabled=true;
    document.getElementById('btnExportGood').disabled=true;
    document.getElementById('hint').textContent='粘贴 key（可多行），自动探测 OpenAI / Claude / DeepSeek / Gemini / xAI；识别第三方中转站 key 时，在上方填它的 API 基地址（如 https://xxx/v1）';
    document.getElementById('resultCard').style.display='none';
    document.getElementById('emptyCard').style.display='none';
    if(detectResults)renderDetect();else document.getElementById('detectCard').style.display='none';
    return;
  }
  document.getElementById('urlField').style.display='';
  document.getElementById('modelField').style.display='';
  document.getElementById('btnRun').textContent='▶ 一键测试';
  document.getElementById('btnFetchModels').style.display='';
  document.getElementById('detectCard').style.display='none';
  if(!state[id])state[id]={url:'',model:'',keys:''};
  const st=state[id];
  document.getElementById('url').value=st.url;
  document.getElementById('model').value=st.model;
  document.getElementById('keys').value=st.keys;
  const v=VENDORS.find(x=>x.id===id);
  modelOptions=[...(v.models||[])].filter(Boolean);
  refreshMenu('');
  document.getElementById('hint').textContent=v.hint||'';
  if(resultStore[id]){render(resultStore[id]);}
  else{cur=null;filter='全部';document.getElementById('stats').style.display='none';
    document.getElementById('resultCard').style.display='none';
    document.getElementById('filters').innerHTML='';
    document.getElementById('emptyCard').style.display='block';
    document.getElementById('btnExportCsv').disabled=true;
    document.getElementById('btnExportGood').disabled=true;}
}

async function run(){
  const st=state[activeV];
  const url=document.getElementById('url').value.trim();
  const model=document.getElementById('model').value.trim();
  const keys=parseKeys(document.getElementById('keys').value);
  if(!keys.length){alert('请至少输入一个 key');return;}
  if(!model){document.getElementById('hint').textContent='模型留空将自动探测可用模型';}
  const btn=document.getElementById('btnRun'),spin=document.getElementById('spin');
  btn.disabled=true;spin.style.display='inline';
  try{
    const r=await fetch('/api/test',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({vendor:activeV,url,model,keys})});
    const data=await r.json();
    resultStore[activeV]=data; filter='全部'; render(data);
    document.getElementById('btnExportCsv').disabled=false;
    document.getElementById('btnExportGood').disabled=!(data.results||[]).some(x=>x.usable);
  }catch(e){alert('请求失败：'+e.message);}
  finally{btn.disabled=false;spin.style.display='none';}
}

async function fetchModels(){
  const url=document.getElementById('url').value.trim();
  const keys=parseKeys(document.getElementById('keys').value);
  if(!keys.length){alert('请先粘贴至少一个 key');return;}
  document.getElementById('hint').textContent='拉取中…';
  const r=await fetch('/api/models',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({vendor:activeV,url,keys})});
  const d=await r.json();
  if(d.code===200&&d.models&&d.models.length){
    const seen=new Set(modelOptions);
    d.models.forEach(m=>{if(m&&!seen.has(m)){seen.add(m);modelOptions.push(m);}});
    refreshMenu('');
    openMenu();
    document.getElementById('hint').textContent='已获取 '+d.models.length+' 个模型，点右侧 ▾ 选择';
  }else{document.getElementById('hint').textContent='获取失败(code '+d.code+'): '+(d.err||'');}
}

function refreshMenu(q){
  const menu=document.getElementById('modelMenu');
  const model=document.getElementById('model');
  const qq=(q||'').trim().toLowerCase();
  const items=qq?modelOptions.filter(m=>m.toLowerCase().includes(qq)):modelOptions.slice();
  if(!items.length){menu.innerHTML='<div class="empty">无匹配 · 点「拉取模型列表」获取</div>';return;}
  menu.innerHTML='';
  items.forEach(m=>{
    const d=document.createElement('div');
    d.className='combo-item'+(m===model.value?' sel':'');
    d.textContent=m;
    d.onmousedown=e=>{e.preventDefault();model.value=m;closeMenu();};
    menu.appendChild(d);
  });
}
function openMenu(){document.getElementById('modelMenu').classList.add('open');}
function closeMenu(){document.getElementById('modelMenu').classList.remove('open');}

let detectResults=null;
async function runDetect(){
  const keys=parseKeys(document.getElementById('keys').value);
  if(!keys.length){alert('请先粘贴至少一个 key');return;}
  const url=document.getElementById('url').value.trim();
  const btn=document.getElementById('btnRun'),spin=document.getElementById('spin');
  btn.disabled=true;spin.style.display='inline';
  document.getElementById('hint').textContent=url?('检测中…（并行探测 5 家官方 + 自定义地址 '+url+'）'):'检测中…（并行探测 5 家官方接口）';
  try{
    const r=await fetch('/api/detect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({keys,url})});
    const d=await r.json();
    detectResults=d.results||[];
    renderDetect();
    document.getElementById('hint').textContent='检测完成：共 '+detectResults.length+' 把';
  }catch(e){alert('请求失败：'+e.message);}
  finally{btn.disabled=false;spin.style.display='none';}
}
function renderDetect(){
  document.getElementById('emptyCard').style.display='none';
  document.getElementById('detectCard').style.display='block';
  const rs=detectResults||[];
  const ok=rs.filter(x=>x.winner_state==='通过').length;
  const val=rs.filter(x=>x.winner_state==='有效').length;
  const un=rs.length-ok-val;
  document.getElementById('detectMeta').textContent='共 '+rs.length+' 把 · 可用 '+ok+' · 有效(受限) '+val+' · 未识别 '+un;
  const tb=document.getElementById('detectBody');tb.innerHTML='';
  rs.forEach((x,i)=>{
    const wc=x.winner_state==='通过'?'ok':(x.winner_state==='有效'?'warn':'bad');
    const win=x.winner?'<span class="tag '+wc+'"><span class="d"></span>'+esc(x.winner_label)+'</span>'
      :'<span class="tag bad"><span class="d"></span>未识别</span>';
    const url=x.winner_url?'<code class="mono">'+esc(x.winner_url)+'</code>':'<span class="mono faint">—</span>';
    const chat=x.winner_chat===200?'<span class="tag ok"><span class="d"></span>200</span>'
      :(x.winner_chat?'<span class="mono muted">'+x.winner_chat+'</span>':'<span class="mono faint">—</span>');
    const probes=(x.checks||[]).map(c=>{
      const cls=c.state==='通过'?'ok':(c.state==='有效'?'warn':'bad');
      const mdl=(c.model&&c.state!=='失效')?'·'+esc(c.model):'';
      return '<span class="probe '+cls+'">'+esc(c.label.split(' ')[0])+'·'+esc(c.state)+mdl+'</span>';
    }).join(' ');
    const det=x.detail?'<div class="reply dim">'+esc(trunc(x.detail,130))+'</div>':'';
    tb.insertAdjacentHTML('beforeend','<tr><td class="mono faint">'+String(i+1).padStart(2,'0')+'</td><td><span class="key">'+esc(x.masked)+'</span></td><td>'+win+'</td><td>'+url+'</td><td>'+chat+'</td><td>'+probes+det+'</td></tr>');
  });
}

function render(data){
  cur=data;
  document.getElementById('emptyCard').style.display='none';
  document.getElementById('stats').style.display='grid';
  document.getElementById('resultCard').style.display='block';
  const rs=data.results||[];
  const usable=rs.filter(r=>r.usable).length;
  const valid=rs.filter(r=>r.state!=='失效').length;
  const invalid=rs.length-valid;
  document.getElementById('stats').innerHTML=
    '<div class="stat"><div class="n plain">'+rs.length+'</div><div class="l">总 Key</div></div>'+
    '<div class="stat"><div class="n ok">'+usable+'</div><div class="l">可用</div></div>'+
    '<div class="stat"><div class="n warn">'+valid+'</div><div class="l">有效 key</div></div>'+
    '<div class="stat"><div class="n bad">'+invalid+'</div><div class="l">失效</div></div>';
  const v=VENDORS.find(x=>x.id===activeV);
  document.getElementById('resultMeta').textContent=(v?v.label:activeV)+' · '+(data.model||'');
  renderFilters(rs);
  renderTable();
}

function renderFilters(rs){
  const present={}; rs.forEach(r=>present[r.concl]=(present[r.concl]||0)+1);
  const tags=['全部'].concat(CONCL_ORDER.filter(c=>present[c]));
  if(!tags.includes(filter))filter='全部';
  const bar=document.getElementById('filters');bar.innerHTML='';
  tags.forEach(t=>{
    const b=document.createElement('button');
    b.className='filter-chip'+(t===filter?' on':'');
    const cnt = t==='全部'?rs.length:present[t];
    b.innerHTML=esc(t)+'<span class="cnt">'+cnt+'</span>';
    b.onclick=()=>{filter=t;renderFilters(rs);renderTable();};
    bar.appendChild(b);
  });
}

function renderTable(){
  const showFull=document.getElementById('showFullSwitch').classList.contains('on');
  const rows=cur.results.filter(r=>filter==='全部'||r.concl===filter);
  const tb=document.getElementById('tbody');tb.innerHTML='';
  rows.forEach((r,i)=>{
    const keyTxt=showFull?'<code class="mono">'+esc(r.key)+'</code>':'<span class="key">'+esc(r.masked)+'</span>';
    const ss=STATE_STYLE[r.state]||'bad';
    const auth='<span class="tag '+ss+'"><span class="d"></span>'+esc(r.state)+'</span>';
    const chat = r.usable
      ?'<span class="tag ok"><span class="d"></span>200</span>'
      :(r.chat_code==='ERR'?'<span class="tag bad">连接失败</span>':'<span class="mono muted">'+r.chat_code+'</span>');
    const cs=CONCL_STYLE[r.concl]||'bad';
    const concl='<span class="tag '+cs+'"><span class="d"></span>'+esc(r.concl)+'</span>';
    const detail=r.usable?'<span class="reply">'+esc(trunc(r.reply,140))+'</span>':'<span class="reply dim">'+esc(trunc(r.errmsg,140))+'</span>';
    tb.insertAdjacentHTML('beforeend','<tr><td class="mono faint">'+String(i+1).padStart(2,'0')+'</td><td>'+keyTxt+'</td><td>'+auth+'</td><td>'+chat+'</td><td>'+detail+'</td><td>'+concl+'</td></tr>');
  });
}

function download(name,content,mime){const b=new Blob([content],{type:mime});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;a.click();URL.revokeObjectURL(a.href);}
function ts(){return new Date().toISOString().slice(0,19).replace(/[-:T]/g,'');}
function exportCsv(){
  const data=resultStore[activeV];if(!data||!data.results.length)return;
  const lines=[['序号','Key','Key状态','对话码','结论','详情/回复'].join(',')];
  data.results.forEach((r,i)=>{lines.push([i+1,'"'+r.key+'"',r.state,r.chat_code,r.concl,'"'+(r.usable?r.reply:r.errmsg).replace(/"/g,'""').replace(/\n/g,' ')+'"'].join(','));});
  download(activeV+'-key-test-'+ts()+'.csv','\ufeff'+lines.join('\n'),'text/csv;charset=utf-8');
}
function exportGood(){
  const data=resultStore[activeV];if(!data)return;
  const good=(data.results||[]).filter(r=>r.usable).map(r=>r.key);
  if(!good.length){alert('没有可用 key');return;}
  download(activeV+'-usable-keys-'+ts()+'.txt',good.join('\n'),'text/plain;charset=utf-8');
}

async function init(){
  const d=await (await fetch('/api/vendors')).json();
  VENDORS=d.vendors;
  VENDORS.forEach(v=>{state[v.id]={url:v.base_url,keys:'',model:v.default_model};});
  const tabs=document.getElementById('tabs');
  VENDORS.forEach(v=>{const b=document.createElement('button');b.className='tab';b.id='tab-'+v.id;b.textContent=v.label;b.onclick=()=>switchTab(v.id);tabs.appendChild(b);});
  const db=document.createElement('button');db.className='tab';db.id='tab-detect';db.textContent='⚡ 未知 Key 检测';db.onclick=()=>switchTab('detect');tabs.appendChild(db);
  ['url','model','keys'].forEach(id=>document.getElementById(id).addEventListener('input',()=>{if(activeV==='detect'){state['detect'].keys=document.getElementById('keys').value;state['detect'].url=document.getElementById('url').value;return;}state[activeV][id]=document.getElementById(id).value;}));
  document.getElementById('btnRun').addEventListener('click',()=>{if(activeV==='detect')runDetect();else run();});
  document.getElementById('btnFetchModels').addEventListener('click',fetchModels);
  document.getElementById('modelBtn').addEventListener('click',e=>{e.stopPropagation();refreshMenu('');openMenu();});
  document.getElementById('model').addEventListener('focus',()=>{refreshMenu('');openMenu();});
  document.getElementById('model').addEventListener('input',()=>{refreshMenu(document.getElementById('model').value);openMenu();});
  document.addEventListener('click',e=>{if(!document.getElementById('combo').contains(e.target))closeMenu();});
  document.getElementById('btnExportCsv').addEventListener('click',exportCsv);
  document.getElementById('btnExportGood').addEventListener('click',exportGood);
  document.getElementById('showFullSwitch').addEventListener('click',e=>{e.currentTarget.classList.toggle('on');if(cur)renderTable();});
  document.getElementById('themeSeg').querySelectorAll('.theme-btn').forEach(b=>b.addEventListener('click',()=>applyTheme(b.dataset.m)));
  applyTheme(themeMode());
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if(themeMode()==='system')applyTheme('system');});
  switchTab(VENDORS[0].id);
}
init();
</script>
</body>
</html>
"""


def mask_key(k):
    if len(k) <= 10:
        return k[:3] + "***"
    return k[:13] + "..." + k[-4:]


def http_request(method, url, headers, body=None, timeout=60):
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    # Cloudflare 防护站（如 pojia.org）会拦 Python 默认 UA（403 code 1010），
    # 统一带浏览器 UA，否则后端代发探测对这些站点必失败。
    headers.setdefault("User-Agent",
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, {"raw": raw[:300]}
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode("utf-8", "replace"))
        except Exception:
            msg = {}
        return e.code, msg
    except urllib.error.URLError as e:
        return "ERR", {"error": {"message": "连接失败: %s" % e.reason}}
    except Exception as e:
        return "ERR", {"error": {"message": str(e)}}


def err_text(data):
    if not isinstance(data, dict):
        return str(data)
    e = data.get("error")
    if isinstance(e, dict):
        m = e.get("message")
        return m if m else str(e)[:200]
    if isinstance(e, str) and e:
        return e
    if data.get("message"):
        return str(data["message"])
    return str(data)[:200]


def auth_headers(vendor, key):
    a = vendor["auth"]
    if a == "x-api-key":
        return {"x-api-key": key, "anthropic-version": "2023-06-01"}
    if a == "x-goog-api-key":
        return {"x-goog-api-key": key}
    return {"Authorization": "Bearer " + key}


def normalize_base(vendor, url):
    """归一化 API 基地址，使带不带 /v1 后缀都能用。

    返回候选基址列表（按可能性排序），调用方依次尝试，第一个返回可用结果的胜出。
    - 用户填 https://xxx / https://xxx/ / https://xxx/v1 / https://xxx/v1/ 均可
    - 已带 /v1（或厂商专属后缀）时不重复追加，避免 /v1/v1 -> 404
    - 官方主机（api.openai.com 等）缺后缀时优先补 /v1，中转站则原样优先
    """
    u = (url or "").strip()
    if not u:
        return []
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    u = u.rstrip("/")

    suffix = "/v1" if vendor.get("kind") != "gemini" else "/v1beta"
    path = urllib.parse.urlparse(u).path.rstrip("/")
    segs = [s for s in path.split("/") if s]

    if segs and re.fullmatch(r"v\d+[a-z0-9]*", segs[-1]):
        return [u]                       # 已带版本后缀，原样用

    with_suffix, bare = u + suffix, u
    host = (urllib.parse.urlparse(u).hostname or "").lower()
    # 官方 API 主机通常必须带 /v1；中转站两种都试，原样优先
    official = host in ("api.openai.com", "api.anthropic.com", "api.deepseek.com",
                        "api.x.ai", "generativelanguage.googleapis.com")
    order = [with_suffix, bare] if official else [bare, with_suffix]
    return list(dict.fromkeys(order))


def is_missing_version_path(code, msg):
    """判断失败是否因为缺版本前缀（试另一个候选有用）。"""
    if code == 404:
        return True
    m = (msg or "").lower()
    return bool(re.search(r"not found|no route|invalid url|unknown url|不可用|not_found", m))


def pick_working_model(vendor, base, key, model_ids, limit=6):
    """在模型列表中按顺序找出真正能对话的模型。

    中转站的 /models 常列出该站并不真正支持的模型（如 pojia 列出全部 gpt-* 但实际 404），
    只取第一项会误判为不可用。这里依次试，第一个 200 的胜出。
    """
    # 优先试类似 chat/completion 的模型，跳过明显是图像/向量/语音的
    skip = re.compile(r"(image|embed|tts|whisper|audio|rerank|moderation|dall)", re.I)
    lead = [m for m in model_ids if not skip.search(m)]
    for m in (lead or model_ids)[:limit]:
        code, reply, errmsg = do_chat(vendor, base, key, m)
        if code == 200:
            return m, code, reply, errmsg
    return None, None, "", ""


def _model_or_path_fail(code, errmsg):
    """判断失败原因是否可能靠『换模型 / 换路径』解决（而不是 key 或余额问题）。"""
    if code == 404:
        return True
    m = (errmsg or "").lower()
    return bool(re.search(r"model .* not|not found|does not exist|unknown model|invalid model|no such model|not_found|no route", m))


def chat_with_fallback(vendor, base, key, model):
    """先按指定模型测；若失败且疑似『模型不存在/路径不对』（非鉴权、非限额），
    自动拉真实模型列表（带 /v1 兼容）挑一个能对话的模型重试。

    返回 (code, reply, errmsg, used_base, used_model)。
    """
    code, reply, errmsg = do_chat(vendor, base, key, model)
    used_base, used_model = base, model
    if code == 200 or is_invalid_key(code, errmsg) or not _model_or_path_fail(code, errmsg):
        return code, reply, errmsg, used_base, used_model
    mc, mids, _, auto_base = list_models_auto(vendor, base, key)
    if mc == 200 and mids and auto_base:
        picked, c2, r2, e2 = pick_working_model(vendor, auto_base, key, mids)
        if picked:
            return c2, r2, e2, auto_base, picked
    return code, reply, errmsg, used_base, used_model


def list_models(vendor, base, key):
    base = base.rstrip("/")
    code, data = http_request("GET", base + "/models", auth_headers(vendor, key), timeout=40)
    ids = []
    if code == 200:
        if vendor["kind"] == "gemini":
            for m in data.get("models", []):
                nm = m.get("name", "")
                ids.append(nm.split("/")[-1] if "/" in nm else nm)
        else:
            dl = data.get("data")
            if isinstance(dl, list):
                ids = [str(m.get("id", "")) for m in dl if m.get("id")]
        return code, ids, ""
    return code, ids, err_text(data)


def list_models_auto(vendor, url, key):
    """带 /v1 兼容的模型列表：依次尝试归一化候选地址。"""
    last = (404, [], "no candidate")
    for base in normalize_base(vendor, url):
        code, ids, err = list_models(vendor, base, key)
        if code == 200 and ids:
            return code, ids, err, base
        last = (code, ids, err)
        # 鉴权/额度类错误换个路径也一样，提前停
        if not is_missing_version_path(code, err):
            return code, ids, err, base
    return last[0], last[1], last[2], ""


def do_chat(vendor, base, key, model):
    base = base.rstrip("/")
    headers = auth_headers(vendor, key)
    text = "只用一句话证明你能正常对话"
    if vendor["kind"] == "gemini":
        code, data = http_request("POST", base + "/models/" + model + ":generateContent", headers,
                                  {"contents": [{"parts": [{"text": text}]}]})
        if code == 200:
            try:
                reply = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
            except Exception:
                reply = str(data)[:200]
            return 200, reply, ""
        return code, "", err_text(data)
    if vendor["kind"] == "claude":
        code, data = http_request("POST", base + "/messages", headers,
                                  {"model": model, "max_tokens": 64, "messages": [{"role": "user", "content": text}]})
        if code == 200:
            try:
                reply = "".join(b.get("text", "") for b in data.get("content", []))
            except Exception:
                reply = str(data)[:200]
            return 200, reply, ""
        return code, "", err_text(data)
    code, data = http_request("POST", base + "/chat/completions", headers,
                              {"model": model, "messages": [{"role": "user", "content": text}], "max_tokens": 64})
    if code == 200:
        try:
            reply = data["choices"][0]["message"]["content"]
        except Exception:
            reply = str(data)[:200]
        return 200, reply, ""
    return code, "", err_text(data)


def is_invalid_key(code, msg):
    m = (msg or "").lower()
    if code == 401:
        return True
    if re.search(r"api key (not valid|not provided|invalid)|invalid x-api-key|incorrect api key|authentication fail", m):
        return True
    if "unregistered callers" in m:
        return True
    return False


def conclude(usable, state, chat_code, errmsg):
    if usable:
        return "可用"
    if state == "失效":
        return "认证失败"
    m = (errmsg or "").lower()
    if re.search(r"credit|balance|quota|billing|no credits|insufficient|resource_exhausted", m):
        return "无余额/配额"
    if chat_code == 403:
        return "无权限"
    if chat_code == 404 or re.search(r"not found|does not exist|unknown model|model .* not", m):
        return "模型不存在"
    if chat_code == 429:
        return "限流"
    if chat_code == "ERR":
        return "连接失败"
    return "不可用"


def test_key(vendor, base, key, model):
    # 模型不存在 / 路径缺 /v1 时自动换用真实可用模型，避免误判为不可用
    chat_code, reply, errmsg, used_base, used_model = chat_with_fallback(vendor, base, key, model)
    if chat_code == 200:
        state, usable, auth_ok = "通过", True, True
    elif is_invalid_key(chat_code, errmsg):
        state, usable, auth_ok = "失效", False, False
    else:
        state, usable, auth_ok = "有效", False, True
    r = {
        "key": key, "masked": mask_key(key),
        "state": state, "auth_ok": auth_ok,
        "chat_code": chat_code, "usable": usable,
        "reply": reply, "errmsg": errmsg,
        "model": used_model, "base": used_base,
        "model_switched": bool(used_model and model and used_model != model),
    }
    r["concl"] = conclude(r["usable"], r["state"], r["chat_code"], r["errmsg"])
    return r


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML, "text/html; charset=utf-8")
        elif self.path == "/jianlong-logo-mark.png":
            try:
                with open("/opt/key-tester/jianlong-logo-mark.png", "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(data)
            except OSError:
                self._send(404, {"error": "logo not found"})
        elif self.path == "/api/vendors":
            self._send(200, {"vendors": [
                {"id": k, "label": v["label"], "base_url": v["base_url"],
                 "default_model": v["default_model"], "models": v["models"], "hint": v["hint"]}
                for k, v in VENDORS.items()]})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception:
            self._send(400, {"error": "bad json"})
            return
        vendor = VENDORS.get(payload.get("vendor", "openai")) or VENDORS["openai"]
        url = (payload.get("url") or vendor["base_url"]).strip()
        model = (payload.get("model") or vendor["default_model"]).strip()
        base = url.rstrip("/")

        if self.path == "/api/models":
            ks = [k.strip() for k in (payload.get("keys") or [payload.get("key")]) if k and str(k).strip()]
            ks = list(dict.fromkeys(ks))[:10]
            if not ks:
                self._send(400, {"error": "no key"})
                return
            code, models, err, used_base = 400, [], "no valid key", ""
            for key in ks:
                code, models, err, used_base = list_models_auto(vendor, url, key)
                if code == 200:
                    break
            self._send(200, {"code": code, "models": models, "err": err,
                             "tested": len(ks), "base": used_base or base})
            return

        if self.path == "/api/detect":
            keys = [k.strip() for k in (payload.get("keys") or []) if k and str(k).strip()]
            keys = list(dict.fromkeys(keys))[:100]
            if not keys:
                self._send(400, {"error": "no keys"})
                return
            probes = [("openai", VENDORS["openai"]), ("claude", VENDORS["claude"]),
                      ("deepseek", VENDORS["deepseek"]), ("gemini", VENDORS["gemini"]),
                      ("xai", VENDORS["xai"])]
            custom_url = (payload.get("url") or "").strip().rstrip("/")
            if custom_url:
                # 支持自定义中转站地址：额外加一个 OpenAI 兼容探针
                # input_url 保留用户原始输入，探测时由 normalize_base 兼容 /v1 有无
                probes.append(("custom", {**VENDORS["openai"], "input_url": custom_url,
                                          "label": "自定义 (OpenAI兼容)", "kind": "openai"}))

            def probe(t):
                kid, v, key = t
                # 全协议统一：带不带 /v1 自动归一化；默认模型不适用时自动挑真实可用模型
                in_url = v.get("input_url") or v["base_url"]
                base0 = (normalize_base(v, in_url) or [in_url])[0]
                code, reply, errmsg, used_base, used_model = chat_with_fallback(
                    v, base0, key, v["default_model"])
                used_base = used_base or base0
                if code == 200:
                    state = "通过"
                elif is_invalid_key(code, errmsg):
                    state = "失效"
                else:
                    state = "有效"
                return key, {"vendor": kid, "label": v["label"],
                             "url": used_base or v.get("input_url") or v["base_url"],
                             "model": used_model,
                             "state": state, "chat_code": code,
                             "reply": reply, "errmsg": errmsg}

            all_tasks = [(kid, v, k) for k in keys for kid, v in probes]
            with ThreadPoolExecutor(max_workers=10) as ex:
                pairs = list(ex.map(probe, all_tasks))
            by_key = {}
            for k, c in pairs:
                by_key.setdefault(k, []).append(c)
            results = []
            for key in keys:
                checks = by_key.get(key, [])
                winner = (next((c for c in checks if c["state"] == "通过"), None)
                          or next((c for c in checks if c["state"] == "有效"), None))
                if winner:
                    results.append({
                        "key": key, "masked": mask_key(key),
                        "winner": winner["vendor"], "winner_label": winner["label"],
                        "winner_url": winner["url"], "winner_state": winner["state"],
                        "winner_chat": winner["chat_code"], "winner_model": winner.get("model") or "",
                        "detail": (winner["reply"][:400] if winner["state"] == "通过" else winner["errmsg"][:400]),
                        "checks": [{"vendor": c["vendor"], "label": c["label"],
                                    "state": c["state"], "chat_code": c["chat_code"],
                                    "model": c.get("model") or ""} for c in checks],
                    })
                else:
                    results.append({
                        "key": key, "masked": mask_key(key),
                        "winner": "", "winner_label": "未识别", "winner_url": "",
                        "winner_state": "", "winner_chat": "",
                        "detail": "所有常见厂商均拒绝该 key，无法匹配官方接口",
                        "checks": [{"vendor": c["vendor"], "label": c["label"],
                                    "state": c["state"], "chat_code": c["chat_code"],
                                    "model": c.get("model") or ""} for c in checks],
                    })
            self._send(200, {"results": results, "tested": len(results)})
            return

        if self.path != "/api/test":
            self._send(404, {"error": "not found"})
            return

        keys = [k.strip() for k in (payload.get("keys") or []) if k and str(k).strip()]
        keys = list(dict.fromkeys(keys))[:1000]
        if not keys:
            self._send(400, {"error": "no keys"})
            return
        results = [None] * len(keys)
        # 归一化：带不带 /v1 都能用；先用首个 key 探出真正生效的基址
        cands = normalize_base(vendor, url)
        eff_base = cands[0] if cands else base
        if len(cands) > 1:
            code0, ids0, _, used0 = list_models_auto(vendor, url, keys[0])
            if code0 == 200 and used0:
                eff_base = used0
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(test_key, vendor, eff_base, k, model): i for i, k in enumerate(keys)}
            for fut in futs:
                results[futs[fut]] = fut.result()
        self._send(200, {
            "results": results,
            "summary": {"total": len(results), "usable": sum(1 for r in results if r["usable"]),
                        "auth_ok": sum(1 for r in results if r["auth_ok"])},
            "vendor": vendor["label"], "url": eff_base,
            "model": (results[0].get("model") or model) if results else model,
        })

    def log_message(self, fmt, *args):
        pass


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args()
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()