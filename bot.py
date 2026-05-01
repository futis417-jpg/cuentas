import asyncio
import os
import random
import string
import httpx
from playwright.async_api import async_playwright
from playwright_stealth import stealth

# --- PREPARACIÓN DEL ARCHIVO DE ENTREGA ---
# Esto asegura que siempre haya un archivo para descargar en GitHub
FILE_NAME = "cuentas.txt"
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write("--- REGISTRO DE CUENTAS GENERADAS ---\n")

# --- FUNCIONES DE CORREO (MAIL.TM) ---
async def create_temp_email():
    async with httpx.AsyncClient() as client:
        res = await client.get("https://api.mail.tm/domains")
        domain = res.json()['hydra:member'][0]['domain']
        user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{user}@{domain}"
        await client.post("https://api.mail.tm/accounts", json={"address": email, "password": "Password123!"})
        token_res = await client.post("https://api.mail.tm/token", json={"address": email, "password": "Password123!"})
        return email, token_res.json()['token']

async def get_verification_code(token):
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) as client:
        print("Esperando código de TikTok...")
        for _ in range(20):
            await asyncio.sleep(10)
            msgs = await client.get("https://api.mail.tm/messages")
            data = msgs.json()['hydra:member']
            if data:
                # Extraemos los números del asunto del mensaje
                code = ''.join(filter(str.isdigit, data[0]['subject']))[:6]
                return code
        return None

# --- FLUJO PRINCIPAL ---
async def run_bot():
    email, token = await create_temp_email()
    password_tk = "Contraseña_Dificil_2026!"
    
    async with async_playwright() as p:
        # Lanzamos navegador
        browser = await p.chromium.launch(headless=True)
        # Configuramos para parecer una persona real en USA o Francia (puedes cambiar locale)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        
        # Aplicamos Stealth corregido
        await stealth(page)

        print(f"Iniciando registro con: {email}")
        await page.goto("https://www.tiktok.com/signup/phone-or-email/email")
        await asyncio.sleep(3)

        # Rellenar fecha de nacimiento aleatoria
        await page.select_option('select[aria-label="Month"]', index=random.randint(1, 12))
        await page.select_option('select[aria-label="Day"]', str(random.randint(1, 28)))
        await page.select_option('select[aria-label="Year"]', str(random.randint(1990, 2006)))

        # Rellenar Email y Password
        await page.fill('input[name="email"]', email)
        await page.fill('input[type="password"]', password_tk)
        
        # Click en enviar código
        await page.click('button[type="submit"]')
        print("Formulario enviado. Esperando a ver si salta Captcha...")
        
        # Esperamos al código de verificación
        code = await get_verification_code(token)
        
        if code:
            print(f"Código recibido con éxito: {code}")
            # Guardamos la cuenta en el archivo
            with open(FILE_NAME, "a", encoding="utf-8") as f:
                f.write(f"{email}:{password_tk}\n")
            print("Cuenta guardada en cuentas.txt")
        else:
            print("No se recibió código. Probablemente TikTok bloqueó la IP o el Captcha no se resolvió.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
