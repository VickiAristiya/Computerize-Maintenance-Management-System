// src/components/AssetWOChart.jsx
import React, { useMemo } from 'react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

// Daftarkan komponen Chart.js yang dibutuhkan
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function AssetWOChart({ reportData }) {
    // reportData is expected to be [{asset_name, open, completed}, ...]
    const chartRows = useMemo(() => {
        return [...reportData]
            .map(item => ({
                asset_name: item.asset_name || 'Aset Tanpa Nama',
                open: Number(item.open || 0),
                completed: Number(item.completed || 0),
                total: Number(item.open || 0) + Number(item.completed || 0),
            }))
            .sort((a, b) => b.total - a.total);
    }, [reportData]);

    const labels = chartRows.map(item => item.asset_name);
    const openData = chartRows.map(item => item.open);
    const completedData = chartRows.map(item => item.completed);
    const chartHeight = Math.max(260, labels.length * 44);

    const data = {
        labels,
        datasets: [
            {
                label: 'Open / Berjalan',
                data: openData,
                backgroundColor: '#F97316',
                borderRadius: 8,
                borderSkipped: false,
                barThickness: 18,
            },
            {
                label: 'Selesai',
                data: completedData,
                backgroundColor: '#10B981',
                borderRadius: 8,
                borderSkipped: false,
                barThickness: 18,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
            legend: {
                position: 'top',
                align: 'end',
                labels: {
                    boxWidth: 10,
                    boxHeight: 10,
                    usePointStyle: true,
                    pointStyle: 'circle',
                    color: '#475569',
                    font: { size: 11, weight: '600' },
                },
            },
            title: { display: false },
            tooltip: {
                callbacks: {
                    title: (items) => labels[items[0].dataIndex],
                    footer: (items) => {
                        const row = chartRows[items[0].dataIndex];
                        return `Total WO: ${row.total}`;
                    },
                },
            },
        },
        scales: {
            x: {
                stacked: true,
                beginAtZero: true,
                ticks: {
                    precision: 0,
                    color: '#64748B',
                },
                grid: {
                    color: '#E2E8F0',
                    drawBorder: false,
                },
                title: {
                    display: true,
                    text: 'Jumlah Work Order',
                    color: '#64748B',
                    font: { size: 11, weight: '600' },
                },
            },
            y: {
                stacked: true,
                ticks: {
                    color: '#334155',
                    font: { size: 11, weight: '600' },
                    callback: function(value) {
                        const label = this.getLabelForValue(value);
                        return label.length > 24 ? `${label.slice(0, 24)}...` : label;
                    },
                },
                grid: {
                    display: false,
                    drawBorder: false,
                },
            },
        },
        layout: {
            padding: {
                top: 4,
                right: 16,
                bottom: 0,
                left: 0,
            },
        },
    };

    if (labels.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center rounded-xl border-2 border-dashed border-slate-100 text-center">
                <p className="text-sm text-slate-500">Tidak ada Work Order tercatat untuk analisis aset.</p>
            </div>
        );
    }

    return (
        <div className="min-h-0">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                <span>Diurutkan dari aset dengan beban WO terbanyak.</span>
                <span className="font-semibold text-slate-600">{labels.length} aset dianalisis</span>
            </div>
            <div className="max-h-[420px] overflow-y-auto overflow-x-hidden pr-2 custom-scrollbar">
                <div style={{ height: `${chartHeight}px` }}>
                    <Bar data={data} options={options} />
                </div>
            </div>
        </div>
    );
}
