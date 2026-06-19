// src/components/ErrorState.jsx
import React from 'react';
import { ServerCrash } from 'lucide-react';

export default function ErrorState({ message }) {
  return (
    <div className="flex flex-col items-center justify-center h-40 text-red-600 bg-red-50 rounded-lg">
      <ServerCrash size={48} />
      <p className="mt-2 text-lg font-semibold">Gagal Terhubung</p>
      <p className="text-sm">{message}</p>
    </div>
  );
}