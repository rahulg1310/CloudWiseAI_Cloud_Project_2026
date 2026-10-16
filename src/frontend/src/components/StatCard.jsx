import React from 'react'

const StatCard = (props) => {
  return (
    <div className='flex-1 min-w-[180px] flex flex-col gap-3 bg-[#10151d] border border-white/6 rounded-xl py-4 px-5 hover:border-white/12 hover:-translate-y-0.5 transition-all duration-200'>
      <div className='flex items-center justify-between'>
        <span className='body text-[13px] text-[#8b98a8]'>{props.title}</span>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${props.bg}`}>
          {props.icon} 
        </div>
      </div>
      <h1 className='mono text-2xl font-medium'>{props.value}</h1>
      {props.sub && (
        <span className={`body text-[12px] ${props.subColor || 'text-[#4b5768]'}`}>{props.sub}</span>
      )}
    </div>
  )
}

export default StatCard
