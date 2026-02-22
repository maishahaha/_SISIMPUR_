import { test, expect } from "@playwright/test";

test.describe("Dashboard layout", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
    // Wait for the page to be rendered
    await page.waitForSelector("h1", { timeout: 10000 });
  });

  test("page title is 'Create New Quiz'", async ({ page }) => {
    await expect(page.locator("h1")).toHaveText("Create New Quiz");
  });

  test("Quiz Status panel is rendered on the right side of the form", async ({ page }) => {
    // On lg+ viewports the grid has two columns, quiz-status-panel is the right column
    await page.setViewportSize({ width: 1280, height: 900 });

    const quizStatusPanel = page.getByTestId("quiz-status-panel");
    await expect(quizStatusPanel).toBeVisible();

    // The left column contains the upload drop-zone / form
    const dropZone = page.locator("text=Upload your study material");
    await expect(dropZone).toBeVisible();

    // Get bounding boxes to verify right-side placement
    const formBox = await dropZone.boundingBox();
    const panelBox = await quizStatusPanel.boundingBox();

    expect(formBox).not.toBeNull();
    expect(panelBox).not.toBeNull();

    // Quiz Status panel must start to the RIGHT of the upload drop-zone
    expect(panelBox!.x).toBeGreaterThan(formBox!.x);
  });

  test("Quiz Status panel heading reads 'Quiz Status'", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    const panel = page.getByTestId("quiz-status-panel");
    await expect(panel.locator("h3")).toHaveText("Quiz Status");
  });

  test("Quiz Status panel is always present (not conditional)", async ({ page }) => {
    // The panel must be visible even before any job is submitted
    await page.setViewportSize({ width: 1280, height: 900 });
    await expect(page.getByTestId("quiz-status-panel")).toBeVisible();
  });

  test("Generate Quiz button is in the left column", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });

    const generateBtn = page.locator("button", { hasText: "Generate Quiz" });
    await expect(generateBtn).toBeVisible();

    const quizStatusPanel = page.getByTestId("quiz-status-panel");
    const btnBox = await generateBtn.boundingBox();
    const panelBox = await quizStatusPanel.boundingBox();

    expect(btnBox).not.toBeNull();
    expect(panelBox).not.toBeNull();

    // Generate button must be LEFT of the Quiz Status panel
    expect(btnBox!.x).toBeLessThan(panelBox!.x);
  });

  test("Recent Activity section is in the left column", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });

    const recentActivity = page.locator("text=Recent Activity");
    await expect(recentActivity).toBeVisible();

    const quizStatusPanel = page.getByTestId("quiz-status-panel");
    const activityBox = await recentActivity.boundingBox();
    const panelBox = await quizStatusPanel.boundingBox();

    expect(activityBox).not.toBeNull();
    expect(panelBox).not.toBeNull();

    // Recent Activity must be LEFT of the Quiz Status panel
    expect(activityBox!.x).toBeLessThan(panelBox!.x);
  });
});
