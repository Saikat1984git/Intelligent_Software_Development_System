import { Routes, Route, Outlet } from 'react-router-dom';
import DashboardLayout from './components/DashboardLayout'; // Ensure path is correct
import Codegen from './pages/Codegen';
import Codeedit from './pages/Codeedit';

function App() {
  return (
    <Routes>
      {/* This parent route renders the Layout. 
        The <Outlet /> inside DashboardLayout is replaced by the child elements below.
      */}
      <Route element={<DashboardLayout><Outlet /></DashboardLayout>}>
        <Route path="/" element={<Codegen />} />
        <Route path="/codegen" element={<Codegen />} />
        <Route path="/codemod" element={<Codeedit />} />
        <Route path="/sysdesign" element={<div>System Design Page</div>} />
      </Route>

      {/* 404 Page (Outside the layout, or inside if you prefer) */}
      <Route path="*" element={<div className="p-4">404 Not Found</div>} />
    </Routes>
  );
}

export default App;