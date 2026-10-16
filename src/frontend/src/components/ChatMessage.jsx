import React from 'react'
import { Bot } from 'lucide-react'
import { User } from 'lucide-react'

const ChatMessage = (props) => {
  const isUser = props.role === 'user';
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isUser ? 'bg-[#3b82f6]/15' : 'bg-[#8b5cf6]/15'}`}>
        {isUser ? <User size={16} className='text-[#3b82f6]' /> : <Bot size={16} className='text-[#8b5cf6]' />}
      </div>
      <div className={`body text-sm max-w-[75%] rounded-xl px-4 py-2.5 whitespace-pre-wrap wrap-break-word ${
        isUser ? 'bg-[#3b82f6]/10 text-[#e6edf3]' : 'bg-[#10151d] border border-white/6 text-[#e6edf3]'
      }`}>
        {props.text}
      </div>
    </div>
  )
}

export default ChatMessage
