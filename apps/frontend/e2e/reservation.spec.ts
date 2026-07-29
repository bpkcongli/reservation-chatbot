import { expect, test, type Page, type TestInfo } from "@playwright/test";

import {
  boronganSteps,
  harianSteps,
  installConversationScenario,
} from "./support/conversation-api";

async function openChat(page: Page, testInfo: TestInfo): Promise<void> {
  await page.goto("/");
  await page.getByRole("button", { name: "Buka asisten reservasi" }).click();

  const dialog = page.getByRole("dialog", { name: "Asisten Reservasi" });
  await expect(dialog).toBeVisible();
  await expect(
    page.getByText("Halo! Selamat datang di layanan reservasi tukang."),
  ).toBeVisible();

  const box = await dialog.boundingBox();
  const viewport = page.viewportSize();
  expect(box).not.toBeNull();
  expect(viewport).not.toBeNull();

  if (testInfo.project.name === "mobile-chromium") {
    expect(Math.round(box!.width)).toBe(viewport!.width);
    expect(Math.round(box!.height)).toBe(viewport!.height);
    await expect
      .poll(() => page.evaluate(() => document.body.style.overflow))
      .toBe("hidden");
  } else {
    expect(box!.width).toBeLessThanOrEqual(420);
  }
}

async function chooseReply(
  page: Page,
  label: string,
  expectedBotText: string,
): Promise<void> {
  await page.getByRole("button", { name: label, exact: true }).click();
  await expect(page.getByText(expectedBotText, { exact: true })).toBeVisible();
}

async function sendMessage(
  page: Page,
  text: string,
  expectedBotText: string,
): Promise<void> {
  const composer = page.getByRole("textbox", { name: "Pesan" });
  await composer.fill(text);
  await page.getByRole("button", { name: "Kirim pesan" }).click();
  await expect(page.getByText(expectedBotText, { exact: true })).toBeVisible();
}

test("menyelesaikan happy path Jasa Borongan sampai tiket", async ({
  page,
}, testInfo) => {
  const scenario = await installConversationScenario(page, boronganSteps);
  await openChat(page, testInfo);

  await chooseReply(page, "Langsung reservasi", boronganSteps[0].botText);
  await chooseReply(page, "Jasa Borongan", boronganSteps[1].botText);
  await sendMessage(page, "0123456789", boronganSteps[2].botText);
  await sendMessage(page, "081234567890", boronganSteps[3].botText);
  await chooseReply(page, "Rumah", boronganSteps[4].botText);
  await sendMessage(
    page,
    "Jalan Melati No. 10 Jakarta",
    boronganSteps[5].botText,
  );
  await sendMessage(page, "2 Agustus 2026", boronganSteps[6].botText);
  await sendMessage(page, "09:00", boronganSteps[7].botText);
  await sendMessage(page, "20 juta", boronganSteps[8].botText);

  await expect(
    page.getByRole("heading", { name: "Ringkasan reservasi" }),
  ).toBeVisible();
  await expect(page.getByText(/5\.125\.000/)).toBeVisible();
  await expect(page.getByText(/20\.000\.000/).first()).toBeVisible();

  await chooseReply(page, "Ya, konfirmasi", boronganSteps[9].botText);
  await expect(
    page.getByRole("heading", {
      name: "Tiket reservasi berhasil dibuat",
    }),
  ).toBeVisible();
  await expect(
    page.getByText("TKT-20260729-B0R0NG", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Menunggu pembayaran")).toBeVisible();
  await page.getByRole("button", { name: "Salin nomor tiket" }).click();
  await expect(page.getByText("Tersalin")).toBeVisible();

  scenario.assertComplete();
});

test("menyelesaikan happy path Tukang Harian tanpa foto sampai tiket", async ({
  page,
}, testInfo) => {
  const scenario = await installConversationScenario(page, harianSteps);
  await openChat(page, testInfo);

  await chooseReply(page, "Langsung reservasi", harianSteps[0].botText);
  await chooseReply(page, "Tukang Harian", harianSteps[1].botText);
  await sendMessage(page, "0123456789", harianSteps[2].botText);
  await sendMessage(page, "081234567890", harianSteps[3].botText);
  await chooseReply(page, "Spesialis Listrik", harianSteps[4].botText);
  await sendMessage(
    page,
    "Instalasi listrik sering turun mendadak",
    harianSteps[5].botText,
  );
  await sendMessage(page, "2 orang", harianSteps[6].botText);
  await sendMessage(page, "2 Agustus 2026", harianSteps[7].botText);
  await sendMessage(page, "3 Agustus 2026", harianSteps[8].botText);
  await chooseReply(page, "Pagi", harianSteps[9].botText);
  await chooseReply(page, "Lewati foto", harianSteps[10].botText);
  await sendMessage(
    page,
    "Jalan Mawar No. 20 Jakarta Selatan",
    harianSteps[11].botText,
  );

  await expect(
    page.getByRole("heading", { name: "Ringkasan reservasi" }),
  ).toBeVisible();
  await expect(page.getByText(/805\.000/)).toBeVisible();
  await expect(page.getByText("Tidak dilampirkan")).toBeVisible();

  await chooseReply(page, "Ya, konfirmasi", harianSteps[12].botText);
  await expect(
    page.getByText("TKT-20260729-HAR1AN", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Menunggu pembayaran")).toBeVisible();

  scenario.assertComplete();
});
