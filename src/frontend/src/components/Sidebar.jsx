import React, { useState } from 'react'
import { LayoutDashboard } from 'lucide-react'
import { TrendingUp } from 'lucide-react'
import { LineChart } from 'lucide-react'
import { AlertTriangle } from 'lucide-react'
import { Sparkles } from 'lucide-react'
import { Gauge } from 'lucide-react'
import { MessageSquare } from 'lucide-react'
import { LogOut } from 'lucide-react'
import { Menu } from 'lucide-react'
import { X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useContext } from 'react'
import { UserData } from '../context/UserContext'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/cost-analysis', label: 'Cost Analysis', icon: TrendingUp },
  { path: '/predictions', label: 'Predictions', icon: LineChart },
  { path: '/anomalies', label: 'Anomalies', icon: AlertTriangle },
  { path: '/recommendations', label: 'Recommendations', icon: Sparkles },
  { path: '/utilization', label: 'Utilization', icon: Gauge },
  { path: '/assistant', label: 'Assistant', icon: MessageSquare },
]

const Sidebar = () => {
  const {user, setUser} = useContext(UserData);
  const [modal, setModal] = useState(false);
  const navigate = useNavigate();

  return (
    <>
      <div className='md:hidden h-16 bg-[#0d1219] border-b border-white/6 flex items-center justify-between px-4'>
        <h1 className='display font-bold text-2xl bg-linear-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent'>CloudWiseAI</h1>
        <button onClick={()=>{
          setModal(!modal);
        }}>
          {
            modal===true ? <X size={26}/> : <Menu size={26}/>
          }
        </button>

      {
        modal && (
          <div
          onClick={()=>{
            setModal(false)
          }}
          className='fixed inset-0 z-80 '>
          </div>
        )
      }
        <div className={`fixed inset-x-0 top-16 bottom-0 z-[100] w-full bg-[#0d1219] transition-transform duration-300 ${
          modal ? "translate-x-0" : "-translate-x-full"
        }`}>
          <div className="flex flex-col justify-between h-full py-6">
            <div className="flex flex-col gap-1 px-3 font-medium text-lg text-[#8b98a8]">
              {navItems.map((item)=>{
                const Icon = item.icon;
                return (
                  <button
                    key={item.path}
                    onClick={()=>{
                      navigate(item.path);
                      setModal(false);
                    }}
                    className="flex items-center gap-3 px-3 py-2 hover:bg-white/5 rounded-lg text-left"
                  >
                    <Icon size={19} />
                    {item.label}
                  </button>
                )
              })}
            </div>
            <div className="mt-auto border-t border-white/6 pt-5 px-4">
              <h2 className="text-center text-lg font-semibold mb-4">
                {user?.username}
              </h2>
              <button
                onClick={()=>{
                  setUser(null);
                  localStorage.removeItem("user");
                  localStorage.removeItem("token");
                  navigate('/');
                  setModal(false);
                }}
                className="w-full font-medium flex justify-center items-center gap-2 py-2 hover:bg-white/5 rounded-lg text-[#8b98a8]"
              >
                Sign Out
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className='hidden md:flex w-60 bg-[#0d1219] h-screen border-r border-white/6 px-2 flex-col'>
        <div className='h-full w-full flex flex-col justify-between'>
          <div className='flex flex-col gap-4'>
            <div className='py-6 flex justify-center'>
              <h1 className='display font-bold text-2xl bg-linear-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent'>CloudWiseAI</h1>
            </div>
            <div className='font-medium text-[#8b98a8] text-[15px] flex flex-col gap-1 px-3'>
              {navItems.map((item)=>{
                const Icon = item.icon;
                return (
                  <button
                    key={item.path}
                    onClick={()=>{
                      navigate(item.path);
                    }}
                    className='flex items-center gap-3 w-full hover:bg-white/5 hover:text-[#e6edf3] px-3 py-2 rounded-lg transition-colors duration-150 text-left'
                  >
                    <Icon size={17} />
                    {item.label}
                  </button>
                )
              })}
            </div>
          </div>
          <div className='w-full flex flex-col gap-3 px-4 py-5 border-t border-white/6'>
            <div className='w-full flex justify-center mono text-sm font-medium text-[#8b98a8]'>
              {user?.username}
            </div>
            <button
              onClick={()=>{
                setUser(null);
                localStorage.removeItem("user");
                localStorage.removeItem("token");
                navigate('/');
              }}
              className='w-full py-2 flex justify-center items-center gap-2 font-medium text-sm hover:bg-white/5 rounded-lg transition-colors duration-150 text-[#8b98a8]'
            >
              Sign out <LogOut size={15}/>
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

export default Sidebar
