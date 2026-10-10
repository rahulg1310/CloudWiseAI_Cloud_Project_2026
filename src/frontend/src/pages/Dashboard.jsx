import React, { useContext } from 'react'
import Sidebar from '../components/Sidebar'
import StatCard from '../components/StatCard'
import CostTrendChart from '../components/CostTrendChart'
import ServiceBreakdownCard from '../components/ServiceBreakdownCard'
import { CostData } from '../context/CostContext'
import { DollarSign } from 'lucide-react'
import { TrendingUp } from 'lucide-react'
import { PiggyBank } from 'lucide-react'
import { AlertTriangle } from 'lucide-react'

const Dashboard = () => {
  const {costSummary, costTrend, serviceBreakdown} = useContext(CostData);

  return (
    <div className='flex flex-col md:flex-row h-screen w-full bg-[#0a0e14]'>
      <Sidebar />
      <div className='flex-1 h-full overflow-y-auto'>
        <div className='max-w-6xl mx-auto px-5 md:px-8 py-6 md:py-8 flex flex-col gap-6'>
          <div>
            <h1 className='display font-bold text-2xl'>Dashboard</h1>
            <p className='body text-sm text-[#8b98a8] mt-1'>Your AWS cost overview, updated daily.</p>
          </div>

          <div className='flex flex-wrap gap-4'>
            <StatCard
              title='Current Month Spend'
              value={`$${costSummary.totalCost.toLocaleString()}`}
              sub={`${costSummary.monthOverMonthChange >= 0 ? '+' : ''}${costSummary.monthOverMonthChange}% vs last month`}
              subColor={costSummary.monthOverMonthChange >= 0 ? 'text-[#f59e0b]' : 'text-[#10b981]'}
              icon={<DollarSign size={16} className='text-[#22d3ee]' />}
              bg='bg-[#22d3ee]/10'
            />
            <StatCard
              title='Forecasted Spend'
              value={`$${costSummary.forecastedCost.toLocaleString()}`}
              sub='End of month projection'
              icon={<TrendingUp size={16} className='text-[#3b82f6]' />}
              bg='bg-[#3b82f6]/10'
            />
            <StatCard
              title='Potential Savings'
              value={`$${costSummary.potentialSavings.toLocaleString()}`}
              sub='From open recommendations'
              subColor='text-[#10b981]'
              icon={<PiggyBank size={16} className='text-[#10b981]' />}
              bg='bg-[#10b981]/10'
            />
            <StatCard
              title='Active Anomalies'
              value={costSummary.anomalyCount}
              sub='Needs review'
              subColor='text-[#f43f5e]'
              icon={<AlertTriangle size={16} className='text-[#f43f5e]' />}
              bg='bg-[#f43f5e]/10'
            />
          </div>

          <div className='grid grid-cols-1 lg:grid-cols-3 gap-4'>
            <div className='lg:col-span-2 bg-[#10151d] border border-white/6 rounded-xl p-5'>
              <h2 className='body font-semibold mb-4'>Cost trend — last 14 days</h2>
              <CostTrendChart data={costTrend} />
            </div>
            <div className='bg-[#10151d] border border-white/6 rounded-xl p-5'>
              <h2 className='body font-semibold mb-4'>Spend by service</h2>
              <ServiceBreakdownCard data={serviceBreakdown} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
