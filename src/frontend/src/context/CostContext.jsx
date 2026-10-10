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
  const {user} = useContext(UserData);
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
    setLoadModal(true);
    const fetchCostData = async ()=>{
      try{
        const token = JSON.parse(localStorage.getItem("token"));
        const headers = { Authorization: `Bearer ${token}` };

        const [summaryRes, trendRes, breakdownRes, predictionsRes, anomaliesRes, recsRes, utilRes] = await Promise.all([
          axios.get(`${import.meta.env.VITE_API_URL}/costs/summary`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/costs/trend`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/costs/breakdown`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/predictions`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/anomalies`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/recommendations`, {headers}),
          axios.get(`${import.meta.env.VITE_API_URL}/utilization`, {headers}),
        ]);

        setCostSummary({
          totalCost: Number(summaryRes.data?.totalCost ?? mockCostSummary.totalCost),
          forecastedCost: Number(summaryRes.data?.forecastedCost ?? mockCostSummary.forecastedCost),
          potentialSavings: Number(summaryRes.data?.potentialSavings ?? mockCostSummary.potentialSavings),
          anomalyCount: Number(summaryRes.data?.anomalyCount ?? mockCostSummary.anomalyCount),
          monthOverMonthChange: Number(summaryRes.data?.monthOverMonthChange ?? mockCostSummary.monthOverMonthChange),
        });
        setCostTrend(trendRes.data);
        setServiceBreakdown(breakdownRes.data);
        setPredictions(predictionsRes.data);
        setAnomalies(anomaliesRes.data);
        setRecommendations(recsRes.data);
        setUtilization(utilRes.data);
      }
      catch(error){
        // Backend isn't live yet — keep the mock data so the UI still works.
        console.log(error);
      }
      finally{
        setLoadModal(false);
      }
    }
    fetchCostData();
  },[user])

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
