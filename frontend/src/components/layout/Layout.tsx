import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { motion, AnimatePresence } from 'framer-motion';

export function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-background relative selection:bg-primary/30 selection:text-primary-foreground text-foreground">
      {/* Immersive Background Effects */}
      <div className="absolute inset-0 bg-cyber-grid pointer-events-none z-0 opacity-60" />
      <div className="absolute top-0 left-[20%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-0 right-[10%] w-[600px] h-[600px] bg-accent/5 rounded-full blur-[150px] pointer-events-none z-0" />
      
      {/* Sidebar */}
      <div className="z-20 relative border-r border-border/50 bg-background/50 backdrop-blur-xl">
        <Sidebar />
      </div>

      <div className="flex-1 flex flex-col overflow-hidden relative z-10">
        <Header />
        <main className="flex-1 overflow-y-auto relative">
          <AnimatePresence mode="wait">
            <motion.div
              initial={{ opacity: 0, filter: 'blur(4px)' }}
              animate={{ opacity: 1, filter: 'blur(0px)' }}
              exit={{ opacity: 0, filter: 'blur(4px)' }}
              transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              className="h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
