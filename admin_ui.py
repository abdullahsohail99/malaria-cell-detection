"""Admin dashboard: overview, users, predictions, model, settings, audit log, system."""
import os
import platform
import sys
import time
from importlib import metadata

import pandas as pd
import streamlit as st

import db
import ui

MODEL_PATH = "malaria_model.keras"
CLASSES_PATH = "class_names.json"
TZS = ["Asia/Karachi", "UTC", "Asia/Dubai", "Asia/Kolkata", "Asia/Singapore", "Europe/London", "America/New_York"]


def _local(df, col, tz, fmt="%Y-%m-%d %H:%M"):
    if df.empty or col not in df:
        return df
    df = df.copy()
    ts = pd.to_datetime(df[col], utc=True, errors="coerce")
    df[col] = ts.dt.tz_convert(tz).dt.strftime(fmt).fillna("")
    return df


def _ver(pkg):
    try:
        return metadata.version(pkg)
    except Exception:
        return "not installed"


def _days_frame(df, col, tz, days=14, by=None):
    """Count rows per local day for the last N days (empty days included)."""
    today = pd.Timestamp.now(tz=tz).normalize()
    idx = [today - pd.Timedelta(days=i) for i in range(days - 1, -1, -1)]
    labels = pd.DatetimeIndex([d.tz_localize(None) for d in idx])  # asli dates: chronological order
    cols = ["Parasitized", "Uninfected"] if by else ["Count"]
    out = pd.DataFrame(0, index=labels, columns=cols)
    if df.empty:
        return out
    ts = pd.to_datetime(df[col], utc=True).dt.tz_convert(tz).dt.normalize()
    for d, lab in zip(idx, labels):
        sub = df[ts == d]
        if by:
            for c in cols:
                out.loc[lab, c] = int((sub[by] == c).sum())
        else:
            out.loc[lab, "Count"] = len(sub)
    return out


# ------------------------------------------------------------- overview
def _overview(tz):
    users, preds = db.users_df(), db.predictions_df()
    s = db.get_settings()
    now = pd.Timestamp.now(tz="UTC")
    created = pd.to_datetime(users["created_at"], utc=True) if not users.empty else pd.Series(dtype="datetime64[ns, UTC]")
    new7 = int((created > now - pd.Timedelta(days=7)).sum())
    ptime = pd.to_datetime(preds["created_at"], utc=True) if not preds.empty else pd.Series(dtype="datetime64[ns, UTC]")
    last24 = int((ptime > now - pd.Timedelta(hours=24)).sum())
    n = len(preds)
    para = (preds["label"] == "Parasitized").mean() * 100 if n else 0
    avg = preds["confidence"].mean() * 100 if n else 0
    low = int((preds["confidence"] < float(s["conf_warn"])).sum()) if n else 0
    guests = int(preds["user_id"].isna().sum()) if n else 0

    a = st.columns(4)
    a[0].metric("Total users", len(users))
    a[1].metric("Active users", int((users["status"] == "active").sum()) if len(users) else 0)
    a[2].metric("New in 7 days", new7)
    a[3].metric("Admins", int((users["role"] == "admin").sum()) if len(users) else 0)
    b = st.columns(4)
    b[0].metric("Total predictions", n)
    b[1].metric("Last 24 hours", last24)
    b[2].metric("Parasitized share", f"{para:.1f}%")
    b[3].metric("Avg confidence", f"{avg:.1f}%")
    c = st.columns(2)
    c[0].metric("Low-confidence results", low, help=f"Below {float(s['conf_warn']) * 100:.0f}%")
    c[1].metric("Guest predictions", guests)

    l, r = st.columns(2)
    with l:
        st.markdown("##### Predictions per day (14 days)")
        ui.bar_chart(_days_frame(preds, "created_at", tz, by="label"), ["#eb6834", "#2a78d6"], 280)
    with r:
        st.markdown("##### New sign-ups per day (14 days)")
        ui.bar_chart(_days_frame(users, "created_at", tz), ["#2a78d6"], 280)
    st.markdown("##### Confidence distribution")
    if n:
        bins = pd.cut(preds["confidence"] * 100, [50, 60, 70, 80, 90, 100], include_lowest=True,
                      labels=["50-60", "60-70", "70-80", "80-90", "90-100"])
        ui.bar_chart(bins.value_counts().sort_index().rename("Predictions").to_frame(), ["#2a78d6"], 260)
    else:
        st.info("No predictions recorded yet.")
    st.markdown("##### Recent activity")
    st.dataframe(_local(db.audit_df(8), "ts", tz), hide_index=True)


