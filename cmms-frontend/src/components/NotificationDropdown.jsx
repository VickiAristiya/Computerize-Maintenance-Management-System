// src/components/NotificationDropdown.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { Bell, CalendarClock, ShieldCheck, Loader2, X, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';

const API_BASE_URL = 'http://localhost:5000/api';
const NOTIFICATION_POLL_MS = 10000;

export default function NotificationDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);

  // Fetch Data Notifikasi
  const fetchNotifications = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/dashboard/stats`);
      const data = response.data;
      
      const newNotifications = [];

      // 1. Jadwal Mendekati
      if (data.upcoming_schedules) {
          data.upcoming_schedules.forEach(sch => {
              const scheduleMessage = sch.days_left < 0
                  ? `${sch.task_name} pada ${sch.asset_name} sudah terlewat ${Math.abs(sch.days_left)} hari.`
                  : sch.days_left === 0
                    ? `${sch.task_name} pada ${sch.asset_name} jatuh tempo hari ini.`
                    : `${sch.task_name} pada ${sch.asset_name} jatuh tempo dalam ${sch.days_left} hari.`;

              newNotifications.push({
                  id: `sch-${sch.id}`,
                  type: 'schedule',
                  title: sch.days_left < 0 ? 'Jadwal Perawatan Terlewat' : 'Jadwal Perawatan Dekat',
                  message: scheduleMessage,
                  link: '/schedules',
                  priority: sch.days_left < 0 || sch.priority === 'high' ? 'high' : 'medium',
                  date: sch.due_date
              });
          });
      }

      // 2. Work order yang butuh verifikasi
      if (data.verification_needed_list) {
          data.verification_needed_list.forEach(wo => {
              newNotifications.push({
                  id: `verif-${wo.id}`,
                  type: 'verification',
                  title: 'Work Order Butuh Verifikasi',
                  message: `${wo.title} pada ${wo.asset_name} menunggu verifikasi.`,
                  link: '/work-orders',
                  priority: 'medium',
                  date: wo.completed_at
              });
          });
      }

      // 3. Predictive Maintenance Notifications
      if (data.predictive_maintenance_notifications) {
          data.predictive_maintenance_notifications.forEach(pred => {
              newNotifications.push({
                  id: pred.id,
                  type: 'predictive',
                  title: pred.title,
                  message: `${pred.asset_name}: ${pred.message}`,
                  link: pred.link,
                  priority: pred.priority === 'critical' ? 'high' : pred.priority,
                  date: pred.due_date,
                  predicted_days: pred.predicted_days,
                  failure_probability: pred.failure_probability,
                  health_score: pred.health_score,
                  risk_level: pred.risk_level
              });
          });
      }

      setNotifications(newNotifications);
      setUnreadCount(newNotifications.length);

    } catch (error) {
      console.error("Gagal memuat notifikasi:", error);
    }
    if (showLoading) setLoading(false);
  }, []);

  // Load data saat komponen mount (atau bisa dipasang interval polling)
  useEffect(() => {
    const initialFetch = window.setTimeout(() => fetchNotifications(false), 0);
    const interval = setInterval(fetchNotifications, NOTIFICATION_POLL_MS);
    return () => {
      window.clearTimeout(initialFetch);
      clearInterval(interval);
    };
  }, [fetchNotifications]);

  // Tutup dropdown saat klik di luar
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
        // Saat dibuka, refresh data untuk memastikan akurat
        fetchNotifications(); 
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      
      {/* Tombol Lonceng */}
      <button 
        onClick={toggleDropdown}
        className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition relative focus:outline-none"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 border-2 border-white"></span>
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 md:w-96 bg-white rounded-xl shadow-2xl border border-slate-100 overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-200 origin-top-right">
          
          {/* Header */}
          <div className="px-4 py-3 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h3 className="font-bold text-slate-700 text-sm">Notifikasi</h3>
            <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={16} />
            </button>
          </div>

          {/* List Notifikasi */}
          <div className="max-h-80 overflow-y-auto custom-scrollbar">
            {loading ? (
                <div className="p-8 flex justify-center">
                    <Loader2 className="animate-spin text-slate-300" />
                </div>
            ) : notifications.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-sm">
                    Tidak ada notifikasi baru.
                </div>
            ) : (
                <div className="divide-y divide-slate-50">
                    {notifications.map((notif) => (
                        <Link 
                            key={notif.id} 
                            to={notif.link} 
                            onClick={() => setIsOpen(false)}
                            className="block p-4 hover:bg-slate-50 transition-colors"
                        >
                            <div className="flex gap-3">
                                <div className={`shrink-0 mt-1 p-2 rounded-full ${
                                    notif.type === 'verification' ? 'bg-purple-100 text-purple-600' : 
                                    notif.type === 'predictive' ? 'bg-red-100 text-red-600' :
                                    'bg-blue-100 text-blue-600'
                                }`}>
                                    {notif.type === 'verification' ? <ShieldCheck size={16}/> : 
                                     notif.type === 'predictive' ? <AlertTriangle size={16}/> :
                                     <CalendarClock size={16}/>}
                                </div>
                                <div>
                                    <p className={`text-sm font-bold ${
                                        notif.priority === 'high' ? 'text-red-600' : 'text-slate-700'
                                    }`}>
                                        {notif.title}
                                    </p>
                                    <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
                                        {notif.message}
                                    </p>
                                    <p className="text-[10px] text-slate-400 mt-1">
                                        {notif.type === 'predictive' && notif.predicted_days !== undefined
                                          ? `Risiko ${notif.risk_level || '-'} | Estimasi tindakan: ${notif.predicted_days === 0 ? 'segera' : `${notif.predicted_days} hari lagi`}`
                                          : 'Klik untuk melihat detail'}
                                    </p>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
          </div>
          
          {/* Footer */}
          <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 text-center">
              <Link to="/dashboard" onClick={() => setIsOpen(false)} className="text-xs font-bold text-blue-600 hover:underline">
                  Lihat Dashboard Lengkap
              </Link>
          </div>
        </div>
      )}
    </div>
  );
}
