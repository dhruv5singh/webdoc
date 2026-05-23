import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

from feedback_db import (
    get_bug_reports,
    get_feature_requests,
    update_bug_status,
    update_feature_status,
    delete_bug_report,
    delete_feature_request,
    init_feedback_db
)

# Initialize database schemas
init_feedback_db()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="WebDoc - Admin Control Panel",
    page_icon="🛠️",
    layout="wide"
)

# ================================================================
# ADMIN AUTHENTICATION GATE
# ================================================================
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin1234")  # Set ADMIN_PASSWORD on Render

if 'admin_authenticated' not in st.session_state:
    st.session_state['admin_authenticated'] = False

if not st.session_state['admin_authenticated']:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, .stApp { font-family: 'Inter', sans-serif !important; background-color: #0b0f1a !important; }
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stHeaderActionElements"] { display: none !important; }
    .stApp { display: flex; align-items: center; justify-content: center; }
    .stTextInput > div > div > input {
        background: #111827 !important; border: 1px solid #1f2d45 !important;
        color: #e2e8f0 !important; border-radius: 10px !important;
        font-size: 14px !important; padding: 0.6rem 1rem !important;
    }
    .stTextInput > div > div > input:focus { border-color: #7c3aed !important; box-shadow: 0 0 0 3px rgba(124,58,237,0.2) !important; }
    .stTextInput > label { color: #94a3b8 !important; font-size: 13px !important; }
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
        color: white !important; border: none !important; border-radius: 10px !important;
        font-weight: 700 !important; padding: 0.6rem 1.5rem !important;
        width: 100% !important; font-size: 15px !important;
        box-shadow: 0 4px 20px rgba(124,58,237,0.4) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover { box-shadow: 0 6px 28px rgba(124,58,237,0.65) !important; transform: translateY(-1px) !important; }
    </style>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("""
        <div style="text-align:center; padding: 3rem 2rem 2rem;">
            <div style="font-size:3.5rem; margin-bottom:0.5rem;">🛠️</div>
            <h1 style="color:#ffffff; font-weight:800; font-size:1.8rem; margin:0 0 6px;">WebDoc Admin</h1>
            <p style="color:#4b5563; font-size:13px; margin:0 0 2rem; text-transform:uppercase; letter-spacing:1px;">Restricted Access — Control Panel</p>
        </div>
        """, unsafe_allow_html=True)

        pwd_input = st.text_input("Admin Password", type="password", placeholder="Enter admin password...", key="admin_pwd_input")

        if st.button("🔐 Sign In to Admin Panel", use_container_width=True):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state['admin_authenticated'] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Access denied.")

        st.markdown("""
        <div style="text-align:center; margin-top:2rem;">
            <p style="color:#2d3a55; font-size:11px;">🔒 This panel is restricted to authorised administrators only.</p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ================================================================
# GLOBAL CSS (Matching WebDoc UI Aesthetics)
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, .stApp, .stMarkdown, .stButton, .stTextInput, .stSelectbox, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
}

#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }

.stApp {
    background-color: #0b0f1a !important;
    color: #e2e8f0 !important;
}

[data-testid="stSidebar"] {
    background: #0d1321 !important;
    border-right: 1px solid #1f2d45 !important;
    min-width: 240px !important;
}

/* Sidebar buttons — Flat ghost style */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #64748b !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.75rem !important;
    text-align: left !important;
    box-shadow: none !important;
    transition: all 0.18s ease !important;
    font-size: 13px !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.05) !important;
    color: #e2e8f0 !important;
    transform: none !important;
    box-shadow: none !important;
    border: none !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
    font-size: 13px !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5) !important;
    background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
}

/* Inputs styling */
.stTextInput > div > div > input {
    background: #111827 !important;
    border: 1px solid #1f2d45 !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    padding: 0.6rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.2) !important;
}
.stTextInput > label { color: #94a3b8 !important; font-size: 13px !important; }

/* Custom metric containers */
[data-testid="metric-container"] {
    background: linear-gradient(145deg, #111827, #0f172a) !important;
    border: 1px solid #1f2d45 !important;
    border-radius: 16px !important;
    padding: 1.2rem !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}

.stSelectbox > div > div {
    background: #111827 !important;
    border: 1px solid #1f2d45 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}
.stSelectbox label { color: #94a3b8 !important; font-size: 13px !important; }

details {
    background: #111827 !important;
    border: 1px solid #1f2d45 !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    margin-bottom: 0.8rem !important;
    padding: 0.4rem 0.8rem !important;
}
details summary { color: #a78bfa !important; font-size: 14px !important; cursor: pointer; font-weight:600; }

.stAlert { border-radius: 10px !important; }
.stSpinner > div { border-top-color: #7c3aed !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0b0f1a; }
::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #4a5568; }

hr { border-color: #1f2d45 !important; margin: 1.5rem 0 !important; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
</style>
""", unsafe_allow_html=True)


# ================================================================
# DATA HELPERS
# ================================================================
def get_global_scans():
    try:
        conn = sqlite3.connect("user_data.db", check_same_thread=False)
        df = pd.read_sql_query("SELECT * FROM records ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def status_badge(status):
    status = (status or "Pending").strip()
    color_map = {
        "Pending": ("#f59e0b", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.25)"),
        "In Progress": ("#3b82f6", "rgba(59,130,246,0.12)", "rgba(59,130,246,0.25)"),
        "Resolved": ("#10b981", "rgba(16,185,129,0.12)", "rgba(16,185,129,0.25)")
    }
    fg, bg, border = color_map.get(status, ("#94a3b8", "rgba(148,163,184,0.12)", "rgba(148,163,184,0.25)"))
    return f'<span style="color:{fg}; background:{bg}; border:1px solid {border}; border-radius:12px; padding:3px 10px; font-size:11px; font-weight:700; display:inline-block; letter-spacing:0.5px; text-transform:uppercase;">{status}</span>'


def severity_badge(severity):
    severity = (severity or "Low").strip()
    color_map = {
        "Critical": ("#ef4444", "rgba(239,68,68,0.12)", "rgba(239,68,68,0.25)"),
        "High": ("#f97316", "rgba(249,115,22,0.12)", "rgba(249,115,22,0.25)"),
        "Medium": ("#eab308", "rgba(234,179,8,0.12)", "rgba(234,179,8,0.25)"),
        "Low": ("#3b82f6", "rgba(59,130,246,0.12)", "rgba(59,130,246,0.25)")
    }
    fg, bg, border = color_map.get(severity, ("#94a3b8", "rgba(148,163,184,0.12)", "rgba(148,163,184,0.25)"))
    return f'<span style="color:{fg}; background:{bg}; border:1px solid {border}; border-radius:12px; padding:3px 10px; font-size:11px; font-weight:700; display:inline-block; letter-spacing:0.5px; text-transform:uppercase;">{severity}</span>'


def priority_badge(priority):
    priority = (priority or "Nice to have").strip()
    color_map = {
        "Critical": ("#ec4899", "rgba(236,72,153,0.12)", "rgba(236,72,153,0.25)"),
        "Important": ("#8b5cf6", "rgba(139,92,246,0.12)", "rgba(139,92,246,0.25)"),
        "Nice to have": ("#10b981", "rgba(16,185,129,0.12)", "rgba(16,185,129,0.25)")
    }
    fg, bg, border = color_map.get(priority, ("#94a3b8", "rgba(148,163,184,0.12)", "rgba(148,163,184,0.25)"))
    return f'<span style="color:{fg}; background:{bg}; border:1px solid {border}; border-radius:12px; padding:3px 10px; font-size:11px; font-weight:700; display:inline-block; letter-spacing:0.5px; text-transform:uppercase;">{priority}</span>'


# ================================================================
# SIDEBAR ROUTER
# ================================================================
if 'admin_page' not in st.session_state:
    st.session_state['admin_page'] = 'dashboard'

current_page = st.session_state['admin_page']

st.sidebar.markdown("""
<div style="text-align:center; padding: 1.5rem 0.5rem 0.5rem;">
    <span style="font-size:2.8rem;">🛠️</span>
    <h2 style="color:#ffffff; font-weight:800; font-size:1.4rem; margin:10px 0 2px; letter-spacing:-0.5px;">WebDoc Admin</h2>
    <p style="color:#4b5563; font-size:11px; font-weight:500; margin:0; text-transform:uppercase; letter-spacing:1px;">Control Panel</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown('<hr style="border-color:#1f2d45; margin:0.8rem 0 1rem;">', unsafe_allow_html=True)


def nav_btn(label, icon, page_name):
    is_active = current_page == page_name
    if is_active:
        st.sidebar.markdown(f"""
        <div style="background:rgba(124,58,237,0.15); border-left:3px solid #7c3aed;
                    border-radius:10px; padding:9px 12px; margin-bottom:6px;
                    display:flex; align-items:center; gap:9px;">
            <span style="font-size:15px; line-height:1;">{icon}</span>
            <span style="color:#a78bfa; font-weight:700; font-size:13px;">{label}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.sidebar.button(f"{icon}  {label}", key=f"nav_{page_name}", use_container_width=True):
            st.session_state['admin_page'] = page_name
            st.rerun()


st.sidebar.markdown(
    '<div style="font-size:9px; font-weight:800; color:#2d3a55; '
    'letter-spacing:1.5px; text-transform:uppercase; padding:0 0.4rem; margin-bottom:6px;">Overview</div>',
    unsafe_allow_html=True
)
nav_btn("Dashboard", "🏠", "dashboard")
nav_btn("Global Scans Log", "📊", "scans")

st.sidebar.markdown(
    '<div style="font-size:9px; font-weight:800; color:#2d3a55; '
    'letter-spacing:1.5px; text-transform:uppercase; padding:0 0.4rem; margin:15px 0 6px;">Feedback Inbox</div>',
    unsafe_allow_html=True
)
nav_btn("Bug Reports", "🐛", "bugs")
nav_btn("Feature Requests", "💡", "features")

st.sidebar.markdown('<hr style="border-color:#1f2d45; margin:1.2rem 0 0.8rem;">', unsafe_allow_html=True)
if st.sidebar.button("🚪  Sign Out", key="admin_logout", use_container_width=True):
    st.session_state['admin_authenticated'] = False
    st.rerun()


# ================================================================
# FETCH ALL DATA
# ================================================================
bugs_df = get_bug_reports()
features_df = get_feature_requests()
scans_df = get_global_scans()

# Total calculations
total_bugs = len(bugs_df)
pending_bugs = len(bugs_df[bugs_df['status'] != 'Resolved']) if total_bugs > 0 else 0
total_features = len(features_df)
pending_features = len(features_df[features_df['status'] != 'Resolved']) if total_features > 0 else 0
total_scans = len(scans_df)
unique_users = 0

all_emails = set()
if not bugs_df.empty:
    all_emails.update(bugs_df['email'].dropna().tolist())
if not features_df.empty:
    all_emails.update(features_df['email'].dropna().tolist())
if not scans_df.empty:
    all_emails.update(scans_df['email'].dropna().tolist())
unique_users = len(all_emails)


# ================================================================
# PAGE 1 — DASHBOARD OVERVIEW
# ================================================================
if current_page == 'dashboard':
    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <h1 style="color:#ffffff; font-weight:800; font-size:1.8rem; margin:0;">
            🏠 Admin Control Dashboard
        </h1>
        <p style="color:#4b5563; margin-top:4px; font-size:14px;">WebDoc global activities and user submissions health summary</p>
    </div>
    """, unsafe_allow_html=True)

    # Metric Cards row
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    with mc1:
        st.metric("Total Bug Reports", total_bugs, delta=f"{pending_bugs} Pending", delta_color="inverse")
    with mc2:
        st.metric("Feature Requests", total_features, delta=f"{pending_features} Pending", delta_color="inverse")
    with mc3:
        st.metric("Global Website Scans", total_scans)
    with mc4:
        st.metric("Distinct Users", unique_users)
    with mc5:
        system_status = "HEALTHY" if pending_bugs < 3 else "ATTENTION REQUIRED"
        st.metric("System Health State", system_status)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Row 2: Charts
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("<h4 style='color:#e2e8f0; margin-bottom:1rem;'>🐛 Bug Severity Distribution</h4>", unsafe_allow_html=True)
        if not bugs_df.empty and 'severity' in bugs_df.columns:
            sev_counts = bugs_df['severity'].value_counts().reset_index()
            sev_counts.columns = ['Severity', 'Count']
            
            fig = px.pie(
                sev_counts, names='Severity', values='Count', hole=0.45,
                color='Severity',
                color_discrete_map={
                    "Critical": "#ef4444",
                    "High": "#f97316",
                    "Medium": "#eab308",
                    "Low": "#3b82f6"
                }
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#94a3b8',
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No bug submissions yet to build charts.")

    with col_chart2:
        st.markdown("<h4 style='color:#e2e8f0; margin-bottom:1rem;'>💡 Feature Priority Matrix</h4>", unsafe_allow_html=True)
        if not features_df.empty and 'priority' in features_df.columns:
            pri_counts = features_df['priority'].value_counts().reset_index()
            pri_counts.columns = ['Priority', 'Count']
            
            fig2 = px.bar(
                pri_counts, x='Priority', y='Count',
                color='Priority',
                color_discrete_map={
                    "Critical": "#ec4899",
                    "Important": "#8b5cf6",
                    "Nice to have": "#10b981"
                }
            )
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#94a3b8',
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(gridcolor='#1f2d45'),
                yaxis=dict(gridcolor='#1f2d45'),
                showlegend=False
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No feature requests yet to build charts.")

    # Recent scans chart
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#e2e8f0; margin-bottom:0.5rem;'>📈 Recent User Scans Trend</h4>", unsafe_allow_html=True)
    if not scans_df.empty and 'timestamp' in scans_df.columns:
        scans_df['date'] = pd.to_datetime(scans_df['timestamp']).dt.date
        date_counts = scans_df['date'].value_counts().reset_index().sort_values('date')
        date_counts.columns = ['Date', 'Scans']

        fig3 = px.line(date_counts, x='Date', y='Scans', markers=True)
        fig3.update_traces(line_color='#7c3aed', line_width=3, marker=dict(size=8, color='#a78bfa'))
        fig3.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#94a3b8',
            xaxis=dict(gridcolor='#1f2d45'),
            yaxis=dict(gridcolor='#1f2d45'),
            margin=dict(t=20, b=20, l=10, r=10)
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No scan records generated yet.")


# ================================================================
# PAGE 2 — BUG REPORTS INBOX
# ================================================================
elif current_page == 'bugs':
    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <h1 style="color:#ffffff; font-weight:800; font-size:1.8rem; margin:0;">
            🐛 User Bug Reports Inbox
        </h1>
        <p style="color:#4b5563; margin-top:4px; font-size:14px;">Audit user-reported technical issues, track severity, and update status</p>
    </div>
    """, unsafe_allow_html=True)

    if bugs_df.empty:
        st.markdown("""
        <div style="background:#111827; border:1px solid #1f2d45; border-radius:16px;
                    padding:3rem; text-align:center; margin-top:2rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">🎉</div>
            <div style="color:#10b981; font-size:1.1rem; font-weight:700;">No Bugs Reported!</div>
            <div style="color:#4b5563; font-size:13px; margin-top:4px;">
                Everything seems to be running flawlessly on the user end.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Filters
        fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
        with fcol1:
            search_query = st.text_input("🔍 Search Bug reports", placeholder="Search by title, description, or email...")
        with fcol2:
            sev_filter = st.selectbox("Severity Filter", ["All", "Critical", "High", "Medium", "Low"])
        with fcol3:
            status_filter = st.selectbox("Status Filter", ["All", "Pending", "In Progress", "Resolved"])

        # Filter logic
        filtered_bugs = bugs_df.copy()
        if search_query:
            q = search_query.lower()
            filtered_bugs = filtered_bugs[
                filtered_bugs['title'].str.lower().str.contains(q) |
                filtered_bugs['description'].str.lower().str.contains(q) |
                filtered_bugs['email'].str.lower().str.contains(q)
            ]
        if sev_filter != "All":
            filtered_bugs = filtered_bugs[filtered_bugs['severity'] == sev_filter]
        if status_filter != "All":
            filtered_bugs = filtered_bugs[filtered_bugs['status'] == status_filter]

        # Table or list view
        if filtered_bugs.empty:
            st.info("No bug reports match your filter criteria.")
        else:
            st.markdown(f"<div style='color:#64748b; font-size:13px; margin-bottom:10px;'>Showing {len(filtered_bugs)} records</div>", unsafe_allow_html=True)
            
            for index, row in filtered_bugs.iterrows():
                bug_id = row['id']
                created_at = row['timestamp']
                
                # Format a nice title line inside the expander
                expander_label = f"#{bug_id} — {row['title']} | Email: {row['email']}"
                
                with st.expander(expander_label):
                    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
                    
                    # Columns inside details
                    dcol1, dcol2 = st.columns([3, 1])
                    
                    with dcol1:
                        st.markdown(f"**🐛 Description:**")
                        st.write(row['description'])
                        
                        if row.get('steps'):
                            st.markdown(f"**📋 Steps to Reproduce:**")
                            st.write(row['steps'])
                            
                        st.markdown(f"<div style='font-size:11px; color:#4b5563; margin-top:10px;'>Reported on: {created_at}</div>", unsafe_allow_html=True)

                    with dcol2:
                        with st.container(border=True):
                            st.markdown(f"<div style='margin-bottom:8px;'>Severity: {severity_badge(row['severity'])}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div style='margin-bottom:12px;'>Current Status: {status_badge(row['status'])}</div>", unsafe_allow_html=True)
                            
                            # Interactive Status updates
                            status_options = ["Pending", "In Progress", "Resolved"]
                            current_status_idx = status_options.index(row['status']) if row['status'] in status_options else 0
                            new_status = st.selectbox("Update Status", status_options, index=current_status_idx, key=f"status_select_bug_{bug_id}")
                            
                            if new_status != row['status']:
                                update_bug_status(bug_id, new_status)
                                st.success(f"Status updated to {new_status}!")
                                st.rerun()

                            st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                            
                            # Delete action
                            if st.button("🗑️ Delete / Resolve Report", key=f"del_bug_{bug_id}", use_container_width=True):
                                delete_bug_report(bug_id)
                                st.success("Bug report deleted successfully!")
                                st.rerun()


            # Export to CSV
            st.markdown("<hr>", unsafe_allow_html=True)
            csv = filtered_bugs.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Filtered Bug Reports to CSV",
                data=csv,
                file_name=f"bug_reports_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
                use_container_width=True
            )


# ================================================================
# PAGE 3 — FEATURE REQUESTS INBOX
# ================================================================
elif current_page == 'features':
    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <h1 style="color:#ffffff; font-weight:800; font-size:1.8rem; margin:0;">
            💡 User Feature Requests Inbox
        </h1>
        <p style="color:#4b5563; margin-top:4px; font-size:14px;">Audit user-submitted ideas, prioritize requirements, and manage status</p>
    </div>
    """, unsafe_allow_html=True)

    if features_df.empty:
        st.markdown("""
        <div style="background:#111827; border:1px solid #1f2d45; border-radius:16px;
                    padding:3rem; text-align:center; margin-top:2rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">💡</div>
            <div style="color:#10b981; font-size:1.1rem; font-weight:700;">No Feature Requests!</div>
            <div style="color:#4b5563; font-size:13px; margin-top:4px;">
                Ask your users for feedback to compile ideas here.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Filters
        fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
        with fcol1:
            search_query = st.text_input("🔍 Search Feature requests", placeholder="Search by title, description, or email...")
        with fcol2:
            pri_filter = st.selectbox("Priority Filter", ["All", "Critical", "Important", "Nice to have"])
        with fcol3:
            status_filter = st.selectbox("Status Filter", ["All", "Pending", "In Progress", "Resolved"])

        # Filter logic
        filtered_frs = features_df.copy()
        if search_query:
            q = search_query.lower()
            filtered_frs = filtered_frs[
                filtered_frs['title'].str.lower().str.contains(q) |
                filtered_frs['description'].str.lower().str.contains(q) |
                filtered_frs['email'].str.lower().str.contains(q)
            ]
        if pri_filter != "All":
            filtered_frs = filtered_frs[filtered_frs['priority'] == pri_filter]
        if status_filter != "All":
            filtered_frs = filtered_frs[filtered_frs['status'] == status_filter]

        # List view
        if filtered_frs.empty:
            st.info("No feature requests match your filter criteria.")
        else:
            st.markdown(f"<div style='color:#64748b; font-size:13px; margin-bottom:10px;'>Showing {len(filtered_frs)} records</div>", unsafe_allow_html=True)
            
            for index, row in filtered_frs.iterrows():
                fr_id = row['id']
                created_at = row['timestamp']
                
                expander_label = f"#{fr_id} — {row['title']} | Email: {row['email']}"
                
                with st.expander(expander_label):
                    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
                    
                    # Columns inside details
                    dcol1, dcol2 = st.columns([3, 1])
                    
                    with dcol1:
                        st.markdown(f"**💡 Idea Description:**")
                        st.write(row['description'])
                        
                        if row.get('use_case'):
                            st.markdown(f"**🎯 Intended Use Case:**")
                            st.write(row['use_case'])
                            
                        st.markdown(f"<div style='font-size:11px; color:#4b5563; margin-top:10px;'>Submitted on: {created_at}</div>", unsafe_allow_html=True)

                    with dcol2:
                        with st.container(border=True):
                            st.markdown(f"<div style='margin-bottom:8px;'>Priority: {priority_badge(row['priority'])}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div style='margin-bottom:12px;'>Current Status: {status_badge(row['status'])}</div>", unsafe_allow_html=True)
                            
                            # Interactive Status updates
                            status_options = ["Pending", "In Progress", "Resolved"]
                            current_status_idx = status_options.index(row['status']) if row['status'] in status_options else 0
                            new_status = st.selectbox("Update Status", status_options, index=current_status_idx, key=f"status_select_fr_{fr_id}")
                            
                            if new_status != row['status']:
                                update_feature_status(fr_id, new_status)
                                st.success(f"Status updated to {new_status}!")
                                st.rerun()

                            st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                            
                            # Delete action
                            if st.button("🗑️ Delete / Dismiss Request", key=f"del_fr_{fr_id}", use_container_width=True):
                                delete_feature_request(fr_id)
                                st.success("Feature request deleted successfully!")
                                st.rerun()

            # Export to CSV
            st.markdown("<hr>", unsafe_allow_html=True)
            csv = filtered_frs.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Filtered Feature Requests to CSV",
                data=csv,
                file_name=f"feature_requests_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
                use_container_width=True
            )


# ================================================================
# PAGE 4 — GLOBAL SCANS AUDIT LOG
# ================================================================
elif current_page == 'scans':
    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <h1 style="color:#ffffff; font-weight:800; font-size:1.8rem; margin:0;">
            📊 Global Scans Audit Log
        </h1>
        <p style="color:#4b5563; margin-top:4px; font-size:14px;">Audit global scans ran by all users, including average latencies, IP queries, and AI diagnostics</p>
    </div>
    """, unsafe_allow_html=True)

    if scans_df.empty:
        st.markdown("""
        <div style="background:#111827; border:1px solid #1f2d45; border-radius:16px;
                    padding:3rem; text-align:center; margin-top:2rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">📭</div>
            <div style="color:#4b5563; font-size:1rem;">
                No website scans audit log found. Once users run scans, logs will be arranged here.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # KPI calculations for scans
        avg_response = scans_df['avg_response'].mean() if 'avg_response' in scans_df.columns else 0
        dns_average = scans_df['dns_time'].mean() if 'dns_time' in scans_df.columns else 0
        success_scans = len(scans_df[scans_df['final_status'] == 'UP']) if 'final_status' in scans_df.columns else 0
        success_rate = (success_scans / total_scans) * 100 if total_scans > 0 else 0

        # Metrics display
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric("Total Scans Audited", total_scans)
        with sc2:
            st.metric("Success Rate (UP status)", f"{success_rate:.1f}%")
        with sc3:
            st.metric("Average Response Latency", f"{avg_response:.0f} ms")
        with sc4:
            st.metric("Average DNS Lookup Speed", f"{dns_average:.0f} ms")

        st.markdown("<hr style='margin:1.5rem 0;'>", unsafe_allow_html=True)

        # Filters for scans
        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            search_scan = st.text_input("🔍 Search scan domains or user emails", placeholder="Search domains (e.g. google.com) or user email logins...")
        with col_f2:
            alert_filter = st.selectbox("Alert Level Filter", ["All", "NORMAL", "ACCEPTABLE", "CRITICAL"])

        # Filter logic
        filtered_scans = scans_df.copy()
        if search_scan:
            qs = search_scan.lower()
            filtered_scans = filtered_scans[
                filtered_scans['website'].str.lower().str.contains(qs) |
                filtered_scans['email'].str.lower().str.contains(qs)
            ]
        if alert_filter != "All":
            filtered_scans = filtered_scans[filtered_scans['alert'] == alert_filter]

        if filtered_scans.empty:
            st.info("No scan logs match your search filters.")
        else:
            st.markdown(f"<div style='color:#64748b; font-size:13px; margin-bottom:10px;'>Showing {len(filtered_scans)} audit records</div>", unsafe_allow_html=True)
            
            # Interactive expandable table structure
            for idx, row in filtered_scans.iterrows():
                # Form label
                time_str = row.get('timestamp', '?')
                try:
                    time_formatted = datetime.fromisoformat(time_str).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    time_formatted = time_str
                    
                site_label = f"[{row.get('alert', '?')}] {row.get('website', '?')} — Ran by {row.get('email', '?')} ({time_formatted})"
                
                with st.expander(site_label):
                    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
                    
                    # Columns inside scan details
                    sc_col1, sc_col2 = st.columns([2, 1])
                    
                    with sc_col1:
                        st.markdown("**🧠 AI Diagnosis Log:**")
                        st.markdown(
                            f"<div style='background:#0d1321; border:1px solid #1f2d45; padding:15px; "
                            f"border-radius:10px; color:#94a3b8; font-size:13px; line-height:1.6;'>"
                            f"{row.get('diagnosis', 'No diagnosis available.')}</div>",
                            unsafe_allow_html=True
                        )

                    with sc_col2:
                        with st.container(border=True):
                            st.markdown(f"**🔍 Scan Metrics:**")
                            st.markdown(f"IP Query: `{row.get('ip_address', 'N/A')}`")
                            st.markdown(f"HTTP Status: `{row.get('http_status', 'N/A')} ({row.get('final_status', '?')})`")
                            st.markdown(f"Latency: `{row.get('avg_response', 0):.0f} ms`")
                            st.markdown(f"DNS Resolution: `{row.get('dns_time', 0):.0f} ms`")
                            st.markdown(f"SSL Days Left: `{row.get('ssl_days_left', 'N/A')}`")

            # Export scans
            st.markdown("<hr>", unsafe_allow_html=True)
            csv_scans = filtered_scans.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Filtered Audit Logs to CSV",
                data=csv_scans,
                file_name=f"webdoc_scans_audit_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
                use_container_width=True
            )
