import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

// Placeholder Pages - We will create these next
import Home from './pages/Home';
import Upload from './pages/Upload';
import Result from './pages/Result';

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Home />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/result" element={<Result />} />
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <AnimatedRoutes />
      </div>
    </Router>
  );
}

export default App;
