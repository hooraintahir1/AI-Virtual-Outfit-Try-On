/**
 * Entry point — wires presentation layer to application & infrastructure.
 */
import { ApiClient } from "../infrastructure/ApiClient.js";
import { PoseTracker } from "../infrastructure/PoseTracker.js";
import { OutfitCatalogService } from "../application/OutfitCatalogService.js";
import { ScreenshotService } from "../application/ScreenshotService.js";
import { TryOnRenderService } from "../application/TryOnRenderService.js";
import { CameraService } from "../application/CameraService.js";
import { AppController } from "./AppController.js";

const canvas = document.getElementById("output");
const video = document.getElementById("video");
const photoSource = document.getElementById("photo-source");

const api = new ApiClient("");
const catalog = new OutfitCatalogService(api);
const renderer = new TryOnRenderService(canvas);
const camera = new CameraService(video);
const screenshots = new ScreenshotService(api);
const poseTracker = new PoseTracker();

const controller = new AppController(
  {
    loading: document.getElementById("loading"),
    cameraHint: document.getElementById("camera-hint"),
    photoHint: document.getElementById("photo-hint"),
    outfitGrid: document.getElementById("outfit-grid"),
    gallery: document.getElementById("screenshot-gallery"),
    status: document.getElementById("status"),
    video,
    photoSource,
    tabs: [...document.querySelectorAll(".tab")],
    livePanel: document.getElementById("live-controls"),
    photoPanel: document.getElementById("photo-controls"),
    btnStart: document.getElementById("btn-start"),
    btnStop: document.getElementById("btn-stop"),
    btnCapture: document.getElementById("btn-capture"),
    btnCapturePhoto: document.getElementById("btn-capture-photo"),
    btnDetectPhoto: document.getElementById("btn-detect-photo"),
    uploadPhoto: document.getElementById("upload-photo"),
    uploadOutfit: document.getElementById("upload-outfit"),
    scale: document.getElementById("scale"),
    offsetY: document.getElementById("offset-y"),
    mirror: document.getElementById("mirror"),
  },
  { catalog, renderer, camera, screenshots, poseTracker }
);

controller.init().catch((err) => {
  console.error(err);
  document.getElementById("status").textContent =
    "Startup failed. Run: python backend/main.py";
});

window.addEventListener("beforeunload", () => controller.dispose());
