"use client";
import {useState} from "react";

export default function Home(){
  const [file,setFile]=useState(null);
  const [url,setUrl]=useState("");
  const [status,setStatus]=useState("");

  async function upload(){
    if(!file) return;
    setStatus("Uploading...");
    const form=new FormData();
    form.append("file",file);
    const res=await fetch("/api/upload",{method:"POST",body:form});
    const data=await res.json();
    if(!res.ok){setStatus(data.error||"Upload failed");return;}
    setUrl(data.url);
    setStatus("Uploaded successfully");
  }

  return <main style={{padding:24,fontFamily:"sans-serif"}}>
    <h1>Vision Bridge</h1>
    <p>Latest-frame test</p>
    <input type="file" accept="image/*" onChange={e=>setFile(e.target.files?.[0]||null)}/>
    <br/><br/>
    <button onClick={upload} disabled={!file}>Upload latest frame</button>
    <p>{status}</p>
    {url && <img src={url} alt="Latest frame" style={{maxWidth:"100%",height:"auto"}}/>}
  </main>
}