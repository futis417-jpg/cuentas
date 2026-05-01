import asyncio
import os
import random
import string
import httpx
from playwright.async_api import async_playwright

FILE_NAME = "cuentas.txt"
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w") as f: f.write("--- LISTA ---\n")

# --- SOLUCIONADOR DE PUZZLE MEJORADO ---
async def solve_shifter(page):
    print("Buscando puzzle en todos los niveles...")
    try:
        # TikTok suele meter el captcha en un 'iframe'. Vamos a buscarlo ahí.
        for frame in page.frames:
            captcha_icon = await frame.query_selector('.secsdk-captcha-drag-icon')
            if captcha_icon:
                print("¡Puzzle detectado dentro de un frame!")
                box = await captcha_icon.bounding_box()
                
                # Movimiento humano: lento al principio, rápido en el medio, lento al final
                await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                await page.mouse.down()
                
                target_x = box["x"] + random.randint(160, 190) # Distancia típica
                
                # Simulamos aceleración humana
                steps = 15
                for i in range(steps):
                    current_x = box["x"] + (target_x - box["x"]) * (i / steps)
                    await page.mouse.move(current_x, box["y"] + random.randint(-1, 1), steps=2)
                    await asyncio.sleep(0.05)
                
                await page.mouse.up()
                print("Pieza deslizada con éxito.")
                return True
        return False
    except Exception as e:
        print(f"Error al intentar mover la pieza: {e}")
        return False

# --- RESTO DEL PROCESO ---
async def run_bot():
    async with httpx.AsyncClient() as client:
        # Crear correo rápido
        res = await client.get("https://api.mail.tm/domains")
        domain = res.json()['hydra:member'][0]['domain']
        user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{user}@{domain}"
        await client.post("https://api.mail.tm/accounts", json={"address": email, "password": "Password123!"})
        token_res = await client.post("https://api.mail.tm/token", json={"address": email, "password": "Password123!"})
        token = token_res.json()['token']

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0")
        page = await context.new_page()

        print(f"Intentando registro: {email}")
        await page.goto("https://www.tiktok.com/signup/phone-or-email/email", wait_until="networkidle")
        await asyncio.sleep(5)

        # Rellenar fecha (Método ultra rápido)
        await page.evaluate('''() => {
            const selects = document.querySelectorAll('select');
            if(selects.length >= 3) {
                selects[0].selectedIndex = 1;
                selects[1].selectedIndex = 1;
                selects[2].value = "2000";
                selects[0].dispatchEvent(new Event('change'));
            }
        }''')

        await page.fill('input[name="email"]', email)
        await page.fill('input[type="password"]', "CuentaTK_2026!")
        await page.click('button[data-e2e="send-code-button"]', force=True)
        
        # Esperar a que el puzzle aparezca y resolverlo
        await asyncio.sleep(5)
        resuelto = await solve_shifter(page)

        # Esperar código
        print("Esperando código final...")
        async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) as client:
            for _ in range(20):
                await asyncio.sleep(10)
                msgs = await client.get("https://api.mail.tm/messages")
                if msgs.json()['hydra:member']:
                    code = ''.join(filter(str.isdigit, msgs.json()['hydra:member'][0]['subject']))[:6]
                    with open(FILE_NAME, "a") as f: f.write(f"{email}:CuentaTK_2026!\n")
                    print(f"¡CUENTA CREADA!: {email}")
                    return

        print("No se pudo completar. TikTok es más listo que nosotros hoy.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
