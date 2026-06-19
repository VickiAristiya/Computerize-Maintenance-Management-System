# /cmms-backend/app/api/wo_routes.py
from flask import Blueprint, request, jsonify, make_response
from app.models import WorkOrder, Asset, User, ComponentItem 
from mongoengine.errors import DoesNotExist
import datetime
import csv 
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm

wo_bp = Blueprint('wo_bp', __name__)

# --- Helper Report ---
def calculate_asset_report_data():
    all_wos = WorkOrder.objects().all()
    report_data = {}
    
    for wo in all_wos:
        try:
            if not wo.asset: continue 
            
            asset_id = str(wo.asset.id)
            asset_name = wo.asset.name
            status = wo.status
            
            if asset_id not in report_data:
                report_data[asset_id] = {
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "open": 0,
                    "in_progress": 0,
                    "pending_approval": 0,
                    "pending_verification": 0,
                    "completed": 0,
                    "total_wo": 0
                }
            
            stats = report_data[asset_id]
            stats["total_wo"] += 1
            
            if status == 'open': stats["open"] += 1
            elif status == 'in_progress': stats["in_progress"] += 1
            elif status == 'pending_approval': stats["pending_approval"] += 1
            elif status == 'pending_verification': stats["pending_verification"] += 1
            elif status == 'completed': stats["completed"] += 1
        
        except Exception as e:
            continue

    return list(report_data.values())

