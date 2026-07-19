import { Bell, User, Search } from 'lucide-react';
import { useState, useEffect } from 'react';

export function Header() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-20 border-b border-border/50 bg-background/40 backdrop-blur-md flex items-center justify-between px-8 sticky top-0 z-10 w-full">
      <div className="flex items-center gap-4 flex-1">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-foreground">Welcome, Pratik</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Deputy Superintendent of Police (Control Room)</p>
        </div>
      </div>
      
      <div className="flex items-center gap-8">
        
        {/* System Status */}
        <div className="flex flex-col items-end">
          <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest mb-1">System Status</span>
          <div className="px-3 py-1 rounded-sm bg-success/10 border border-success/30 text-success text-xs font-bold tracking-wide flex items-center gap-2 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
            OPERATIONAL
          </div>
        </div>

        {/* Live Clock */}
        <div className="flex flex-col items-end min-w-[120px]">
          <span className="text-sm font-mono text-foreground">{time.toLocaleTimeString()}</span>
          <span className="text-[10px] text-muted-foreground">{time.toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' })}</span>
        </div>

        {/* Search */}
        <button className="w-10 h-10 rounded-full border border-border/50 bg-background/50 flex items-center justify-center hover:bg-secondary/20 hover:border-primary/50 transition-all text-muted-foreground hover:text-primary">
          <Search className="w-4 h-4" />
        </button>
        
        {/* Notifications */}
        <button className="w-10 h-10 rounded-full border border-border/50 bg-background/50 flex items-center justify-center hover:bg-secondary/20 hover:border-primary/50 transition-all text-muted-foreground hover:text-primary relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-danger border-2 border-background shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
        </button>

        <div className="h-8 w-px bg-border/50 mx-2" />
        
        {/* Profile */}
        <button className="flex items-center gap-3 hover:bg-secondary/10 p-1.5 pr-4 rounded-full border border-transparent hover:border-border/50 transition-all">
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-secondary to-primary flex items-center justify-center shadow-[0_0_15px_rgba(14,165,233,0.3)]">
            <User className="w-4 h-4 text-white" />
          </div>
          <div className="flex flex-col items-start">
            <span className="text-sm font-semibold text-foreground">Pratik</span>
            <span className="text-[10px] text-muted-foreground">DSP</span>
          </div>
        </button>
      </div>
    </header>
  );
}
