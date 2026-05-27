from flask import Flask, render_template_string, current_app, request, jsonify, redirect, url_for
import json
import os

app = Flask(__name__)

def load(f):
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}

def save(f, d):
    json.dump(d, open(f, 'w', encoding='utf-8'), indent=2)

def xp_for_level(level):
    return 5 * (level ** 2) + 50 * level + 100

def total_xp_for_level(level):
    return sum(xp_for_level(i) for i in range(level))

def get_level_from_xp(xp):
    level = 0
    while xp >= total_xp_for_level(level + 1):
        level += 1
        if level > 500: 
            break
    return level

def get_gid():
    bot = current_app.config.get('BOT')
    if bot and hasattr(bot, 'cached_data'):
        for key in ['moderation', 'levels', 'counting', 'smashkarts', 'story']:
            d = bot.cached_data.get(key, {})
            if d:
                return list(d.keys())[0]
    return None

def resolve_name(uid, lvl_data):
    bot = current_app.config.get('BOT')
    if uid in lvl_data and 'name' in lvl_data[uid]:
        return lvl_data[uid]['name']
    if bot:
        user = bot.get_user(int(uid))
        if user: 
            return user.display_name
    return f"User {uid}"

def render(route, title, desc, body, is_enabled=True):
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>{{ title }}</title>
      <link href="https://fonts.googleapis.com/css2?family=GG+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
      <style>
        :root { --b-dark: #1e1f22; --b-mid: #2b2d31; --b-light: #313338; --b-nav: #111214; --accent: #5865f2; --text: #f2f3f5; --sub: #b5bac1; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'GG Sans', sans-serif; }
        body { display: flex; height: 100vh; background: var(--b-dark); color: var(--text); overflow: hidden; }
        
        .sidebar { width: 260px; background: var(--b-nav); padding: 24px 12px; display: flex; flex-direction: column; gap: 4px; }
        .brand { font-size: 18px; font-weight: 700; padding: 0 12px 20px 12px; border-bottom: 1px solid #2e3035; margin-bottom: 16px; color: #fff; }
        .nav-item { display: flex; align-items: center; padding: 10px 12px; border-radius: 4px; color: var(--sub); text-decoration: none; font-size: 14px; font-weight: 500; transition: .15s; }
        .nav-item:hover { background: #35373c; color: #fff; }
        .nav-item.active { background: var(--accent); color: #fff; }
        
        .main { flex: 1; display: flex; flex-direction: column; height: 100vh; background: var(--b-dark); }
        .header { background: var(--b-mid); padding: 20px 32px; border-bottom: 1px solid #1f2023; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; font-weight: 700; color: #fff; }
        .header p { font-size: 14px; color: var(--sub); margin-top: 4px; }
        
        .content { flex: 1; padding: 32px; overflow-y: auto; }
        
        /* Disabled Module Wrapper Styles */
        fieldset[disabled] {
          opacity: 0.35;
          pointer-events: none;
          cursor: not-allowed;
        }
        
        .card { background: var(--b-mid); border-radius: 8px; border: 1px solid #232428; padding: 24px; margin-bottom: 24px; }
        .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #3f4248; padding-bottom: 16px; margin-bottom: 20px; }
        .card-header h3 { font-size: 18px; color: #fff; }
        .card-header p { font-size: 13px; color: var(--sub); margin-top: 2px; }
        
        /* Form Controls */
        .field { margin-bottom: 20px; }
        .field label { display: block; font-size: 12px; font-weight: 700; color: var(--sub); text-transform: uppercase; margin-bottom: 8px; }
        .field input, .field select, .field textarea { width: 100%; background: var(--b-dark); border: 1px solid #111214; padding: 10px; border-radius: 4px; color: #fff; font-size: 14px; }
        .field input:focus, .field select:focus, .field textarea:focus { border-color: var(--accent); outline: none; }
        
        /* Toggles */
        .toggle-row { display: flex; justify-content: space-between; align-items: center; padding: 16px 0; border-bottom: 1px solid #2e3035; }
        .toggle-row:last-child { border-bottom: none; }
        .toggle-info h4 { margin: 0; font-size: 15px; color: #fff; }
        .toggle-info p { margin: 4px 0 0 0; font-size: 13px; color: var(--sub); }
        .toggle { position: relative; display: inline-block; width: 48px; height: 26px; }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #4e5058; transition: .2s; border-radius: 34px; }
        .toggle-slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 4px; bottom: 4px; background-color: white; transition: .2s; border-radius: 50%; }
        input:checked + .toggle-slider { background-color: #23a55a; }
        input:checked + .toggle-slider:before { transform: translateX(22px); }
        
        /* Grid Layout Utilities */
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .grid-blocks { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
        .block-item { background: var(--b-dark); border: 1px solid #111214; padding: 16px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }
        
        /* Leaderboards & Lists */
        .lb-row { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: var(--b-light); border-radius: 4px; margin-bottom: 8px; }
        .lb-name { display: flex; align-items: center; font-size: 14px; }
        .lb-val { font-size: 14px; color: var(--sub); font-weight: 600; }
        .lb-empty { text-align: center; color: var(--sub); padding: 20px; font-size: 14px; }
        
        .btn { display: inline-block; background: var(--accent); color: #fff; border: none; padding: 10px 20px; border-radius: 4px; font-size: 14px; font-weight: 500; cursor: pointer; transition: .15s; text-decoration: none; }
        .btn:hover { background: #4752c4; }
        .btn-danger { background: #ed4245; }
        .btn-danger:hover { background: #c03b3e; }
        .btn-secondary { background: #4e5058; }
        .btn-secondary:hover { background: #6d6f78; }
        .btn-save-row { display: flex; justify-content: flex-end; margin-top: 12px; gap: 10px; }
        
        .section-title { font-size: 12px; font-weight: 700; color: var(--sub); text-transform: uppercase; margin: 24px 0 12px 0; letter-spacing: 0.5px; }
      </style>
    </head>
    <body>
      <div class="sidebar">
        <div class="brand">👑 Admin Panel</div>
        <a href="/moderation" class="nav-item {% if route=='moderation' %}active{% endif %}">🛡️ Moderation</a>
        <a href="/levels" class="nav-item {% if route=='levels' %}active{% endif %}">⭐ Leveling System</a>
        <a href="/counting" class="nav-item {% if route=='counting' %}active{% endif %}">🔢 Counting Game</a>
        <a href="/qotd" class="nav-item {% if route=='qotd' %}active{% endif %}">❓ Question Of The Day</a>
        <a href="/birthdays" class="nav-item {% if route=='birthdays' %}active{% endif %}">📅 Birthdays</a>
        <a href="/ai-settings" class="nav-item {% if route=='ai-settings' %}active{% endif %}">🤖 AI Assistant</a>
        <a href="/smashkarts" class="nav-item {% if route=='smashkarts' %}active{% endif %}">🏎️ Smash Karts</a>
        <a href="/story" class="nav-item {% if route=='story' %}active{% endif %}">📖 Story Mode</a>
      </div>
      <div class="main">
        <div class="header">
          <div>
            <h1>{{ title }}</h1>
            <p>{{ desc }}</p>
          </div>
          <div>
            <button class="btn btn-secondary" style="background:#da373c; font-weight:600;" onclick="resetModule('{{ route }}')">Reset to Default</button>
            <button class="btn" style="background: {% if is_enabled %}#4e5058{% else %}#23a55a{% endif %}; font-weight:600; margin-left:8px;" onclick="toggleModule('{{ route }}', {{ 'true' if is_enabled else 'false' }})">
              {% if is_enabled %}Disable{% else %}Enable{% endif %}
            </button>
          </div>
        </div>
        <div class="content">
          <fieldset id="global-module-fieldset" style="border:none; padding:0; margin:0;" {% if not is_enabled %}disabled{% endif %}>
            {{ body|safe }}
          </fieldset>
        </div>
      </div>

      <script>
        function toggleModule(route, currentStatus) {
          fetch('/api/module/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ route: route, enabled: !currentStatus })
          }).then(() => location.reload());
        }
        function resetModule(route) {
          if (confirm('Сигурен ли си, че искаш да занулиш настройките на този модул по подразбиране?')) {
            fetch('/api/module/reset', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ route: route })
            }).then(() => location.reload());
          }
        }
      </script>
    </body>
    </html>
    """, route=route, title=title, desc=desc, body=body, is_enabled=is_enabled)

# ══════════════════════════════════════════════════════════
#  GLOBAL MODULE STATE SYNC CONTROL
# ══════════════════════════════════════════════════════════
@app.route('/api/module/toggle', methods=['POST'])
def api_module_toggle():
    data = request.json
    route = data.get('route')
    status = data.get('enabled')
    gid = get_gid() or 'default'
    
    if route == 'counting':
        c_cfg = load('counting.json')
        c_cfg.setdefault(gid, {})['enabled'] = status
        save('counting.json', c_cfg)
    elif route in ['qotd', 'birthdays']:
        cfg = load('config.json')
        cfg.setdefault(gid, {}).setdefault(route, {})['enabled'] = status
        save('config.json', cfg)
    else:
        cfg = load('config.json')
        key = 'ai_enabled' if route == 'ai-settings' else f"{route}_enabled"
        cfg.setdefault(gid, {})[key] = status
        save('config.json', cfg)
        
    return jsonify({'ok': True})

@app.route('/api/module/reset', methods=['POST'])
def api_module_reset():
    data = request.json
    route = data.get('route')
    gid = get_gid() or 'default'
    
    if route == 'counting':
        c_cfg = load('counting.json')
        c_cfg[gid] = {"count": 0, "high_score": 0, "enabled": False}
        save('counting.json', c_cfg)
    elif route in ['qotd', 'birthdays']:
        cfg = load('config.json')
        if gid in cfg and route in cfg[gid]:
            cfg[gid][route] = {"enabled": False}
        save('config.json', cfg)
    else:
        cfg = load('config.json')
        if gid in cfg:
            keys = []
            if route == 'moderation': keys = ['automod_enabled', 'block_invites', 'log_channel', 'banned_words', 'moderation_enabled']
            elif route == 'levels': keys = ['enable_levelup_message', 'enable_voice_xp', 'levelup_type', 'level_channel', 'levelup_message', 'levels_enabled']
            elif route == 'ai-settings': keys = ['ai_enabled', 'ai_reply_on_mention', 'ai_auto_emojis']
            for k in keys: cfg[gid].pop(k, None)
        save('config.json', cfg)
        
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
#  MODERATION PAGE
# ══════════════════════════════════════════════════════════
@app.route('/')
@app.route('/moderation')
def moderation():
    gid = get_gid() or 'default'
    cfg = load('config.json').get(gid, {})
    
    is_enabled = cfg.get('moderation_enabled', True)
    automod_on = 'checked' if cfg.get('automod_enabled', False) else ''
    invite_block_on = 'checked' if cfg.get('block_invites', False) else ''
    banned_words = cfg.get('banned_words', "")
    log_channel = cfg.get('log_channel', "")
    
    body = f"""
    <form id="modForm" onsubmit="saveMod(event)">
    <div class="card">
      <div class="card-header"><div><h3>Auto-Moderation</h3><p>Configure automated filter rules</p></div></div>
      <div class="card-body">
        <div class="toggle-row">
          <div class="toggle-info"><h4>Enable Word Filter (AutoMod)</h4><p>Scan and delete messages containing blacklisted phrases</p></div>
          <label class="toggle"><input type="checkbox" id="automod_enabled" {automod_on}> <span class="toggle-slider"></span></label>
        </div>
        <div class="toggle-row">
          <div class="toggle-info"><h4>Block Server Invites</h4><p>Automatically remove raw Discord server invitation links</p></div>
          <label class="toggle"><input type="checkbox" id="block_invites" {invite_block_on}> <span class="toggle-slider"></span></label>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><div><h3>Logging & Blacklists</h3><p>Manage system logging channels and terms</p></div></div>
      <div class="card-body">
        <div class="field"><label>Mod Log Channel ID</label><input type="text" id="log_channel" value="{log_channel}" placeholder="123456789012345678"></div>
        <div class="field"><label>Banned Words List (comma separated)</label><textarea id="banned_words" rows="3" placeholder="badword1, badword2, toxic">{banned_words}</textarea></div>
      </div>
    </div>
    <div class="btn-save-row"><button type="submit" class="btn btn-primary">Save Moderation Config</button></div>
    </form>

    <div id="toast_mod" style="display:none;position:fixed;bottom:24px;right:24px;background:#23a55a;color:#fff;padding:12px 20px;border-radius:6px;font-weight:600;font-size:14px;z-index:9999;">✅ Moderation configs saved successfully!</div>

    <script>
    function saveMod(e){{
      e.preventDefault();
      fetch('/api/moderation/save', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          automod_enabled: document.getElementById('automod_enabled').checked,
          block_invites: document.getElementById('block_invites').checked,
          log_channel: document.getElementById('log_channel').value,
          banned_words: document.getElementById('banned_words').value
        }})
      }}).then(() => {{
         var t = document.getElementById('toast_mod'); t.style.display='block'; setTimeout(()=>t.style.display='none',2500);
      }});
    }}
    </script>
    """
    return render('moderation', '🛡️ Moderation Settings', 'Control automod configurations, blacklisted word definitions, and execution protocols', body, is_enabled=is_enabled)

@app.route('/api/moderation/save', methods=['POST'])
def api_moderation_save():
    gid = get_gid() or 'default'
    cfg = load('config.json')
    cfg.setdefault(gid, {}).update(request.json)
    save('config.json', cfg)
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
#  LEVELING PAGE
# ══════════════════════════════════════════════════════════
@app.route('/levels')
def levels():
    gid = get_gid() or 'default'
    cfg = load('config.json').get(gid, {})
    
    is_enabled = cfg.get('levels_enabled', True)
    lvl_msg_on = 'checked' if cfg.get('enable_levelup_message', True) else ''
    vc_xp_on = 'checked' if cfg.get('enable_voice_xp', True) else ''
    
    type_opt = cfg.get('levelup_type', 'channel')
    opts = f"""
    <option value="channel" {'selected' if type_opt=='channel' else ''}>Specific Channel</option>
    <option value="current" {'selected' if type_opt=='current' else ''}>Current Channel</option>
    <option value="dm" {'selected' if type_opt=='dm' else ''}>Direct Message (DM)</option>
    <option value="disabled" {'selected' if type_opt=='disabled' else ''}>Disabled</option>
    """
    
    msg_val = cfg.get('levelup_message', "GG {{user.mention}}! You just leveled up to **Level {{level}}**!")
    ch_val = cfg.get('level_channel', "")

    lvl_data = load('levels.json').get(gid, {})
    sorted_users = sorted(lvl_data.items(), key=lambda x: x[1].get('xp', 0) if isinstance(x[1], dict) else x[1], reverse=True)[:10]
    
    lb_rows = ""
    for rank, (uid, data) in enumerate(sorted_users, 1):
        xp = data.get('xp', 0) if isinstance(data, dict) else data
        lvl = get_level_from_xp(xp)
        name = resolve_name(uid, lvl_data)
        lb_rows += f"""
        <div class="lb-row">
            <div class="lb-name"><b>#{rank}</b> &nbsp; {name}</div>
            <div class="lb-val">Lvl {lvl} &nbsp;<span style="color:#4e5058;font-weight:normal;">({xp} XP)</span></div>
        </div>"""
    if not lb_rows:
        lb_rows = '<div class="lb-empty">No level data available yet.</div>'

    body = f"""
    <form id="lvlForm" onsubmit="saveLvl(event)">
    <div class="card">
      <div class="card-header"><div><h3>General Settings</h3><p>Configure automated level alerts and behaviors</p></div></div>
      <div class="card-body">
        <div class="toggle-row">
          <div class="toggle-info"><h4>Level Up Messages</h4><p>Enable announcements when server members level up</p></div>
          <label class="toggle"><input type="checkbox" id="enable_levelup_message" {lvl_msg_on}> <span class="toggle-slider"></span></label>
        </div>
        <div class="toggle-row">
          <div class="toggle-info"><h4>Voice Channel XP</h4><p>Award XP passively to members active in voice chats</p></div>
          <label class="toggle"><input type="checkbox" id="enable_voice_xp" {vc_xp_on}> <span class="toggle-slider"></span></label>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><div><h3>Alert Behavior & Templates</h3><p>Customize where and how leveling up is displayed</p></div></div>
      <div class="card-body">
        <div class="field"><label>Alert Destination</label><select id="levelup_type">{opts}</select></div>
        <div class="field"><label>Target Channel ID (Only if Specific Channel is active)</label><input type="text" id="level_channel" value="{ch_val}" placeholder="123456789012345678"></div>
        <div class="field"><label>Custom Announcement Message</label><textarea id="levelup_message" rows="3">{msg_val}</textarea></div>
      </div>
    </div>
    <div class="btn-save-row"><button type="submit" class="btn btn-primary">Save Configuration</button></div>
    </form>

    <div class="card" style="margin-top:24px">
      <div class="card-header"><h3>🏆 Server Top 10 Leaderboard</h3></div>
      <div class="card-body">{lb_rows}</div>
    </div>

    <div id="toast" style="display:none;position:fixed;bottom:24px;right:24px;background:#23a55a;color:#fff;padding:12px 20px;border-radius:6px;font-weight:600;font-size:14px;z-index:9999;">✅ Leveling configs saved successfully!</div>

    <script>
    function saveLvl(e){{
      e.preventDefault();
      fetch('/api/levels/save', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          enable_levelup_message: document.getElementById('enable_levelup_message').checked,
          enable_voice_xp: document.getElementById('enable_voice_xp').checked,
          levelup_type: document.getElementById('levelup_type').value,
          level_channel: document.getElementById('level_channel').value,
          levelup_message: document.getElementById('levelup_message').value
        }})
      }}).then(() => {{
         var t = document.getElementById('toast'); t.style.display='block'; setTimeout(()=>t.style.display='none',2500);
      }});
    }}
    </script>
    """
    return render('levels', '⭐ Leveling System', 'Manage configurations and track active user XP records', body, is_enabled=is_enabled)

@app.route('/api/levels/save', methods=['POST'])
def api_levels_save():
    gid = get_gid() or 'default'
    cfg = load('config.json')
    cfg.setdefault(gid, {}).update(request.json)
    save('config.json', cfg)
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
#  COUNTING GAME PAGE
# ══════════════════════════════════════════════════════════
@app.route('/counting')
def counting():
    gid = get_gid() or 'default'
    c_data = load('counting.json').get(gid, {})
    
    is_enabled = c_data.get('enabled', False)
    current_count = c_data.get('count', 0)
    high_score = c_data.get('high_score', 0)
    
    counting_on = 'checked' if is_enabled else ''
    same_user_on = 'checked' if c_data.get('allow_same_user', False) else ''
    shame_role_on = 'checked' if c_data.get('shame_role', False) else ''
    delete_invalid_on = 'checked' if c_data.get('delete_invalid', False) else ''
    
    ch_val = c_data.get('channel', "")
    shame_name_val = c_data.get('shame_role_name', "💀 Count Ruiner")

    body = f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px;">
      <div class="card" style="margin:0; text-align:center;">
        <h4 style="color:#b5bac1;text-transform:uppercase;font-size:12px;letter-spacing:1px;">Current Counter</h4>
        <h1 style="font-size:48px;color:#5865f2;margin-top:10px;">{current_count}</h1>
      </div>
      <div class="card" style="margin:0; text-align:center;">
        <h4 style="color:#b5bac1;text-transform:uppercase;font-size:12px;letter-spacing:1px;">Server High Score</h4>
        <h1 style="font-size:48px;color:#23a55a;margin-top:10px;">{high_score}</h1>
      </div>
    </div>

    <form id="countingForm" onsubmit="saveCounting(event)">
    <div class="card">
      <div class="card-header"><div><h3>Game Execution Channels</h3><p>Configure channel binding and system automation state</p></div></div>
      <div class="card-body">
        <div class="toggle-row">
          <div class="toggle-info"><h4>Enable Counting Game</h4><p>Toggle the mathematics simulation module status</p></div>
          <label class="toggle"><input type="checkbox" id="counting_enabled" {counting_on}> <span class="toggle-slider"></span></label>
        </div>
        <div class="field" style="margin-top:20px;">
          <label>Counting Channel ID</label>
          <input type="text" id="counting_channel" value="{ch_val}" placeholder="123456789012345678">
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><div><h3>Gameplay & Restriction Mechanics</h3><p>Manage restriction logic and anti-spam protocols</p></div></div>
      <div class="card-body">
        <div class="toggle-row">
          <div class="toggle-info"><h4>Allow Consecutive Counting</h4><p>Can a single individual submit two values in a row?</p></div>
          <label class="toggle"><input type="checkbox" id="allow_same_user" {same_user_on}> <span class="toggle-slider"></span></label>
        </div>
        <div class="toggle-row">
          <div class="toggle-info"><h4>Enforce Shame Mute (Block on Fail)</h4><p>Give shame role and block user from counting until removed</p></div>
          <label class="toggle"><input type="checkbox" id="shame_role" {shame_role_on}> <span class="toggle-slider"></span></label>
        </div>
        <div class="toggle-row">
          <div class="toggle-info"><h4>Auto-Clean Chat (Delete Invalid Messages)</h4><p>Instantly remove general chatter or wrong submissions to keep channel clean</p></div>
          <label class="toggle"><input type="checkbox" id="delete_invalid" {delete_invalid_on}> <span class="toggle-slider"></span></label>
        </div>
        
        <div class="field" style="margin-top:20px;">
          <label>Shame Role Designation Name</label>
          <input type="text" id="shame_role_name" value="{shame_name_val}" placeholder="💀 Count Ruiner">
        </div>
      </div>
    </div>
    
    <div class="btn-save-row"><button type="submit" class="btn btn-primary">Save Counting Configurations</button></div>
    </form>
    <div id="toast_count" style="display:none;position:fixed;bottom:24px;right:24px;background:#23a55a;color:#fff;padding:12px 20px;border-radius:6px;font-weight:600;font-size:14px;z-index:9999;">✅ Counting configs updated!</div>
    <script>
    function saveCounting(e){{
      e.preventDefault();
      fetch('/api/counting/save', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          enabled: document.getElementById('counting_enabled').checked,
          channel: document.getElementById('counting_channel').value,
          allow_same_user: document.getElementById('allow_same_user').checked,
          shame_role: document.getElementById('shame_role').checked,
          delete_invalid: document.getElementById('delete_invalid').checked,
          shame_role_name: document.getElementById('shame_role_name').value
        }})
      }}).then(() => {{
         var t = document.getElementById('toast_count'); t.style.display='block'; setTimeout(()=>t.style.display='none',2500);
      }});
    }}
    </script>
    """
    return render('counting', '🔢 Counting System', 'Real-time synchronization data tracking counting parameters', body, is_enabled=is_enabled)

@app.route('/api/counting/save', methods=['POST'])
def api_counting_save():
    gid = get_gid() or 'default'
    cfg = load('counting.json')
    cfg.setdefault(gid, {}).update(request.json)
    save('counting.json', cfg)
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
#  QUESTION OF THE DAY (QOTD) PAGE
# ══════════════════════════════════════════════════════════
@app.route('/qotd')
def qotd():
    gid = get_gid() or 'default'
    cfg = load('config.json').get(gid, {}).get('qotd', {})
    
    is_enabled = cfg.get('enabled', True)
    channel = cfg.get('channel', '')
    roles = cfg.get('roles', '')
    private_mode = 'checked' if cfg.get('private_mode', False) else ''
    embed_enabled = 'checked' if cfg.get('embed_enabled', True) else ''
    
    author = cfg.get('author', '❓ Question Of The Day')
    thumb = cfg.get('thumbnail', '')
    msg_content = cfg.get('message', "It is {day}, and time for a new daily question for you all to answer! If you would like to participate, check the question below, and feel free to leave any comments and replies in the thread below this post. The question of today is:\\n\\n\"{question}\"")
    img_url = cfg.get('image_url', '')
    footer = cfg.get('footer', 'Please leave your replies in the thread attached to this message!')
    color = cfg.get('color', '#f45142')
    
    thread_name = cfg.get('thread_name', '💬 Leave your replies here!')
    duration = cfg.get('duration', 'One Day')
    slowmode = cfg.get('slowmode', '0')

    body = f"""
    <form id="qotdForm" onsubmit="saveQotd(event)">
      <div class="section-title">Question of the day</div>
      <h3>Main Settings</h3>
      <br>
      <div class="card">
        <div class="field">
          <label>QOTD Channel</label>
          <input type="text" id="qotd_channel" value="{channel}" placeholder="Select Channel ID">
        </div>
        <div class="field">
          <label>Mentioned Roles</label>
          <input type="text" id="qotd_roles" value="{roles}" placeholder="Add Role IDs (comma separated)">
        </div>
        <div class="toggle-row">
          <div class="toggle-info"><h4>Private Mode</h4><p>When private mode is enabled, only people with the mentioned roles will have access to the thread to send replies.</p></div>
          <label class="toggle"><input type="checkbox" id="qotd_private" {private_mode}> <span class="toggle-slider"></span></label>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div><h3>QOTD Announcement Message</h3><p>This embed or plain text message will be sent every day to prompt your members.</p></div>
          <label class="toggle"><input type="checkbox" id="qotd_embed" {embed_enabled}> <span class="toggle-slider"></span></label>
        </div>
        <div class="grid-2">
          <div class="field"><label>Author</label><input type="text" id="qotd_author" value="{author}"></div>
          <div class="field"><label>Thumbnail URL</label><input type="text" id="qotd_thumb" value="{thumb}"></div>
        </div>
        <div class="field">
          <label>Message Text ({'{question}'} and {'{day}'} variables supported)</label>
          <textarea id="qotd_msg" rows="5">{msg_content}</textarea>
        </div>
        <div class="field"><label>Image URL</label><input type="text" id="qotd_img" value="{img_url}"></div>
        <div class="field"><label>Footer</label><input type="text" id="qotd_footer" value="{footer}"></div>
        <div class="field" style="width: 150px;"><label>Embed Color</label><input type="color" id="qotd_color" value="{color}"></div>
      </div>

      <div class="card">
        <div class="field">
          <label>Created Thread Name</label>
          <input type="text" id="qotd_thread_name" value="{thread_name}">
        </div>
      </div>

      <div class="card">
        <div class="field">
          <label>Thread Archive Duration</label>
          <select id="qotd_duration">
            <option value="One Day" {"selected" if duration == "One Day" else ""}>One Day</option>
            <option value="Three Days" {"selected" if duration == "Three Days" else ""}>Three Days</option>
            <option value="One Week" {"selected" if duration == "One Week" else ""}>One Week</option>
          </select>
        </div>
      </div>

      <div class="card">
        <div class="field">
          <label>Thread Slowmode (in seconds)</label>
          <input type="number" id="qotd_slowmode" value="{slowmode}">
        </div>
      </div>

      <div class="btn-save-row"><button type="submit" class="btn btn-primary">Save QOTD Config</button></div>
    </form>
    <div id="toast_qotd" style="display:none;position:fixed;bottom:24px;right:24px;background:#23a55a;color:#fff;padding:12px 20px;border-radius:6px;font-weight:600;font-size:14px;z-index:9999;">✅ QOTD configuration saved!</div>
    <script>
    function saveQotd(e){{
      e.preventDefault();
      fetch('/api/qotd/save', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          enabled: true,
          channel: document.getElementById('qotd_channel').value,
          roles: document.getElementById('qotd_roles').value,
          private_mode: document.getElementById('qotd_private').checked,
          embed_enabled: document.getElementById('qotd_embed').checked,
          author: document.getElementById('qotd_author').value,
          thumbnail: document.getElementById('qotd_thumb').value,
          message: document.getElementById('qotd_msg').value,
          image_url: document.getElementById('qotd_img').value,
          footer: document.getElementById('qotd_footer').value,
          color: document.getElementById('qotd_color').value,
          thread_name: document.getElementById('qotd_thread_name').value,
          duration: document.getElementById('qotd_duration').value,
          slowmode: document.getElementById('qotd_slowmode').value
        }})
      }}).then(() => {{
         var t = document.getElementById('toast_qotd'); t.style.display='block'; setTimeout(()=>t.style.display='none',2500);
      }});
    }}
    </script>
    """
    return render('qotd', 'Main Settings', 'Boost the engagement of your server with daily questions to answer!', body, is_enabled=is_enabled)

@app.route('/api/qotd/save', methods=['POST'])
def api_qotd_save():
    gid = get_gid() or 'default'
    cfg = load('config.json')
    cfg.setdefault(gid, {}).setdefault('qotd', {}).update(request.json)
    save('config.json', cfg)
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
#  BIRTHDAYS MODULE PAGE
# ══════════════════════════════════════════════════════════
@app.route('/birthdays')
def birthdays():
    gid = get_gid() or 'default'
    cfg = load('config.json').get(gid, {}).get('birthdays', {})
    
    is_enabled = cfg.get('enabled', True)
    tz = cfg.get('timezone', 'UTC±0:00 [London]')
    time_send = cfg.get('time', '12:00 - 12 PM [Midday]')
    save_year = cfg.get('save_year', 'Enabled')
    color = cfg.get('embed_color', '#f45142')
    
    custom_card = 'checked' if cfg.get('custom_card', False) else ''
    send_msg = 'checked' if cfg.get('send_msg', True) else ''
    add_role = 'checked' if cfg.get('add_role', False) else ''
    enable_showcase = 'checked' if cfg.get('enable_showcase', True) else ''
    
    admin_roles = cfg.get('admin_roles', '')
    ch_restrict = cfg.get('ch_restrict', 'No channel restrictions')
    role_restrict = cfg.get('role_restrict', 'No role restrictions')
    
    cmd_set = 'checked' if cfg.get('cmd_set', True) else ''
    cmd_remove = 'checked' if cfg.get('cmd_remove', True) else ''
    cmd_view = 'checked' if cfg.get('cmd_view', True) else ''
    cmd_upcoming = 'checked' if cfg.get('cmd_upcoming', True) else ''
    cmd_showcase = 'checked' if cfg.get('cmd_showcase', True) else ''
    cmd_manage = 'checked' if cfg.get('cmd_manage', True) else ''
    
    evt_handler = 'checked' if cfg.get('evt_handler', True) else ''
    evt_leaves = 'checked' if cfg.get('evt_leaves', True) else ''

    body = f"""
    <form id="bdayForm" onsubmit="saveBirthdays(event)">
      <div class="section-title">Birthdays</div>
      <h3>General Settings</h3>
      <br>
      <div class="card">
        <div class="field">
          <label>Timezone</label>
          <select id="bd_tz">
            <option value="UTC±0:00 [London]" {"selected" if tz=="UTC±0:00 [London]" else ""}>UTC±0:00 [London]</option>
            <option value="UTC+2:00 [Sofia]" {"selected" if tz=="UTC+2:00 [Sofia]" else ""}>UTC+2:00 [Sofia]</option>
          </select>
        </div>
        <div class="field">
          <label>Time</label>
          <select id="bd_time">
            <option value="12:00 - 12 PM [Midday]" {"selected" if time_send=="12:00 - 12 PM [Midday]" else ""}>12:00 - 12 PM [Midday]</option>
            <option value="09:00 - 9 AM [Morning]" {"selected" if time_send=="09:00 - 9 AM [Morning]" else ""}>09:00 - 9 AM [Morning]</option>
          </select>
        </div>
        <div class="field">
          <label>Save Birth Year</label>
          <select id="bd_save_year">
            <option value="Enabled" {"selected" if save_year=="Enabled" else ""}>Enabled</option>
            <option value="Disabled" {"selected" if save_year=="Disabled" else ""}>Disabled</option>
            <option value="Required" {"selected" if save_year=="Required" else ""}>Required</option>
          </select>
        </div>
        <div class="field" style="width:150px;">
          <label>Embeds Color</label>
          <input type="color" id="bd_color" value="{color}">
        </div>
      </div>

      <div class="section-title">Birthdays</div>
      <h3>Birthday Card</h3><br>
      <div class="card">
        <div class="toggle-row">
          <div class="toggle-info"><h4>Enable Custom Card</h4><p>Enable and setup a custom birthday card graphic template alignment.</p></div>
          <label class="toggle"><input type="checkbox" id="bd_custom_card" {custom_card}> <span class="toggle-slider"></span></label>
        </div>
      </div>

      <div class="section-title">Birthdays</div>
      <h3>Birthday Message</h3><br>
      <div class="card">
        <div class="toggle-row">
          <div class="toggle-info"><h4>Send message on Birthday</h4><p>Enable this option to automatically send a message on a birthday.</p></div>
          <label class="toggle"><input type="checkbox" id="bd_send_msg" {send_msg}> <span class="toggle-slider"></span></label>
        </div>
      </div>

      <div class="section-title">Birthdays</div>
      <h3>Add Role on Birthday</h3><br>
      <div class="card">
        <div class="toggle-row">
          <div class="toggle-info"><h4>Add a Role on Birthday</h4><p>Enable this option to add a role to the user during their birthday for 24 hours.</p></div>
          <label class="toggle"><input type="checkbox" id="bd_add_role" {add_role}> <span class="toggle-slider"></span></label>
        </div>
      </div>

      <div class="section-title">Birthdays</div>
      <h3>/birthday showcase Command</h3><br>
      <div class="card">
        <div class="toggle-row">
          <div class="toggle-info"><h4>Enable /birthday showcase Command</h4><p>Allow users celebrating their birthday to send a pre-set message in the channel.</p></div>
          <label class="toggle"><input type="checkbox" id="bd_showcase" {enable_showcase}> <span class="toggle-slider"></span></label>
        </div>
      </div>

      <div class="section-title">Birthdays</div>
      <h3>Commands Permissions</h3><br>
      <div class="card">
        <div class="field"><label>Admin Roles</label><input type="text" id="bd_admin_roles" value="{admin_roles}" placeholder="Click + or add Admin Role IDs"></div>
        <div class="field">
          <label>Channel Restrictions - Blacklist Type</label>
          <select id="bd_ch_restrict">
            <option value="No channel restrictions" {"selected" if ch_restrict=="No channel restrictions" else ""}>No channel restrictions</option>
            <option value="Blacklist" {"selected" if ch_restrict=="Blacklist" else ""}>Blacklist Channels</option>
          </select>
        </div>
        <div class="field">
          <label>Role Restrictions - Blacklist Type</label>
          <select id="bd_role_restrict">
            <option value="No role restrictions" {"selected" if role_restrict=="No role restrictions" else ""}>No role restrictions</option>
            <option value="Blacklist" {"selected" if role_restrict=="Blacklist" else ""}>Blacklist Roles</option>
          </select>
        </div>
      </div>

      <div class="section-title">Module</div>
      <h3>Commands</h3><br>
      <div class="grid-blocks">
        <div class="block-item"><div><strong>/birthday set</strong><p style="font-size:12px;color:var(--sub);">Save your birthday!</p></div><label class="toggle"><input type="checkbox" id="cmd_set" {cmd_set}><span class="toggle-slider"></span></label></div>
        <div class="block-item"><div><strong>/birthday remove</strong><p style="font-size:12px;color:var(--sub);">Remove your birthday</p></div><label class="toggle"><input type="checkbox" id="cmd_remove" {cmd_remove}><span class="toggle-slider"></span></label></div>
        <div class="block-item"><div><strong>/birthday view</strong><p style="font-size:12px;color:var(--sub);">View yours or someone else's birthday!</p></div><label class="toggle"><input type="checkbox" id="cmd_view" {cmd_view}><span class="toggle-slider"></span></label></div>
        <div class="block-item"><div><strong>/birthday upcoming</strong><p style="font-size:12px;color:var(--sub);">View all next birthdays!</p></div><label class="toggle"><input type="checkbox" id="cmd_upcoming" {cmd_upcoming}><span class="toggle-slider"></span></label></div>
        <div class="block-item"><div><strong>/birthday showcase</strong><p style="font-size:12px;color:var(--sub);">Flex off your birthday!</p></div><label class="toggle"><input type="checkbox" id="cmd_showcase" {cmd_showcase}><span class="toggle-slider"></span></label></div>
        <div class="block-item"><div><strong>/birthday user-manage</strong><p style="font-size:12px;color:var(--sub);">Manage someone's birthday!</p></div><label class="toggle"><input type="checkbox" id="cmd_manage" {cmd_manage}><span class="toggle-slider"></span></label></div>
      </div>
      <br><button type="button" class="btn btn-secondary">+ Add Command</button>

      <div class="section-title">Module</div>
      <h3>Events</h3><br>
      <div class="grid-blocks">
        <div class="block-item"><div><strong>Birthdays Handler</strong><p style="font-size:12px;color:var(--sub);">When a timed event is executed</p></div><label class="toggle"><input type="checkbox" id="evt_handler" {evt_handler}><span class="toggle-slider"></span></label></div>
        <div class="block-item"><div><strong>Leaves Handler</strong><p style="font-size:12px;color:var(--sub);">When a user leaves or is kicked</p></div><label class="toggle"><input type="checkbox" id="evt_leaves" {evt_leaves}><span class="toggle-slider"></span></label></div>
      </div>
      <br><button type="button" class="btn btn-secondary">+ Add Event</button>

      <div class="btn-save-row"><button type="submit" class="btn btn-primary">Save Birthday Config</button></div>
    </form>
    <div id="toast_bday" style="display:none;position:fixed;bottom:24px;right:24px;background:#23a55a;color:#fff;padding:12px 20px;border-radius:6px;font-weight:600;font-size:14px;z-index:9999;">✅ Birthday settings synchronized live!</div>
    <script>
    function saveBirthdays(e){{
      e.preventDefault();
      fetch('/api/birthdays/save', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          enabled: true,
          timezone: document.getElementById('bd_tz').value,
          time: document.getElementById('bd_time').value,
          save_year: document.getElementById('bd_save_year').value,
          embed_color: document.getElementById('bd_color').value,
          custom_card: document.getElementById('bd_custom_card').checked,
          send_msg: document.getElementById('bd_send_msg').checked,
          add_role: document.getElementById('bd_add_role').checked,
          enable_showcase: document.getElementById('bd_showcase').checked,
          admin_roles: document.getElementById('bd_admin_roles').value,
          ch_restrict: document.getElementById('bd_ch_restrict').value,
          role_restrict: document.getElementById('bd_role_restrict').value,
          cmd_set: document.getElementById('cmd_set').checked,
          cmd_remove: document.getElementById('cmd_remove').checked,
          cmd_view: document.getElementById('cmd_view').checked,
          cmd_upcoming: document.getElementById('cmd_upcoming').checked,
          cmd_showcase: document.getElementById('cmd_showcase').checked,
          cmd_manage: document.getElementById('cmd_manage').checked,
          evt_handler: document.getElementById('evt_handler').checked,
          evt_leaves: document.getElementById('evt_leaves').checked
        }})
      }}).then(() => {{
         var t = document.getElementById('toast_bday'); t.style.display='block'; setTimeout(()=>t.style.display='none',2500);
      }});
    }}
    </script>
    """
    return render('birthdays', 'General Settings', 'Wish your members a Happy Birthday!', body, is_enabled=is_enabled)

@app.route('/api/birthdays/save', methods=['POST'])
def api_birthdays_save():
    gid = get_gid() or 'default'
    cfg = load('config.json')
    cfg.setdefault(gid, {}).setdefault('birthdays', {}).update(request.json)
    save('config.json', cfg)
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
#  AI SETTINGS & CUSTOM EMOJIS
# ══════════════════════════════════════════════════════════
@app.route('/ai-settings')
def ai_settings():
    gid = get_gid() or 'default'
    cfg = load('config.json').get(gid, {})
    
    is_enabled = cfg.get('ai_enabled', True)
    ai_on = 'checked' if is_enabled else ''
    reply_on = 'checked' if cfg.get('ai_reply_on_mention', True) else ''
    emojis_on = 'checked' if cfg.get('ai_auto_emojis', True) else ''
    
    custom_emojis = cfg.get('custom_external_emojis', {})
    emoji_rows = ''
    for name, url in custom_emojis.items():
        emoji_rows += f"""
        <div class="lb-row">
            <div class="lb-name"><img src="{url}" style="width:24px;height:24px;border-radius:4px;margin-right:8px;vertical-align:middle"><b>:{name}:</b></div>
            <div class="lb-val"><button onclick="deleteEmoji('{name}')" style="background:#ed4245;color:white;border:none;padding:4px 8px;border-radius:4px;cursor:pointer">Remove</button></div>
        </div>"""
    if not emoji_rows:
        emoji_rows = '<div class="lb-empty">No custom external emojis added yet</div>'

    body = f"""
    <form id="aiForm" onsubmit="saveAiSettings(event)">
    <div class="card">
      <div class="card-header">
        <div><h3>AI Control Panel</h3><p>Manage the behavior of your bot's smart AI assistant</p></div>
        <label class="toggle"><input type="checkbox" id="ai_enabled" {ai_on}><span class="toggle-slider"></span></label>
      </div>
      <div class="card-body">
        <div class="toggle-row">
          <div class="toggle-info"><h4>Reply on Mention / Reply</h4><p>Should the AI answer when someone pings or replies to its messages (like Level Up alerts)?</p></div>
          <label class="toggle"><input type="checkbox" id="ai_reply_on_mention" {reply_on}><span class="toggle-slider"></span></label>
        </div>
        <div class="toggle-row">
          <div class="toggle-info"><h4>Auto Emoji Reactions</h4><p>Allow the AI to automatically place smart emojis on messages</p></div>
          <label class="toggle"><input type="checkbox" id="ai_auto_emojis" {emojis_on}><span class="toggle-slider"></span></label>
        </div>
      </div>
    </div>
    <div class="btn-save-row">
      <button type="submit" class="btn btn-primary">Save Settings</button>
    </div>
    </form>

    <div class="card" style="margin-top:24px">
      <div class="card-header"><h3>✨ Add External Emojis</h3></div>
      <div class="card-body">
        <div style="display:grid;grid-template-columns:1fr 2fr;gap:12px;margin-bottom:12px">
          <div class="field"><label>Emoji Name</label><input type="text" id="em_name" placeholder="pepe_smile"></div>
          <div class="field"><label>Image URL</label><input type="text" id="em_url" placeholder="https://example.com/image.png"></div>
        </div>
        <button onclick="addEmoji()" class="btn btn-primary" style="background:#57f287;color:black;font-weight:bold;">Add External Emoji</button>
        <div style="margin-top:20px">
            <h4>Current Custom External Emojis:</h4>
            {emoji_rows}
        </div>
      </div>
    </div>
    <div id="toast" style="display:none;position:fixed;bottom:24px;right:24px;background:#57f287;color:#000;padding:12px 20px;border-radius:6px;font-weight:600;font-size:14px;z-index:9999;">✅ Updated!</div>
    <script>
    function showToast(){{var t=document.getElementById('toast'); t.style.display='block'; setTimeout(()=>t.style.display='none',2500);}}
    function saveAiSettings(e){{
      e.preventDefault();
      fetch('/api/ai/save',{{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{
          ai_enabled: document.getElementById('ai_enabled').checked,
          ai_reply_on_mention: document.getElementById('ai_reply_on_mention').checked,
          ai_auto_emojis: document.getElementById('ai_auto_emojis').checked
        }})
      }}).then(()=>showToast());
    }}
    function addEmoji(){{
      var name = document.getElementById('em_name').value; var url = document.getElementById('em_url').value;
      if(!name || !url) return alert('Please fill both fields!');
      fetch('/api/ai/emoji/add',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{name:name, url:url}})}}).then(()=>location.reload());
    }}
    function deleteEmoji(name){{
      fetch('/api/ai/emoji/delete',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{name:name}})}}).then(()=>location.reload());
    }}
    </script>
    """
    return render('ai-settings', 'AI Assistant', 'Configure AI actions and external emojis', body, is_enabled=is_enabled)

@app.route('/api/ai/save', methods=['POST'])
def api_ai_save():
    gid = get_gid() or 'default'
    cfg = load('config.json')
    cfg.setdefault(gid, {}).update(request.json)
    save('config.json', cfg)
    return jsonify({'ok':True})

@app.route('/api/ai/emoji/add', methods=['POST'])
def api_ai_emoji_add():
    gid = get_gid() or 'default'
    cfg = load('config.json')
    cfg.setdefault(gid, {}).setdefault('custom_external_emojis', {})[request.json['name']] = request.json['url']
    save('config.json', cfg)
    return jsonify({'ok':True})

@app.route('/api/ai/emoji/delete', methods=['POST'])
def api_ai_emoji_delete():
    gid = get_gid() or 'default'
    cfg = load('config.json')
    if gid in cfg and 'custom_external_emojis' in cfg[gid]:
        cfg[gid]['custom_external_emojis'].pop(request.json['name'], None)
        save('config.json', cfg)
    return jsonify({'ok':True})

# ══════════════════════════════════════════════════════════
#  SMASH KARTS PAGE
# ══════════════════════════════════════════════════════════
@app.route('/smashkarts')
def smashkarts():
    gid = get_gid() or 'default'
    sk_data = load('smashkarts.json').get(gid, {})
    sorted_sk = sorted(sk_data.items(), key=lambda x: x[1].get('wins', 0) if isinstance(x[1], dict) else 0, reverse=True)[:10]
    
    lb_rows = ""
    for rank, (uid, data) in enumerate(sorted_sk, 1):
        wins = data.get('wins', 0)
        lb_rows += f"""
        <div class="lb-row">
            <div class="lb-name"><b>#{rank}</b> &nbsp; User {uid}</div>
            <div class="lb-val" style="color:#57f287;">{wins} Wins 🏎️</div>
        </div>"""
    if not lb_rows:
        lb_rows = '<div class="lb-empty">No active matches recorded yet.</div>'

    body = f"""<div class="card"><div class="card-header"><h3>🏎️ Competitive Leaderboard</h3></div><div class="card-body">{lb_rows}</div></div>"""
    return render('smashkarts', '🏎️ Smash Karts Statistics', 'Global race metrics and win record compilations', body, is_enabled=True)

# ══════════════════════════════════════════════════════════
#  STORY MODE PAGE
# ══════════════════════════════════════════════════════════
@app.route('/story')
def story():
    gid = get_gid() or 'default'
    st_data = load('story.json').get(gid, {})
    
    body = f"""
    <div class="card">
      <div class="card-header"><h3>📖 Ongoing Story Session</h3></div>
      <div class="card-body">
        <p style="font-size:14px;color:#b5bac1;">Active Authors/Contributors recorded: <b style="color:#fff;">{len(st_data)} members</b></p>
        <p style="font-size:13px;color:#4e5058;margin-top:12px;">Full adventure configurations are generated directly via storytelling interactions inside discord channels.</p>
      </div>
    </div>
    """
    return render('story', '📖 Story Adventure Mode', 'Track server generated text simulations and interactive histories', body, is_enabled=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
