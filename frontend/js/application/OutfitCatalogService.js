/**
 * Application layer — outfit catalog and image cache.
 */
import { Outfit } from "../domain/Outfit.js";

export class OutfitCatalogService {
  constructor(apiClient) {
    this.api = apiClient;
    /** @type {Map<string, { outfit: Outfit, image: HTMLImageElement }>} */
    this.cache = new Map();
    this.selectedId = null;
  }

  async loadCatalog() {
    const rows = await this.api.getOutfits();
    const outfits = rows.map((r) => new Outfit(r));
    for (const outfit of outfits) {
      if (this.cache.has(outfit.id)) continue;
      const image = await this._loadImage(outfit.url);
      this.cache.set(outfit.id, { outfit, image });
    }
    return outfits.filter((o) => this.cache.has(o.id));
  }

  async addFromFile(file) {
    const saved = await this.api.uploadOutfit(file, file.name.replace(/\.png$/i, ""));
    const outfit = new Outfit(saved);
    const image = await this._loadImage(outfit.url);
    this.cache.set(outfit.id, { outfit, image });
    return outfit;
  }

  select(id) {
    this.selectedId = this.cache.has(id) ? id : null;
    return this.getSelectedImage();
  }

  getSelectedImage() {
    if (!this.selectedId) return null;
    return this.cache.get(this.selectedId)?.image ?? null;
  }

  getSelectedOutfit() {
    if (!this.selectedId) return null;
    return this.cache.get(this.selectedId)?.outfit ?? null;
  }

  getEntries() {
    return [...this.cache.values()];
  }

  _loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error(`Cannot load ${src}`));
      img.src = src;
    });
  }
}
