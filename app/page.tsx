"use client";
import Link from "next/link";
import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [password, setPassword] = useState("");

  async function updateInvestory() {
    if (!file) {
      alert("Please upload a CSV file");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("password", password); // ✅ send password


    try {
      const res = await fetch("/api/py/reserve_stock", {
        method: "POST",
        body: formData, // ✅ No headers needed for FormData
      });

      const data = await res.json();
      if (res.ok) {
        alert("Inventory updated successfully, " + (data?.admin_url ?? ""));
        console.log(data);
      } else {
        alert("❌ Inventory update failed");
        console.error(data);
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("❌ Something went wrong.");
    }
  }
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
      <input type="password" title="password" 
      className="rounded-md border-2 border-gray-300 px-4 py-2 text-gray-700 focus:border-blue-500 focus:outline-none"
      placeholder="password" 
      onChange={(e)=>setPassword(e.target.value)}
      />
        <input onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
          }
        }} type="file" accept="text/csv"
        />
        <button onClick={updateInvestory} className="rounded-md bg-blue-500 px-4 py-2 text-white">
          upload
        </button>
        {/* <Link href="/api/py/helloFastApi">
        <code className="font-mono font-bold">app/api/helloNextJs</code>
          </Link> */}
      </div>
    </main>
  );
}
