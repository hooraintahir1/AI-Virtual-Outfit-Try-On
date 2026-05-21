/**
 * Infrastructure — canvas drawing and pose-to-garment alignment.
 */

const L = {
  LEFT_SHOULDER: 11,
  RIGHT_SHOULDER: 12,
};

const MIN_VISIBILITY = 0.5;

function isVisible(lm) {
  return (lm?.visibility ?? 1) >= MIN_VISIBILITY;
}

/**
 * Draw background (video or photo) on canvas.
 */
export function drawBackground(ctx, source, width, height, mirror) {
  ctx.save();
  if (mirror) {
    ctx.translate(width, 0);
    ctx.scale(-1, 1);
  }
  ctx.drawImage(source, 0, 0, width, height);
  ctx.restore();
}

/**
 * Overlay transparent PNG outfit aligned to pose landmarks.
 * @returns {boolean} true if drawn successfully
 */
export function drawOutfitOnPose(ctx, outfitImg, landmarks, width, height, config) {
  const ls = landmarks[L.LEFT_SHOULDER];
  const rs = landmarks[L.RIGHT_SHOULDER];

  if (!ls || !rs || !isVisible(ls) || !isVisible(rs)) return false;

  // Screen space — matches mirrored or normal video background
  const toScreen = (lm) => ({
    x: (config.mirror ? 1 - lm.x : lm.x) * width,
    y: lm.y * height,
  });

  // Camera space — used only for rotation (mirror must not flip angle)
  const toCamera = (lm) => ({
    x: lm.x * width,
    y: lm.y * height,
  });

  const camLeft = toCamera(ls);
  const camRight = toCamera(rs);
  const left = toScreen(ls);
  const right = toScreen(rs);

  const shoulderMid = {
    x: (left.x + right.x) / 2,
    y: (left.y + right.y) / 2,
  };

  const shoulderWidth = Math.hypot(right.x - left.x, right.y - left.y);

  // Rotation from real body geometry (person's left → right in camera frame)
  const angle = Math.atan2(camLeft.y - camRight.y, camLeft.x - camRight.x);
  const drawWidth = shoulderWidth * config.scale;
  const drawHeight = drawWidth * (outfitImg.height / outfitImg.width);
  const anchorY = shoulderMid.y + config.offsetY;
  // Anchor near neckline (top of garment image)
  const pivotY = drawHeight * 0.18;

  ctx.save();
  ctx.translate(shoulderMid.x, anchorY);
  ctx.rotate(angle);
  ctx.drawImage(outfitImg, -drawWidth / 2, -pivotY, drawWidth, drawHeight);
  ctx.restore();
  return true;
}

export function drawGuidanceText(ctx, message, width, height) {
  ctx.fillStyle = "rgba(255,255,255,0.85)";
  ctx.font = "15px Segoe UI, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(message, width / 2, height - 28);
}
