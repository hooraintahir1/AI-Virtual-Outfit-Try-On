
import { TryOnConfig } from "../domain/TryOnConfig.js";
import { TryOnMode } from "../domain/TryOnMode.js";
import { CameraService } from "../application/CameraService.js";
import { OutfitCatalogService } from "../application/OutfitCatalogService.js";
import { ScreenshotService } from "../application/ScreenshotService.js";
import { TryOnRenderService } from "../application/TryOnRenderService.js";

export class AppController {
  constructor(refs, services) {
    this.refs = refs;
    this.catalog = services.catalog;
    this.renderer = services.renderer;
    this.camera = services.camera;
    this.screenshots = services.screenshots;
    this.poseTracker = services.poseTracker;

    this.mode = TryOnMode.LIVE;
    this.animationId = null;
    this._liveRunning = false;
    this.photoLandmarks = null;
    this.photoLoaded = false;

    this._bindEvents();
  }

  _bindEvents() {
    const r = this.refs;
    r.tabs.forEach((tab) =>
      tab.addEventListener("click", () => this._setMode(tab.dataset.mode))
    );
    r.btnStart.addEventListener("click", () => this.startLive());
    r.btnStop.addEventListener("click", () => this.stopLive());
    r.btnCapture.addEventListener("click", () =>
      this.saveScreenshot(TryOnMode.LIVE)
    );
    r.btnCapturePhoto.addEventListener("click", () =>
      this.saveScreenshot(TryOnMode.PHOTO)
    );
    r.uploadPhoto.addEventListener("change", (e) => this.loadPhoto(e));
    r.btnDetectPhoto.addEventListener("click", () => this.detectPhotoPose());
    r.uploadOutfit.addEventListener("change", (e) => this.uploadOutfit(e));
    r.scale.addEventListener("input", () => {
      if (this.mode === TryOnMode.PHOTO) this._rerenderPhoto();
    });
    r.offsetY.addEventListener("input", () => {
      if (this.mode === TryOnMode.PHOTO) this._rerenderPhoto();
    });
    r.mirror.addEventListener("change", () => {
      if (this.mode === TryOnMode.LIVE && this.camera.isActive()) this._liveLoop();
      else this._rerenderPhoto();
    });
  }

  async init() {
    await this.poseTracker.init();
    this.refs.loading.classList.add("hidden");
    this.refs.btnStart.disabled = false;
    const outfits = await this.catalog.loadCatalog();
    this._renderOutfitGrid();
    if (outfits.length) this.catalog.select(outfits[0].id);
    await this.refreshGallery();
    this.setStatus("Ready — choose Live Webcam or Photo Try-On", true);
  }

  _config() {
    return new TryOnConfig({
      scale: parseFloat(this.refs.scale.value),
      offsetY: parseFloat(this.refs.offsetY.value),
      mirror: this.refs.mirror.checked,
    });
  }

  _setMode(mode) {
    this.mode = mode;
    this.refs.tabs.forEach((t) => {
      const active = t.dataset.mode === mode;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", active ? "true" : "false");
    });
    this.refs.livePanel.classList.toggle("hidden", mode !== TryOnMode.LIVE);
    this.refs.photoPanel.classList.toggle("hidden", mode !== TryOnMode.PHOTO);
    this.refs.mirror.disabled = mode !== TryOnMode.LIVE;

    if (mode === TryOnMode.LIVE) {
      this.refs.photoHint.classList.add("hidden");
      if (!this.camera.isActive()) this.refs.cameraHint.classList.remove("hidden");
    } else {
      this.stopLive();
      this.refs.cameraHint.classList.add("hidden");
      if (!this.photoLoaded) this.refs.photoHint.classList.remove("hidden");
      else this.refs.photoHint.classList.add("hidden");
    }
  }

  _renderOutfitGrid() {
    const grid = this.refs.outfitGrid;
    grid.innerHTML = "";
    for (const { outfit, image } of this.catalog.getEntries()) {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "outfit-card";
      card.dataset.id = outfit.id;
      card.title = outfit.name;
      const thumb = document.createElement("img");
      thumb.src = image.src;
      thumb.alt = outfit.name;
      card.append(thumb);
      card.addEventListener("click", () => {
        document.querySelectorAll(".outfit-card").forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");
        this.catalog.select(outfit.id);
        this.setStatus(`Selected: ${outfit.name}`, true);
        this._rerenderPhoto();
        if (this.camera.isActive()) this._liveLoop();
      });
      grid.append(card);
    }
    const selected = this.catalog.selectedId;
    if (selected) {
      grid.querySelector(`[data-id="${selected}"]`)?.classList.add("selected");
    }
  }

