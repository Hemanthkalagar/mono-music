import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import base64
import html
import re
import os

PORT = int(os.environ.get('PORT', 3000))

# DES Decryption Tables
PC1 = [56, 48, 40, 32, 24, 16, 8, 0, 57, 49, 41, 33, 25, 17, 9, 1, 58, 50, 42, 34, 26, 18, 10, 2, 59, 51, 43, 35,
       62, 54, 46, 38, 30, 22, 14, 6, 61, 53, 45, 37, 29, 21, 13, 5, 60, 52, 44, 36, 28, 20, 12, 4, 27, 19, 11, 3]
PC2 = [13, 16, 10, 23, 0, 4, 2, 27, 14, 5, 20, 9, 22, 18, 11, 3, 25, 7, 15, 6, 26, 19, 12, 1, 40, 51, 30, 36,
       46, 54, 29, 39, 50, 44, 32, 47, 43, 48, 38, 55, 33, 52, 45, 41, 49, 35, 28, 31]
SHIFTS = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]
IP = [57, 49, 41, 33, 25, 17, 9, 1, 59, 51, 43, 35, 27, 19, 11, 3, 61, 53, 45, 37, 29, 21, 13, 5, 63, 55, 47, 39, 31, 23, 15, 7,
      56, 48, 40, 32, 24, 16, 8, 0, 58, 50, 42, 34, 26, 18, 10, 2, 60, 52, 44, 36, 28, 20, 12, 4, 62, 54, 46, 38, 30, 22, 14, 6]
IP_INV = [39, 7, 47, 15, 55, 23, 63, 31, 38, 6, 46, 14, 54, 22, 62, 30, 37, 5, 45, 13, 53, 21, 61, 29, 36, 4, 44, 12, 52, 20, 60, 28,
          35, 3, 43, 11, 51, 19, 59, 27, 34, 2, 42, 10, 50, 18, 58, 26, 33, 1, 41, 9, 49, 17, 57, 25, 32, 0, 40, 8, 48, 16, 56, 24]
E = [31, 0, 1, 2, 3, 4, 3, 4, 5, 6, 7, 8, 7, 8, 9, 10, 11, 12, 11, 12, 13, 14, 15, 16,
     15, 16, 17, 18, 19, 20, 19, 20, 21, 22, 23, 24, 23, 24, 25, 26, 27, 28, 27, 28, 29, 30, 31, 0]
P = [15, 6, 19, 20, 28, 11, 27, 16, 0, 14, 22, 25, 4, 17, 30, 9, 1, 7, 23, 13, 31, 26, 2, 8, 18, 12, 29, 5, 21, 10, 3, 24]
S_BOX = [
    [14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7,0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8,4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0,15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13],
    [15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10,3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5,0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15,13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9],
    [10,0,9,14,6,3,15,5,1,13,12,7,11,4,2,8,13,7,0,9,3,4,6,10,2,8,5,14,12,11,15,1,13,6,4,9,8,15,3,0,11,1,2,12,5,10,14,7,1,10,13,0,6,9,8,7,4,15,14,3,11,5,2,12],
    [7,13,14,3,0,6,9,10,1,2,8,5,11,12,4,15,13,8,11,5,6,15,0,3,4,7,2,12,1,10,14,9,10,6,9,0,12,11,7,13,15,1,3,14,5,2,8,4,3,15,0,6,10,1,13,8,9,4,5,11,12,7,2,14],
    [2,12,4,1,7,10,11,6,8,5,3,15,13,0,14,9,14,11,2,12,4,7,13,1,5,0,15,10,3,9,8,6,4,2,1,11,10,13,7,8,15,9,12,5,6,3,0,14,11,8,12,7,1,14,2,13,6,15,0,9,10,4,5,3],
    [12,1,10,15,9,2,6,8,0,13,3,4,14,7,5,11,10,15,4,2,7,12,9,5,6,1,13,14,0,11,3,8,9,14,15,5,2,8,12,3,7,0,4,10,1,13,11,6,4,3,2,12,9,5,15,10,11,14,1,7,6,0,8,13],
    [4,11,2,14,15,0,8,13,3,12,9,7,5,10,6,1,13,0,11,7,4,9,1,10,14,3,5,12,2,15,8,6,1,4,11,13,12,3,7,14,10,15,6,8,0,5,9,2,6,11,13,8,1,4,10,7,9,5,0,15,14,2,3,12],
    [13,2,8,4,6,15,11,1,10,9,3,14,5,0,12,7,1,15,13,8,10,3,7,4,12,5,6,11,0,14,9,2,7,11,4,1,9,12,14,2,0,6,10,13,15,3,5,8,2,1,14,7,4,10,8,13,15,12,9,0,3,5,6,11]
]