# ---------------------------------------------------------------- users
def _users(me, tz):
    df = db.users_df()
    c1, c2, c3 = st.columns([3, 1, 1])
    q = c1.text_input("Search", placeholder="Search username, email or name", label_visibility="collapsed")
    status = c2.selectbox("Status", ["All statuses", "active", "suspended"], label_visibility="collapsed")
    role = c3.selectbox("Role", ["All roles", "user", "admin"], label_visibility="collapsed")
    view = df
    if q:
        m = view[["username", "email", "full_name"]].fillna("").apply(lambda col: col.str.contains(q, case=False, regex=False)).any(axis=1)
        view = view[m]
    if status != "All statuses":
        view = view[view["status"] == status]
    if role != "All roles":
        view = view[view["role"] == role]
    shown = _local(_local(view, "created_at", tz), "last_login", tz)
    st.dataframe(shown, hide_index=True)
    st.download_button("Download users CSV", shown.to_csv(index=False).encode(), "users.csv", "text/csv")

    st.markdown("##### Manage a user")
    if df.empty:
        return
    sel = st.selectbox("Select user", df["username"].tolist())
    u = db.get_user_by_name(sel)
    if not u:
        return
    is_me = u["id"] == me["id"]
    if is_me:
        st.caption("This is your own account: role and status changes are disabled here.")
    a, b, c = st.columns([1, 1, 1])
    role_new = a.selectbox("Role", ["user", "admin"], index=["user", "admin"].index(u["role"]), disabled=is_me)
    status_new = b.selectbox("Status", ["active", "suspended"], index=["active", "suspended"].index(u["status"]), disabled=is_me)
    if c.button("Save changes", type="primary", disabled=is_me):
        msgs = []
        if role_new != u["role"]:
            msgs.append(db.set_role(u["id"], role_new, me["username"]))
        if status_new != u["status"]:
            msgs.append(db.set_status(u["id"], status_new, me["username"]))
        if not msgs:
            st.info("Nothing to change.")
        for ok, msg in msgs:
            (st.success if ok else st.error)(msg)
        if any(ok for ok, _ in msgs):
            st.rerun()
    with st.expander("Reset password"):
        with st.form(f"reset_{u['id']}", clear_on_submit=True):
            npw = st.text_input("New password", type="password", help="Tell the user this password; they can change it after signing in.")
            go = st.form_submit_button("Set new password")
        if go:
            ok, msg = db.reset_password(u["id"], npw, me["username"])
            (st.success if ok else st.error)(msg)
    with st.expander("Delete user", expanded=False):
        st.warning(f"Deletes @{u['username']} and all of their saved predictions.")
        sure = st.checkbox("I understand", key=f"del_ok_{u['id']}")
        if st.button("Delete this user", disabled=is_me or not sure, key=f"del_{u['id']}"):
            ok, msg = db.delete_user(u["id"], me["username"])
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()


# ---------------------------------------------------------- predictions
def _predictions(me, tz):
    df = db.predictions_df()
    if df.empty:
        st.info("No predictions recorded yet. They appear here as soon as someone uses the demo.")
        return
    c = st.columns(3)
    lab = c[0].multiselect("Result", ["Parasitized", "Uninfected"], default=["Parasitized", "Uninfected"])
    who = c[1].selectbox("Who", ["Everyone", "Guests only", "Signed-in users only"])
    low = c[2].toggle("Low confidence only")
    view = df[df["label"].isin(lab)]
    if who == "Guests only":
        view = view[view["user_id"].isna()]
    elif who == "Signed-in users only":
        view = view[view["user_id"].notna()]
    if low:
        view = view[view["confidence"] < float(db.get_setting("conf_warn"))]
    view = _local(view, "created_at", tz)
    view = view.assign(confidence=(view["confidence"] * 100).round(1)).rename(columns={"confidence": "confidence %", "created_at": "time"})
    st.caption(f"{len(view)} of {len(df)} predictions")
    st.dataframe(view[["id", "time", "username", "filename", "label", "confidence %", "source"]], hide_index=True)
    st.download_button("Download CSV", view.to_csv(index=False).encode(), "predictions.csv", "text/csv")
    with st.expander("Clean up old predictions"):
        days = st.number_input("Delete predictions older than (days)", 1, 3650, 90)
        sure = st.checkbox("I understand this is permanent", key="pred_clean_ok")
        if st.button("Delete old predictions", disabled=not sure):
            n = db.delete_predictions(older_than_days=days, actor=me["username"])
            st.success(f"Deleted {n} predictions.")


