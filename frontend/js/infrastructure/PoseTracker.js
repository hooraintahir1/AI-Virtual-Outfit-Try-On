/**
 * Infrastructure — MediaPipe pose landmarker adapter.
 */
import {
  FilesetResolver,
  PoseLandmarker,
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14";

const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

export class PoseTracker {
  #landmarker = null;
  #lastVideoTime = -1;
  #lastDetectMs = 0;
  #cachedLandmarks = null;
  #mode = "VIDEO";

  async init() {
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
    );
    this.#landmarker = await PoseLandmarker.createFromOptions(vision, {
      baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
      runningMode: "VIDEO",
      numPoses: 1,
    });
    this.#mode = "VIDEO";
  }

  async detectVideo(video) {
    if (!this.#landmarker || video.readyState < 2) {
      return this.#cachedLandmarks;
    }
    if (this.#mode !== "VIDEO") {
      this.#landmarker.setOptions({ runningMode: "VIDEO" });
      this.#mode = "VIDEO";
      this.#lastVideoTime = -1;
    }

    const now = performance.now();
    const frameAdvanced = video.currentTime !== this.#lastVideoTime;
    const throttleElapsed = now - this.#lastDetectMs >= 33;

    // Run detection on new frames or periodically; never return null if we have a cache
    if (frameAdvanced || throttleElapsed) {
      this.#lastVideoTime = video.currentTime;
      this.#lastDetectMs = now;
      const result = this.#landmarker.detectForVideo(video, now);
      const pose = result.landmarks?.[0];
      if (pose) {
        this.#cachedLandmarks = pose;
      }
    }

    return this.#cachedLandmarks;
  }

  /**
   * Single-frame detection for uploaded photos.
   * @param {HTMLImageElement | HTMLCanvasElement} imageSource
   */
  async detectImage(imageSource) {
    if (!this.#landmarker) return null;
    if (this.#mode !== "IMAGE") {
      this.#landmarker.setOptions({ runningMode: "IMAGE" });
      this.#mode = "IMAGE";
      this.#cachedLandmarks = null;
    }
    const result = this.#landmarker.detect(imageSource);
    const pose = result.landmarks?.[0] ?? null;
    this.#cachedLandmarks = pose;
    return pose;
  }

  clearCache() {
    this.#cachedLandmarks = null;
    this.#lastVideoTime = -1;
    this.#lastDetectMs = 0;
  }

  close() {
    this.#landmarker?.close();
    this.#landmarker = null;
    this.#cachedLandmarks = null;
  }
}
