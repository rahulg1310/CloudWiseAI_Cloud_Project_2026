import React from 'react'

const PredictionChart = (props) => {
  const historical = props.historical || [];
  const forecast = props.forecast || [];
  const all = [...historical, ...forecast];
  const max = Math.max(...all.map((d)=>d.cost)) || 1;

  return (
    <div className='flex items-end gap-3 h-52 w-full'>
      {historical.map((elem)=>(
        <div key={elem.month} className='flex-1 flex flex-col items-center gap-2 h-full justify-end'>
          <span className='mono text-[11px] text-[#8b98a8]'>${(elem.cost/1000).toFixed(1)}k</span>
          <div
            className='w-full rounded-t-md bg-[#3b82f6]'
            style={{height: `${(elem.cost/max)*100}%`}}
          ></div>
          <span className='body text-[11px] text-[#4b5768]'>{elem.month}</span>
        </div>
      ))}
      {forecast.map((elem)=>(
        <div key={elem.month} className='flex-1 flex flex-col items-center gap-2 h-full justify-end'>
          <span className='mono text-[11px] text-[#22d3ee]'>${(elem.cost/1000).toFixed(1)}k</span>
          <div
            className='w-full rounded-t-md bg-[#22d3ee]/40 border border-dashed border-[#22d3ee]'
            style={{height: `${(elem.cost/max)*100}%`}}
          ></div>
          <span className='body text-[11px] text-[#22d3ee]'>{elem.month}</span>
        </div>
      ))}
    </div>
  )
}

export default PredictionChart
