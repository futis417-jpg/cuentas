import asyncio
import os
import random
import string
import httpx
from playwright.async_api import async_playwright

# --- INICIALIZACIÓN ---
FILE_NAME = "cuentas.txt"
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write("--- LISTA DE CUENTAS ENTREGADAS ---\n")

# --- CORREO (MAIL.TM) ---
async def create_temp_email():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get("https://api.mail.tm/domains")
            domain = res.json()['hydra:member'][0]['domain']
            user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            email = f"{user}@{domain}"
            await client.post("https://api.mail.tm/accounts", json={"address": email, "password": "Password123!"})
            token_res = await client.post("https://api.mail.tm/token", json={"address": email, "password": "Password123!"})
            return email, token_res.json()['token']
        except:
            return None, None

async def get_verification_code(token):
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) as client:
        for _ in range(25):
            await asyncio.sleep(10)
            try:
                msgs = await client.get("https://api.mail.tm/messages")
                data = msgs.json()['hydra:member']
                if data:
                    return ''.join(filter(str.isdigit, data[0]['subject']))[:6]
            except:
                continue
        return None

# --- BOT ---
async def run_bot():
    email, token = await create_temp_email()
    if not email: return
    
    password_tk = "TikTok_Pass_2026!"
    
    async with async_playwright() as p:
        # Usamos argumentos para intentar saltar el captcha sin la librería stealth que daba error
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
        ])
        
        regiones = [
            {"locale": "en-US", "tz": "America/New_York", "url": "https://www.tiktok.com/signup/phone-or-email/email"},
            {"locale": "fr-FR", "tz": "Europe/Paris", "url": "https://www.tiktok.com/signup/phone-or-email/email"}
        ]
        config = random.choice(regiones)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale=config["locale"],
            timezone_id=config["tz"]
        )
        
        page = await context.new_page()
        print(f"Probando región: {config['locale']} con {email}")
        
        try:
            await page.goto(config["url"], wait_until="domcontentloaded")
            await asyncio.sleep(8) # Espera extra para que cargue todo bien

            # --- NUEVO SISTEMA DE SELECCIÓN DE FECHA (MÁS FUERTE) ---
            # Buscamos los selectores por posición (el 1º es mes, el 2º día, el 3º año)
            selects = await page.query_selector_all("select")
            if len(selects) >= 3:
                await selects[0].select_option(index=random.randint(1, 12))
                await asyncio.sleep(1)
                await selects[1].select_option(str(random.randint(1, 28)))
                await asyncio.sleep(1)
                await selects[2].select_option(str(random.randint(1990, 2005)))
            else:
                print("No se encontraron los selectores de fecha tradicionales, intentando por texto...")
                # Intento alternativo si fallan los selects
                await page.get_by_placeholder("Month").select_option(index=1)

            # --- RELLENAR DATOS ---
            # Buscamos inputs de tipo email y password
            await page.fill('input[name="email"]', email)
            await asyncio.sleep(1)
            await page.fill('input[type="password"]', password_tk)
            
            # Click en el botón de "Next" o "Submit"
            await page.click('button[type="submit"]')
            print("Formulario enviado. Esperando código...")
            
            code = await get_verification_code(token)
            if code:
                with open(FILE_NAME, "a", encoding="utf-8") as f:
                    f.write(f"{email}:{password_tk} | {config['locale']}\n")
                print(f"¡ÉXITO! Cuenta guardada: {email}")
            else:
                print("Fallo: El código no llegó. TikTok probablemente pidió un Puzzle Captcha.")

        except Exception as e:
            # Hacemos una captura de pantalla si falla para que puedas ver el error (opcional)
            # await page.screenshot(path="error.png")
            print(f"Error en ejecución: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
