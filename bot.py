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
        for _ in range(25):
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
    password_tk = "Contraseña_Real_2026!"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        print(f"Iniciando registro para: {email}")
        
        try:
            await page.goto("https://www.tiktok.com/signup/phone-or-email/email", wait_until="networkidle")
            await asyncio.sleep(7)

            # 1. RELLENAR FECHA (Selector mejorado)
            # Buscamos los contenedores de los selectores de fecha
            print("Rellenando fecha...")
            try:
                # Intentamos seleccionar por el orden en que aparecen en el formulario
                await page.locator('div[class*="Month"]').click() # Abrir menú mes
                await asyncio.sleep(1)
                await page.locator('div[id*="month-Option-1"]').click() # Enero
                
                await page.locator('div[class*="Day"]').click()
                await asyncio.sleep(1)
                await page.locator('div[id*="day-Option-1"]').click() # Día 1
                
                await page.locator('div[class*="Year"]').click()
                await asyncio.sleep(1)
                await page.locator('div[id*="year-Option-2000"]').click() # Año 2000
            except:
                # Si el método anterior falla, intentamos el método directo de selects
                selects = await page.locator('select').all()
                if len(selects) >= 3:
                    await selects[0].select_option(index=1)
                    await selects[1].select_option("1")
                    await selects[2].select_option("2000")

            # 2. RELLENAR EMAIL Y PASSWORD
            print("Rellenando datos de usuario...")
            await page.fill('input[name="email"]', email)
            await page.fill('input[type="password"]', password_tk)
            await asyncio.sleep(2)

            # 3. PULSAR BOTÓN (Usando el ID que vimos en tu log)
            print("Pulsando botón de envío...")
            send_btn = page.locator('button[data-e2e="send-code-button"]')
            
            # Forzamos el click aunque TikTok crea que no hemos terminado
            await send_btn.click(force=True)

            # 4. ESPERAR CÓDIGO
            code = await get_verification_code(token)
            if code:
                with open(FILE_NAME, "a", encoding="utf-8") as f:
                    f.write(f"{email}:{password_tk}\n")
                print(f"¡CUENTA CREADA CON ÉXITO!: {email}")
            else:
                print("No se recibió el código. TikTok probablemente mostró un puzzle.")

        except Exception as e:
            print(f"Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
