// src/components/LoadingState.jsx
import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center h-40 text-slate-500">
      <Loader2 className="animate-spin" size={48} />
      <p className="mt-2 text-lg">Loading data...</p>
    </div>
  );
}