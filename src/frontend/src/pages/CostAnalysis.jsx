import React, { useContext } from 'react'
import Sidebar from '../components/Sidebar'
import CostTrendChart from '../components/CostTrendChart'
import { CostData } from '../context/CostContext'
import formatMoney from '../utils/formatMoney'

const CostAnalysis = () => {
  const {costTrend, serviceBreakdown} = useContext(CostData);
  const totalCost = serviceBreakdown.reduce((sum, elem)=>sum + elem.cost, 0);

  return (
    <div className='flex flex-col md:flex-row h-screen w-full bg-[#0a0e14]'>
      <Sidebar />
      <div className='flex-1 h-full overflow-y-auto'>
        <div className='max-w-6xl mx-auto px-5 md:px-8 py-6 md:py-8 flex flex-col gap-6'>
          <div>
            <h1 className='display font-bold text-2xl'>Cost Analysis</h1>
            <p className='body text-sm text-[#8b98a8] mt-1'>Historical spend across your AWS account.</p>
          </div>

          <div className='bg-[#10151d] border border-white/6 rounded-xl p-5'>
            <h2 className='body font-semibold mb-4'>Daily spend</h2>
            <CostTrendChart data={costTrend} />
          </div>

          <div className='bg-[#10151d] border border-white/6 rounded-xl overflow-hidden'>
            <div className='px-5 py-4 border-b border-white/6'>
              <h2 className='body font-semibold'>Cost by service</h2>
            </div>
            <div className='overflow-x-auto'>
              <table className='w-full text-sm'>
                <thead>
                  <tr className='text-left text-[#4b5768] body text-[12px] border-b border-white/6'>
                    <th className='px-5 py-3 font-medium'>Service</th>
                    <th className='px-5 py-3 font-medium'>Cost</th>
                    <th className='px-5 py-3 font-medium'>Share</th>
                  </tr>
                </thead>
                <tbody>
                  {serviceBreakdown.map((elem)=>(
                    <tr key={elem.service} className='border-b border-white/6 last:border-b-0'>
                      <td className='px-5 py-3 body flex items-center gap-2'>
                        <span className='w-2 h-2 rounded-full' style={{backgroundColor: elem.color}}></span>
                        {elem.service}
                      </td>
                      <td className='px-5 py-3 mono'>${formatMoney(elem.cost)}</td>
                      <td className='px-5 py-3 mono text-[#8b98a8]'>{elem.percent}%</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td className='px-5 py-3 body font-semibold'>Total</td>
                    <td className='px-5 py-3 mono font-semibold'>${formatMoney(totalCost)}</td>
                    <td className='px-5 py-3'></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CostAnalysis
