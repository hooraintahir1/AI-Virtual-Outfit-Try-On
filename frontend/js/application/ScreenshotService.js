/**
 * Application layer — persist captures via backend.
 */
export class ScreenshotService {
  constructor(apiClient) {
    this.api = apiClient;
  }

  async save(canvasDataUrl, mode, outfitId) {
    return this.api.saveScreenshot(canvasDataUrl, mode, outfitId);
  }

  async list() {
    return this.api.listScreenshots();
  }
}
