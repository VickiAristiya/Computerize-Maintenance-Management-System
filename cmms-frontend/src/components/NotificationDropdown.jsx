// src/components/NotificationDropdown.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import api from '../services/api';
import { Bell, CalendarClock, ShieldCheck, Loader2, X, AlertTriangle, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';
import MLNotificationDetailModal from './MLNotificationDetailModal';

const RISK_BADGE = {
  critical: 'bg-rose-100 text-rose-700',
  high:     'bg-red-100 text-red-700',
  medium:   'bg-orange-100 text-orange-700',
  low:      'bg-yellow-100 text-yellow-700',
  very_low: 'bg-green-100 text-green-700',
};

const NOTIFICATION_POLL_MS = 10000;

export default function NotificationDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedNotif, setSelectedNotif] = useState(null);
  const dropdownRef = useRef(null);

  // Fetch Data Notifikasi
  const fetchNotifications = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const response = await api.get('/dashboard/stats');
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
                  asset_id: pred.asset_id,
                  asset_name: pred.asset_name,
                  message: pred.message,
                  recommendation: pred.recommendation,
                  link: pred.link,
                  priority: pred.priority,
                  date: pred.due_date,
                  predicted_days: pred.predicted_days,
                  failure_probability: pred.failure_probability,
                  health_score: pred.health_score,
                  overall_health_score: pred.overall_health_score,
                  risk_level: pred.risk_level,
                  faulty_components: pred.faulty_components,
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
    <>
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
                    {notifications.map((notif) => {
                        const isPredictive = notif.type === 'predictive';
                        const Wrapper = isPredictive ? 'div' : Link;
                        const wrapperProps = isPredictive
                            ? {
                                role: 'button',
                                tabIndex: 0,
                                onClick: () => { setSelectedNotif(notif); setIsOpen(false); },
                                onKeyDown: (e) => e.key === 'Enter' && (setSelectedNotif(notif), setIsOpen(false)),
                              }
                            : {
                                to: notif.link,
                                onClick: () => setIsOpen(false),
                              };

                        return (
                            <Wrapper
                                key={notif.id}
                                {...wrapperProps}
                                className="block p-4 hover:bg-slate-50 transition-colors cursor-pointer"
                            >
                                <div className="flex gap-3">
                                    {/* Icon */}
                                    <div className={`shrink-0 mt-0.5 p-2 rounded-full ${
                                        notif.type === 'verification' ? 'bg-purple-100 text-purple-600' :
                                        notif.type === 'predictive'   ? 'bg-red-100 text-red-600' :
                                        'bg-blue-100 text-blue-600'
                                    }`}>
                                        {notif.type === 'verification' ? <ShieldCheck size={14}/> :
                                         notif.type === 'predictive'   ? <Activity size={14}/> :
                                         <CalendarClock size={14}/>}
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        {/* Title + risk badge */}
                                        <div className="flex items-start justify-between gap-2">
                                            <p className={`text-xs font-bold leading-snug ${
                                                notif.priority === 'critical' || notif.priority === 'high'
                                                    ? 'text-red-600' : 'text-slate-700'
                                            }`}>
                                                {notif.title}
                                            </p>
                                            {isPredictive && notif.risk_level && (
                                                <span className={`shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded ${RISK_BADGE[notif.risk_level] || RISK_BADGE.very_low}`}>
                                                    {notif.risk_level}
                                                </span>
                                            )}
                                        </div>

                                        {/* Asset name */}
                                        <p className="text-[11px] text-slate-500 font-medium mt-0.5">
                                            {notif.asset_name || notif.message}
                                        </p>

                                        {/* Faulty component badges */}
                                        {isPredictive && notif.faulty_components?.length > 0 && (
                                            <div className="flex flex-wrap gap-1 mt-1.5">
                                                {notif.faulty_components.map((c) => (
                                                    <span
                                                        key={c.key}
                                                        className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${
                                                            RISK_BADGE[c.risk_level] || RISK_BADGE.very_low
                                                        }`}
                                                    >
                                                        {c.label} · {c.prediction} · {Math.round((c.health_score ?? 0) * 100)}%
                                                    </span>
                                                ))}
                                            </div>
                                        )}

                                        {/* Aggregate recommendation */}
                                        {isPredictive && notif.recommendation && (
                                            <p className="text-[10px] text-slate-600 mt-1.5 leading-relaxed italic">
                                                {notif.recommendation}
                                            </p>
                                        )}

                                        {/* Schedule / verification message */}
                                        {!isPredictive && (
                                            <p className="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                                                {notif.message}
                                            </p>
                                        )}

                                        {/* Footer */}
                                        <p className="text-[10px] text-slate-400 mt-1">
                                            {isPredictive && notif.predicted_days !== undefined
                                                ? `Health ${Math.round((notif.overall_health_score ?? notif.health_score ?? 0) * 100)}% · ${notif.predicted_days === 0 ? 'Tindakan segera' : `${notif.predicted_days} hari lagi`} · Klik untuk detail`
                                                : 'Klik untuk melihat detail'}
                                        </p>
                                    </div>
                                </div>
                            </Wrapper>
                        );
                    })}
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

    {/* Modal detail ML — render di luar dropdown agar tidak ter-clip */}
    {selectedNotif && (
      <MLNotificationDetailModal
        notification={selectedNotif}
        onClose={() => setSelectedNotif(null)}
      />
    )}
    </>
  );
}
