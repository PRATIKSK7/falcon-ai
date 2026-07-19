import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Video, 
  ShieldAlert, 
  LineChart, 
  Camera, 
  Cpu, 
  Activity, 
  History, 
  BellRing, 
  Settings,
  Flame
} from 'lucide-react';

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: Video, label: 'Live Monitor', path: '/monitor' },
  { icon: ShieldAlert, label: 'Incidents', path: '/incidents' },
  { icon: LineChart, label: 'Analytics', path: '/analytics' },
  { icon: Camera, label: 'Cameras', path: '/cameras' },
  { icon: Cpu, label: 'AI Engine', path: '/ai-model' },
  { icon: Activity, label: 'System Health', path: '/health' },
  { icon: History, label: 'History', path: '/history' },
  { icon: BellRing, label: 'Alerts', path: '/alerts' },
  { icon: Settings, label: 'Settings', path: '/settings' },
];

export function Sidebar() {
  return (
    <aside className="w-64 h-full flex flex-col pt-8 pb-6 shadow-[4px_0_24px_rgba(0,0,0,0.6)] z-30 relative overflow-hidden bg-gradient-to-b from-[#030b1c] to-[#07132a] border-r border-white/5">
      {/* Noise Texture */}
      <div className="absolute inset-0 opacity-[0.015] pointer-events-none" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }} />

      {/* Logo Area */}
      <div className="px-6 mb-12 flex items-center gap-3 relative z-10">
        <div className="w-7 h-7 rounded bg-primary/20 flex items-center justify-center border border-primary/40 shadow-[0_0_10px_rgba(14,165,233,0.3)] shrink-0">
          <Flame className="w-4 h-4 text-primary" />
        </div>
        <div className="flex flex-col">
          <h2 className="text-lg font-bold tracking-wide text-foreground leading-none">FALCON AI</h2>
          <p className="text-[8px] uppercase tracking-widest text-muted-foreground mt-1.5 leading-tight">Intelligent Stampede<br/>Detection System</p>
        </div>
      </div>

      {/* Section Label */}
      <div className="px-6 mb-3 relative z-10">
        <p className="text-[10px] font-semibold text-white/30 tracking-widest uppercase">Command Center</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-2 overflow-y-auto no-scrollbar relative z-10">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 relative group ${
                isActive 
                  ? 'bg-[#0a1930] shadow-sm' 
                  : 'hover:bg-white/[0.03] hover:shadow-sm'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-cyan-400 rounded-r-sm" />
                )}
                <item.icon className={`w-4 h-4 transition-all duration-200 ${
                  isActive ? 'text-white' : 'text-muted-foreground group-hover:text-white group-hover:scale-110'
                }`} />
                <span className={`font-medium text-sm tracking-wide transition-colors duration-200 ${
                  isActive ? 'text-cyan-400' : 'text-muted-foreground group-hover:text-white'
                }`}>
                  {item.label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
      
      {/* System Status Card */}
      <div className="px-4 mt-6 relative z-10">
        <div className="border border-white/10 bg-black/20 rounded-lg p-4 flex flex-col backdrop-blur-sm">
          <h4 className="text-[10px] font-bold text-white/40 tracking-widest uppercase mb-3 text-center border-b border-white/5 pb-2">
            System Status
          </h4>
          
          <div className="space-y-2.5">
            <StatusRow label="AI Engine" status="ONLINE" />
            <StatusRow label="Backend" status="CONNECTED" />
            <StatusRow label="Twilio" status="READY" />
            <StatusRow label="TensorFlow" status="ACTIVE" />
          </div>
          
          <div className="mt-4 pt-3 border-t border-white/5 text-center">
            <p className="text-[9px] text-white/30 font-mono tracking-wider">Version v2.1.0</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

function StatusRow({ label, status }: { label: string, status: string }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
        <span className="text-xs text-muted-foreground font-medium">{label}</span>
      </div>
      <span className="text-[10px] text-cyan-400 font-mono tracking-wider">{status}</span>
    </div>
  );
}
