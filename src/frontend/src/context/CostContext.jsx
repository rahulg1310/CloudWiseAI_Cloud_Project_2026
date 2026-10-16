import React, { createContext, useContext, useEffect, useState } from 'react'
import axios from 'axios'
import { UserData } from './UserContext'
import LoadModal from '../components/LoadModal'
import {
  mockCostSummary,
  mockCostTrend,
  mockServiceBreakdown,
  mockPredictions, 
  mockAnomalies,
  mockRecommendations,
  mockUtilization,
} from '../data/mockData'

export const CostData = createContext();

const CostContext = ({children}) => {
  const {user, setUser} = useContext(UserData);
  const [loadModal, setLoadModal] = useState(false);

  const [costSummary, setCostSummary] = useState(mockCostSummary);
  const [costTrend, setCostTrend] = useState(mockCostTrend);
  const [serviceBreakdown, setServiceBreakdown] = useState(mockServiceBreakdown);
  const [predictions, setPredictions] = useState(mockPredictions);
  const [anomalies, setAnomalies] = useState(mockAnomalies);
  const [recommendations, setRecommendations] = useState(mockRecommendations);
  const [utilization, setUtilization] = useState(mockUtilization);

  useEffect(()=>{
    if(!user) return;
    const fetchCostData = async ()=>{
      setLoadModal(true);
      try{
        const token = JSON.parse(localStorage.getItem("token"));
        const headers = { Authorization: `Bearer ${token}` };

        // allSettled so one missing endpoint doesn't throw away the ones that worked.
        const results = await Promise.allSettled([
          axios.get(`${import.meta.env.VITE_API_URL}/costs/summary`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/costs/trend`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/costs/breakdown`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/predictions`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/anomalies`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/recommendations`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/utilization`, {headers}),
        ]);

        const [summaryRes, trendRes, breakdownRes, predictionsRes, anomaliesRes, recsRes, utilRes] = results;

        // An expired or invalid token makes every request 401. Sign out instead of
        // quietly showing sample data as if it were the user's real numbers.
        const sessionExpired = results.some((res)=> res.status === 'rejected' && res.reason?.response?.status === 401);
        if(sessionExpired){
          setUser(null);
          localStorage.removeItem("user");
          localStorage.removeItem("token");
          return;
        }

        // Only replace the mock data when the response has the shape the UI expects.
        if(summaryRes.status === 'fulfilled' && summaryRes.value.data?.totalCost !== undefined) setCostSummary(summaryRes.value.data);
        if(trendRes.status === 'fulfilled' && Array.isArray(trendRes.value.data)) setCostTrend(trendRes.value.data);
        if(breakdownRes.status === 'fulfilled' && Array.isArray(breakdownRes.value.data)) setServiceBreakdown(breakdownRes.value.data);
        if(predictionsRes.status === 'fulfilled' && predictionsRes.value.data?.forecast) setPredictions(predictionsRes.value.data);
        if(anomaliesRes.status === 'fulfilled' && Array.isArray(anomaliesRes.value.data)) setAnomalies(anomaliesRes.value.data);
        if(recsRes.status === 'fulfilled' && Array.isArray(recsRes.value.data)) setRecommendations(recsRes.value.data);
        if(utilRes.status === 'fulfilled' && Array.isArray(utilRes.value.data)) setUtilization(utilRes.value.data);

        results.forEach((res)=>{
          if(res.status === 'rejected') console.log(res.reason);
        });
      }
      catch(error){
        // Keep the mock data so the UI still works if something unexpected fails.
        console.log(error);
      }
      finally{
        setLoadModal(false);
      }
    }
    fetchCostData();
  },[user, setUser])

  return (
    <div>
      <CostData.Provider value={{
        costSummary,
        costTrend,
        serviceBreakdown,
        predictions,
        anomalies,
        recommendations,
        utilization,
      }}>
        {children}
      </CostData.Provider>
      {
        user && loadModal && (<LoadModal />)
      }
    </div>
  )
}

export default CostContext
