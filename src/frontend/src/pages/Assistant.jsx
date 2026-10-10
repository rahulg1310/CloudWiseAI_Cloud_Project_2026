import React, { useState } from 'react'
import axios from 'axios'
import Sidebar from '../components/Sidebar'
import ChatMessage from '../components/ChatMessage'
import { Send } from 'lucide-react'

const Assistant = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hi, I'm your CloudWise assistant. Ask me about your spend, anomalies, or how to cut costs." },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if(!text) return;

    const nextMessages = [...messages, { role: 'user', text }];
    setMessages(nextMessages);
    setInput('');
    setSending(true);

    try{
      const token = JSON.parse(localStorage.getItem("token"));
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/assistant/chat`, {
        message: text,
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages([...nextMessages, { role: 'assistant', text: res.data.reply }]);
    }
    catch(error){
      console.log(error);
      setMessages([...nextMessages, { role: 'assistant', text: "I can't reach the backend yet — once it's connected I'll be able to answer this." }]);
    }
    finally{
      setSending(false);
    }
  }

  return (
    <div className='flex flex-col md:flex-row h-screen w-full bg-[#0a0e14]'>
      <Sidebar />
      <div className='flex-1 h-full flex flex-col overflow-hidden'>
        <div className='max-w-3xl mx-auto w-full px-5 md:px-8 py-6 md:py-8 flex flex-col h-full'>
          <div className='mb-4'>
            <h1 className='display font-bold text-2xl'>Assistant</h1>
            <p className='body text-sm text-[#8b98a8] mt-1'>Ask questions about your AWS spend in plain language.</p>
          </div>

          <div className='flex-1 overflow-y-auto flex flex-col gap-4 py-2'>
            {messages.map((m, i)=>(
              <ChatMessage key={i} role={m.role} text={m.text} />
            ))}
          </div>

          <form onSubmit={handleSend} className='flex items-center gap-2 pt-4 border-t border-white/6'>
            <input
              type='text'
              value={input}
              onChange={(e)=>setInput(e.target.value)}
              placeholder='e.g. Why did EC2 spend spike this week?'
              className='flex-1 bg-[#10151d] border border-white/6 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-[#8b5cf6]/60'
            />
            <button
              type='submit'
              disabled={sending}
              className='bg-[#8b5cf6] text-white rounded-lg p-2.5 hover:bg-[#8b5cf6]/90 transition-colors duration-150 disabled:opacity-60'
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Assistant