# --- GET Work Orders ---
@wo_bp.route('/workorders', methods=['GET'])
def get_work_orders():
    try:
        # Ambil semua yang belum COMPLETED sepenuhnya
        wos_raw = WorkOrder.objects(status__ne='completed').order_by('status', '-created_at')
        
        safe_wos = []
        for wo in wos_raw:
            try:
                safe_wos.append(wo.to_json())
            except Exception:
                continue 
                
        return jsonify(safe_wos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- GET History ---
@wo_bp.route('/workorders/history', methods=['GET'])
def get_work_order_history():
    try:
        wos_raw = WorkOrder.objects(status='completed').order_by('-completed_at')
        
        safe_wos = []
        for wo in wos_raw:
            try:
                safe_wos.append(wo.to_json())
            except Exception:
                continue
                
        return jsonify(safe_wos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- POST Create Work Order ---
@wo_bp.route('/workorders', methods=['POST'])
def create_work_order():
    try:
        data = request.get_json()
        
        # 1. Cek Role Pembuat
        creator_role = data.get('created_by_role', 'technician').lower()
        
        # Teknisi dan Admin tidak boleh membuat WO
        if creator_role in ('technician', 'admin'):
            return jsonify({"error": "Akses Ditolak: Hanya Manager yang dapat membuat Work Order."}), 403
            
        # Tentukan Status Awal
        initial_status = 'open'
        if creator_role == 'manager':
            # Jika Manajer yang buat, harus diverifikasi Admin dulu (Pending Approval)
            initial_status = 'pending_approval'

        # 2. Validasi Input
        if not data.get('title') or not data.get('asset_id') or not data.get('type'):
            return jsonify({"error": "Input tidak lengkap: title, asset_id, dan type diperlukan"}), 400

        # 3. Validasi Foto Awal (Wajib)
        if not data.get('initial_image'):
             return jsonify({"error": "Wajib menyertakan foto bagian yang harus diperbaiki."}), 400

        try:
            asset = Asset.objects.get(id=data['asset_id'])
        except DoesNotExist:
            return jsonify({"error": "Aset tidak ditemukan"}), 404
        
        assigned_user = None
        if data.get('assigned_to_id'):
            try:
                assigned_user = User.objects.get(id=data['assigned_to_id'])
            except DoesNotExist:
                pass 

        wo_component = None
        if data.get('component_id'): 
            try:
                wo_component = ComponentItem.objects.get(id=data['component_id'])
            except DoesNotExist:
                return jsonify({"error": "Komponen tidak ditemukan di gudang"}), 404

        new_wo = WorkOrder(
            title=data['title'],
            description=data.get('description', ''),
            priority=data.get('priority', 'medium'),
            type=data['type'],
            status=initial_status, # Set status awal sesuai role
            asset=asset,
            assigned_to=assigned_user,
            component=wo_component,
            created_by_role=creator_role,
            initial_image=data.get('initial_image')
        )
        
        if data.get('due_date'):
            try:
                new_wo.due_date = datetime.datetime.fromisoformat(data['due_date'])
            except ValueError:
                return jsonify({"error": "Format due_date salah."}), 400

        new_wo.save()
        
        return jsonify(new_wo.to_json()), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- PATCH Update Work Order (PERBAIKAN UTAMA ADA DI SINI) ---
@wo_bp.route('/workorders/<wo_id>', methods=['PATCH'])
def update_work_order(wo_id):
    try:
        data = request.get_json()
        wo = WorkOrder.objects.get(id=wo_id)
        old_status = wo.status

        # Update fields umum
        if 'title' in data: wo.title = data['title']
        if 'description' in data: wo.description = data['description']
        if 'priority' in data: wo.priority = data['priority']
        if 'evidence_image' in data: wo.evidence_image = data['evidence_image']
        
        # --- NEW LOGIC: Update Teknisi (Assigned To) ---
        # Ini penting agar nama teknisi tersimpan saat dia klik 'Mulai' atau 'Selesai'
        if 'assigned_to_id' in data and data['assigned_to_id']:
            try:
                technician = User.objects.get(id=data['assigned_to_id'])
                wo.assigned_to = technician
            except DoesNotExist:
                pass 
        # ------------------------------------------------
        
        if 'component_id' in data:
             if data['component_id']:
                 wo.component = ComponentItem.objects.get(id=data['component_id'])
             else:
                 wo.component = None

        if 'status' in data:
            new_status = data['status']
            allowed_statuses = ['open', 'in_progress', 'pending_approval', 'pending_verification', 'completed']
            
            if new_status not in allowed_statuses:
                return jsonify({"error": "Status tidak valid"}), 400
            
            # --- LOGIC FLOW ---
            
            # 1. Approval (Pending Approval -> Open)
            if old_status == 'pending_approval' and new_status == 'open':
                pass 
            
            # 2. Technician Finish (In Progress -> Pending Verification)
            if new_status == 'pending_verification':
                has_evidence = data.get('evidence_image') or wo.evidence_image
                if not has_evidence:
                    return jsonify({"error": "Gagal: Wajib upload bukti foto sebelum verifikasi."}), 400

            # 3. Final Verification (Pending Verification -> Completed)
            if new_status == 'completed':
                if old_status != 'completed':
                    # Kurangi Stok
                    wo.completed_at = datetime.datetime.utcnow()
                    if wo.component:
                        try:
                            comp_item = ComponentItem.objects.get(id=wo.component.id)
                            if comp_item.stock_quantity > 0:
                                comp_item.stock_quantity -= 1
                                comp_item.save()
                        except DoesNotExist: pass
            
            wo.status = new_status

        wo.save()
        return jsonify(wo.to_json()), 200

    except DoesNotExist:
        return jsonify({"error": "Work Order tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DELETE Work Order ---
@wo_bp.route('/workorders/<wo_id>', methods=['DELETE'])
def delete_work_order(wo_id):
    try:
        wo = WorkOrder.objects.get(id=wo_id)
        wo.delete()
        return jsonify({"message": "Work Order dihapus."}), 200
    except DoesNotExist:
        return jsonify({"error": "Work Order tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Reject Verification (Admin/Manager tolak verifikasi) ---
@wo_bp.route('/workorders/<wo_id>/reject-verification', methods=['PATCH'])
def reject_verification(wo_id):
    try:
        data = request.get_json() or {}
        wo = WorkOrder.objects.get(id=wo_id)
        
        # Hanya bisa menolak dari status pending_verification
        if wo.status != 'pending_verification':
            return jsonify({"error": "Hanya Work Order dengan status 'pending_verification' yang bisa ditolak"}), 400
        
        # Kembalikan status ke in_progress
        wo.status = 'in_progress'
        
        # Hapus bukti foto (evidence_image)
        wo.evidence_image = None
        
        # Jika ada catatan penolakan, simpan (optional)
        # rejection_reason = data.get('rejection_reason', '')
        
        wo.save()
        
        return jsonify({
            "message": "Verifikasi ditolak. Status dikembalikan ke 'In Progress'.",
            "work_order": wo.to_json()
        }), 200
    
    except DoesNotExist:
        return jsonify({"error": "Work Order tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Reports (Export CSV/PDF) ---
@wo_bp.route('/workorders/report/asset_stats', methods=['GET'])
def get_asset_report_stats():
    try:
        final_report = calculate_asset_report_data()
        return jsonify(final_report), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@wo_bp.route('/workorders/report/export/csv', methods=['GET'])
def export_asset_report_csv():
    try:
        report_data = calculate_asset_report_data()
        if not report_data: return jsonify({"error": "No data"}), 404
        si = StringIO()
        cw = csv.writer(si)
        header = ['Asset_ID', 'Asset_Name', 'Total_WO', 'Open', 'Pending_Approval', 'Pending_Verify', 'Completed']
        cw.writerow(header)
        for row in report_data:
            cw.writerow([row['asset_id'], row['asset_name'], row['total_wo'], row['open'], row['pending_approval'], row['pending_verification'], row['completed']])
        response = make_response(si.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=Laporan.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@wo_bp.route('/workorders/report/export/pdf', methods=['GET'])
def export_asset_report_pdf():
    try:
        report_data = calculate_asset_report_data()
        if not report_data: return jsonify({"error": "No data"}), 404
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph("Laporan Kinerja Aset", styles['Title'])]
        data = [['Aset', 'Total', 'Open', 'Pending Appr', 'Pending Verif', 'Done']]
        for row in report_data:
            data.append([row['asset_name'], row['total_wo'], row['open'], row['pending_approval'], row['pending_verification'], row['completed']])
        table = Table(data)
        table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
        story.append(table)
        doc.build(story)
        pdf_value = buffer.getvalue()
        buffer.close()
        response = make_response(pdf_value)
        response.headers['Content-Disposition'] = 'attachment; filename=Laporan.pdf'
        response.headers['Content-type'] = 'application/pdf'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- History Export ---

def get_history_export_data():
    """Kumpulkan data riwayat WO selesai untuk ekspor."""
    wos = WorkOrder.objects(status='completed').order_by('-completed_at')
    rows = []
    for idx, wo in enumerate(wos, start=1):
        try:
            asset_name = wo.asset.name if wo.asset else '-'
        except Exception:
            asset_name = '-'
        try:
            technician = wo.assigned_to.name if wo.assigned_to else '-'
        except Exception:
            technician = '-'
        try:
            component_name = wo.component.name if wo.component else '-'
        except Exception:
            component_name = '-'

        def fmt_dt(dt, include_time=True):
            if not dt:
                return '-'
            fmt = '%d/%m/%Y %H:%M' if include_time else '%d/%m/%Y'
            return dt.strftime(fmt)

        rows.append({
            'no': idx,
            'id': str(wo.id),
            'title': wo.title or '',
            'description': (wo.description or '').replace('\n', ' '),
            'asset_name': asset_name,
            'component_name': component_name,
            'assigned_to': technician,
            'type': 'Preventive' if wo.type == 'preventive' else 'Corrective',
            'priority': (wo.priority or '').capitalize(),
            'created_by_role': (wo.created_by_role or '').capitalize(),
            'created_at': fmt_dt(wo.created_at),
            'due_date': fmt_dt(wo.due_date, include_time=False),
            'completed_at': fmt_dt(wo.completed_at),
            'foto_awal': 'Ada' if wo.initial_image else 'Tidak Ada',
            'foto_bukti': 'Ada' if wo.evidence_image else 'Tidak Ada',
        })
    return rows


@wo_bp.route('/workorders/history/export/csv', methods=['GET'])
def export_history_csv():
    try:
        rows = get_history_export_data()
        if not rows:
            return jsonify({"error": "Belum ada riwayat perawatan"}), 404

        si = StringIO()
        cw = csv.writer(si)
        cw.writerow([
            'No', 'ID_WO', 'Judul_WO', 'Deskripsi', 'Aset', 'Komponen',
            'Teknisi', 'Tipe', 'Prioritas', 'Dibuat_Oleh',
            'Tanggal_Dibuat', 'Target_Selesai', 'Tanggal_Selesai',
            'Foto_Awal', 'Foto_Bukti'
        ])
        for r in rows:
            cw.writerow([
                r['no'], r['id'], r['title'], r['description'],
                r['asset_name'], r['component_name'], r['assigned_to'],
                r['type'], r['priority'], r['created_by_role'],
                r['created_at'], r['due_date'], r['completed_at'],
                r['foto_awal'], r['foto_bukti']
            ])

        response = make_response('﻿' + si.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=Riwayat_Perawatan.csv'
        response.headers['Content-type'] = 'text/csv; charset=utf-8'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@wo_bp.route('/workorders/history/export/pdf', methods=['GET'])
def export_history_pdf():
    try:
        rows = get_history_export_data()
        if not rows:
            return jsonify({"error": "Belum ada riwayat perawatan"}), 404

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'HistoryTitle', parent=styles['Title'],
            alignment=TA_CENTER, fontSize=16, spaceAfter=2,
        )
        subtitle_style = ParagraphStyle(
            'HistorySubtitle', parent=styles['Normal'],
            alignment=TA_CENTER, fontSize=9,
            textColor=colors.HexColor('#64748b'), spaceAfter=10,
        )
        cell_style = ParagraphStyle(
            'Cell', parent=styles['Normal'],
            fontSize=7, leading=9,
        )

        story = [
            Paragraph("Riwayat Perawatan", title_style),
            Paragraph(
                f"Diekspor pada: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} &nbsp;|&nbsp; Total: {len(rows)} Work Order",
                subtitle_style,
            ),
            Spacer(1, 0.3 * cm),
        ]

        header_row = ['No', 'Judul WO', 'Aset', 'Komponen', 'Teknisi', 'Tipe', 'Prioritas', 'Tgl Dibuat', 'Tgl Selesai']
        table_data = [header_row]
        for r in rows:
            table_data.append([
                str(r['no']),
                Paragraph(r['title'], cell_style),
                Paragraph(r['asset_name'], cell_style),
                Paragraph(r['component_name'], cell_style),
                Paragraph(r['assigned_to'], cell_style),
                r['type'],
                r['priority'],
                r['created_at'],
                r['completed_at'],
            ])

        # A4 landscape usable width ≈ 26.7 cm (after 1.5cm margins each side)
        col_widths = [0.8*cm, 5.8*cm, 3.5*cm, 3.0*cm, 3.2*cm, 2.2*cm, 2.2*cm, 3.0*cm, 3.0*cm]

        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (5, 1), (6, -1), 'CENTER'),
        ]
        for i in range(1, len(table_data)):
            bg = colors.white if i % 2 == 1 else colors.HexColor('#f1f5f9')
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle(style_cmds))
        story.append(table)

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(
            "* Kolom 'Foto Awal' dan 'Foto Bukti' tersedia dalam ekspor CSV.",
            ParagraphStyle('Note', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#94a3b8')),
        ))

        doc.build(story)
        pdf_value = buffer.getvalue()
        buffer.close()

        response = make_response(pdf_value)
        response.headers['Content-Disposition'] = 'attachment; filename=Riwayat_Perawatan.pdf'
        response.headers['Content-type'] = 'application/pdf'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500