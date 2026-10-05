"""Regenerate the README images of GAIA Studio from the live UI.

    pip install playwright pillow
    python assets/make_screenshots.py       # uses your installed Chrome, no browser download
"""
import io
import os
import sys
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from gaia.server import make_server  # noqa: E402


def main():
    srv = make_server(0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=["--lang=en-US"])
        page = browser.new_page(viewport={"width": 1480, "height": 940}, device_scale_factor=1.25)
        page.goto(url)
        page.wait_for_selector("#p-cells .cell", timeout=120000)       # pack built
        page.wait_for_function("document.querySelectorAll('.meter').length == 3", timeout=180000)   # SOC lab done
        page.wait_for_timeout(500)
        shot = lambda name: page.screenshot(path=os.path.join(HERE, f"studio_{name}.png"))

        # 1. normal 1C discharge with balancing, 8 minutes in
        page.click("#p-run")
        page.wait_for_timeout(8000)
        page.click("#p-run")
        shot("pack")

        # 2. internal short on cell 4, animated: the cell drains, the others bleed to follow
        page.select_option("#p-spread", "0")
        page.click("#p-build")
        page.wait_for_timeout(500)
        page.click("[data-c='0']")                    # rest, so only the short and balancing act
        page.click("#p-cells .cell[data-id='3']")
        page.click("[data-f='short']")
        page.click("#p-speed button[data-v='300']")
        page.click("#p-run")
        frames = []
        for _ in range(28):
            page.wait_for_timeout(450)
            png = page.screenshot(clip={"x": 300, "y": 54, "width": 1180, "height": 420})
            frames.append(Image.open(io.BytesIO(png)).convert("RGB").resize((944, 336), Image.LANCZOS))
        page.click("#p-run")
        frames[0].save(os.path.join(HERE, "studio_short.gif"), save_all=True, append_images=frames[1:],
                       duration=220, loop=0, optimize=True)

        # 3. over-temperature trip: emergency, contactors open, event log
        page.click("#p-build")
        page.wait_for_timeout(500)
        page.click("[data-c='1']")                     # 1C discharge, then the fault
        page.click("#p-speed button[data-v='60']")
        page.click("#p-run")
        page.wait_for_timeout(5000)
        page.click("#p-cells .cell[data-id='6']")
        page.click("[data-f='overheat']")
        page.wait_for_timeout(2500)
        page.click("#p-reset")                      # refused: still hot
        page.wait_for_timeout(1500)
        page.click("#p-run")
        shot("trip")

        # 4. cell lab: three chemistries
        page.click(".tab[data-page=cell]")
        for chem in ("NMC", "LFP", "NCA"):
            page.select_option("#c-chem", chem)
            page.click("#c-run")
            page.wait_for_function("!document.querySelector('#c-run').disabled", timeout=180000)
        shot("cell")

        # 5. SOC lab
        page.click(".tab[data-page=soc]")
        page.wait_for_function("document.querySelectorAll('.meter').length == 3", timeout=180000)
        page.wait_for_timeout(600)
        shot("soc")
        browser.close()
    srv.shutdown()
    print("images written to", HERE)


if __name__ == "__main__":
    main()
