import React, { createContext, useState } from 'react'

export const UserData = createContext();

const UserContext = ({children}) => {
  const [user, setUser] = useState(()=>{
    const storedUser = localStorage.getItem("user");
    if(storedUser){
        return JSON.parse(storedUser);
    }
    return null;
  });
  return (
    <div>
        <UserData.Provider value={{user , setUser}}>
            {children}
        </UserData.Provider>
    </div>
  )
}

export default UserContext
