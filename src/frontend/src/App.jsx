import React, { useContext } from 'react'
import Landing from './pages/Landing'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import Dashboard from './pages/Dashboard'
import CostAnalysis from './pages/CostAnalysis'
import Predictions from './pages/Predictions'
import Anomalies from './pages/Anomalies'
import Recommendations from './pages/Recommendations' 
import Utilization from './pages/Utilization'
import Assistant from './pages/Assistant'
import { Routes, Route } from 'react-router-dom'
import { Navigate } from 'react-router-dom'
import { UserData } from './context/UserContext'

const App = () => {
  const {user} = useContext(UserData);
  return (
    <div className='flex h-screen overflow-hidden'>
      <Routes>
        <Route path="/" element={user ? <Navigate to='/dashboard' /> : <Landing />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/dashboard" element={user ? <Dashboard /> : <Navigate to='/signin'/>} />
        <Route path="/cost-analysis" element={user ? <CostAnalysis /> : <Navigate to='/signin'/>} />
        <Route path="/predictions" element={user ? <Predictions /> : <Navigate to='/signin'/>} />
        <Route path="/anomalies" element={user ? <Anomalies /> : <Navigate to='/signin'/>} />
        <Route path="/recommendations" element={user ? <Recommendations /> : <Navigate to='/signin'/>} />
        <Route path="/utilization" element={user ? <Utilization /> : <Navigate to='/signin'/>} />
        <Route path="/assistant" element={user ? <Assistant /> : <Navigate to='/signin'/>} />
      </Routes>
    </div>
  )
}

export default App
