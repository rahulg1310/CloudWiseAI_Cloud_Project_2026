import React from 'react'
import { Sparkles } from 'lucide-react'

const effortStyles = {
  Low: 'text-[#10b981] bg-[#10b981]/10',
  Medium: 'text-[#f59e0b] bg-[#f59e0b]/10',
  High: 'text-[#f43f5e] bg-[#f43f5e]/10',
}

const RecommendationCard = (props) => {
  return (
    <div className='bg-[#10151d] border border-white/6 rounded-xl p-4 flex flex-col gap-3 hover:border-white/12 transition-all duration-200'>
      <div className='flex justify-between items-start gap-3'>
        <div className='flex items-start gap-2'>
          <Sparkles size={17} className='text-[#22d3ee] mt-0.5 shrink-0' />
          <div>
            <h1 className='body font-semibold'>{props.title}</h1>
            <span className='body text-[12px] text-[#4b5768]'>{props.service} · {props.category}</span>
          </div>
        </div>
        <span className={`body font-medium text-[12px] py-1 px-3 rounded-full shrink-0 ${effortStyles[props.effort] || effortStyles.Medium}`}>
          {props.effort} effort
        </span>
      </div>
      <p className='body text-[13px] text-[#8b98a8]'>{props.description}</p>
      <div className='flex justify-between items-center pt-1'>
        <span className='body text-[12px] text-[#4b5768]'>Estimated monthly savings</span>
        <span className='mono text-[16px] text-[#10b981]'>${props.potentialSavings.toLocaleString()}</span>
      </div>
    </div>
  )
}

export default RecommendationCard
