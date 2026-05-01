import asyncio
import os
import random
import string
import httpx
from playwright.async_api import async_playwright

FILE_NAME = "cuentas.txt"
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write("--- LISTA DE CUENTAS ---\n")

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
        except: return None, None

async def get_verification_code(token):
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) as client:
        for _ in range(20):
            await asyncio.sleep(12)
            try:
                msgs = await client.get("https://api.mail.tm/messages")
                data = msgs.json()['hydra:member']
                if data: return ''.join(filter(str.isdigit, data[0]['subject']))[:6]
            except: continue
        return None

async def run_bot():
    email, token = await create_temp_email()
    if not email: return
    password_tk = "Admin_TK_2026!"
    
    async with async_playwright() as p:
        # Argumentos extra para evitar ser detectado como bot de servidor
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ])
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        # Evitar detección de webdriver
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Navegando a TikTok para registrar: {email}")
        
        try:
            # Ir al registro con un tiempo de espera largo
            await page.goto("https://www.tiktok.com/signup/phone-or-email/email", wait_until="networkidle", timeout=90000)
            await asyncio.sleep(10)

            # --- BUSCADOR DE INPUTS DINÁMICO ---
            # En lugar de buscar por nombre, buscamos TODOS los inputs y selects
            print("Buscando campos de registro...")
            
            # 1. Rellenar Fecha (buscando cualquier select disponible)
            all_selects = await page.locator("select").all()
            if len(all_selects) >= 3:
                await all_selects[0].select_option(index=random.randint(1, 12))
                await all_selects[1].select_option(str(random.randint(1, 28)))
                await all_selects[2].select_option(str(random.randint(1990, 2004)))
                print("Fecha completada.")
            else:
                print("No se encontró el formato de fecha esperado.")

            # 2. Rellenar Email y Password por tipo de campo (más seguro)
            await page.locator('input[name="email"], input[type="email"]').first.fill(email)
            await asyncio.sleep(1)
            await page.locator('input[type="password"]').first.fill(password_tk)
            
            # 3. Click en el botón que NO sea de redes sociales (suele ser el que tiene texto de enviar o siguiente)
            btn = page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Send code")').first
            await btn.click()
            print("Botón de registro pulsado.")

            # Esperar código
            code = await get_verification_code(token)
            if code:
                with open(FILE_NAME, "a", encoding="utf-8") as f:
                    f.write(f"{email}:{password_tk}\n")
                print(f"CUENTA CREADA: {email}")
            else:
                print("Timeout: El código no llegó. Probablemente saltó un puzzle captcha invisible.")

        except Exception as e:
            print(f"Error detectado: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
