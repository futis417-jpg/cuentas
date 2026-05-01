import asyncio
import os
import random
import string
import httpx
from playwright.async_api import async_playwright
import playwright_stealth

# --- INICIALIZACIÓN DE ARCHIVO ---
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
        for _ in range(20):
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
        browser = await p.chromium.launch(headless=True)
        
        # Selección de región
        regiones = [
            {"locale": "en-US", "tz": "America/New_York"},
            {"locale": "fr-FR", "tz": "Europe/Paris"}
        ]
        config = random.choice(regiones)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale=config["locale"],
            timezone_id=config["tz"]
        )
        
        page = await context.new_page()
        
        # IMPORTACIÓN SEGURA DE STEALTH
        await playwright_stealth.stealth_async(page)

        print(f"Probando región: {config['locale']} con {email}")
        
        try:
            await page.goto("https://www.tiktok.com/signup/phone-or-email/email")
            await asyncio.sleep(4)

            # Rellenar fecha
            await page.select_option('select[aria-label="Month"]', index=random.randint(1, 12))
            await page.select_option('select[aria-label="Day"]', str(random.randint(1, 28)))
            await page.select_option('select[aria-label="Year"]', str(random.randint(1990, 2005)))

            # Email y Pass
            await page.fill('input[name="email"]', email)
            await page.fill('input[type="password"]', password_tk)
            
            await page.click('button[type="submit"]')
            
            code = await get_verification_code(token)
            if code:
                with open(FILE_NAME, "a", encoding="utf-8") as f:
                    f.write(f"{email}:{password_tk} | Región: {config['locale']}\n")
                print(f"ÉXITO: Cuenta creada para {email}")
            else:
                print("No llegó el código (posible Captcha)")

        except Exception as e:
            print(f"Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
