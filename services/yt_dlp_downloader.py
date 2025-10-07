import sys
import subprocess
import time
from pathlib import Path

# per version check
try:
    from importlib import metadata
except Exception:
    metadata = None

# yt-dlp API
try:
    import yt_dlp as ytdlp_pkg
    from yt_dlp import YoutubeDL
except Exception:
    ytdlp_pkg = None
    YoutubeDL = None

COOKIES_FILE = Path("cookies.txt")
DOMAINS_TO_EXTRACT = ("youtube.com", "music.youtube.com")


def ensure_package_up_to_date(package_name="yt-dlp", do_update=True):
    """
    Controlla versione installata (se presente). Se do_update True prova ad aggiornare con pip -U.
    Ritorna (installed_version or None, updated_bool).
    """
    installed = None
    try:
        if metadata:
            installed = metadata.version(package_name)
        else:
            import pkg_resources
            installed = pkg_resources.get_distribution(package_name).version
    except Exception:
        installed = None

    updated = False
    if do_update:
        try:
            print(f"[setup] Aggiornamento {package_name} con pip...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", package_name])
            updated = True
            if package_name == "yt-dlp":
                import importlib
                importlib.invalidate_caches()
                try:
                    importlib.reload(ytdlp_pkg)
                except Exception:
                    pass
        except subprocess.CalledProcessError as e:
            print("[setup] Errore aggiornamento pip:", e)
    return installed, updated


def extract_cookies_from_browser_and_save(target_file=COOKIES_FILE, domains=DOMAINS_TO_EXTRACT):
    """
    Usa browser_cookie3 per leggere i cookie del browser correntemente loggato
    e salvarli in formato 'netscape' (compatibile con yt-dlp --cookies).
    """
    try:
        import browser_cookie3
    except Exception:
        print("[cookies] browser_cookie3 non installato. Installalo con: pip install browser-cookie3")
        return False

    try:
        cj_all = browser_cookie3.load()
    except Exception as e:
        print("[cookies] errore lettura cookie dal browser:", e)
        return False

    from http.cookiejar import MozillaCookieJar
    mcj = MozillaCookieJar(str(target_file))
    added = 0
    for cookie in cj_all:
        if any(d in cookie.domain for d in domains):
            mcj.set_cookie(cookie)
            added += 1

    if added == 0:
        print("[cookies] Nessun cookie utile trovato per i domini:", domains)
        return False

    mcj.save(ignore_discard=True, ignore_expires=True)
    print(f"[cookies] Salvati {added} cookie in {target_file}")
    return True


def cookies_need_refresh(cookiefile=COOKIES_FILE, required_names=None):
    """
    Controlla se il file cookies.txt esiste e contiene cookie non scaduti.
    Ritorna True se serve aggiornare.
    """
    from http.cookiejar import MozillaCookieJar
    if not cookiefile.exists():
        return True

    mcj = MozillaCookieJar()
    try:
        mcj.load(cookiefile, ignore_discard=True, ignore_expires=True)
    except Exception:
        return True

    now = time.time()
    any_valid = False
    for c in mcj:
        if getattr(c, "expires", None) is None or c.expires > now:
            any_valid = True
            break

    if not any_valid:
        return True

    if required_names:
        names = {c.name for c in mcj}
        for rn in required_names:
            if rn not in names:
                return True

    return False


def test_accessible_with_cookies(url, cookiefile=COOKIES_FILE, timeout=30):
    """
    Prova ad estrarre metadata senza scaricare (download=False).
    """
    opts = {
        "quiet": True,
        "no_warnings": True,
        "cookiefile": str(cookiefile) if cookiefile.exists() else None,
        "format": "bestaudio/best",
    }
    if opts["cookiefile"] is None:
        opts.pop("cookiefile")

    try:
        with YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=False)
        return True, None
    except Exception as e:
        return False, str(e)


def prepare_and_test(url, auto_update=True, try_extract_cookies=True):
    print("[setup] check yt-dlp")
    installed_version, updated = ensure_package_up_to_date("yt-dlp", do_update=auto_update)
    print(f"[setup] versione installata: {installed_version}, aggiornato: {updated}")

    need_refresh = cookies_need_refresh(required_names=["SSID", "LOGIN_INFO"])
    if need_refresh and try_extract_cookies:
        print("[cookies] cookies assenti o scaduti -> estrazione dal browser")
        ok = extract_cookies_from_browser_and_save(COOKIES_FILE)
        if not ok:
            print("[cookies] estrazione automatica fallita. Esporta manualmente cookies.txt dal browser.")
    else:
        print("[cookies] cookies sembrano presenti e validi.")

    ok, err = test_accessible_with_cookies(url, cookiefile=COOKIES_FILE)
    if ok:
        print("[test] accesso OK.")
        return True
    else:
        print("[test] accesso FALLITO:", err)
        print("Se il contenuto è privato, rigenera cookies o controlla il file cookies.txt.")
        return False

def download_with_dlp(url, auto_update=True, try_extract_cookies=True, output_template="%(title)s.%(ext)s"):
    """
    Fa pre-flight check + scarica con yt-dlp.
    output_template: come nominare i file, es. "%(title)s.%(ext)s"
    """
    ok = prepare_and_test(url, auto_update=auto_update, try_extract_cookies=try_extract_cookies)
    if not ok:
        print("[download] impossibile procedere al download per errore di accesso.")
        return False

    print("[download] avvio download playlist/video…")
    opts = {
        "cookiefile": str(COOKIES_FILE) if COOKIES_FILE.exists() else None,
        "format": "bestaudio/best",
        "outtmpl": output_template
    }
    if opts["cookiefile"] is None:
        opts.pop("cookiefile")

    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
        print("[download] completato.")
        return True
    except Exception as e:
        print("[download] errore durante il download:", e)
        return False
