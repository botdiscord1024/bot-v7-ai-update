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

# ══════════════════════════════════════════════════════════
#  ГЛОВЕН ШАБЛОН С КРАСИВА ПЛАВАЩА ЛЕНТА И АВТОМАТИЧНА ЗАЩИТА
# ══════════════════════════════════════════════════════════
def render(route, title, desc, body):
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
        
        .sidebar { width: 260px; background: var(--b-nav); padding: 24px 12px; display: flex; flex-direction: column; gap: 4px; overflow-y: auto; }
        .brand { font-size: 18px; font-weight: 700; padding: 0 12px 20px 12px; border-bottom: 1px solid #2e3035; margin-bottom: 16px; color: #fff; }
        .nav-item { display: flex; align-items: center; padding: 10px 12px; border-radius: 4px; color: var(--sub); text-decoration: none; font-size: 14px; font-weight: 500; transition: .15s; }
        .nav-item:hover { background: #35373c; color: #fff; }
        .nav-item.active { background: var(--accent); color: #fff; }
        
        .main { flex: 1; display: flex; flex-direction: column; height: 100vh; background: var(--b-dark); position: relative; }
        .header { background: var(--b-mid); padding: 20px 32px; border-bottom: 1px solid #1f2023; }
        .header h1 { font-size: 24px; font-weight: 700; color: #fff; }
        .header p { font-size: 14px; color: var(--sub); margin-top: 4px; }
        
        .content { flex: 1; padding: 32px; overflow-y: auto; padding-bottom: 100px; }
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
        
        /* Leaderboards & Lists */
        .lb-row { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: var(--b-light); border-radius: 4px; margin-bottom: 8px; }
        .lb-name { display: flex; align-items: center; font-size: 14px; }
        .lb-val { font-size: 14px; color: var(--sub); font-weight: 600; }
        .lb-empty { text-align: center; color: var(--sub); padding: 20px; font-size: 14px; }
        
        .btn { display: inline-block; background: var(--accent); color: #fff; border: none; padding: 10px 20px; border-radius: 4px; font-size: 14px; font-weight: 500; cursor: pointer; transition: .15s; text-decoration: none; }
        .btn:hover { background: #4752c4; }
        .btn-primary { background: var(--accent); }
        .btn-save-row { display: flex; justify-content: flex-end; margin-top: 12px; }

        /* ── 🎨 КРАСИВА DISCORD-STYLE ЛЕНТА ЗА НЕЗАПАЗЕНИ ПРОМЕНИ ── */
        .unsaved-bar {
          position: fixed;
          bottom: -100px;
          left: 292px;
          right: 32px;
          background: #111214;
          border-radius: 6px;
          padding: 14px 24px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          box-shadow: 0 4px 20px rgba(0,0,0,0.6);
          transition: bottom 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          z-index: 10000;
        }
        .unsaved-bar.show { bottom: 24px; }
        .unsaved-bar span { color: #fff; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
        .bar-btns { display: flex; gap: 16px; align-items: center; }
        .btn-reset { background: transparent; color: #fff; border: none; cursor: pointer; font-size: 14px; font-weight: 500; }
        .btn-reset:hover { text-decoration: underline; }
        .btn-save-bar { background: #23a55a; color: white; padding: 10px 20px; border-radius: 4px; font-weight: 600; cursor: pointer; border: none; font-size: 14px; transition: .15s; }
        .btn-save-bar:hover { background: #1a7f43; }
      </style>
    </head>
    <body>
      <div class="sidebar">
        <div class="brand">👑 Admin Panel</div>
        <a href="/moderation" class="nav-item {% if route=='moderation' %}active{% endif %}">🛡️ Moderation</a>
        <a href="/levels" class="nav-item {% if route=='levels' %}active{% endif %}">⭐ Leveling System</a>
        <a href="/counting" class="nav-item {% if route=='counting' %}active{% endif %}">🔢 Counting Game</a>
        <a href="/ai-settings" class="nav-item {% if route=='ai-settings' %}active{% endif %}">🤖 AI Assistant</a>
        <a href="/qotd" class="nav-item {% if route=='qotd_settings' %}active{% endif %}">❓ QOTD Settings</a>
        <a href="/fotd" class="nav-item {% if route=='fotd_settings' %}active{% endif %}">💡 FOTD Settings</a>
        <a href="/rotd" class="nav-item {% if route=='rotd_settings' %}active{% endif %}">🧠 ROTD Settings</a>
        <a href="/sotd" class="nav-item {% if route=='sotd_settings' %}active{% endif %}">🎵 SOTD Settings</a>
        <a href="/smashkarts" class="nav-item {% if route=='smashkarts' %}active{% endif %}">🏎️ Smash Karts</a>
        <a href="/story" class="nav-item {% if route=='story' %}active{% endif %}">📖 Story Mode</a>
      </div>
      <div class="main">
        <div class="header">
          <h1>{{ title }}</h1>
          <p>{{ desc }}</p>
        </div>
        <div class="content">
          {{ body|safe }}
        </div>

        <div id="unsaved-changes-bar" class="unsaved-bar">
          <span>⚠️ Внимавай — имаш незапазени промени по конфигурацията!</span>
          <div class="bar-btns">
            <button type="button" class="btn-reset" id="reset-bar-btn">Отхвърли</button>
            <button type="button" class="btn-save-bar" id="save-bar-btn">Запази промените</button>
          </div>
        </div>
      </div>

      <script>
      document.addEventListener("DOMContentLoaded", function() {
          let hasChanges = false;
          const form = document.querySelector('form');
          const bar = document.getElementById('unsaved-changes-bar');
          const saveBarBtn = document.getElementById('save-bar-btn');
          const resetBarBtn = document.getElementById('reset-bar-btn');

          if (form && bar) {
              // 1. Слушаме за писане или цъкане по бутони и кутийки във формата
              form.addEventListener('input', () => { hasChanges = true; bar.classList.add('show'); });
              form.addEventListener('change', () => { hasChanges = true; bar.classList.add('show'); });

              // 2. Когато формата се запази успешно, махаме лентата
              form.addEventListener('submit', () => {
                  setTimeout(() => {
                      hasChanges = false;
                      bar.classList.remove('show');
                  }, 500);
              });

              // 3. Зеленият бутон в изскачащата лента автоматично пуска записването на съответната форма
              if (saveBarBtn) {
                  saveBarBtn.addEventListener('click', () => {
                      form.requestSubmit();
                  });
              }

              // 4. Бутонът за отхвърляне презарежда страницата
              if (resetBarBtn) {
                  resetBarBtn.addEventListener('click', () => {
                      if (confirm('Сигурен ли си, че искаш да отхвърлиш направените промени?')) {
                          hasChanges = false;
                          window.location.reload();
                      }
                  });
              }
          }

          // 5. 🔥 БЛОКИРАНЕ НА СТРАНИЧНОТО МЕНЮ ПРИ НЕЗАПАЗЕНИ ПРОМЕНИ
          document.querySelectorAll('.nav-item').forEach(link => {
              link.addEventListener('click', (e) => {
                  if (hasChanges) {
                      e.preventDefault(); // Спира пренасочването!
                      alert('🛑 Имаш незапазени промени! Моля, запиши ги или ги отхвърли чрез долната лента, преди да напуснеш страницата.');
                  }
              });
          });

          // 6. 🔥 БЛОКИРАНЕ НА ЗАТВАРЯНЕ НА ТАБА ИЛИ РЕФРЕШ НА БРАУЗЪРА
          window.onbeforeunload = function(e) {
              if (hasChanges) {
                  e.preventDefault();
                  e.returnValue = 'Имаш незапазени промени!';
                  return 'Имаш незапазени промени!';
              }
          };
      });
      </script>
    </body>
    </html>
    """, route=route, title=title, desc=desc, body=body)

# ══════════════════════════════════════════════════════════
#  MODERATION PAGE
# ══════════════════════════════════════════════════════════
@app.route('/')
@app.route('/moderation')
def moderation():
    gid = get_gid() or 'default'
    cfg = load('config.json').get(gid, {})
    
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
    return render('moderation', '🛡️ Moderation Settings', 'Control automod configurations, blacklisted word definitions, and execution protocols', body)

@app.route('/api/moderation/save', methods=['POST'])
def api_moderation_save():
    gid = get_gid() or 'default'
    cfg = load('config.json')
    cfg.setdefault(gid, {}).update(request.json)
    save('config.json', cfg)
    import builtins
    if hasattr(builtins, 'refresh_bot_cache'): 
        builtins.refresh_bot_cache()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
#  ⚙️ ДИНАМИЧЕН ГЕНЕРАТОР ЗА ЕЖЕДНЕВНИТЕ МОДУЛИ (QOTD, FOTD, ROTD, SOTD)
# ══════════════════════════════════════════════════════════
def render_daily_page(key, title, icon, default_msg):
    gid = get_gid() or 'default'
    cfg = load('config.json').get(gid, {}).get(key, {})
    
    enabled_checked = 'checked' if cfg.get('enabled', True) else ''
    channel_id = cfg.get('channel_id', '')
    roles = ", ".join(cfg.get('mentioned_roles', [])) if isinstance(cfg.get('mentioned_roles'), list) else cfg.get('mentioned_roles', '')
    msg = cfg.get('announcement_message', default_msg)
    t_name = cfg.get('thread_name', '💬 Leave comments here!')
    slowmode = cfg.get('slowmode', 0)
    
    duration = str(cfg.get('archive_duration', 1440))
    dur_opts = f"""
    <option value="60" {'selected' if duration=='60' else ''}>1 Hour</option>
    <option value="1440" {'selected' if duration=='1440' else ''}>1 Day (Default)</option>
    <option value="4320" {'selected' if duration=='4320' else ''}>3 Days</option>
    <option value="10080" {'selected' if duration=='10080' else ''}>1 Week</option>
    """

    body = f"""
    <form id="dailyForm" onsubmit="saveDaily(event, '{key}')">
    <div class="card">
      <div class="card-header">
        <div><h3>{icon} {title} Module Activation</h3><p>Configure automated system state and targets</p></div>
        <label class="toggle"><input type="checkbox" id="enabled" {enabled_checked}><span class="toggle-slider"></span></label>
      </div>
      <div class="card-body">
        <div class="field"><label>Target Channel ID</label><input type="text" id="channel_id" value="{channel_id}" placeholder="123456789012345678"></div>
        <div class="field"><label>Mentioned Role IDs (comma separated)</label><input type="text" id="mentioned_roles" value="{roles}" placeholder="888888888888, 999999999999"></div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><div><h3>📝 Embed Layout & Automated Thread Configuration</h3><p>Customize the presentation view and community responses</p></div></div>
      <div class="card-body">
        <div class="field">
            <label>Announcement Message Template (Use {{content}} where the AI generation belongs)</label>
            <textarea id="announcement_message" rows="4">{msg}</textarea>
        </div>
        <div class="field"><label>Created Thread Name</label><input type="text" id="thread_name" value="{t_name}"></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div class="field"><label>Thread Auto-Archive Duration</label><select id="archive_duration">{dur_opts}</select></div>
            <div class="field"><label>Thread Slowmode (In seconds, 0 to disable)</label><input type="number" id="slowmode" value="{slowmode}"></div>
        </div>
      </div>
    </div>
    
    <div class="btn-save-row"><button type="submit" class="btn btn-primary">Save {title} Configurations</button></div>
    </form>

    <div id="toast_daily" style="display:none;position:fixed;bottom:24px;right:24px;background:#23a55a;color:#fff;padding:12px 20px;border-radius:6px;font-weight:600;font-size:14px;z-index:9999;">✅ {title} configurations updated successfully!</div>

    <script>
    function saveDaily(e, saveKey){{
      e.preventDefault();
      let rolesRaw = document.getElementById('mentioned_roles').value;
      let rolesArray = rolesRaw.split(',').map(s => s.trim()).filter(s => s.length > 0);
      
      fetch('/api/daily/save/' + saveKey, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          enabled: document.getElementById('enabled').checked,
          channel_id: document.getElementById('channel_id').value,
          mentioned_roles: rolesArray,
          announcement_message: document.getElementById('announcement_message').value,
          thread_name: document.getElementById('thread_name').value,
          archive_duration: parseInt(document.getElementById('archive_duration').value),
          slowmode: parseInt(document.getElementById('slowmode').value) || 0
        }})
      }}).then(() => {{
         var t = document.getElementById('toast_daily'); t.style.display='block'; setTimeout(()=>t.style.display='none',2500);
      }});
    }}
    </script>
    """
    return render(key, icon + ' ' + title, f'Manage automatic daily {title.lower()} generation metrics and thread setups', body)

@app.route('/qotd')
def qotd_page():
    return render_daily_page('qotd_settings', 'Question of the Day', '❓', 'New question for today!\n\n> {content}')

@app.route('/fotd')
def fotd_page():
    return render_daily_page('fotd_settings', 'Fact of the Day', '💡', 'Expand your mind today!\n\n> {content}')

@app.route('/rotd')
def rotd_page():
    return render_daily_page('rotd_settings', 'Riddle of the Day', '🧠', "Can you solve today's riddle?\n\n> {content}")

@app.route('/sotd')
def sotd_page():
    return render_daily_page('sotd_settings', 'Song of the Day', '🎵', "Today's lobby track:\n\n{content}")

@app.route('/api/daily/save/<key>', methods=['POST'])
def api_daily_save(key):
    if key not in ['qotd_settings', 'fotd_settings', 'rotd_settings', 'sotd_settings']:
        return jsonify({'ok': False}), 400
    gid = get_gid() or 'default'
    cfg = load('config.json')
    cfg.setdefault(gid, {}).setdefault(key, {}).update(request.json)
    save('config.json', cfg)
    import builtins
    if hasattr(builtins, 'refresh_bot_cache'): 
        builtins.refresh_bot_cache()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
#  LEVELING PAGE
# ══════════════════════════════════════════════════════════
@app.route('/levels')
def levels():
    gid = get_gid() or 'default'
    cfg = load('config.json').get(gid, {})
    
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
    return render('levels', '⭐ Leveling System', 'Manage configurations and track active user XP records', body)

@app.route('/api/levels/save', methods=['POST'])
def api_levels_save():
    gid = get_gid() or 'default'
    cfg = load('config.json')
    cfg.setdefault(gid, {}).update(request.json)
    save('config.json', cfg)
    import builtins
    if hasattr(builtins, 'refresh_bot_cache'): 
        builtins.refresh_bot_cache()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════
#  COUNTING GAME PAGE
# ══════════════════════════════════════════════════════════
@app.route('/counting')
def counting():
    gid = get_gid() or 'default'
    c_data = load('counting.json').get(gid, {})
    
    current_count = c_data.get('count', 0)
    high_score = c_data.get('high_score', 0)
    
    counting_on = 'checked' if c_data.get('enabled', False) else ''
    same_user_on = 'checked' if c_data.get('allow_same_user', False) else ''
    shame_role_on = 'checked' if c_data.get('shame_role', False) else ''
    delete_invalid_on = 'checked' if c_data.get('delete_invalid', False) else ''
    
    ch_val = c_data.get('channel', "") or ""
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

    <div id="toast_count" style="display:none;position:fixed;bottom:24px;right:24px;background:#23a55a;color:#fff;padding:12px 20px;border-radius:6px;font-weight:600;font-size:14px;z-index:9999;">✅ Counting configs updated and live!</div>

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
