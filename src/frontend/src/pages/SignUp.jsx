import React, { useContext, useState } from 'react'
import axios from 'axios'
import { useNavigate, Link } from 'react-router-dom'
import { UserData } from '../context/UserContext'
import { Cloud } from 'lucide-react'

const SignUp = () => {
  const {setUser} = useContext(UserData);
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try{
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/auth/signup`, {
        username,
        email,
        password,
      });
      setUser(res.data.user);
      localStorage.setItem("user", JSON.stringify(res.data.user));
      localStorage.setItem("token", JSON.stringify(res.data.token));
      navigate('/dashboard');
    }
    catch(error){
      console.log(error);
      setError('Could not create your account. Please try again.');
    }
    finally{
      setLoading(false);
    }
  }

  return (
    <div className='w-full h-screen overflow-y-auto bg-[#0a0e14]'>
      <div className='min-h-full flex items-center justify-center px-4 py-8'>
        <div className='w-full max-w-sm flex flex-col gap-6'>
          <div className='flex flex-col items-center gap-2'>
            <div className='w-11 h-11 rounded-xl bg-[#22d3ee]/10 flex items-center justify-center'>
              <Cloud size={22} className='text-[#22d3ee]' />
            </div>
            <h1 className='display font-bold text-2xl'>Create your account</h1>
            <p className='body text-sm text-[#8b98a8]'>Start monitoring your AWS costs in minutes</p>
          </div>

          <form onSubmit={handleSubmit} className='flex flex-col gap-4'>
            <div className='flex flex-col gap-1.5'>
              <label className='body text-[13px] text-[#8b98a8]'>Username</label>
              <input
                type='text'
                required
                value={username}
                onChange={(e)=>setUsername(e.target.value)}
                className='bg-[#10151d] border border-white/6 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-[#22d3ee]/60'
                placeholder='jane.doe'
              />
            </div>
            <div className='flex flex-col gap-1.5'>
              <label className='body text-[13px] text-[#8b98a8]'>Email</label>
              <input
                type='email'
                required
                value={email}
                onChange={(e)=>setEmail(e.target.value)}
                className='bg-[#10151d] border border-white/6 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-[#22d3ee]/60'
                placeholder='you@company.com'
              />
            </div>
            <div className='flex flex-col gap-1.5'>
              <label className='body text-[13px] text-[#8b98a8]'>Password</label>
              <input
                type='password'
                required
                value={password}
                onChange={(e)=>setPassword(e.target.value)}
                className='bg-[#10151d] border border-white/6 rounded-lg px-3 py-2.5 text-sm outline-none focus:border-[#22d3ee]/60'
                placeholder='••••••••'
              />
            </div>

            {error && <p className='body text-[13px] text-[#f43f5e]'>{error}</p>}

            <button
              type='submit'
              disabled={loading}
              className='mt-2 bg-[#22d3ee] text-[#0a0e14] font-semibold text-sm rounded-lg py-2.5 hover:bg-[#22d3ee]/90 transition-colors duration-150 disabled:opacity-60'
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className='body text-sm text-[#8b98a8] text-center'>
            Already have an account? <Link to='/signin' className='text-[#22d3ee]'>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default SignUp
