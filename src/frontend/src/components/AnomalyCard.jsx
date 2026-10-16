import React from 'react'
import { AlertTriangle } from 'lucide-react'
import formatMoney from '../utils/formatMoney'

const severityStyles = {
  Critical: 'text-[#f43f5e] bg-[#f43f5e]/10',
  High: 'text-[#f59e0b] bg-[#f59e0b]/10',
  Medium: 'text-[#22d3ee] bg-[#22d3ee]/10',
  Low: 'text-[#8b98a8] bg-white/5',
  Default: 'text-[#8b98a8] bg-white/5',
}

const AnomalyCard = (props) => {
  return (
    <div className='bg-[#10151d] border border-white/6 rounded-xl p-4 flex flex-col gap-3 hover:border-white/12 transition-all duration-200'>
      <div className='flex justify-between items-start gap-3'>
        <div className='flex items-center gap-2'>
          <AlertTriangle size={17} className='text-[#f43f5e]' />
           <h1 className='body font-semibold truncate'>{props.service}</h1>
        </div>
        <span className={`body font-medium text-[12px] py-1 px-3 rounded-full ${severityStyles[props.severity] || severityStyles.Low}`}>
          {props.severity}
        </span>
      </div>
      <p className='body text-[13px] text-[#8b98a8]'>{props.note}</p>
      <div className='flex gap-6 flex-wrap pt-1'>
        <div className='flex flex-col gap-0.5'>
          <span className='mono text-[15px] text-[#e6edf3]'>${formatMoney(props.expectedCost)}</span>
          <span className='body text-[11px] text-[#4b5768]'>EXPECTED</span>
        </div>
        <div className='flex flex-col gap-0.5'>
          <span className='mono text-[15px] text-[#f43f5e]'>${formatMoney(props.actualCost)}</span>
          <span className='body text-[11px] text-[#4b5768]'>ACTUAL</span>
        </div>
        <div className='flex flex-col gap-0.5'>
          <span className='mono text-[15px] text-[#f43f5e]'>+{props.deviation}%</span>
          <span className='body text-[11px] text-[#4b5768]'>DEVIATION</span>
        </div>
        <div className='flex flex-col gap-0.5'>
          <span className='mono text-[15px]'>{new Date(props.date).toLocaleDateString()}</span>
          <span className='body text-[11px] text-[#4b5768]'>DETECTED</span>
        </div>
      </div>
    </div>
  )
}

export default AnomalyCard
