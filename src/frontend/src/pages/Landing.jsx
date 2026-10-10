import React from 'react'
import { Link } from 'react-router-dom'
import { Cloud } from 'lucide-react'
import { TrendingUp } from 'lucide-react'
import { AlertTriangle } from 'lucide-react'
import { Sparkles } from 'lucide-react'
import { LineChart } from 'lucide-react'

const features = [
  { icon: TrendingUp, title: 'Historical spend analysis', text: 'See exactly where your AWS bill comes from, broken down by service and account.' },
  { icon: LineChart, title: 'Cost forecasting', text: 'Predict next month\'s spend before it happens, with confidence ranges built in.' },
  { icon: AlertTriangle, title: 'Anomaly detection', text: 'Catch unexpected spikes the moment they diverge from your normal baseline.' },
  { icon: Sparkles, title: 'Optimization recommendations', text: 'Right-sizing, storage tiering, and commitment suggestions with savings attached.' },
]

const Landing = () => {
  return (
    <div className='w-full min-h-screen bg-[#0a0e14]'>
      <nav className='max-w-6xl mx-auto flex items-center justify-between px-6 py-5'>
        <div className='flex items-center gap-2'>
          <Cloud size={20} className='text-[#22d3ee]' />
          <span className='display font-bold text-lg'>CloudWiseAI</span>
        </div>
        <div className='flex items-center gap-3'>
          <Link to='/signin' className='body text-sm text-[#8b98a8] hover:text-[#e6edf3] px-3 py-2'>Sign in</Link>
          <Link to='/signup' className='body text-sm font-semibold bg-[#22d3ee] text-[#0a0e14] px-4 py-2 rounded-lg hover:bg-[#22d3ee]/90'>Get started</Link>
        </div>
      </nav>

      <section className='max-w-4xl mx-auto text-center px-6 pt-20 pb-16'>
        <h1 className='display font-bold text-4xl md:text-5xl leading-tight'>
          Know where your AWS spend is going,<br className='hidden md:block' /> before the bill arrives.
        </h1>
        <p className='body text-[#8b98a8] text-lg mt-5 max-w-2xl mx-auto'>
          CloudWiseAI monitors, forecasts, and explains your cloud costs — then tells you exactly what to cut.
        </p>
        <div className='flex justify-center gap-3 mt-8'>
          <Link to='/signup' className='body font-semibold text-sm bg-[#22d3ee] text-[#0a0e14] px-6 py-3 rounded-lg hover:bg-[#22d3ee]/90'>
            Start for free
          </Link>
          <Link to='/signin' className='body font-semibold text-sm border border-white/10 px-6 py-3 rounded-lg hover:bg-white/5'>
            Sign in
          </Link>
        </div>
      </section>

      <section className='max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-4 px-6 pb-24'>
        {features.map((f)=>{
          const Icon = f.icon;
          return (
            <div key={f.title} className='bg-[#10151d] border border-white/6 rounded-xl p-5 flex flex-col gap-3'>
              <div className='w-9 h-9 rounded-lg bg-[#22d3ee]/10 flex items-center justify-center'>
                <Icon size={18} className='text-[#22d3ee]' />
              </div>
              <h2 className='body font-semibold'>{f.title}</h2>
              <p className='body text-sm text-[#8b98a8]'>{f.text}</p>
            </div>
          )
        })}
      </section>
    </div>
  )
}

export default Landing
