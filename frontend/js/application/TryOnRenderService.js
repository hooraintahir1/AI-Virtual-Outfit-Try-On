/**
 * Application layer — composes background + outfit overlay.
 */
import { TryOnConfig } from "../domain/TryOnConfig.js";
import {
  drawBackground,
  drawGuidanceText,
  drawOutfitOnPose,
} from "../infrastructure/OutfitRenderer.js";

export class TryOnRenderService {
  /**
   * @param {HTMLCanvasElement} canvas
   */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
  }

  resize(width, height) {
    this.canvas.width = width;
    this.canvas.height = height;
  }

  /**
   * @param {HTMLVideoElement|HTMLImageElement} source
   * @param {Array|null} landmarks
   * @param {HTMLImageElement|null} outfitImg
   * @param {TryOnConfig} config
   * @param {{ mirrorBackground?: boolean }} opts
   */
  renderFrame(source, landmarks, outfitImg, config, opts = {}) {
    const w = this.canvas.width;
    const h = this.canvas.height;
    const mirrorBg = opts.mirrorBackground ?? config.mirror;

    this.ctx.clearRect(0, 0, w, h);
    drawBackground(this.ctx, source, w, h, mirrorBg);

    if (landmarks && outfitImg) {
      const ok = drawOutfitOnPose(
        this.ctx,
        outfitImg,
        landmarks,
        w,
        h,
        config
      );
      if (!ok) {
        drawGuidanceText(
          this.ctx,
          "Move so shoulders and torso are visible",
          w,
          h
        );
      }
    } else if (outfitImg && !landmarks) {
      drawGuidanceText(this.ctx, "Detect pose or face the camera", w, h);
    }
  }

  toDataURL() {
    return this.canvas.toDataURL("image/png");
  }
}
