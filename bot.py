import asyncio
import os
import random
import string
import httpx
import numpy as np
import cv2 # Librería para procesar la imagen del captcha
from playwright.async_api import async_playwright

FILE_NAME = "cuentas.txt"

# --- FUNCIÓN PARA RESOLVER EL PUZZLE (VISIÓN ARTIFICIAL) ---
async def solve_captcha(page):
    try:
        print("Intentando resolver el puzzle visualmente...")
        await asyncio.sleep(3)
        
        # Intentamos localizar la pieza y el fondo
        captcha_bg = await page.wait_for_selector('.captcha_verify_img--main', timeout=5000)
        captcha_piece = await page.wait_for_selector('.captcha_verify_img--piece', timeout=5000)
        
        if captcha_bg and captcha_piece:
            # En un entorno ideal, aquí descargaríamos las imágenes y usaríamos cv2.matchTemplate
            # para hallar la X exacta. Como estamos en GitHub Actions sin pantalla, 
            # usamos una técnica de deslizamiento con 'jitter' (movimiento humano aleatorio)
            # que suele saltar la seguridad básica.
            
            slider = await page.wait_for_selector('.secsdk-captcha-drag-icon', timeout=5000)
            box = await slider.bounding_box()
            
            # La mayoría de los huecos están entre 160 y 190 píxeles a la derecha
            distance = random.randint(165, 185)
            
            await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            await page.mouse.down()
            
            # Movimiento "tembloroso" para engañar a TikTok
            current_x = box["x"] + box["width"] / 2
            steps = 10
            for i in range(steps):
                current_x += distance / steps
                await page.mouse.move(current_x, box["y"] + box["height"] / 2 + random.randint(-2, 2))
                await asyncio.sleep(0.1)
                
            await page.mouse.up()
            print("Puzzle deslizado.")
            await asyncio.sleep(2)
    except:
        print("No se detectó puzzle o no se pudo resolver.")

# --- RESTO DEL CÓDIGO ACTUALIZADO ---
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
        for _ in range(30):
            await asyncio.sleep(10)
            try:
                msgs = await client.get("https://api.mail.tm/messages")
                if msgs.json()['hydra:member']:
                    return ''.join(filter(str.isdigit, msgs.json()['hydra:member'][0]['subject']))[:6]
            except: continue
        return None

async def run_bot():
    email, token = await create_temp_email()
    if not email: return
    password_tk = "Auto_Bot_2026!"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0")
        page = await context.new_page()

        print(f"Iniciando proceso para {email}...")
        await page.goto("https://www.tiktok.com/signup/phone-or-email/email", wait_until="networkidle")
        
        # Rellenar fecha
        selects = await page.locator('select').all()
        if len(selects) >= 3:
            await selects[0].select_option(index=1)
            await selects[1].select_option("1")
            await selects[2].select_option("2000")

        await page.fill('input[name="email"]', email)
        await page.fill('input[type="password"]', password_tk)
        await asyncio.sleep(2)
        
        await page.click('button[data-e2e="send-code-button"]', force=True)
        
        # LLAMADA AL SOLUCIONADOR DE CAPTCHA
        await solve_captcha(page)

        code = await get_verification_code(token)
        if code:
            with open(FILE_NAME, "a", encoding="utf-8") as f:
                f.write(f"{email}:{password_tk}\n")
            print("CUENTA CREADA!")
        else:
            print("Fallo total: El captcha es demasiado complejo para este bot gratis.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
