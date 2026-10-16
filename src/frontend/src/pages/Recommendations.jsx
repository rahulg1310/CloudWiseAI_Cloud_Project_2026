import React, { useContext } from 'react'
import Sidebar from '../components/Sidebar'
import RecommendationCard from '../components/RecommendationCard'
import { CostData } from '../context/CostContext'
import formatMoney from '../utils/formatMoney'

const Recommendations = () => {
  const {recommendations} = useContext(CostData);
  const totalSavings = recommendations.reduce((sum, elem)=>sum + elem.potentialSavings, 0);

  return (
    <div className='flex flex-col md:flex-row h-screen w-full bg-[#0a0e14]'>
      <Sidebar />
      <div className='flex-1 h-full overflow-y-auto'>
        <div className='max-w-6xl mx-auto px-5 md:px-8 py-6 md:py-8 flex flex-col gap-6'>
          <div className='flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3'>
            <div>
              <h1 className='display font-bold text-2xl'>Recommendations</h1>
              <p className='body text-sm text-[#8b98a8] mt-1'>Ways to cut your AWS bill without cutting capacity.</p>
            </div>
            <div className='bg-[#10b981]/10 border border-[#10b981]/20 rounded-xl px-4 py-2.5'>
              <span className='body text-[12px] text-[#10b981]'>Total potential savings</span>
              <p className='mono text-lg text-[#10b981] font-medium'>${formatMoney(totalSavings)}/mo</p>
            </div>
          </div>

          {recommendations.length === 0 ? (
            <div className='body text-sm text-[#4b5768] py-10 text-center'>No open recommendations — you're well optimized.</div>
          ) : (
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              {recommendations.map((elem)=>(
                <RecommendationCard key={elem.id} {...elem} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Recommendations
