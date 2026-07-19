import { motion } from 'framer-motion';
import { ShieldAlert, Video, BellRing, Activity, Cpu, PlaySquare, AlertTriangle, Info } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const mockMseData = [
  { time: '10:10', mse: 0.005, threshold: 0.020 },
  { time: '10:15', mse: 0.008, threshold: 0.020 },
  { time: '10:20', mse: 0.004, threshold: 0.020 },
  { time: '10:25', mse: 0.019, threshold: 0.020 }, // Spike
  { time: '10:30', mse: 0.012, threshold: 0.020 },
];

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants: any = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

export function Dashboard() {
  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6 pb-12"
    >
      {/* Massive Hero Section */}
      <motion.div variants={itemVariants} className="relative w-full h-[400px] rounded-3xl overflow-hidden border border-primary/20 shadow-[0_0_50px_rgba(14,165,233,0.15)] group">
        <div className="absolute inset-0 bg-black" />
        
        {/* Falcon Eyes Image */}
        <img 
          src="/src/assets/falcon_eyes.png" 
          alt="Falcon AI Core Vision" 
          className="absolute inset-0 w-full h-full object-cover opacity-80 mix-blend-screen scale-105 group-hover:scale-100 transition-transform duration-[10s] ease-out"
        />
        
        {/* Gradients to fade edges */}
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-black/50" />
        <div className="absolute inset-0 bg-gradient-to-r from-background via-transparent to-background/80" />
        
        {/* HUD Scanning Grid Overlay */}
        <div className="absolute inset-0 bg-cyber-grid opacity-30 mix-blend-overlay" />
        <div className="absolute inset-0 scanline opacity-20 mix-blend-screen" />
        
        {/* Typography Content */}
        <div className="absolute inset-0 flex flex-col justify-center px-16 z-10">
          <motion.div 
            initial={{ opacity: 0, x: -30 }} 
            animate={{ opacity: 1, x: 0 }} 
            transition={{ delay: 0.5, duration: 1 }}
          >
            <h2 className="text-xl font-mono text-primary/80 uppercase tracking-[0.3em] mb-2 drop-shadow-[0_0_10px_rgba(14,165,233,0.8)]">We don't just watch.</h2>
            <h1 className="text-7xl font-black text-white tracking-tighter mb-4 drop-shadow-[0_0_20px_rgba(14,165,233,0.5)]">WE PROTECT.</h1>
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium tracking-widest text-muted-foreground uppercase border-b border-primary/30 pb-1">FALCON AI</span>
              <div className="w-12 h-px bg-primary shadow-[0_0_10px_rgba(14,165,233,1)]" />
              <div className="w-2 h-2 rounded bg-primary animate-pulse shadow-[0_0_10px_rgba(14,165,233,1)]" />
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <KpiCard title="Active Cameras" value="128" trend="+12% vs yesterday" icon={Video} color="cyan" />
        <KpiCard title="Total Incidents" value="7" trend="-22% vs yesterday" icon={ShieldAlert} color="red" />
        <KpiCard title="Alerts Today" value="23" trend="+8% vs yesterday" icon={BellRing} color="yellow" />
        <KpiCard title="System Uptime" value="99.8%" trend="All systems normal" icon={Activity} color="emerald" />
        <KpiCard title="Processing FPS" value="24.5" trend="Optimal" icon={Cpu} color="purple" />
      </div>

      {/* Tri-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[500px]">
        
        {/* Column 1: Live Camera Feed */}
        <motion.div variants={itemVariants} className="lg:col-span-4 glass-panel rounded-2xl p-5 flex flex-col relative group border border-border/50">
          <h3 className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-4 flex justify-between items-center">
            Live Camera Feed
            <span className="text-primary hover:text-cyan-300 cursor-pointer text-[10px]">VIEW ALL</span>
          </h3>
          
          <div className="flex-1 rounded-xl overflow-hidden relative border border-white/10 bg-black mb-4 group-hover:border-primary/30 transition-colors">
            <div className="absolute top-3 left-3 px-2 py-0.5 bg-red-500/80 backdrop-blur rounded text-[10px] font-bold tracking-wider text-white flex items-center gap-1.5 shadow-[0_0_10px_rgba(239,68,68,0.5)] z-10">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" /> LIVE
            </div>
            
            {/* Fake Video Feed (We use a gradient + scanning line for the aesthetic mockup, assuming real video goes here) */}
            <div className="absolute inset-0 bg-slate-900">
              <div className="absolute inset-0 bg-cyber-grid opacity-20" />
              <div className="absolute inset-0 scanline opacity-30 mix-blend-screen" />
              
              {/* Fake Bounding Boxes */}
              <div className="absolute top-1/4 left-1/4 w-12 h-20 border border-cyan-500/50 bg-cyan-500/10 shadow-[0_0_10px_rgba(6,182,212,0.3)]" />
              <div className="absolute top-1/3 left-1/2 w-16 h-24 border border-cyan-500/50 bg-cyan-500/10 shadow-[0_0_10px_rgba(6,182,212,0.3)]" />
              <div className="absolute bottom-1/4 right-1/4 w-14 h-22 border border-red-500/80 bg-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.5)]" />
            </div>

            {/* Alert Overlay */}
            <div className="absolute bottom-3 left-3 right-3 glass-panel border border-red-500/40 p-2.5 rounded-lg flex items-center gap-3 bg-red-500/10 z-10">
              <div className="w-8 h-8 rounded bg-red-500/20 flex items-center justify-center">
                <BellRing className="w-4 h-4 text-red-500 animate-pulse" />
              </div>
              <div>
                <p className="text-xs font-bold text-red-400">Density Alert</p>
                <p className="text-[10px] text-red-400/80 font-mono">Gate A - Platform 2</p>
              </div>
            </div>
          </div>
          
          {/* Thumbnails */}
          <div className="grid grid-cols-4 gap-2 h-16">
            <Thumbnail id="01" active />
            <Thumbnail id="02" />
            <Thumbnail id="03" />
            <Thumbnail id="04" />
          </div>
        </motion.div>

        {/* Column 2: AI Pipeline & Chart */}
        <motion.div variants={itemVariants} className="lg:col-span-5 flex flex-col gap-6">
          {/* AI Analysis Overview */}
          <div className="glass-panel rounded-2xl p-5 border border-border/50 h-[180px]">
            <h3 className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-4 flex justify-between items-center">
              AI Analysis Overview
              <span className="text-[10px] text-primary/70 bg-primary/10 px-2 py-0.5 rounded border border-primary/20">Real-time Processing</span>
            </h3>
            
            <div className="flex items-center justify-between mt-6 px-4">
              <PipelineNode icon={PlaySquare} label="Frames" sub="Extracting" active />
              <div className="flex-1 h-px bg-gradient-to-r from-primary/50 to-primary/10 mx-2 relative">
                <div className="absolute right-0 -top-1 w-2 h-2 border-t border-r border-primary/50 rotate-45" />
              </div>
              <PipelineNode icon={Cpu} label="Preprocessing" sub="96x96 Gray" active />
              <div className="flex-1 h-px bg-gradient-to-r from-primary/50 to-primary/10 mx-2 relative">
                <div className="absolute right-0 -top-1 w-2 h-2 border-t border-r border-primary/50 rotate-45" />
              </div>
              <PipelineNode icon={Activity} label="AI Engine" sub="Autoencoder" active />
              <div className="flex-1 h-px bg-gradient-to-r from-primary/50 to-transparent mx-2 relative">
                <div className="absolute right-0 -top-1 w-2 h-2 border-t border-r border-primary/20 rotate-45" />
              </div>
              <PipelineNode icon={ShieldAlert} label="Anomaly Score" sub="Scanning..." pending />
            </div>
          </div>
          
          {/* MSE Chart */}
          <div className="glass-panel rounded-2xl p-5 border border-border/50 flex-1 relative group">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
            <h3 className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-4">
              Reconstruction Error (MSE)
            </h3>
            <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={mockMseData} margin={{ top: 10, right: 30, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorMse" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorThreshold" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#ef4444" stopOpacity={0.8}/>
                      <stop offset="100%" stopColor="#ef4444" stopOpacity={0.2}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                  <XAxis dataKey="time" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#475569" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(v) => v.toFixed(3)} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'rgba(2,6,23,0.95)', border: '1px solid rgba(14,165,233,0.3)', borderRadius: '8px', boxShadow: '0 0 20px rgba(14,165,233,0.2)' }}
                    itemStyle={{ color: '#fff' }}
                    labelStyle={{ color: '#94a3b8' }}
                  />
                  <ReferenceLine y={0.02} stroke="url(#colorThreshold)" strokeDasharray="4 4" strokeWidth={1} label={{ position: 'insideTopRight', value: 'Threshold 0.020', fill: '#ef4444', fontSize: 10 }} />
                  <Area type="monotone" dataKey="mse" stroke="#0ea5e9" fillOpacity={1} fill="url(#colorMse)" strokeWidth={2} activeDot={{ r: 4, fill: '#0ea5e9', stroke: '#fff', strokeWidth: 2, className: "animate-pulse shadow-[0_0_10px_rgba(14,165,233,1)]" }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>

        {/* Column 3: Health & Alerts */}
        <motion.div variants={itemVariants} className="lg:col-span-3 flex flex-col gap-6">
          
          {/* Holographic System Health */}
          <div className="glass-panel rounded-2xl p-5 border border-border/50 h-[240px] flex flex-col relative overflow-hidden group">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/10 via-transparent to-transparent opacity-50" />
            <h3 className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2 z-10">
              System Health
            </h3>
            
            <div className="flex-1 flex items-center justify-between relative z-10">
              <div className="relative w-32 h-32 flex items-center justify-center -ml-4">
                <div className="absolute inset-0 rounded-full border-[0.5px] border-primary/20 border-t-primary/60 animate-[spin_10s_linear_infinite]" />
                <div className="absolute inset-4 rounded-full border-[0.5px] border-accent/20 border-b-accent/60 animate-[spin_6s_linear_infinite_reverse]" />
                <div className="absolute inset-8 rounded-full border-[0.5px] border-cyan-400/20 border-l-cyan-400/60 animate-[spin_8s_linear_infinite]" />
                <img 
                  src="/src/assets/falcon_hologram.png" 
                  alt="Hologram" 
                  className="w-24 h-24 object-contain mix-blend-screen opacity-90 drop-shadow-[0_0_15px_rgba(14,165,233,0.8)] z-10 group-hover:scale-110 transition-transform duration-700" 
                />
              </div>
              
              <div className="flex flex-col gap-3 text-xs font-mono w-[100px]">
                <div className="flex justify-between items-center"><span className="text-muted-foreground">AI Engine</span> <span className="text-emerald-400">Healthy</span></div>
                <div className="flex justify-between items-center"><span className="text-muted-foreground">Database</span> <span className="text-emerald-400">Healthy</span></div>
                <div className="flex justify-between items-center"><span className="text-muted-foreground">Cameras</span> <span className="text-foreground">128/128</span></div>
                <div className="flex justify-between items-center"><span className="text-muted-foreground">Storage</span> <span className="text-primary">78%</span></div>
                <div className="flex justify-between items-center"><span className="text-muted-foreground">Network</span> <span className="text-primary">Stable</span></div>
              </div>
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="glass-panel rounded-2xl p-5 border border-border/50 flex-1 flex flex-col">
            <h3 className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-4 flex justify-between items-center">
              Recent Alerts
              <span className="text-primary hover:text-cyan-300 cursor-pointer text-[10px]">VIEW ALL</span>
            </h3>
            
            <div className="flex-1 space-y-3 overflow-y-auto no-scrollbar pr-2">
              <AlertItem type="danger" title="Stampede Detected" loc="Main Gate - Platform 1" time="10:20 AM" />
              <AlertItem type="warning" title="High Density Warning" loc="North Exit - Area B" time="10:15 AM" />
              <AlertItem type="info" title="System Check" loc="All systems operational" time="10:10 AM" />
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

// Subcomponents

function KpiCard({ title, value, trend, icon: Icon, color }: any) {
  const colorMap: Record<string, string> = {
    cyan: 'bg-primary/10 text-primary border-primary/30 shadow-[0_0_15px_rgba(14,165,233,0.15)] group-hover:border-primary/50 group-hover:shadow-[0_0_25px_rgba(14,165,233,0.3)]',
    red: 'bg-red-500/10 text-red-500 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.15)] group-hover:border-red-500/50 group-hover:shadow-[0_0_25px_rgba(239,68,68,0.3)]',
    yellow: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30 shadow-[0_0_15px_rgba(234,179,8,0.15)] group-hover:border-yellow-500/50 group-hover:shadow-[0_0_25px_rgba(234,179,8,0.3)]',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.15)] group-hover:border-emerald-500/50 group-hover:shadow-[0_0_25px_rgba(16,185,129,0.3)]',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.15)] group-hover:border-purple-500/50 group-hover:shadow-[0_0_25px_rgba(168,85,247,0.3)]',
  };
  
  const textColors: Record<string, string> = {
    cyan: 'text-primary', red: 'text-red-500', yellow: 'text-yellow-500', emerald: 'text-emerald-400', purple: 'text-purple-400'
  };

  return (
    <motion.div variants={itemVariants} whileHover={{ y: -4 }} className={`glass-panel rounded-xl p-4 flex items-center gap-4 border transition-all duration-300 group ${colorMap[color]}`}>
      <div className={`w-10 h-10 rounded-lg bg-black/40 border border-white/5 flex items-center justify-center ${textColors[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1">
        <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono mb-1">{title}</p>
        <div className="flex items-end gap-2">
          <h4 className="text-2xl font-bold leading-none text-foreground">{value}</h4>
          <span className={`text-[9px] mb-0.5 ${trend.includes('+') ? 'text-emerald-400' : trend.includes('-') ? 'text-red-400' : 'text-muted-foreground'}`}>{trend}</span>
        </div>
      </div>
    </motion.div>
  );
}

function Thumbnail({ id, active = false }: { id: string, active?: boolean }) {
  return (
    <div className={`relative rounded-lg overflow-hidden border ${active ? 'border-primary shadow-[0_0_10px_rgba(14,165,233,0.3)]' : 'border-white/10 opacity-60'} cursor-pointer hover:opacity-100 transition-opacity bg-black`}>
      <div className="absolute inset-0 bg-cyber-grid opacity-30" />
      <span className={`absolute bottom-1 left-2 text-[8px] font-mono ${active ? 'text-primary' : 'text-muted-foreground'}`}>Cam {id}</span>
    </div>
  );
}

function PipelineNode({ icon: Icon, label, sub, active, pending }: any) {
  return (
    <div className="flex flex-col items-center gap-2 group">
      <div className={`w-10 h-10 rounded-xl border flex items-center justify-center transition-all ${active ? 'border-primary/50 bg-primary/10 shadow-[0_0_15px_rgba(14,165,233,0.3)]' : 'border-white/10 bg-black/40 opacity-50'}`}>
        <Icon className={`w-5 h-5 ${active ? 'text-primary' : 'text-muted-foreground'} ${pending ? 'animate-pulse' : ''}`} />
      </div>
      <div className="text-center">
        <p className={`text-[10px] font-bold tracking-wider uppercase ${active ? 'text-foreground' : 'text-muted-foreground'}`}>{label}</p>
        <p className="text-[9px] text-muted-foreground/60">{sub}</p>
      </div>
    </div>
  );
}

function AlertItem({ type, title, loc, time }: any) {
  const styles = {
    danger: { icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/20' },
    warning: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
    info: { icon: Info, color: 'text-primary', bg: 'bg-primary/10', border: 'border-primary/20' },
  };
  const s = styles[type as keyof typeof styles];
  const Icon = s.icon;
  
  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${s.border} bg-black/40 hover:${s.bg} transition-colors cursor-pointer group`}>
      <Icon className={`w-4 h-4 mt-0.5 ${s.color} group-hover:scale-110 transition-transform`} />
      <div className="flex-1">
        <p className={`text-xs font-bold ${s.color}`}>{title}</p>
        <div className="flex justify-between items-center mt-1">
          <p className="text-[10px] text-muted-foreground">{loc}</p>
          <span className="text-[9px] text-muted-foreground/60 font-mono">{time}</span>
        </div>
      </div>
    </div>
  );
}
