import React, { useContext, useEffect, useRef, useState } from 'react'
import axios from 'axios'
import Sidebar from '../components/Sidebar'
import ChatMessage from '../components/ChatMessage'
import { UserData } from '../context/UserContext'
import { Send } from 'lucide-react'

const suggestions = [
  'Why did my spend change this month?',
  'What are my biggest savings opportunities?',
  'Are there any anomalies I should look at?',
  'What will I spend next month?',
]

const Assistant = () => {
  const {setUser} = useContext(UserData);
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hi, I'm your CloudWise assistant. Ask me about your spend, anomalies, or how to cut costs." },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(()=>{
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  },[messages, sending])

  const sendMessage = async (text) => {
    const question = text.trim();
    if(!question || sending) return;

    const nextMessages = [...messages, { role: 'user', text: question }];
    setMessages(nextMessages);
    setInput('');
    setSending(true);

    try{
      const token = JSON.parse(localStorage.getItem("token"));
      // send the earlier conversation so follow-up questions make sense (error bubbles are not part of it)
      const history = messages.filter((m)=>!m.isError).map((m)=>({ role: m.role, text: m.text }));
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/assistant/chat`, {
        message: question,
        history,
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages([...nextMessages, { role: 'assistant', text: res.data.reply }]);
    }
    catch(error){
      console.log(error);
      if(error.response?.status === 401){
        // expired login: sign out, the route guard sends the user to /signin
        setUser(null);
        localStorage.removeItem("user");
        localStorage.removeItem("token");
        return;
      }
      const detail = error.response?.data?.detail;
      setMessages([...nextMessages, {
        role: 'assistant',
        isError: true,
        text: typeof detail === 'string' ? detail : "I couldn't reach the server. Check that the backend is running and try again.",
      }]);
    }
    finally{
      setSending(false);
    }
  }

  const handleSend = (e) => {
    e.preventDefault();
    sendMessage(input);
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

            {messages.length === 1 && (
              <div className='flex flex-wrap gap-2 pl-11'>
                {suggestions.map((s)=>(
                  <button
                    key={s}
                    onClick={()=>sendMessage(s)}
                    className='body text-[13px] text-[#8b98a8] border border-white/10 rounded-full px-3 py-1.5 hover:text-[#e6edf3] hover:border-[#8b5cf6]/50 hover:bg-white/5 transition-colors duration-150'
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {sending && <ChatMessage role='assistant' text='Thinking…' />}
            <div ref={bottomRef}></div>
          </div>

          <form onSubmit={handleSend} className='flex items-center gap-2 pt-4 border-t border-white/6'>
            <input
              type='text'
              value={input}
              onChange={(e)=>setInput(e.target.value)}
              maxLength={2000}
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
