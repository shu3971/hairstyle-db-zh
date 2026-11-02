#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SimpAI Studio 本机批量生发型号参考图脚本
================================================
在你自己 Windows 电脑上运行（Studio 就在同机，无需 SSH 隧道）

用法:
    python local_gen.py

首次运行会自动引导配对（浏览器里点一下授权即可，30 天有效）。
之后 token 过期自动刷新，无需再管。

依赖: 仅 Python 3 标准库
输出: %USERPROFILE%\\hairstyle_batch_local\\male|female\\*.jpg + metadata.json
"""
import json, time, os, sys, urllib.request, urllib.parse, urllib.error

# ============ 配置 ============
# Studio 端口（每次启动可能变，如果连不上:
#   在 Studio 里看地址栏，或 PowerShell 跑 netstat -ano | findstr LISTENING | findstr 818
PORT = 8189

BASE = f'http://127.0.0.1:{PORT}'
OUT = os.path.join(os.path.expanduser('~'), 'hairstyle_batch_local')
META_PATH = os.path.join(OUT, 'metadata.json')
TOKEN_FILE = os.path.join(OUT, 'token.json')
TARGET = 1000           # 目标总张数
AUTORUN = True          # False = 只配对不生图

STYLE_TPL = ('photorealistic hairstyle reference photo, {desc}, {angle}, '
             'no face visible, back of head only, person not in frame, '
             'plain light grey studio background, soft even lighting, '
             'high detail hair texture, professional salon photography, 85mm lens')

ANGLES = [
    ('back-45', 'three-quarter back view, angled 45 degrees away from camera'),
    ('side', 'profile side view from behind, ear and jawline barely visible'),
]

MALE_STYLES = [
    ('taper-fade', 'taper fade with textured top'), ('high-tight', 'high and tight military crop'),
    ('caesar', 'caesar cut with short horizontal fringe'), ('faux-hawk', 'faux hawk with faded sides'),
    ('slick-back', 'slicked back hair with pompadour volume'), ('crew-cut', 'classic crew cut'),
    ('flat-top', 'flat top with squared silhouette'), ('side-part-fade', 'side part with skin fade'),
    ('textured-fringe', 'textured fringe forward over forehead'), ('modern-mullet', 'modern mullet with faded sides'),
    ('curly-fade', 'curly top with high fade'), ('afro-taper', 'afro taper with rounded volume'),
    ('dreadlocks', 'long dreadlocks pulled back'), ('viking-braid', 'viking braids with shaved sides'),
    ('korean-perm', 'korean soft perm with side split'), ('two-block', 'korean two-block cut'),
    ('slick-quiff', 'slicked quiff with tapered sides'), ('buzz-fade', 'buzz cut with burst fade'),
    ('long-shag', 'long shaggy layered hair'), ('man-braid', 'single long braid down the back'),
    ('spiky-top', 'spiky textured top with fade'), ('messy-mop', 'messy mop top with long fringe'),
    ('undercut-long', 'undercut with long top swept back'), ('comma-hair', 'korean comma fringe style'),
    ('wolf-shag', 'wolf cut shag with chin length layers'), ('wet-look', 'wet look slicked hair'),
    ('silver-fox', 'salt and pepper swept back mature style'), ('pompadour-fade', 'pompadour with high fade'),
    ('bowl-modern', 'modern bowl cut with blunt fringe'), ('layer-long-male', 'long layered male hair'),
]
FEMALE_STYLES = [
    ('hush-cut', 'hush cut with soft face framing layers'), ('wolf-cut-female', 'wolf cut with curtain bangs'),
    ('jelly-perm', 'jelly perm with bouncy waves'), ('sleek-bun', 'sleek low bun with middle part'),
    ('space-bun', 'double space buns with loose strands'), ('braided-crown', 'braided crown updo'),
    ('fishtail-braid', 'long fishtail side braid'), ('french-twist', 'elegant french twist updo'),
    ('pixie-long', 'long pixie with side swept bangs'), ('curtain-long', 'long hair with curtain bangs'),
    ('ash-layered', 'ash brown layered long hair'), ('mermaid-wave', 'mermaid waves waist length'),
    ('half-up', 'half up half down with clip'), ('korean-pony', 'korean high ponytail with face framing'),
    ('bubble-pony', 'bubble ponytail with sectioned ties'), ('ribbon-braid', 'ribbon braid woven style'),
    ('hime-layer', 'hime cut with straight side locks'), ('y2k-streak', 'y2k chunky highlights with layers'),
    ('baby-bangs', 'baby bangs with chin length bob'), ('wavy-lob', 'wavy lob just above shoulders'),
    ('layered-shag-f', 'shaggy layered medium hair'), ('curly-afro-f', 'natural curly afro'),
    ('twist-out', 'two strand twist out'), ('cornrows', 'cornrows braided close to scalp'),
    ('short-pixie-crop', 'cropped pixie with textured top'), ('wet-bob', 'wet look sleek bob'),
    ('low-pony-wave', 'low ponytail with wavy ends'), ('pigtail-braid', 'twin dutch braid pigtails'),
    ('long-straight', 'long straight hair with blunt ends'), ('butterfly-layer', 'butterfly layered long hair'),
]
COLORS = [('base', ''), ('black', 'jet black hair color'), ('brown', 'chestnut brown hair color'),
          ('blonde', 'honey blonde hair color'), ('silver', 'ash silver grey hair color')]


# ============ token 管理 ============
def _post(path, payload, timeout=20):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def pair_interactive():
    """设备码流程配对，打印授权 URL，轮询等用户点授权"""
    print('=== 首次配对（30 天有效，只需做一次）===')
    try:
        d = _post('/api/v1/auth/device',
                  {'client_name': 'HairLibrary-Local', 'authorization_days': 30})
    except Exception as e:
        print(f'[失败] 连不上 Studio: {e}')
        print(f'请确认 Studio 已启动，且端口是 {PORT}（改脚本顶部 PORT 也行）')
        return None
    if not d.get('ok'):
        print('[失败]', d)
        return None
    info = d['data']
    code = info['user_code']
    url = f'{BASE}{info["verification_url"]}'
    device_code = info['device_code']

    print()
    print('  ★ 在浏览器打开下面这个链接完成授权：')
    print()
    print('     ' + url)
    print()
    print('  配对码: ' + code + '   （10 分钟内有效）')
    print()
    print('  授权时如果有"授权天数"选项，请选 30 天。')
    print('  授权完成后本脚本会自动继续，无需其他操作…')
    print()

    for _ in range(120):  # 最多等 20 分钟
        time.sleep(10)
        try:
            t = _post('/api/v1/auth/token', {'device_code': device_code})
        except Exception:
            continue
        if t.get('ok') and t['data'].get('access_token'):
            json.dump(t['data'], open(TOKEN_FILE, 'w'), indent=1)
            print('  ✅ 配对成功，token 已保存到', TOKEN_FILE)
            print(f'     access 有效 {t["data"].get("expires_in")}s，'
                  f'refresh 有效 {t["data"].get("refresh_expires_in")}s')
            return t['data']
        # 用户还没点授权，继续等
    print('  ✗ 等待超时，请重新运行脚本')
    return None


def load_tokens():
    if os.path.exists(TOKEN_FILE):
        try:
            return json.load(open(TOKEN_FILE))
        except Exception:
            pass
    return None


def refresh_token():
    d = json.load(open(TOKEN_FILE))
    try:
        r = _post('/api/v1/auth/refresh', {'refresh_token': d['refresh_token']})
        if r.get('ok') and r['data'].get('access_token'):
            json.dump(r['data'], open(TOKEN_FILE, 'w'), indent=1)
            print('  [token 已自动刷新]')
            return True
    except Exception as e:
        print(f'  [refresh 异常] {e}')
    print('  [refresh 失败，需要重新配对]')
    return False


def api(path, data=None, method=None, retries=5):
    last = None
    for i in range(retries):
        tok = json.load(open(TOKEN_FILE))['access_token']
        try:
            req = urllib.request.Request(
                BASE + path,
                data=json.dumps(data).encode('utf-8') if data is not None else None,
                headers={'Authorization': f'Bearer {tok}',
                         'Content-Type': 'application/json; charset=utf-8'},
                method=method)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                if not refresh_token():
                    sys.exit('token 失效，请删除 token.json 后重跑脚本重新配对')
                continue
            last = f'HTTP {e.code}: {e.read()[:200]}'
        except Exception as e:
            last = f'{type(e).__name__}: {e}'
        time.sleep(4 * (i + 1))
    raise RuntimeError(last)


def download(asset_id, path, retries=6):
    url = BASE + '/api/v1/assets/' + urllib.parse.quote(asset_id, safe='') + '/content'
    last = None
    for i in range(retries):
        try:
            tok = json.load(open(TOKEN_FILE))['access_token']
            req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}'})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if len(data) < 5000:
                raise RuntimeError(f'too small: {len(data)} bytes')
            tmp = path + '.part'
            open(tmp, 'wb').write(data)
            os.replace(tmp, path)
            return
        except Exception as e:
            last = e
            time.sleep(4 * (i + 1))
    raise RuntimeError(f'download failed: {last}')


def gen_one(rid, prompt, retries=3):
    for attempt in range(retries):
        try:
            r = api('/api/v1/runs', {
                'request_id': f'{rid}-{int(time.time())}-{attempt}',
                'preset_id': 'Z-imageT', 'task': 'text_to_image',
                'instruction': '发型参考图',
                'prompt': prompt, 'lang': 'en',
                'output': {'aspect_ratio': '2:3', 'count': 1},
            }, 'POST')
            if not r.get('ok'):
                return None, r
            run_id = r['data']['run_id']
            for _ in range(60):
                time.sleep(4)
                s = api(f'/api/v1/runs/{run_id}')
                d = s['data']
                if d['state'] == 'finished':
                    a = d.get('assets', [])
                    return (a[0] if a else None), d
                if d['state'] in ('failed', 'canceled'):
                    break
        except SystemExit:
            raise
        except Exception:
            time.sleep(10)
    return None, {'error': 'retries exhausted'}


def main():
    os.makedirs(os.path.join(OUT, 'male'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'female'), exist_ok=True)

    # 1. 配对环境
    if not load_tokens():
        if not pair_interactive():
            return 1
    if not AUTORUN:
        print('AUTORUN=False，配对完成即退出。')
        return 0

    META = json.load(open(META_PATH)) if os.path.exists(META_PATH) else []
    have = {m['id'] for m in META}
    print(f'\n已有 {len(META)} 张，目标 {TARGET} 张')

    jobs = []
    for gender, styles, folder in [('male', MALE_STYLES, 'male'), ('female', FEMALE_STYLES, 'female')]:
        for key, desc in styles:
            for cname, cdesc in COLORS:
                for aname, adesc in ANGLES:
                    rid = f'h4-{gender}-{key}-{cname}-{aname}'
                    if rid not in have:
                        jobs.append((gender, folder, key, desc, cname, cdesc, aname, adesc, rid))

    room = max(0, TARGET - len(META))
    jobs = jobs[:room]
    print(f'本轮生成 {len(jobs)} 张（约 {len(jobs)*0.4:.0f} 分钟）\n')
    if not jobs:
        print('已达目标，无需生成。')
        return 0

    n_new, errs = 0, []
    t0 = time.time()
    for gender, folder, key, desc, cname, cdesc, aname, adesc, rid in jobs:
        full = desc + (', ' + cdesc if cdesc else '')
        prompt = STYLE_TPL.format(desc=full, angle=adesc)
        if cname == 'silver':
            prompt += ', mature adult'
        try:
            asset, info = gen_one(rid, prompt)
            if not asset:
                errs.append(rid)
                print(f'  [skip] {rid}')
                continue
            fn = os.path.join(OUT, folder, f'{key}_{cname}_{aname}.jpg')
            download(asset['asset_id'], fn)
            META.append({'id': rid, 'gender': gender, 'style': key, 'style_desc': desc,
                         'angle': aname, 'color': cname,
                         'asset_id': asset['asset_id'], 'file': fn})
            n_new += 1
            if n_new % 10 == 0:
                el = time.time() - t0
                eta = el / n_new * (len(jobs) - n_new) / 60
                print(f'... {n_new}/{len(jobs)} done, {el/60:.0f}min 已用, 剩余约 {eta:.0f}min', flush=True)
        except KeyboardInterrupt:
            print('\n\n用户中断，进度已保存。再次运行可续跑。')
            break
        except SystemExit:
            json.dump(META, open(META_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            raise
        except Exception as e:
            errs.append(f'{rid}: {e}')
            print(f'  [err] {rid}: {str(e)[:100]}')
        json.dump(META, open(META_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print(f'\n=== 完成 ===\n新增 {n_new} 张，失败 {len(errs)}，总计 {len(META)} 张')
    print(f'图片目录: {OUT}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\n已退出')
