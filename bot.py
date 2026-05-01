import asyncio
import os
import random
import string
import httpx
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- CONFIGURACIÓN INICIAL ---
FILE_NAME = "cuentas.txt"

# Aseguramos que el archivo exista para que GitHub Actions no de error al subir el artifact
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write("--- CUENTAS GENERADAS ---\n")

# --- FUNCIONES DE CORREO (MAIL.TM) ---
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
        except Exception as e:
            print(f"Error creando correo: {e}")
            return None, None

async def get_verification_code(token):
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) as client:
        print("Esperando mensaje de confirmación de TikTok...")
        for _ in range(24):  # Esperar hasta 4 minutos
            await asyncio.sleep(10)
            try:
                msgs = await client.get("https://api.mail.tm/messages")
                data = msgs.json()['hydra:member']
                if data:
                    # Extraer el código de 6 dígitos del asunto
                    code = ''.join(filter(str.isdigit, data[0]['subject']))[:6]
                    return code
            except:
                continue
        return None

# --- PROCESO DE REGISTRO ---
async def run_bot():
    email, token = await create_temp_email()
    if not email:
        return

    password_tk = "TikTok_Gen_2026!"
    
    async with async_playwright() as p:
        # Lanzar navegador en modo headless (obligatorio para GitHub Actions)
        browser = await p.chromium.launch(headless=True)
        
        # Elegir región (USA o Francia aleatoriamente)
        region = random.choice([
            {"locale": "en-US", "tz": "America/New_York"},
            {"locale": "fr-FR", "tz": "Europe/Paris"}
        ])
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale=region["locale"],
            timezone_id=region["tz"]
        )
        
        page = await context.new_page()
        # Aplicar modo incógnito/stealth para evitar detección
        await stealth_async(page)

        print(f"Registrando en región: {region['locale']} con email: {email}")
        
        try:
            await page.goto("https://www.tiktok.com/signup/phone-or-email/email", timeout=60000)
            await asyncio.sleep(5)

            # Rellenar Fecha de Nacimiento
            await page.select_option('select[aria-label="Month"]', index=random.randint(1, 12))
            await page.select_option('select[aria-label="Day"]', str(random.randint(1, 28)))
            await page.select_option('select[aria-label="Year"]', str(random.randint(1990, 2005)))

            # Rellenar Datos
            await page.fill('input[name="email"]', email)
            await page.fill('input[type="password"]', password_tk)
            
            # Click en enviar código
            await page.click('button[type="submit"]')
            print("Formulario enviado. Buscando código...")

            code = await get_verification_code(token)
            
            if code:
                # Si el código llega, lo guardamos directamente
                print(f"¡Código obtenido!: {code}")
                with open(FILE_NAME, "a", encoding="utf-8") as f:
                    f.write(f"{email}:{password_tk} | Región: {region['locale']}\n")
            else:
                print("No se recibió código. Probablemente saltó un captcha manual o bloqueo de IP.")

        except Exception as e:
            print(f"Error durante el proceso: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
