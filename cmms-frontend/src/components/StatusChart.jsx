// src/components/StatusChart.jsx
import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function StatusChart({ open, inProgress, completed }) {
    // Hitung total
    const total = open + inProgress + completed;
    
    // Jika Pending Verification dianggap bagian dari 'In Progress' secara visual chart,
    // atau bisa dibuat warna sendiri. Di sini saya gabung logika visualnya.

    const data = {
        labels: ['Open', 'In Progress', 'Completed'],
        datasets: [
            {
                data: [open, inProgress, completed],
                backgroundColor: [
                    '#EF4444', // Red (Open)
                    '#F59E0B', // Amber (In Progress + Pending)
                    '#10B981', // Green (Completed)
                ],
                borderWidth: 0,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: { usePointStyle: true, padding: 20 }
            }
        },
        cutout: '70%', // Membuat lubang tengah lebih besar (gaya modern)
    };

    return (
        <div className="relative h-64 w-full">
            {total > 0 ? (
                <>
                    <Doughnut data={data} options={options} />
                    {/* Angka Persentase di Tengah */}
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                        <div className="text-3xl font-extrabold text-slate-800">
                            {Math.round((completed / total) * 100)}%
                        </div>
                        <div className="text-xs text-slate-400 font-medium uppercase">Selesai</div>
                    </div>
                </>
            ) : (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                    Belum ada data
                </div>
            )}
        </div>
    );
}