def bytes_to_bits(data):
    bits = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits

def bits_to_bytes(bits):
    data = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i:i+8]:
            byte = (byte << 1) | bit
        data.append(byte)
    return bytes(data)

def generate_subkeys(key_bytes):
    key_bits = bytes_to_bits(key_bytes)
    permuted = [key_bits[i] for i in PC1]
    c, d = permuted[:28], permuted[28:]
    subkeys = []
    for shift in SHIFTS:
        c = c[shift:] + c[:shift]
        d = d[shift:] + d[:shift]
        cd = c + d
        subkeys.append([cd[i] for i in PC2])
    return subkeys

def des_block(block_bits, subkeys):
    bits = [block_bits[i] for i in IP]
    l, r = bits[:32], bits[32:]
    for k in reversed(subkeys):
        er = [r[i] for i in E]
        x = [a ^ b for a, b in zip(er, k)]
        s_out = []
        for i in range(8):
            chunk = x[i*6:(i+1)*6]
            row = (chunk[0] << 1) | chunk[5]
            col = (chunk[1] << 3) | (chunk[2] << 2) | (chunk[3] << 1) | chunk[4]
            val = S_BOX[i][(row << 4) | col]
            for j in range(3, -1, -1):
                s_out.append((val >> j) & 1)
        p_out = [s_out[i] for i in P]
        new_r = [a ^ b for a, b in zip(l, p_out)]
        l, r = r, new_r
    final_bits = r + l
    return [final_bits[i] for i in IP_INV]

def decrypt_jiosaavn(enc_b64):
    try:
        raw = base64.b64decode(enc_b64.strip())
        subkeys = generate_subkeys(b"38346591")
        out = bytearray()
        for i in range(0, len(raw), 8):
            block = raw[i:i+8]
            if len(block) < 8:
                break
            dec_bits = des_block(bytes_to_bits(block), subkeys)
            out.extend(bits_to_bytes(dec_bits))
        pad_len = out[-1]
        if 1 <= pad_len <= 8:
            out = out[:-pad_len]
        url = out.decode("utf-8", errors="ignore")
        return url.replace("_96.mp4", "_160.mp4")
    except Exception:
        return ""

