import React, { useContext } from 'react'
import Sidebar from '../components/Sidebar'
import UtilizationRow from '../components/UtilizationRow'
import { CostData } from '../context/CostContext'

const Utilization = () => { 
  const {utilization} = useContext(CostData);

  return (
    <div className='flex flex-col md:flex-row h-screen w-full bg-[#0a0e14]'>
      <Sidebar />
      <div className='flex-1 h-full overflow-y-auto'>
        <div className='max-w-6xl mx-auto px-5 md:px-8 py-6 md:py-8 flex flex-col gap-6'>
          <div>
            <h1 className='display font-bold text-2xl'>Resource Utilization</h1>
            <p className='body text-sm text-[#8b98a8] mt-1'>How well your provisioned resources are actually being used.</p>
          </div>

          <div className='bg-[#10151d] border border-white/6 rounded-xl overflow-hidden'>
            <div className='hidden sm:flex items-center gap-4 py-3 px-4 border-b border-white/6 body text-[12px] text-[#4b5768] font-medium'>
              <span className='flex-1'>Resource</span>
              <span className='w-32'>Utilization</span>
              <span className='w-28'>Status</span>
              <span className='w-24 text-right'>Cost</span>
            </div>
            {utilization.map((elem)=>(
              <UtilizationRow key={elem.resource} {...elem} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Utilization
