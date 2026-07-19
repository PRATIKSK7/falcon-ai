import { useQuery } from '@tanstack/react-query';
import { aiService } from '../services/api';
import { Cpu, Activity, Loader2, AlertTriangle, Database, Zap, Layers } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../lib/utils';

export function AiModel() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['ai-health'],
    queryFn: aiService.getHealth,
    refetchInterval: 5000,
  });

  if (isLoading) {
    return (
      <div className="h-[80vh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="h-[80vh] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto">
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-semibold text-red-500">Backend Offline</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            {error instanceof Error ? error.message : "Unable to connect to the FastAPI inference engine."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Engine Health</h1>
        <p className="text-muted-foreground mt-1 text-[10px] tracking-widest uppercase font-mono">
          Real-time status of the neural pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatusCard 
          icon={Activity}
          title="Backend API"
          value={data.backend_running ? "ONLINE" : "OFFLINE"}
          subtitle={`Version ${data.api_version}`}
          active={data.backend_running}
        />
        <StatusCard 
          icon={Cpu}
          title="Inference Engine"
          value={data.tensorflow_loaded ? "INITIALIZED" : "UNAVAILABLE"}
          subtitle={`Running on ${data.gpu_cpu_status}`}
          active={data.tensorflow_loaded}
        />
        <StatusCard 
          icon={Database}
          title="VideoMAE Weights"
          value={data.model_loaded ? "RESIDENT" : "NOT LOADED"}
          subtitle={data.model_loaded ? "Ready for inference" : "Awaiting load"}
          active={data.model_loaded}
        />
        <StatusCard 
          icon={Layers}
          title="Computer Vision"
          value={data.opencv_available ? "ACTIVE" : "MISSING"}
          subtitle="OpenCV cv2 bindings"
          active={data.opencv_available}
        />
        <StatusCard 
          icon={Zap}
          title="Emergency Alerts"
          value={data.twilio_configured ? "CONFIGURED" : "DISABLED"}
          subtitle="Twilio REST Client"
          active={data.twilio_configured}
        />
      </div>
    </div>
  );
}

function StatusCard({ icon: Icon, title, value, subtitle, active }: any) {
  return (
    <motion.div 
      whileHover={{ y: -4 }}
      className="glass-panel rounded-2xl p-6 relative overflow-hidden flex flex-col"
    >
      <div className={`absolute -right-4 -top-4 w-24 h-24 rounded-full blur-2xl opacity-20 ${active ? 'bg-primary' : 'bg-red-500'}`} />
      <div className="flex items-start justify-between z-10 relative">
        <div className={cn(
          "p-3 rounded-xl border flex items-center justify-center shadow-lg", 
          active ? 'bg-black/60 border-primary/30 text-cyan-400' : 'bg-red-950/40 border-red-500/30 text-red-500'
        )}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="mt-6 z-10 relative flex-1">
        <p className="text-[10px] tracking-widest font-mono text-muted-foreground uppercase">{title}</p>
        <h3 className={cn(
          "text-2xl font-black mt-2 tracking-wide font-mono",
          active ? 'text-foreground' : 'text-red-400'
        )}>{value}</h3>
      </div>
      <div className="mt-4 z-10 relative border-t border-white/5 pt-4">
         <p className="text-[10px] text-muted-foreground font-mono">{subtitle}</p>
      </div>
    </motion.div>
  );
}
