"use client";
import {useEffect, useState} from "react";

export default function Home(){
  const [file,setFile]=useState(null);
  const [url,setUrl]=useState("");
  const [status,setStatus]=useState("");

  async function refreshLatest(){
    setUrl("/api/latest?ts="+Date.now());
    setStatus("Showing latest frame");
  }

  async function upload(){
    if(!file) return;
    setStatus("Uploading...");
    const form=new FormData();
    form.append("file",file);
    const res=await fetch("/api/upload",{method:"POST",body:form});
    const data=await res.json();
    if(!res.ok){setStatus(data.error||"Upload failed");return;}
    setStatus("Uploaded successfully");
    setUrl("/api/latest?ts="+Date.now());
  }

  useEffect(()=>{ refreshLatest(); },[]);

  return <main style={{padding:24,fontFamily:"sans-serif",maxWidth:700,margin:"0 auto"}}>
    <h1>Vision Bridge</h1>
    <p>Latest-frame bridge</p>
    <input type="file" accept="image/*" onChange={e=>setFile(e.target.files?.[0]||null)}/>
    <br/><br/>
    <button onClick={upload} disabled={!file}>Upload latest frame</button>
    <button onClick={refreshLatest} style={{marginLeft:10}}>Refresh latest</button>
    <p>{status}</p>
    {url && <img src={url} alt="Latest frame" style={{display:"block",maxWidth:"100%",height:"auto"}}/>}
  </main>
}