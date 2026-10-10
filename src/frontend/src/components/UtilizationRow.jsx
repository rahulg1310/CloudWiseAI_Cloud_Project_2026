import React from 'react'

const statusStyles = {
  Healthy: 'text-[#10b981] bg-[#10b981]/10',
  Underutilized: 'text-[#f59e0b] bg-[#f59e0b]/10',
  Unattached: 'text-[#f43f5e] bg-[#f43f5e]/10',
}

const barColor = (utilization)=>{
  if(utilization >= 50) return '#10b981';
  if(utilization >= 20) return '#f59e0b';
  return '#f43f5e';
}

const UtilizationRow = (props) => {
  return (
    <div className='flex items-center gap-4 py-3 px-4 border-b border-white/6 last:border-b-0'>
      <div className='flex-1 min-w-0'>
        <h1 className='body font-medium text-sm truncate'>{props.resource}</h1>
        <span className='body text-[12px] text-[#4b5768]'>{props.type}</span>
      </div>
      <div className='hidden sm:flex flex-col gap-1 w-32'>
        <div className='h-1.5 bg-[#182230] rounded-full overflow-hidden w-full'>
          <div className='h-full rounded-full' style={{width: `${props.utilization}%`, backgroundColor: barColor(props.utilization)}}></div>
        </div>
        <span className='mono text-[11px] text-[#8b98a8]'>{props.utilization}%</span>
      </div>
      <span className={`body font-medium text-[12px] py-1 px-3 rounded-full shrink-0 ${statusStyles[props.status] || statusStyles.Healthy}`}>
        {props.status}
      </span>
      <span className='mono text-sm w-16 text-right shrink-0'>${props.cost}</span>
    </div>
  )
}

export default UtilizationRow
