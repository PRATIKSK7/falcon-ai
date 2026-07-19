// Web Worker for Real-time Optical Flow and Object Tracking
// Uses Frame Differencing and Centroid Tracking (Simplified SORT)

type Track = {
  id: number;
  x: number;
  y: number;
  dx: number;
  dy: number;
  historyX: number[];
  historyY: number[];
  missedFrames: number;
};

let previousGrayscale: Uint8ClampedArray | null = null;
let activeTracks: Track[] = [];
let nextTrackId = 1;

// Configuration
const THRESHOLD = 30; // Pixel intensity difference threshold
const MIN_BLOB_AREA = 20; // Minimum pixels to consider a blob
const MAX_DISTANCE = 50; // Max pixel distance to link tracks
const MAX_MISSED_FRAMES = 5;

// Helper: Convert RGBA to Grayscale
function toGrayscale(imageData: ImageData): Uint8ClampedArray {
  const data = imageData.data;
  const gray = new Uint8ClampedArray(imageData.width * imageData.height);
  for (let i = 0, j = 0; i < data.length; i += 4, j++) {
    gray[j] = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
  }
  return gray;
}

// Helper: Simple Blob Detection (Grid-based approximation for speed)
function detectBlobs(diff: Uint8ClampedArray, width: number, height: number, gridSize = 10) {
  const blobs: { x: number, y: number, mass: number }[] = [];
  
  for (let y = 0; y < height; y += gridSize) {
    for (let x = 0; x < width; x += gridSize) {
      let mass = 0;
      let cx = 0;
      let cy = 0;
      
      for (let dy = 0; dy < gridSize; dy++) {
        for (let dx = 0; dx < gridSize; dx++) {
          const px = x + dx;
          const py = y + dy;
          if (px < width && py < height) {
            const idx = py * width + px;
            if (diff[idx] > THRESHOLD) {
              mass++;
              cx += px;
              cy += py;
            }
          }
        }
      }
      
      if (mass >= MIN_BLOB_AREA) {
        blobs.push({ x: cx / mass, y: cy / mass, mass });
      }
    }
  }
  return blobs;
}

// Process Frame
self.onmessage = function (e) {
  const { imageData, width, height, isStampede } = e.data;
  
  const currentGrayscale = toGrayscale(imageData);
  
  if (!previousGrayscale) {
    previousGrayscale = currentGrayscale;
    self.postMessage({ tracks: [], metrics: null });
    return;
  }

  // Frame differencing
  const diff = new Uint8ClampedArray(width * height);
  for (let i = 0; i < diff.length; i++) {
    diff[i] = Math.abs(currentGrayscale[i] - previousGrayscale[i]);
  }
  previousGrayscale = currentGrayscale;

  // Detect moving blobs
  const blobs = detectBlobs(diff, width, height, 20); // 20px grid for speed

  // Link blobs to active tracks (Centroid Tracking)
  const unassignedBlobs = [...blobs];
  
  activeTracks.forEach(track => {
    let bestMatchIdx = -1;
    let minDistance = MAX_DISTANCE;

    for (let i = 0; i < unassignedBlobs.length; i++) {
      const blob = unassignedBlobs[i];
      const dist = Math.hypot(blob.x - track.x, blob.y - track.y);
      if (dist < minDistance) {
        minDistance = dist;
        bestMatchIdx = i;
      }
    }

    if (bestMatchIdx !== -1) {
      // Update track
      const match = unassignedBlobs[bestMatchIdx];
      const rawDx = match.x - track.x;
      const rawDy = match.y - track.y;
      
      // EMA Smoothing for motion vectors
      track.dx = track.dx * 0.7 + rawDx * 0.3;
      track.dy = track.dy * 0.7 + rawDy * 0.3;
      
      track.x = match.x;
      track.y = match.y;
      track.missedFrames = 0;
      
      track.historyX.push(match.x);
      track.historyY.push(match.y);
      if (track.historyX.length > 5) {
        track.historyX.shift();
        track.historyY.shift();
      }
      
      unassignedBlobs.splice(bestMatchIdx, 1);
    } else {
      track.missedFrames++;
    }
  });

  // Remove lost tracks
  activeTracks = activeTracks.filter(t => t.missedFrames < MAX_MISSED_FRAMES);

  // Spawn new tracks
  unassignedBlobs.forEach(blob => {
    activeTracks.push({
      id: nextTrackId++,
      x: blob.x,
      y: blob.y,
      dx: 0,
      dy: 0,
      historyX: [blob.x],
      historyY: [blob.y],
      missedFrames: 0
    });
  });

  // Calculate Metrics
  let avgDx = 0;
  let avgDy = 0;
  let variance = 0;
  let avgAngle = 0;
  
  if (activeTracks.length > 0) {
    activeTracks.forEach(t => {
      avgDx += t.dx;
      avgDy += t.dy;
    });
    avgDx /= activeTracks.length;
    avgDy /= activeTracks.length;
    avgAngle = Math.atan2(avgDy, avgDx) * (180 / Math.PI);

    // Variance (Directional Entropy proxy)
    activeTracks.forEach(t => {
      variance += Math.pow(t.dx - avgDx, 2) + Math.pow(t.dy - avgDy, 2);
    });
    variance /= activeTracks.length;
  }
  
  // Calculate Danger Zone if Stampede
  let dangerZone = null;
  if (isStampede && activeTracks.length > 0) {
    // Find the center of mass of tracks with highest variance
    let cx = 0, cy = 0;
    activeTracks.forEach(t => { cx += t.x; cy += t.y; });
    dangerZone = { x: cx / activeTracks.length, y: cy / activeTracks.length, radius: 100 }; // Radius in pixels relative to worker resolution
  }

  // Normalize tracks to percentages for easy UI rendering
  const normalizedTracks = activeTracks.map(t => ({
    id: t.id,
    x: (t.x / width) * 100,
    y: (t.y / height) * 100,
    dx: (t.dx / width) * 100,
    dy: (t.dy / height) * 100,
    speed: Math.hypot(t.dx, t.dy),
    angle: Math.atan2(t.dy, t.dx) * (180 / Math.PI)
  }));
  
  const normalizedDangerZone = dangerZone ? {
    x: (dangerZone.x / width) * 100,
    y: (dangerZone.y / height) * 100,
    radius: (dangerZone.radius / Math.min(width, height)) * 100
  } : null;

  self.postMessage({
    tracks: normalizedTracks,
    metrics: {
      averageDirection: avgAngle,
      entropy: variance,
      density: activeTracks.length,
      isChaotic: variance > 10 || isStampede
    },
    dangerZone: normalizedDangerZone
  });
};
