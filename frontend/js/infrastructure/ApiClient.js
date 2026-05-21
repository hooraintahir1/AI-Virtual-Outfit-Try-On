
export class ApiClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
  }

  async getOutfits() {
    const res = await fetch(`${this.baseUrl}/api/outfits`);
    if (!res.ok) throw new Error("Failed to load outfits");
    const data = await res.json();
    return data.outfits ?? [];
  }

  async uploadOutfit(file, name) {
    const form = new FormData();
    form.append("file", file);
    form.append("name", name || file.name);
    const res = await fetch(`${this.baseUrl}/api/outfits`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Upload failed");
    }
    return res.json();
  }

  async saveScreenshot(dataUrl, mode, outfitId) {
    const res = await fetch(`${this.baseUrl}/api/screenshots`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: dataUrl, mode, outfitId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Save failed");
    }
    return res.json();
  }

  async listScreenshots() {
    const res = await fetch(`${this.baseUrl}/api/screenshots`);
    if (!res.ok) throw new Error("Failed to list screenshots");
    const data = await res.json();
    return data.screenshots ?? [];
  }
}
