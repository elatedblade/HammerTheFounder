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
}
