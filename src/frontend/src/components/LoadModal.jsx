import React from 'react'
import { Loader2 } from 'lucide-react'

const LoadModal = () => {
  return (
    <div className='fixed inset-0 z-[200] bg-[#0a0e14]/70 backdrop-blur-sm flex items-center justify-center'>
      <div className='flex flex-col items-center gap-3'>
        <Loader2 size={32} className='animate-spin text-[#22d3ee]' />
        <p className='body text-sm text-[#8b98a8]'>Loading cost data…</p>
      </div>
    </div>
  )
}

export default LoadModal