# ---------------------------------------------------------------- model
def _model(tz):
    exists = os.path.exists(MODEL_PATH)
    c = st.columns(4)
    c[0].metric("Weights file", "Found" if exists else "Missing")
    c[1].metric("File size", f"{os.path.getsize(MODEL_PATH) / 1e6:.1f} MB" if exists else "-")
    c[2].metric("Validation accuracy", "92.85%")
    c[3].metric("Input size", "128 x 128")
    l, r = st.columns(2)
    with l:
        st.markdown("##### Architecture and training")
        st.table(pd.DataFrame({"Setting": ["Base network", "Head", "Loss / Optimizer", "Epochs / Batch", "Classes (index 0, 1)", "Weights file"],
                               "Value": ["MobileNetV2 (frozen, ImageNet)", "GlobalAvgPool, Dropout 0.3, Dense(1, sigmoid)",
                                         "Binary cross-entropy / Adam", "5 / 64", "Parasitized, Uninfected", MODEL_PATH]}).set_index("Setting"))
    with r:
        st.markdown("##### Training log")
        st.table(pd.DataFrame({"Epoch": [1, 2, 3, 4, 5],
                               "Train acc": ["85.32%", "90.38%", "91.22%", "91.41%", "91.63%"],
                               "Val acc": ["91.36%", "92.38%", "92.51%", "92.78%", "92.85%"],
                               "Val loss": [0.2241, 0.2008, 0.1937, 0.1886, 0.1877]}).set_index("Epoch"))
    st.markdown("##### Health check")
    st.caption("Loads the model and runs one prediction on a blank image to confirm everything works.")
    if st.button("Run health check", disabled=not exists):
        try:
            import numpy as np
            from home import load_model
            t0 = time.time()
            model = load_model()
            t1 = time.time()
            p = float(model.predict(np.zeros((1, 128, 128, 3), dtype="float32"), verbose=0)[0][0])
            st.success(f"Model OK. Load {t1 - t0:.1f}s, prediction {time.time() - t1:.2f}s, output {p:.4f}.")
        except Exception as e:
            st.error(f"Health check failed: {e}")
    if not exists:
        st.error(f"{MODEL_PATH} was not found next to app.py. Upload it to the GitHub repository.")


# ------------------------------------------------------------- settings
def _settings(me):
    s = db.get_settings()
    with st.form("settings_form"):
        st.markdown("##### Access")
        signups = st.toggle("Allow new sign-ups", value=s["signups_enabled"] == "1")
        maint = st.toggle("Maintenance mode (turns the demo off for visitors, admins can still use it)", value=s["maintenance"] == "1")
        st.markdown("##### Announcement banner")
        ann_on = st.toggle("Show a banner on the home page", value=s["announcement_on"] == "1")
        ann = st.text_input("Banner text", value=s["announcement"], max_chars=200)
        st.markdown("##### Prediction behaviour")
        conf = st.slider("Warn when confidence is below", 0.50, 0.99, float(s["conf_warn"]), 0.01)
        log_guest = st.toggle("Save anonymous guest predictions (no images are stored, only result and confidence)", value=s["log_guest"] == "1")
        st.markdown("##### Display")
        tz = st.selectbox("Timezone for dates", TZS, index=TZS.index(s["timezone"]) if s["timezone"] in TZS else 0)
        go = st.form_submit_button("Save settings", type="primary")
    if go:
        new = {"signups_enabled": "1" if signups else "0", "maintenance": "1" if maint else "0",
               "announcement_on": "1" if ann_on else "0", "announcement": ann.strip(),
               "conf_warn": f"{conf:.2f}", "log_guest": "1" if log_guest else "0", "timezone": tz}
        changed = [k for k, v in new.items() if s.get(k) != v]
        for k, v in new.items():
            db.set_setting(k, v)
        if changed:
            db.audit(me["username"], "settings_changed", ", ".join(changed))
        st.success("Settings saved." if changed else "No changes.")
        st.rerun()
    st.info("Tip: leave Maintenance mode OFF while the instructor's automated evaluation runs, otherwise it cannot test the demo.")