  async startLive() {
    if (this._liveRunning) return;
    try {
      this.poseTracker.clearCache();
      const settings = await this.camera.start();
      if (settings.width && settings.height) {
        this.renderer.resize(settings.width, settings.height);
      }
      this.refs.cameraHint.classList.add("hidden");
      this.refs.btnStart.disabled = true;
      this.refs.btnStop.disabled = false;
      this.refs.btnCapture.disabled = false;
      this.setStatus("Live try-on active", true);
      if (this.animationId) cancelAnimationFrame(this.animationId);
      this._liveRunning = true;
      const loop = async () => {
        if (!this._liveRunning) return;
        const landmarks = await this.poseTracker.detectVideo(this.refs.video);
        this.renderer.renderFrame(
          this.refs.video,
          landmarks,
          this.catalog.getSelectedImage(),
          this._config(),
          { mirrorBackground: this.refs.mirror.checked }
        );
        this.animationId = requestAnimationFrame(loop);
      };
      loop();
    } catch {
      this.refs.cameraHint.classList.remove("hidden");
      this.setStatus("Camera permission denied");
    }
  }

  stopLive() {
    this._liveRunning = false;
    if (this.animationId) cancelAnimationFrame(this.animationId);
    this.animationId = null;
    this.camera.stop();
    this.refs.btnStart.disabled = false;
    this.refs.btnStop.disabled = true;
    this.refs.btnCapture.disabled = true;
    this.setStatus("Camera stopped");
  }

  async loadPhoto(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    event.target.value = "";
    try {
      const img = await this._loadOrientedPhoto(file);
      this.refs.photoSource.src = img.src;
      this.refs.photoSource.onload = null;
      this.renderer.resize(img.naturalWidth, img.naturalHeight);
      this.photoLoaded = true;
      this.refs.photoHint.classList.add("hidden");
      this.refs.btnDetectPhoto.disabled = false;
      this.refs.btnCapturePhoto.disabled = false;
      await this.detectPhotoPose();
    } catch {
      this.setStatus("Could not load photo");
    }
  }

  async _loadOrientedPhoto(file) {
    const bitmap = await createImageBitmap(file, {
      imageOrientation: "from-image",
    });
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    canvas.getContext("2d").drawImage(bitmap, 0, 0);
    bitmap.close();
    const dataUrl = canvas.toDataURL("image/png");
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = dataUrl;
    });
  }

  async detectPhotoPose() {
    if (!this.refs.photoSource.src) return;
    this.setStatus("Detecting pose in photo…");
    this.photoLandmarks = await this.poseTracker.detectImage(this.refs.photoSource);
    this._rerenderPhoto();
    this.setStatus(
      this.photoLandmarks ? "Pose detected — outfit applied" : "No pose found — use a clearer photo",
      !!this.photoLandmarks
    );
  }

  _rerenderPhoto() {
    if (this.mode !== TryOnMode.PHOTO || !this.photoLoaded) return;
    const cfg = this._config();
    this.renderer.renderFrame(
      this.refs.photoSource,
      this.photoLandmarks,
      this.catalog.getSelectedImage(),
      { ...cfg, mirror: false },
      { mirrorBackground: false }
    );
  }

  _liveLoop() {

  }

  async saveScreenshot(mode) {
    try {
      const outfit = this.catalog.getSelectedOutfit();
      const result = await this.screenshots.save(
        this.renderer.toDataURL(),
        mode,
        outfit?.id
      );
      this.setStatus(`Saved: ${result.filename}`, true);
      await this.refreshGallery();
    } catch (err) {
      this.setStatus(`Save failed: ${err.message}`);
    }
  }

  async uploadOutfit(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await this.catalog.addFromFile(file);
      this._renderOutfitGrid();
      this.setStatus("Outfit added to catalog", true);
    } catch (err) {
      this.setStatus(err.message);
    }
    event.target.value = "";
  }

  async refreshGallery() {
    const list = await this.screenshots.list();
    const container = this.refs.gallery;
    if (!list.length) {
      container.innerHTML = '<p class="empty-gallery">No screenshots yet.</p>';
      return;
    }
    container.innerHTML = "";
    for (const item of list.slice(0, 12)) {
      const a = document.createElement("a");
      a.href = item.url;
      a.target = "_blank";
      a.title = item.filename;
      const img = document.createElement("img");
      img.src = item.url;
      img.alt = item.filename;
      a.append(img);
      container.append(a);
    }
  }

  setStatus(text, active = false) {
    this.refs.status.textContent = text;
    this.refs.status.classList.toggle("active", active);
  }

  dispose() {
    this.stopLive();
    this.poseTracker.close();
  }
}
