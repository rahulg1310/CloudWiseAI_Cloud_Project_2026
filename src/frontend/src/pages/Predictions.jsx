import React, { useContext } from 'react'
import Sidebar from '../components/Sidebar'
import PredictionChart from '../components/PredictionChart'
import { CostData } from '../context/CostContext'

const Predictions = () => {
  const {predictions} = useContext(CostData);

  return (
    <div className='flex flex-col md:flex-row h-screen w-full bg-[#0a0e14]'>
      <Sidebar />
      <div className='flex-1 h-full overflow-y-auto'>
        <div className='max-w-6xl mx-auto px-5 md:px-8 py-6 md:py-8 flex flex-col gap-6'>
          <div>
            <h1 className='display font-bold text-2xl'>Predictions</h1>
            <p className='body text-sm text-[#8b98a8] mt-1'>Forecasted spend based on your historical trend.</p>
          </div>

          <div className='bg-[#10151d] border border-white/6 rounded-xl p-5'>
            <div className='flex items-center gap-4 mb-5'>
              <div className='flex items-center gap-2'>
                <span className='w-2.5 h-2.5 rounded-sm bg-[#3b82f6]'></span>
                <span className='body text-[13px] text-[#8b98a8]'>Actual</span>
              </div>
              <div className='flex items-center gap-2'>
                <span className='w-2.5 h-2.5 rounded-sm bg-[#22d3ee]/40 border border-dashed border-[#22d3ee]'></span>
                <span className='body text-[13px] text-[#8b98a8]'>Forecast</span>
              </div>
            </div>
            <PredictionChart historical={predictions.historical} forecast={predictions.forecast} />
          </div>

          <div className='grid grid-cols-1 sm:grid-cols-3 gap-4'>
            {predictions.forecast.map((elem)=>(
              <div key={elem.month} className='bg-[#10151d] border border-white/6 rounded-xl p-5 flex flex-col gap-2'>
                <span className='body text-sm text-[#8b98a8]'>{elem.month} forecast</span>
                <span className='mono text-2xl font-medium'>${elem.cost.toLocaleString()}</span>
                <span className='body text-[12px] text-[#4b5768]'>{Math.round(elem.confidence * 100)}% confidence</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Predictions
