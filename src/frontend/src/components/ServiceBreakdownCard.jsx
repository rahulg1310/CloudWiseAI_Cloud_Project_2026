import React from 'react'
import formatMoney from '../utils/formatMoney'

const ServiceBreakdownCard = (props) => {
  return (
    <div className='flex flex-col gap-3'>
      {props.data.map((elem)=>(
        <div key={elem.service} className='flex flex-col gap-1'>
          <div className='flex justify-between items-center'>
            <span className='body text-sm text-[#e6edf3]'>{elem.service}</span>
            <span className='mono text-sm text-[#8b98a8]'>${formatMoney(elem.cost)}</span>
          </div>
          <div className='h-1.5 bg-[#182230] rounded-full overflow-hidden w-full'>
            <div
              className='h-full rounded-full'
              style={{width: `${elem.percent}%`, backgroundColor: elem.color}}
            ></div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default ServiceBreakdownCard
