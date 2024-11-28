const puppeteer = require('puppeteer-core');

(async () => {
  // Lanzar el navegador
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'] // Requerido para Docker
  });
  const page = await browser.newPage();

  // Navegar a la página
  await page.goto('https://generalfoodargentina.movizen.com/pwa/', { waitUntil: 'networkidle2' });

  // Esperar a que el campo de entrada esté disponible
  await page.waitForSelector('input');

  // Escribir en el campo de entrada
  await page.type('input', '123456789');

  // Cerrar el navegador
  await browser.close();
})();