# ---------------------------------------------------------------- audit
def _audit(tz):
    df = db.audit_df()
    if df.empty:
        st.info("The audit log is empty.")
        return
    acts = st.multiselect("Filter by action", sorted(df["action"].unique()))
    view = df[df["action"].isin(acts)] if acts else df
    view = _local(view, "ts", tz)
    st.dataframe(view, hide_index=True)
    st.download_button("Download audit CSV", view.to_csv(index=False).encode(), "audit_log.csv", "text/csv")


# --------------------------------------------------------------- system
def _system(me):
    counts = db.table_counts()
    c = st.columns(4)
    c[0].metric("Database size", f"{db.db_size() / 1024:.0f} KB")
    c[1].metric("Users", counts["users"])
    c[2].metric("Predictions", counts["predictions"])
    c[3].metric("Audit entries", counts["audit"])

    st.markdown("##### Security checklist")
    default_pw = db.default_admin_in_use()
    try:
        has_secret = bool(st.secrets.get("ADMIN_PASSWORD"))
    except Exception:
        has_secret = False
    rows = [("Admin password is not the built-in default", not default_pw),
            ("Admin credentials come from Streamlit secrets", has_secret),
            ("Passwords are hashed (PBKDF2-SHA256, per-user salt)", True),
            ("Login lockout after 5 failed attempts (5 minutes)", True)]
    for text, ok in rows:
        st.markdown(f'<span class="{"ok" if ok else "no"}">{"✔" if ok else "✖"}</span>&nbsp; {text}', unsafe_allow_html=True)
    if not has_secret:
        st.caption("Set ADMIN_USERNAME and ADMIN_PASSWORD in Streamlit Cloud: Manage app, Settings, Secrets.")

    st.markdown("##### Environment")
    st.table(pd.DataFrame({"Component": ["Python", "Streamlit", "TensorFlow", "Pandas", "OS"],
                           "Version": [sys.version.split()[0], _ver("streamlit"),
                                       _ver("tensorflow-cpu") if _ver("tensorflow-cpu") != "not installed" else _ver("tensorflow"),
                                       _ver("pandas"), platform.platform()]}).set_index("Component"))

    st.markdown("##### Backup and restore")
    st.caption("Streamlit Cloud can wipe local files when the app restarts. Download a backup regularly.")
    st.download_button("Download database backup", db.backup_bytes(), f"malaria_app_backup_{time.strftime('%Y%m%d_%H%M')}.db",
                       "application/octet-stream")
    up = st.file_uploader("Restore from a backup file", type=["db", "sqlite"], key="restore_up")
    if up is not None:
        sure = st.checkbox("Replace ALL current data with this backup", key="restore_ok")
        if st.button("Restore backup", disabled=not sure):
            ok, msg = db.restore(up.getvalue(), me["username"])
            (st.success if ok else st.error)(msg)
            if ok:
                st.session_state.pop("user", None)
                st.session_state["view"] = "auth"
                st.rerun()

    with st.expander("Danger zone"):
        sure = st.checkbox("I understand these actions are permanent", key="danger_ok")
        a, b = st.columns(2)
        if a.button("Delete ALL predictions", disabled=not sure):
            st.success(f"Deleted {db.delete_predictions(actor=me['username'])} predictions.")
        if b.button("Clear audit log", disabled=not sure):
            st.success(f"Cleared {db.clear_audit(me['username'])} entries.")


# ----------------------------------------------------------------- page
def admin_view(me):
    if me["role"] != "admin":  # extra guard, role db se aaya hai
        st.error("Admins only.")
        return
    tz = db.get_setting("timezone")
    ui.page_head("Administration", "Admin dashboard", "Monitor usage, manage users and control how the site behaves.")
    if db.default_admin_in_use():
        ui.banner("The built-in default admin password is still in use. Anyone who reads the public repository can sign in as admin. "
                  "Add ADMIN_USERNAME and ADMIN_PASSWORD to Streamlit secrets (see System tab), or change the password from Dashboard, Security.", "bad")
    st.markdown(f'<span class="who">Signed in as <b>@{me["username"]}</b> (admin)</span>', unsafe_allow_html=True)
    tabs = st.tabs(["Overview", "Users", "Predictions", "Model", "Settings", "Audit log", "System"])
    with tabs[0]:
        _overview(tz)
    with tabs[1]:
        _users(me, tz)
    with tabs[2]:
        _predictions(me, tz)
    with tabs[3]:
        _model(tz)
    with tabs[4]:
        _settings(me)
    with tabs[5]:
        _audit(tz)
    with tabs[6]:
        _system(me)
