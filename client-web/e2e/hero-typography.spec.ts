import { expect, test } from "@playwright/test";

for (const viewport of [
  { width: 320, height: 568 },
  { width: 375, height: 667 },
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 844, height: 390 },
]) {
  test(`hero stays readable at ${viewport.width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize(viewport);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    const heading = page.locator("#hero-title");
    await expect(heading).toHaveText("You go chill. We’ll apply.");

    // Check the text itself, not just document overflow: the hero clips overflow.
    for (const enlarged of [false, true]) {
      if (enlarged) {
        await page.addStyleTag({ content: "html { font-size: 32px !important; }" });
      }
      const geometry = await heading.evaluate((element) => {
        const style = getComputedStyle(element);
        const box = element.getBoundingClientRect();
        const range = document.createRange();
        range.selectNodeContents(element);
        return {
          fontSize: parseFloat(style.fontSize),
          lineHeight: parseFloat(style.lineHeight),
          tracking: style.letterSpacing === "normal" ? 0 : parseFloat(style.letterSpacing),
          left: box.left, right: box.right, bottom: box.bottom,
          width: window.innerWidth,
          fragments: Array.from(range.getClientRects(), rect => ({ left: rect.left, right: rect.right })),
        };
      });
      expect(geometry.lineHeight).toBeGreaterThanOrEqual(geometry.fontSize);
      expect(geometry.tracking).toBeGreaterThanOrEqual(0);
      expect(geometry.left).toBeGreaterThanOrEqual(0);
      expect(geometry.right).toBeLessThanOrEqual(geometry.width);
      for (const rect of geometry.fragments) {
        expect(rect.left).toBeGreaterThanOrEqual(geometry.left - 1);
        expect(rect.right).toBeLessThanOrEqual(geometry.right + 1);
      }
      const cta = await page.getByRole("link", { name: /See the plans/ }).first().boundingBox();
      expect(cta).not.toBeNull();
      expect(cta!.y).toBeGreaterThanOrEqual(geometry.bottom);
      if (!enlarged && viewport.width === 390) {
        await page.screenshot({ path: testInfo.outputPath("hero-iphone.png") });
      }
    }
  });

  test(`marketing headings stay readable at ${viewport.width}px`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto("/", { waitUntil: "domcontentloaded" });

    const headings = page.locator("main h1, main h2, main h3");
    await expect(headings).not.toHaveCount(0);

    for (const enlarged of [false, true]) {
      if (enlarged) {
        await page.addStyleTag({ content: "html { font-size: 32px !important; }" });
      }
      const measurements = await headings.evaluateAll((elements) => elements.map((element) => {
        const style = getComputedStyle(element);
        const box = element.getBoundingClientRect();
        const range = document.createRange();
        range.selectNodeContents(element);
        return {
          text: element.textContent?.trim(),
          fontFamily: style.fontFamily,
          fontSize: parseFloat(style.fontSize),
          lineHeight: parseFloat(style.lineHeight),
          tracking: style.letterSpacing === "normal" ? 0 : parseFloat(style.letterSpacing),
          left: box.left,
          right: box.right,
          fragments: Array.from(range.getClientRects(), rect => ({ left: rect.left, right: rect.right })),
        };
      }));

      for (const heading of measurements) {
        expect(heading.text).not.toBe("");
        expect(heading.fontFamily).not.toMatch(/Arial Black|Impact|Haettenschweiler|Arial Narrow Bold/i);
        expect(heading.tracking).toBeGreaterThanOrEqual(0);
        expect(heading.lineHeight).toBeGreaterThanOrEqual(heading.fontSize);
        expect(heading.left).toBeGreaterThanOrEqual(-1);
        expect(heading.right).toBeLessThanOrEqual(viewport.width + 1);
        for (const fragment of heading.fragments) {
          expect(fragment.left).toBeGreaterThanOrEqual(heading.left - 1);
          expect(fragment.right).toBeLessThanOrEqual(heading.right + 1);
          expect(fragment.right).toBeLessThanOrEqual(viewport.width + 1);
        }
      }
    }
  });
}