class TeluguHiFiHandler(http.server.SimpleHTTPRequestHandler):
    def send_json(self, data, status=200):
        try:
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        raw_path = (self.headers.get('x-forwarded-uri') or 
                    self.headers.get('x-matched-path') or 
                    self.headers.get('x-original-url') or 
                    self.path)
        parsed = urllib.parse.urlparse(raw_path)
        if parsed.path == '/favicon.ico':
            svg_data = b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%23111111'/><circle cx='50' cy='50' r='18' fill='%23faf9f5'/><circle cx='50' cy='50' r='6' fill='%23111111'/></svg>"
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
            self.send_header('Content-Length', str(len(svg_data)))
            self.end_headers()
            self.wfile.write(svg_data)
            return
        if parsed.path in ('/mobile', '/mobile/'):
            self.path = '/mobile.html'
            return super().do_GET()

        if parsed.path == '/api/download':
            query_params = urllib.parse.parse_qs(parsed.query)
            target_url = query_params.get('url', [''])[0].strip()
            raw_title = query_params.get('title', ['Telugu_Song'])[0].strip()
            clean_title = re.sub(r'[^\w\s-]', '', raw_title).strip() or "Telugu_Song"
            clean_title = clean_title.replace(' ', '_')
            
            if not target_url or not target_url.startswith('http'):
                self.send_response(400)
                self.end_headers()
                return

            try:
                ext = ".m4a" if target_url.endswith('.mp4') else ".mp3"
                filename = f"{clean_title}{ext}"
                req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                with urllib.request.urlopen(req, timeout=15) as remote_stream:
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mp4' if ext == '.m4a' else 'audio/mpeg')
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    content_len = remote_stream.headers.get('Content-Length')
                    if content_len:
                        self.send_header('Content-Length', content_len)
                    self.end_headers()
                    
                    while True:
                        chunk = remote_stream.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except Exception as e:
                print("Download proxy error:", e)
            return

        if parsed.path == '/api/suggest':
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get('q', [''])[0].strip()
            if not q:
                self.send_json({"albums": [], "songs": []})
                return

            url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&ctx=web6dot0&query={urllib.parse.quote(q)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            
            albums_out = []
            songs_out = []
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    data = json.loads(r.read().decode('utf-8'))
                    
                    # Process Telugu Albums
                    for a in data.get('albums', {}).get('data', []):
                        lang = (a.get('more_info', {}).get('language') or '').lower()
                        desc = (a.get('description') or '').lower()
                        title = html.unescape(a.get('title', '')).strip()
                        # Prefer Telugu or matching query
                        if lang == 'telugu' or 'telugu' in desc or 'telugu' in title.lower() or not lang:
                            clean_title = re.sub(r'\s*-\s*\(?Telugu\)?', '', title, flags=re.IGNORECASE).strip()
                            clean_title = clean_title.split('(')[0].strip() if '(' in clean_title and 'telugu' in title.lower() else clean_title
                            year = a.get('more_info', {}).get('year', '')
                            if not year:
                                m = re.search(r'\b(20\d\d|19\d\d)\b', desc)
                                if m:
                                    year = m.group(1)
                            music = a.get('music') or a.get('more_info', {}).get('music') or ''
                            img = a.get('image', '').replace('50x50.jpg', '150x150.jpg')
                            albums_out.append({
                                "id": str(a.get('id', '')),
                                "title": clean_title,
                                "rawTitle": title,
                                "year": year or "2024",
                                "music": html.unescape(music).strip() if music else "",
                                "image": img,
                                "description": html.unescape(a.get('description', '')).strip()
                            })
                            
                    # Process Telugu Songs
                    seen_song_keys = set()
                    for s in data.get('songs', {}).get('data', []):
                        lang = (s.get('more_info', {}).get('language') or '').lower()
                        desc = (s.get('description') or '').lower()
                        title = html.unescape(s.get('title', '')).strip()
                        album = html.unescape(s.get('album', '') or s.get('more_info', {}).get('album', '')).strip()
                        singers = html.unescape(s.get('more_info', {}).get('singers', '') or s.get('more_info', {}).get('primary_artists', '')).strip()
                        if lang == 'telugu' or 'telugu' in desc or 'telugu' in title.lower() or not lang:
                            clean_title = re.sub(r'\s*-\s*\(?Telugu\)?', '', title, flags=re.IGNORECASE).strip()
                            clean_title = clean_title.split('(')[0].strip() if '(' in clean_title and 'telugu' in title.lower() else clean_title
                            s_key = re.sub(r'[^a-z0-9]', '', clean_title.lower())
                            if s_key in seen_song_keys:
                                continue
                            seen_song_keys.add(s_key)
                            img = s.get('image', '').replace('50x50.jpg', '150x150.jpg')
                            songs_out.append({
                                "id": str(s.get('id', '')),
                                "title": clean_title,
                                "rawTitle": title,
                                "album": album,
                                "singers": singers,
                                "image": img,
                                "description": html.unescape(s.get('description', '')).strip()
                            })
            except Exception as e:
                print("API suggest error:", e)

            # Fallback: if no albums found in autocomplete but user typed a movie name, try search.getAlbumResults
            if not albums_out and len(q) >= 3 and not songs_out:
                try:
                    alb_url = f"https://www.jiosaavn.com/api.php?__call=search.getAlbumResults&_format=json&_marker=0&api_version=4&ctx=web6dot0&n=4&p=1&q={urllib.parse.quote(q + ' Telugu')}"
                    alb_req = urllib.request.Request(alb_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                    with urllib.request.urlopen(alb_req, timeout=4) as r:
                        alb_data = json.loads(r.read().decode('utf-8'))
                        q_words = [w.lower() for w in re.split(r'\s+', q) if len(w) >= 3]
                        for a in alb_data.get('results', []):
                            t = html.unescape(a.get('title', '')).strip()
                            clean_t = re.sub(r'\s*-\s*\(?Telugu\)?', '', t, flags=re.IGNORECASE).strip()
                            clean_low = clean_t.lower()
                            is_match = False
                            if q.lower() in clean_low or clean_low in q.lower():
                                is_match = True
                            elif q_words and all(w in clean_low for w in q_words):
                                is_match = True

                            if is_match:
                                albums_out.append({
                                    "id": str(a.get('id', '')),
                                    "title": clean_t,
                                    "rawTitle": t,
                                    "year": str(a.get('year', '2024')),
                                    "music": html.unescape(a.get('music', '') or a.get('primary_artists', '')).strip(),
                                    "image": a.get('image', '').replace('50x50.jpg', '150x150.jpg'),
                                    "description": html.unescape(a.get('description', '') or f"Telugu Album ({a.get('year', '')})").strip()
                                })
                except Exception as e:
                    print("Album search fallback error:", e)

            self.send_json({"albums": albums_out[:6], "songs": songs_out[:8]})
            return

        if parsed.path == '/api/album':
            query_params = urllib.parse.parse_qs(parsed.query)
            album_id = query_params.get('id', [''])[0].strip()
            if not album_id:
                self.send_json({"error": "id parameter required"}, 400)
                return

            url = f"https://www.jiosaavn.com/api.php?__call=content.getAlbumDetails&_format=json&_marker=0&api_version=4&ctx=web6dot0&albumid={urllib.parse.quote(album_id)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            
            album_res = None
            try:
                with urllib.request.urlopen(req, timeout=6) as r:
                    data = json.loads(r.read().decode('utf-8'))
                    raw_title = html.unescape(data.get('title', '')).strip()
                    clean_title = re.sub(r'\s*-\s*\(?Telugu\)?', '', raw_title, flags=re.IGNORECASE).strip()
                    clean_title = clean_title.split('(')[0].strip() if '(' in clean_title and 'telugu' in raw_title.lower() else clean_title
                    
                    try:
                        year_val = int(data.get('year') or 2024)
                    except:
                        year_val = 2024
                        
                    primary_artists = html.unescape(data.get('primary_artists', '') or data.get('music', '') or '').strip()
                    img = (data.get('image') or '').replace('50x50.jpg', '500x500.jpg').replace('150x150.jpg', '500x500.jpg')
                    
                    songs_list = []
                    for s in data.get('list', []):
                        enc = s.get('more_info', {}).get('encrypted_media_url')
                        if not enc:
                            continue
                        audio_url = decrypt_jiosaavn(enc)
                        if not audio_url.startswith('http'):
                            continue
                            
                        s_title = html.unescape(s.get('title', '')).strip()
                        clean_s_title = re.sub(r'\s*-\s*\(?Telugu\)?', '', s_title, flags=re.IGNORECASE).strip()
                        clean_s_title = clean_s_title.split('(')[0].strip() if '(' in clean_s_title and 'telugu' in s_title.lower() else clean_s_title
                        s_singers = html.unescape(s.get('more_info', {}).get('singers', '') or s.get('singers', '') or '').strip()
                        
                        try:
                            dur_sec = int(s.get('more_info', {}).get('duration') or 210)
                        except:
                            dur_sec = 210
                        dur_min = f"{dur_sec // 60}:{dur_sec % 60:02d}"
                        
                        songs_list.append({
                            "title": clean_s_title,
                            "movie": clean_title,
                            "composer": f"{s_singers} • {clean_title} ({year_val})" if s_singers else f"{clean_title} ({year_val})",
                            "singers": s_singers,
                            "year": year_val,
                            "duration": dur_min,
                            "durationSec": dur_sec,
                            "audioUrl": audio_url,
                            "image": img,
                            "id": str(s.get('id', '')),
                            "category": "all",
                            "genre": f"Telugu • {year_val}"
                        })
                        
                    album_res = {
                        "id": str(album_id),
                        "title": clean_title,
                        "rawTitle": raw_title,
                        "year": year_val,
                        "composer": primary_artists,
                        "image": img,
                        "songs": songs_list
                    }
            except Exception as e:
                print("API album error:", e)

            if not album_res:
                album_res = {"error": "Failed to load album", "songs": []}

            self.send_json(album_res)
            return

        if parsed.path == '/api/search':
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get('q', [''])[0].strip()
            year = query_params.get('year', [''])[0].strip()
            page = int(query_params.get('page', query_params.get('p', [1]))[0])
            limit = int(query_params.get('limit', [25])[0])
            limit = min(50, max(1, limit))
            page = max(1, page)
            
            genre = query_params.get('genre', [''])[0].strip().lower()
            
            # Construct intelligent query for JioSaavn
            if genre == 'mass':
                if q:
                    search_query = f"{q} Telugu Dance {year}".strip()
                elif year:
                    search_query = f"Telugu Dance Dhamaka Hits {year}".strip()
                else:
                    search_query = "Telugu Dance Dhamaka Hits"
            elif genre == 'melody':
                if q:
                    search_query = f"{q} Telugu Melody {year}".strip()
                elif year:
                    search_query = f"Telugu Melody Hits {year}".strip()
                else:
                    search_query = "Telugu Melody Hits"
            elif genre == 'romantic':
                if q:
                    search_query = f"{q} Telugu Romantic {year}".strip()
                elif year:
                    search_query = f"Telugu Romantic Hits {year}".strip()
                else:
                    search_query = "Telugu Romantic Hits"
            elif genre == 'folk':
                if q:
                    search_query = f"{q} Telugu Folk Janapada Songs {year}".strip()
                elif year:
                    search_query = f"Telugu Folk Janapada Geethalu {year}".strip()
                else:
                    search_query = "Telugu Folk Songs Janapada Geethalu Hits"
            else:
                parts = []
                if q:
                    parts.append(q)
                if 'telugu' not in [p.lower() for p in parts]:
                    parts.append("Telugu")
                if year:
                    parts.append(str(year))
                if not q and not year:
                    parts.append("Blockbuster Hits")
                search_query = " ".join(parts).strip()
            
            # Fetch extra items from upstream API so de-duplication still returns full batch
            fetch_count = min(60, limit * 2)
            url = f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&_marker=0&api_version=4&ctx=web6dot0&n={fetch_count}&p={page}&q={urllib.parse.quote(search_query)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            
            results_out = []
            seen_titles = set()
            try:
                with urllib.request.urlopen(req, timeout=6) as r:
                    data = json.loads(r.read().decode('utf-8'))
                    results = data.get('results', [])
                    for s in results:
                        enc = s.get('more_info', {}).get('encrypted_media_url')
                        if not enc:
                            continue
                        audio_url = decrypt_jiosaavn(enc)
                        if not audio_url.startswith('http'):
                            continue
                        
                        raw_title = html.unescape(s.get('title', '')).strip()
                        clean_title = raw_title.split('(')[0].split('-')[0].strip()
                        
                        # Normalize title for robust de-duplication
                        norm_key = re.sub(r'[^a-z0-9]', '', clean_title.lower())
                        if not norm_key or norm_key in seen_titles:
                            continue
                        seen_titles.add(norm_key)

                        movie = html.unescape(s.get('more_info', {}).get('album', '') or s.get('album', '')).strip()
                        singers = html.unescape(s.get('more_info', {}).get('singers', '') or s.get('singers', '')).strip()
                        
                        try:
                            year_val = int(s.get('year') or 2024)
                        except:
                            year_val = 2024
                            
                        try:
                            dur_sec = int(s.get('more_info', {}).get('duration') or 210)
                        except:
                            dur_sec = 210
                            
                        dur_min = f"{dur_sec // 60}:{dur_sec % 60:02d}"
                        
                        results_out.append({
                            "id": str(s.get('id', '')),
                            "title": clean_title,
                            "movie": movie,
                            "composer": f"{singers} • {movie} ({year_val})" if singers else f"{movie} ({year_val})",
                            "singers": singers,
                            "year": year_val,
                            "duration": dur_min,
                            "durationSec": dur_sec,
                            "audioUrl": audio_url,
                            "image": s.get('image', '').replace('50x50.jpg', '500x500.jpg') or s.get('image', ''),
                            "category": genre if genre else "all",
                            "genre": f"Telugu • {year_val}"
                        })
                        if len(results_out) >= limit:
                            break
            except Exception as e:
                print("API search error:", e)
                
            self.send_json(results_out)
            return

        # Serve static files as default
        super().do_GET()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

# Vercel Serverless Function Entrypoints
handler = TeluguHiFiHandler
app = TeluguHiFiHandler

if __name__ == '__main__':
    with ThreadedHTTPServer(("", PORT), TeluguHiFiHandler) as httpd:
        print(f"Telugu Hi-Fi Production Server listening on http://localhost:{PORT}")
        httpd.serve_forever()

