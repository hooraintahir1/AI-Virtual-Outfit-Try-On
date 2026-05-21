/**
 * Domain value object — rendering parameters for outfit overlay.
 */
export class TryOnConfig {
  /**
   * @param {{ scale?: number, offsetY?: number, mirror?: boolean }} params
   */
  constructor(params = {}) {
    this.scale = params.scale ?? 1.35;
    this.offsetY = params.offsetY ?? 0;
    this.mirror = params.mirror ?? true;
  }
}
