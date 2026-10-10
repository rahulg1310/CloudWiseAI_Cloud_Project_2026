import React, { useContext } from 'react'
import Sidebar from '../components/Sidebar'
import AnomalyCard from '../components/AnomalyCard'
import { CostData } from '../context/CostContext'

const Anomalies = () => {
  const {anomalies} = useContext(CostData);

  return (
    <div className='flex flex-col md:flex-row h-screen w-full bg-[#0a0e14]'>
      <Sidebar />
      <div className='flex-1 h-full overflow-y-auto'>
        <div className='max-w-6xl mx-auto px-5 md:px-8 py-6 md:py-8 flex flex-col gap-6'>
          <div>
            <h1 className='display font-bold text-2xl'>Anomalies</h1>
            <p className='body text-sm text-[#8b98a8] mt-1'>Spend that diverges from your normal baseline.</p>
          </div>

          {anomalies.length === 0 ? (
            <div className='body text-sm text-[#4b5768] py-10 text-center'>No anomalies detected right now.</div>
          ) : (
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              {anomalies.map((elem)=>(
                <AnomalyCard key={elem.id} {...elem} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Anomalies
