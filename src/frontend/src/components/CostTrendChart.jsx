import React from 'react'

const CostTrendChart = (props) => {
  const data = props.data || [];
  const width = 640;
  const height = 220;
  const padding = 30;

  if(data.length === 0){
    return <div className='text-[#4b5768] text-sm py-10 text-center'>No cost data yet</div>
  }

  const costs = data.map((d)=>d.cost);
  const max = Math.max(...costs);
  const min = Math.min(...costs);
  const range = (max - min) || 1;

  const points = data.map((d, i)=>{
    const x = padding + (i / (data.length - 1)) * (width - padding * 2);
    const y = height - padding - ((d.cost - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  const areaPoints = `${padding},${height - padding} ${points} ${width - padding},${height - padding}`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className='w-full h-auto'>
      <defs>
        <linearGradient id='costFill' x1='0' y1='0' x2='0' y2='1'>
          <stop offset='0%' stopColor='#22d3ee' stopOpacity='0.25' />
          <stop offset='100%' stopColor='#22d3ee' stopOpacity='0' />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill='url(#costFill)' />
      <polyline points={points} fill='none' stroke='#22d3ee' strokeWidth='2' strokeLinejoin='round' strokeLinecap='round' />
      {data.map((d, i)=>{
        const x = padding + (i / (data.length - 1)) * (width - padding * 2);
        const y = height - padding - ((d.cost - min) / range) * (height - padding * 2);
        return <circle key={d.date} cx={x} cy={y} r='2.5' fill='#0a0e14' stroke='#22d3ee' strokeWidth='1.5' />
      })}
    </svg>
  )
}

export default CostTrendChart
