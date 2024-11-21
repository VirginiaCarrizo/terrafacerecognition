from playwright.sync_api import sync_playwright

def open_google():
    # Iniciar Playwright
    with sync_playwright() as playwright:
        # Lanzar un navegador (Chromium por defecto)
        browser = playwright.chromium.launch(headless=False)  # Cambia a True si quieres que el navegador sea invisible
        # Crear un nuevo contexto de navegador
        context = browser.new_context()
        # Crear una nueva página
        page = context.new_page()
        # Navegar a la página de Google
        page.goto("https://www.google.com")
        # Esperar unos segundos para observar la página
        page.wait_for_timeout(5000)  # 5 segundos
        # Cerrar el navegador
        browser.close()

# Ejecutar la función
if __name__ == "__main__":
    open_google()
