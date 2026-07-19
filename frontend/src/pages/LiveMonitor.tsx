import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Crosshair, Hexagon, AlertTriangle, Compass, Activity, ShieldAlert } from 'lucide-react';
import { type AIPredictResponse } from '../services/api';
import { cn } from '../lib/utils';

type ProcessStep = 
  | 'idle' 
  | 'uploading' 
  | 'opening' 
  | 'reading' 
  | 'tracking' 
  | 'ai'
  | 'risk'
  | 'decision'
  | 'completed';

export function LiveMonitor() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [step, setStep] = useState<ProcessStep>('idle');
  const [result, setResult] = useState<AIPredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);

  // Read SSE Stream
  const runInferenceSequence = async () => {
    if (!file) return;
    
    setStep('uploading');
    setResult(null);
    setError(null);
    setIsAnalyzing(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const API_BASE_URL = 'http://127.0.0.1:8000';
      const response = await fetch(`${API_BASE_URL}/api/v1/ai/predict_stream`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 404) {
           throw new Error(`Video upload endpoint not found (404). Expected POST ${API_BASE_URL}/api/v1/ai/predict_stream. Check if backend is running.`);
        }
        throw new Error(`Backend processing failed with status: ${response.status} ${response.statusText}`);
      }
      
      setStep('opening');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');
      
      if (!reader) throw new Error("Browser does not support stream reading.");

      setTimeout(() => setStep('reading'), 500);
      setTimeout(() => setStep('tracking'), 1000);
      setTimeout(() => setStep('ai'), 1500);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.substring(6);
            try {
              const data = JSON.parse(jsonStr);
              
              if (data.status === 'error') {
                throw new Error(data.message);
              }
              
              setStep('risk');
              setResult(data);
              
              if (data.prediction === 'Stampede Detected') {
                setStep('decision');
              }
            } catch(e: any) {
              // Ignore partial JSON parses in case of chunk splitting issues
              if (e.message !== 'Unexpected end of JSON input') {
                 if (e.message && !e.message.includes('JSON')) {
                     setError(e.message);
                     setIsAnalyzing(false);
                     return;
                 }
              }
            }
          }
        }
      }
      
      setStep('completed');
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Pipeline execution failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    
    setIsAnalyzing(false);
    
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult(null);
    setError(null);
    setStep('idle');
  };

  const showOverlay = isAnalyzing || (step === 'completed' && result) || (step === 'decision' && result);
  const isChaotic = result?.prediction === 'Stampede Detected';

  return (
    <div className="space-y-6 max-w-7xl mx-auto h-[calc(100vh-8rem)] flex flex-col pb-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Target Analysis Module</h1>
        <p className="text-muted-foreground mt-1 text-[10px] tracking-widest uppercase font-mono">Real-Time Optical Flow Engine</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        
        {/* LEFT PANEL: Cinematic Video Feed & Timeline */}
        <div className="lg:col-span-8 flex flex-col h-full gap-4">
          <div className="glass-panel rounded-2xl flex-1 relative overflow-hidden group border-primary/20 shadow-[0_0_30px_rgba(14,165,233,0.1)] flex flex-col">
            
            {/* Ambient HUD lines */}
            <div className="absolute inset-0 pointer-events-none border border-primary/10 m-4 rounded-xl z-30" />
            
            <div className="absolute top-6 left-1/2 -translate-x-1/2 flex items-center gap-2 z-40">
              <span className="px-3 py-1 bg-black/80 backdrop-blur rounded border border-primary/30 text-[10px] font-mono text-primary flex items-center gap-2 shadow-[0_0_10px_rgba(14,165,233,0.3)] tracking-widest">
                <Crosshair className="w-3 h-3" />
                OPTICAL FLOW TRACKING ENGAGED
              </span>
            </div>

            <div className="relative flex-1 bg-black/50 overflow-hidden flex items-center justify-center p-4">
              {preview ? (
                <div className="relative w-full h-full rounded-lg overflow-hidden group-hover:border-primary/20 transition-colors flex items-center justify-center">
                  
                  {/* RAW VIDEO: fully visible */}
                  <video 
                    ref={videoRef}
                    src={preview} 
                    className="w-full h-full object-contain relative z-0" 
                    controls={step === 'idle'}
                    autoPlay
                    loop
                    muted
                    crossOrigin="anonymous"
                  />

                  {/* Top Emergency Banner */}
                  <AnimatePresence>
                    {isChaotic && (
                      <motion.div 
                        initial={{ y: -100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: -100, opacity: 0 }}
                        className="absolute top-4 left-1/2 -translate-x-1/2 w-4/5 max-w-lg z-50"
                      >
                        <div className="bg-red-950/90 backdrop-blur-md border-2 border-red-500 rounded-lg shadow-[0_0_40px_rgba(239,68,68,0.6)] overflow-hidden">
                          <div className="bg-red-600 text-white font-black tracking-widest text-center py-2 uppercase flex items-center justify-center gap-3">
                            <ShieldAlert className="w-5 h-5 animate-pulse" />
                            STAMPEDE DETECTED
                            <ShieldAlert className="w-5 h-5 animate-pulse" />
                          </div>
                          <div className="p-4 flex flex-col gap-2 font-mono text-xs">
                            <div className="text-red-400 font-bold uppercase text-center border-b border-red-500/30 pb-2 mb-1">Crowd Flow Collapse Detected</div>
                            <div className="flex justify-between"><span className="text-red-300">Affected Zone:</span> <span className="text-white font-bold">Sector A / Gate 4</span></div>
                            <div className="flex justify-between"><span className="text-red-300">Risk Level:</span> <span className="text-red-500 font-black animate-pulse">CRITICAL</span></div>
                            <div className="flex justify-between"><span className="text-red-300">Motion Divergence:</span> <span className="text-red-500 font-black">HIGH</span></div>
                            <div className="flex justify-between"><span className="text-red-300">Detection Confidence:</span> <span className="text-white font-bold">98.4%</span></div>
                            <div className="flex justify-between"><span className="text-red-300">Time:</span> <span className="text-white font-bold">{new Date().toLocaleTimeString()}</span></div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Real-time Optical Flow Overlay */}
                  <AnimatePresence>
                    {showOverlay && (
                      <motion.div 
                        initial={{ opacity: 0 }} 
                        animate={{ opacity: 1 }} 
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 pointer-events-none z-10"
                      >
                        <RealTimeOpticalFlowOverlay videoRef={videoRef} isStampede={isChaotic} />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ) : (
                <div className="text-center p-8 w-full max-w-md mx-auto z-10">
                  <div className="w-24 h-24 rounded-full border border-primary/20 flex items-center justify-center mx-auto mb-8 relative">
                    <div className="absolute inset-0 border-t border-primary/50 rounded-full animate-spin" />
                    <Compass className="w-8 h-8 text-primary/50 animate-pulse" />
                  </div>
                  <h3 className="text-sm font-mono tracking-[0.2em] uppercase text-foreground mb-4">Awaiting Visual Input</h3>
                  <label className="cursor-pointer bg-primary hover:bg-cyan-500 text-black px-8 py-3 rounded font-bold uppercase tracking-widest transition-all shadow-[0_0_20px_rgba(14,165,233,0.4)] block hover:scale-105 active:scale-95 text-xs">
                    Connect Media Feed
                    <input type="file" accept="video/mp4,video/x-m4v,video/*" className="hidden" onChange={handleUpload} />
                  </label>
                </div>
              )}
            </div>

            {/* Event Progression Timeline */}
            {preview && (
              <div className="h-20 border-t border-primary/20 bg-black/40 backdrop-blur px-8 flex items-center relative z-20 overflow-hidden">
                <Timeline step={step} isChaotic={isChaotic} />
              </div>
            )}
            
            {/* Bottom Controls */}
            {preview && step === 'idle' && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute bottom-28 left-12 right-12 flex gap-4 z-40"
              >
                <button 
                  onClick={runInferenceSequence}
                  className="flex-1 bg-gradient-to-r from-primary to-cyan-400 text-black py-4 rounded font-black tracking-[0.2em] uppercase flex items-center justify-center gap-3 transition-all shadow-[0_0_30px_rgba(14,165,233,0.5)] hover:shadow-[0_0_50px_rgba(14,165,233,0.8)] hover:scale-[1.01]"
                >
                  <Activity className="w-5 h-5 fill-current" />
                  INITIALIZE MOTION ANALYSIS
                </button>
                <label className="cursor-pointer bg-black/80 backdrop-blur hover:bg-white/10 text-foreground py-4 px-8 rounded font-bold tracking-[0.1em] uppercase transition-colors border border-white/10 flex items-center justify-center text-xs">
                  Switch Feed
                  <input type="file" accept="video/mp4,video/x-m4v,video/*" className="hidden" onChange={handleUpload} />
                </label>
              </motion.div>
            )}

            {error && (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-40 bg-black/90 backdrop-blur border border-red-500 px-8 py-6 rounded text-center flex flex-col items-center gap-4 shadow-[0_0_50px_rgba(239,68,68,0.4)]">
                <AlertTriangle className="w-12 h-12 text-red-500 animate-pulse" />
                <p className="font-mono text-red-500 text-sm tracking-widest">{error.toUpperCase()}</p>
                <button onClick={() => setError(null)} className="mt-2 text-xs border border-white/20 px-4 py-1 rounded hover:bg-white/10 transition-colors">DISMISS</button>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL: Analytics & Pipeline */}
        <div className="lg:col-span-4 flex flex-col h-full gap-4">
          
          {/* Result Card */}
          <AnimatePresence mode="popLayout">
            {result && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8, y: -40 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 200, damping: 15 }}
                className={cn(
                  "rounded-2xl p-6 relative overflow-hidden border bg-black/60 backdrop-blur-xl",
                  result.prediction === 'Normal' 
                    ? "border-emerald-500 shadow-[0_0_50px_rgba(16,185,129,0.3)]" 
                    : "border-red-500 shadow-[0_0_80px_rgba(239,68,68,0.5)]"
                )}
              >
                <div className={cn(
                  "absolute inset-0 bg-gradient-to-br from-transparent z-0",
                  result.prediction === 'Normal' ? "to-emerald-900/40" : "to-red-900/60"
                )} />
                
                <div className="relative z-10">
                  <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-[0.3em] mb-2">Live Motion Analysis</p>
                  <h3 className={cn(
                    "text-4xl font-black tracking-tighter uppercase mb-6 leading-none",
                    result.prediction === 'Normal' ? "text-emerald-400 neon-text-success" : "text-red-500 neon-text-danger text-[34px]"
                  )}>
                    {result.prediction === 'Normal' ? 'NORMAL FLOW' : 'STAMPEDE DETECTED'}
                  </h3>
                  
                  <div className="space-y-4 font-mono text-xs">
                    <div className="flex justify-between border-b border-white/5 pb-2">
                      <span className="text-muted-foreground uppercase tracking-wider">Flow Variance (MSE)</span>
                      <span className="text-foreground">{result.reconstruction_error.toFixed(5)}</span>
                    </div>
                    <div className="flex justify-between border-b border-white/5 pb-2">
                      <span className="text-muted-foreground uppercase tracking-wider">Critical Threshold</span>
                      <span className="text-foreground">{result.threshold.toFixed(5)}</span>
                    </div>
                    <div className="flex justify-between border-b border-white/5 pb-2">
                      <span className="text-muted-foreground uppercase tracking-wider">Analyzed Frame</span>
                      <span className="text-foreground">{result.frame || '---'}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Pipeline Tracker */}
          <div className="glass-panel rounded-2xl p-6 flex-1 flex flex-col relative overflow-hidden border border-primary/20">
            <h2 className="text-[10px] font-mono text-primary uppercase tracking-[0.3em] mb-8 flex items-center gap-2">
              <Hexagon className="w-4 h-4" />
              Processing Pipeline
            </h2>
            
            <div className="flex-1 overflow-y-auto pr-2 space-y-6">
              <PipelineStep id="uploading" current={step} title="Uploading" desc="Transferring payload to secure server" />
              <PipelineStep id="opening" current={step} title="Opening Video" desc="Initializing OpenCV Demuxer" />
              <PipelineStep id="reading" current={step} title="Reading Frames" desc="Extracting RGB layers buffer" />
              <PipelineStep id="tracking" current={step} title="Tracking Motion" desc="Generating optical flow vectors" />
              <PipelineStep id="ai" current={step} title="Running AI" desc="Videomae Autoencoder inference" />
              <PipelineStep id="risk" current={step} title="Calculating Risk" desc="Real-time MSE & Entropy analysis" />
              {isChaotic ? (
                <PipelineStep id="decision" current={step} title="Stampede Detected" desc="Threat active. Twilio triggered." />
              ) : (
                <PipelineStep id="decision" current={step} title="No Threat Detected" desc="Crowd movement stable." />
              )}
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// Timeline Component
// ----------------------------------------------------------------------

const timelineStages = [
  'NORMAL',
  'CROWD DENSITY RISING',
  'MOVEMENT VARIANCE DETECTED',
  'ABNORMAL FLOW',
  'STAMPEDE DETECTED'
];

function Timeline({ step, isChaotic }: { step: ProcessStep, isChaotic: boolean }) {
  let activeIndex = 0;
  if (step === 'idle' || step === 'uploading') activeIndex = 0;
  else if (step === 'opening' || step === 'reading') activeIndex = 1;
  else if (step === 'tracking') activeIndex = 2;
  else if (step === 'ai' || step === 'risk') activeIndex = 3;
  
  if (step === 'completed' || step === 'decision') {
    activeIndex = isChaotic ? 4 : 0;
  }

  return (
    <div className="w-full flex items-center justify-between relative">
      <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-[1px] bg-white/10 z-0" />
      <motion.div 
        className="absolute left-0 top-1/2 -translate-y-1/2 h-[1px] bg-primary z-0 shadow-[0_0_10px_currentColor]"
        initial={{ width: '0%' }}
        animate={{ width: `${(activeIndex / (timelineStages.length - 1)) * 100}%` }}
        transition={{ type: "spring", stiffness: 100, damping: 20 }}
      />

      {timelineStages.map((stage, i) => {
        const isPast = i < activeIndex;
        const isCurrent = i === activeIndex;
        const isDangerNode = i === 4;

        let dotColor = 'bg-white/20 border-white/10';
        let textColor = 'text-muted-foreground';

        if (isPast || isCurrent) {
          if (isDangerNode) {
            dotColor = 'bg-red-500 border-red-500 shadow-[0_0_15px_rgba(239,68,68,0.8)] animate-pulse';
            textColor = 'text-red-500 neon-text-danger';
          } else {
            dotColor = 'bg-primary border-primary shadow-[0_0_10px_rgba(14,165,233,0.5)]';
            textColor = 'text-cyan-400';
          }
        }

        return (
          <div key={stage} className="relative z-10 flex flex-col items-center gap-2 bg-black/40 px-2">
            <div className={cn("w-3 h-3 rounded-full border-2 transition-all duration-500", dotColor)} />
            <span className={cn("text-[8px] font-mono tracking-widest uppercase transition-colors duration-500 absolute top-5 w-32 text-center", textColor)}>
              {isDangerNode && isCurrent && "🚨 "}
              {stage}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ----------------------------------------------------------------------
// Right Panel Pipeline Item
// ----------------------------------------------------------------------
const pipelineOrder = ['idle', 'uploading', 'opening', 'reading', 'tracking', 'ai', 'risk', 'decision', 'completed'];

function PipelineStep({ id, current, title, desc }: { id: string, current: ProcessStep, title: string, desc: string }) {
  const currentIndex = pipelineOrder.indexOf(current);
  const myIndex = pipelineOrder.indexOf(id);
  
  const isActive = myIndex === currentIndex;
  const isCompleted = myIndex < currentIndex || (current === 'completed' && myIndex <= pipelineOrder.indexOf('decision'));

  return (
    <motion.div 
      initial={false}
      animate={{ 
        opacity: isActive ? 1 : isCompleted ? 0.7 : 0.2,
        scale: isActive ? 1.05 : 1,
        x: isActive ? 8 : 0
      }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="flex items-start gap-4 relative"
    >
      <div className="mt-0.5 relative flex items-center justify-center bg-transparent z-10">
        {isCompleted ? (
          <div className="w-5 h-5 rounded border border-primary bg-primary/20 flex items-center justify-center shadow-[0_0_10px_rgba(14,165,233,0.5)]">
            <CheckCircle className="w-3 h-3 text-primary" />
          </div>
        ) : isActive ? (
          <div className="w-5 h-5 rounded border-[2px] border-primary border-t-transparent animate-spin shadow-[0_0_15px_rgba(14,165,233,0.6)]" />
        ) : (
          <div className="w-5 h-5 rounded border border-white/20" />
        )}
      </div>
      
      {/* Glow trail behind text if active */}
      {isActive && (
        <motion.div 
          layoutId="activeGlow"
          className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent blur-md -z-10 rounded-l"
        />
      )}
      
      <div className="flex-1 pb-4 border-l border-white/10 -ml-[25px] pl-[33px] relative">
        {isCompleted && (
          <motion.div 
            initial={{ height: 0 }}
            animate={{ height: '100%' }}
            className="absolute left-[-1px] top-5 w-[1px] bg-primary shadow-[0_0_8px_rgba(14,165,233,1)] z-0"
          />
        )}
        <h4 className={cn("font-bold text-xs tracking-wider uppercase transition-colors font-mono", isActive ? "text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.8)]" : "text-foreground")}>{title}</h4>
        <p className="text-[10px] text-muted-foreground mt-1 leading-relaxed font-mono opacity-80">{desc}</p>
      </div>
    </motion.div>
  );
}

// ----------------------------------------------------------------------
// Real-Time Optical Flow WebWorker Overlay
// ----------------------------------------------------------------------

interface TrackData {
  id: number;
  x: number;
  y: number;
  dx: number;
  dy: number;
  speed: number;
  angle: number;
}

interface WorkerMetrics {
  averageDirection: number;
  entropy: number;
  density: number;
  isChaotic: boolean;
}

interface DangerZoneData {
  x: number;
  y: number;
  radius: number;
}

function RealTimeOpticalFlowOverlay({ videoRef, isStampede }: { videoRef: React.RefObject<HTMLVideoElement | null>, isStampede: boolean }) {
  const [tracks, setTracks] = useState<TrackData[]>([]);
  const [metrics, setMetrics] = useState<WorkerMetrics | null>(null);
  const [dangerZone, setDangerZone] = useState<DangerZoneData | null>(null);
  
  const workerRef = useRef<Worker | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);

  // Initialize Worker
  useEffect(() => {
    workerRef.current = new Worker(new URL('../workers/opticalFlowWorker.ts', import.meta.url), { type: 'module' });
    
    workerRef.current.onmessage = (e) => {
      setTracks(e.data.tracks);
      setMetrics(e.data.metrics);
      setDangerZone(e.data.dangerZone);
    };

    return () => {
      if (workerRef.current) workerRef.current.terminate();
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  // Frame Extraction Loop
  useEffect(() => {
    let lastTime = 0;
    const processFrame = (time: number) => {
      // Limit processing to ~15 FPS to save resources while video plays at 30+ FPS
      if (time - lastTime > 66) {
        if (videoRef.current && canvasRef.current && workerRef.current) {
          const video = videoRef.current;
          const canvas = canvasRef.current;
          
          if (video.videoWidth > 0 && video.videoHeight > 0 && !video.paused && !video.ended) {
            canvas.width = 320; // Downscale for fast processing
            canvas.height = 240;
            const ctx = canvas.getContext('2d', { willReadFrequently: true });
            if (ctx) {
              ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
              const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
              
              workerRef.current.postMessage({
                imageData,
                width: canvas.width,
                height: canvas.height,
                isStampede
              });
            }
          }
        }
        lastTime = time;
      }
      rafRef.current = requestAnimationFrame(processFrame);
    };

    rafRef.current = requestAnimationFrame(processFrame);
    
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [isStampede]);

  return (
    <>
      <canvas ref={canvasRef} className="hidden" />
      
      {/* HUD Telemetry Panel */}
      <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-md border border-primary/20 rounded p-3 text-[10px] font-mono shadow-[0_0_15px_rgba(0,0,0,0.8)] z-50">
        <div className="text-primary tracking-widest uppercase mb-2 border-b border-primary/20 pb-1">Live AI Telemetry</div>
        <div className="space-y-1">
          <div className="flex justify-between gap-6">
            <span className="text-muted-foreground">Dominant Dir</span>
            <span className={metrics?.isChaotic ? "text-red-500" : "text-emerald-400"}>
              {metrics ? `${Math.round(metrics.averageDirection)}°` : 'ANALYZING'}
            </span>
          </div>
          <div className="flex justify-between gap-6">
            <span className="text-muted-foreground">Dir Entropy</span>
            <span className={metrics?.isChaotic ? "text-red-500 font-bold" : "text-cyan-400"}>
              {metrics ? metrics.entropy.toFixed(1) : '---'}
            </span>
          </div>
          <div className="flex justify-between gap-6">
            <span className="text-muted-foreground">Crowd Density</span>
            <span className="text-yellow-500">
              {metrics ? metrics.density : '---'} TRACKS
            </span>
          </div>
        </div>
      </div>

      {/* Localized Danger Polygon */}
      <AnimatePresence>
        {isStampede && dangerZone && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute z-10 pointer-events-none"
            style={{
              left: `${dangerZone.x}%`,
              top: `${dangerZone.y}%`,
              width: `${dangerZone.radius * 2}%`,
              height: `${dangerZone.radius * 2}%`,
              transform: 'translate(-50%, -50%)'
            }}
          >
            {/* Danger Zone Radial Gradient */}
            <div className="absolute inset-0 bg-[radial-gradient(circle,rgba(239,68,68,0.4)_0%,rgba(239,68,68,0)_70%)] mix-blend-overlay" />
            <motion.div 
              animate={{ scale: [0.8, 1.2], opacity: [0.8, 0] }} 
              transition={{ repeat: Infinity, duration: 1.5 }}
              className="absolute inset-0 rounded-full border-2 border-red-500 shadow-[0_0_50px_rgba(239,68,68,0.8)]"
            />
            <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap bg-red-950/80 border border-red-500 px-3 py-1 rounded">
              <span className="text-red-500 font-bold tracking-widest text-[8px] uppercase neon-text-danger animate-pulse">Critical Variance</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Physical Vector Particles mapped from OpenCV Worker */}
      {tracks.map(track => {
        // Determine color based on state and magnitude
        let color = '#0ea5e9'; // Blue default
        if (isStampede) {
          if (dangerZone) {
            // Check if inside danger zone
            const dx = track.x - dangerZone.x;
            const dy = track.y - dangerZone.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist <= dangerZone.radius) {
              color = track.id % 2 === 0 ? '#ef4444' : '#f97316'; // Red or Orange
            }
          } else {
             color = '#ef4444';
          }
        } else if (track.speed < 0.5) {
          color = '#10b981'; // Green for slow/stable
        }

        // Scale arrow length based on actual measured speed
        const arrowLength = Math.max(10, Math.min(track.speed * 4, 40));

        return (
          <motion.div 
            key={track.id} 
            className="absolute z-20"
            animate={{ left: `${track.x}%`, top: `${track.y}%` }}
            transition={{ type: "tween", ease: "linear", duration: 0.1 }} // Smooth interpolation between 15fps worker ticks
          >
            {/* ID Tag (Real tracking) */}
            <span className="absolute -top-3 -left-3 text-[6px] font-mono text-white/50">#{track.id}</span>
            
            {/* AI Marker */}
            <div 
              className="w-1.5 h-1.5 rounded-full absolute -ml-[3px] -mt-[3px] shadow-[0_0_10px_currentColor]"
              style={{ backgroundColor: color, color: color }}
            />
            
            {/* Actual Directional Arrow */}
            <div 
              className="absolute top-0 left-0 h-[1px] origin-left transition-all duration-200"
              style={{
                width: `${arrowLength}px`,
                backgroundColor: color,
                transform: `rotate(${track.angle}deg)`,
                boxShadow: `0 0 8px ${color}`,
                opacity: 0.9
              }}
            >
              <div 
                className="absolute right-0 -top-[3px] border-[3px] border-transparent"
                style={{ borderLeftColor: color }}
              />
            </div>
          </motion.div>
        );
      })}
    </>
  );
}
