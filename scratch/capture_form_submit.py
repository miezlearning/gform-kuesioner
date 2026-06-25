import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create context and page
        context = await browser.new_context()
        page = await context.new_page()
        
        captured_request = {}

        # Set up request interceptor
        async def handle_request(request):
            if "formResponse" in request.url and request.method == "POST":
                print(f"Intercepted formResponse request: {request.url}")
                post_data = request.post_data
                captured_request["url"] = request.url
                captured_request["method"] = request.method
                captured_request["headers"] = request.headers
                captured_request["post_data"] = post_data
                
                # Parse post_data if urlencoded
                try:
                    from urllib.parse import parse_qs
                    captured_request["parsed_post_data"] = parse_qs(post_data)
                except Exception as e:
                    captured_request["parse_error"] = str(e)

        page.on("request", handle_request)

        print("Navigating to Google Form...")
        await page.goto("https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform")
        await page.wait_for_timeout(2000)

        # PAGE 0: Email
        print("Filling Page 0 (Email)...")
        email_input = await page.query_selector('input[type="email"]')
        if email_input:
            await email_input.fill("playwright_test@gmail.com")
        else:
            print("Email input not found.")
        
        # Click Next
        next_button = await page.query_selector('text="Berikutnya"')
        if next_button:
            await next_button.click()
        else:
            print("Next button on Page 0 not found.")
        await page.wait_for_timeout(1500)

        # PAGE 1: Nama, NIM, Angkatan
        print("Filling Page 1 (Identity)...")
        text_inputs = await page.query_selector_all('input[type="text"]')
        if len(text_inputs) >= 2:
            await text_inputs[0].fill("Playwright Test Responden")
            await text_inputs[1].fill("2409106099")
        else:
            print("Identity text inputs not found.")
        
        # Radio button for Angkatan (2024 is the 4th option, let's look for text containing '2024')
        angkatan_radio = await page.query_selector('div[role="radio"][aria-label="2024"]')
        if angkatan_radio:
            await angkatan_radio.click()
        else:
            print("Angkatan radio not found.")
            
        next_button = await page.query_selector('text="Berikutnya"')
        await next_button.click()
        await page.wait_for_timeout(1500)

        # PAGE 2: Usability
        print("Filling Page 2 (Usability)...")
        # Radio buttons (choose option '4' or '5' for all usability questions)
        # There are 5 usability questions. Each question is a row of radio buttons.
        # Let's find all radio options with aria-label="4" or "5"
        radios = await page.query_selector_all('div[role="radio"][aria-label="4"]')
        print(f"Found {len(radios)} radio buttons with label '4'")
        # Click first 5
        for i in range(min(5, len(radios))):
            await radios[i].click()
            await page.wait_for_timeout(100)
            
        next_button = await page.query_selector('text="Berikutnya"')
        await next_button.click()
        await page.wait_for_timeout(1500)

        # PAGE 3: Information Quality
        print("Filling Page 3 (Information Quality)...")
        radios = await page.query_selector_all('div[role="radio"][aria-label="4"]')
        print(f"Found {len(radios)} radio buttons with label '4'")
        for i in range(min(5, len(radios))):
            await radios[i].click()
            await page.wait_for_timeout(100)
            
        next_button = await page.query_selector('text="Berikutnya"')
        await next_button.click()
        await page.wait_for_timeout(1500)

        # PAGE 4: Service Interaction
        print("Filling Page 4 (Service Interaction)...")
        radios = await page.query_selector_all('div[role="radio"][aria-label="4"]')
        print(f"Found {len(radios)} radio buttons with label '4'")
        for i in range(min(5, len(radios))):
            await radios[i].click()
            await page.wait_for_timeout(100)
            
        next_button = await page.query_selector('text="Berikutnya"')
        await next_button.click()
        await page.wait_for_timeout(1500)

        # PAGE 5: User Satisfaction & Opinions
        print("Filling Page 5 (Satisfaction)...")
        radios = await page.query_selector_all('div[role="radio"][aria-label="4"]')
        print(f"Found {len(radios)} radio buttons with label '4'")
        for i in range(min(3, len(radios))):
            await radios[i].click()
            await page.wait_for_timeout(100)
            
        # Textareas for Opinions & Suggestions
        textareas = await page.query_selector_all('textarea')
        if len(textareas) >= 2:
            await textareas[0].fill("Menurut saya website ini sudah sangat baik.")
            await textareas[1].fill("Saran saya adalah terus meningkatkan kecepatan akses.")
        else:
            print("Opinions textareas not found.")
            
        # Submit
        submit_button = await page.query_selector('text="Kirim"')
        if submit_button:
            print("Clicking Kirim (Submit)...")
            await submit_button.click()
        else:
            print("Submit button not found.")
        
        await page.wait_for_timeout(4000)
        
        # Save captured request
        with open("scratch/captured_payload.json", "w", encoding="utf-8") as f:
            json.dump(captured_request, f, indent=2)
            
        print("Done. Saved captured payload to scratch/captured_payload.json")
        await browser.close()

asyncio.run(run())
