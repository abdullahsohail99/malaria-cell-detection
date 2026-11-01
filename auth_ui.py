"""Sign in, sign up, user dashboard and the top bar."""
import pandas as pd
import streamlit as st

import db
import ui


# ------------------------------------------------------------- session
def current_user():
    u = st.session_state.get("user")
    if not u:
        return None
    fresh = db.get_user(u["id"])  # role/status hamesha DB se, session se nahi
    if not fresh or fresh["status"] != "active":
        st.session_state.pop("user", None)
        return None
    st.session_state["user"] = fresh
    return fresh


def _go(view, mode=None):
    st.session_state["view"] = view
    if mode:
        st.session_state["auth_mode"] = mode


def _logout():
    u = st.session_state.get("user")
    if u:
        db.audit(u["username"], "logout", "")
    st.session_state.pop("user", None)
    st.session_state["view"] = "home"


def _login(user):
    st.session_state["user"] = user
    st.session_state["view"] = "admin" if user["role"] == "admin" else "account"


def topbar(user, view):
    items = []  # (label, callback, args, type)
    if view != "home":
        items.append(("Home", _go, ("home",), "secondary"))
    if user:
        if view != "account":
            items.append(("Dashboard", _go, ("account",), "secondary"))
        if user["role"] == "admin" and view != "admin":
            items.append(("Admin", _go, ("admin",), "secondary"))
        items.append(("Sign out", _logout, (), "primary"))
    elif view != "auth":
        items.append(("Sign in", _go, ("auth", "Sign in"), "secondary"))
        items.append(("Sign up", _go, ("auth", "Create account"), "primary"))
    with st.container(key="topbar"):
        n = len(items)
        cols = st.columns([4 - n] + [1] * n) if n < 4 else st.columns(n)
        for col, (label, cb, args, kind) in zip(cols[-n:], items):
            col.button(label, key=f"tb_{label}", on_click=cb, args=args, type=kind)


# ------------------------------------------------------------- auth page
def auth_view():
    s = db.get_settings()
    ui.page_head("Account", "Welcome", "Sign in to save your prediction history, or create a free account. "
                 "The demo on the home page works without an account too.", centered=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.session_state.setdefault("auth_mode", "Sign in")
        mode = st.segmented_control("Mode", ["Sign in", "Create account"], key="auth_mode",
                                    label_visibility="collapsed") or "Sign in"
        if mode == "Sign in":
            with st.form("login_form"):
                ident = st.text_input("Username or email")
                pw = st.text_input("Password", type="password")
                go = st.form_submit_button("Sign in", type="primary")
            if go:
                if not ident or not pw:
                    st.error("Please enter your username/email and password.")
                else:
                    user, msg = db.authenticate(ident, pw)
                    if user:
                        _login(user)
                        st.rerun()
                    st.error(msg)
            st.caption("Forgot your password? Ask the administrator to reset it for you.")
        else:
            if s["signups_enabled"] != "1":
                st.warning("New sign-ups are currently turned off by the administrator.")
            else:
                with st.form("signup_form"):
                    name = st.text_input("Full name")
                    uname = st.text_input("Username", help="3-24 characters: letters, numbers, dot, underscore")
                    email = st.text_input("Email")
                    pw1 = st.text_input("Password", type="password", help="At least 8 characters, with letters and a number")
                    pw2 = st.text_input("Confirm password", type="password")
                    go = st.form_submit_button("Create account", type="primary")
                if go:
                    if pw1 != pw2:
                        st.error("The two passwords do not match.")
                    else:
                        ok, msg, uid = db.create_user(uname, email, pw1, name)
                        if ok:
                            _login(db.get_user(uid))
                            st.rerun()
                        st.error(msg)


# ------------------------------------------------------- user dashboard
def _local(df, col, tz):
    if df.empty:
        return df
    df = df.copy()
    df[col] = pd.to_datetime(df[col], utc=True).dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M")
    return df


def account_view(user):
    tz = db.get_setting("timezone")
    ui.page_head("Your dashboard", f"Hi, {user['full_name'] or user['username']}",
                 "Your predictions, profile and security settings.")
    preds = db.predictions_df(user["id"])
    tab_o, tab_h, tab_p, tab_s, tab_d = st.tabs(["Overview", "My history", "Profile", "Security", "Delete account"])

    with tab_o:
        n = len(preds)
        para = int((preds["label"] == "Parasitized").sum()) if n else 0
        c = st.columns(4)
        c[0].metric("Predictions", n)
        c[1].metric("Parasitized", para)
        c[2].metric("Uninfected", n - para)
        c[3].metric("Avg confidence", f"{preds['confidence'].mean() * 100:.1f}%" if n else "-")
        if n:
            p = preds.copy()
            p["day"] = pd.to_datetime(p["created_at"], utc=True).dt.tz_convert(tz).dt.tz_localize(None).dt.normalize()
            pv = p.pivot_table(index="day", columns="label", values="id", aggfunc="count", fill_value=0).sort_index()
            pv = pv.reindex(columns=["Parasitized", "Uninfected"], fill_value=0)
            st.markdown("##### Predictions per day")
            ui.bar_chart(pv, ["#eb6834", "#2a78d6"], 260)
        else:
            st.info("No predictions yet. Go to Home, run the demo, and your results will appear here.")
        st.caption(f"Member since {pd.to_datetime(user['created_at']).strftime('%d %b %Y')}. "
                   f"Signed in as @{user['username']}.")

    with tab_h:
        if preds.empty:
            st.info("Your history is empty.")
        else:
            lab = st.multiselect("Filter by result", ["Parasitized", "Uninfected"], default=["Parasitized", "Uninfected"])
            view = _local(preds[preds["label"].isin(lab)], "created_at", tz)
            view = view.assign(confidence=(view["confidence"] * 100).round(1)).rename(
                columns={"created_at": "time", "confidence": "confidence %"})
            st.dataframe(view[["time", "filename", "label", "confidence %", "source"]], hide_index=True)
            a, b = st.columns(2)
            a.download_button("Download CSV", view.to_csv(index=False).encode(), "my_predictions.csv", "text/csv")
            with b.popover("Clear my history"):
                st.write("This permanently deletes all your saved predictions.")
                if st.button("Yes, delete my history", key="clear_hist"):
                    db.delete_predictions(user_id=user["id"], actor=user["username"])
                    st.rerun()

    with tab_p:
        with st.form("profile_form"):
            name = st.text_input("Full name", value=user["full_name"] or "")
            email = st.text_input("Email", value=user["email"])
            st.text_input("Username", value=user["username"], disabled=True)
            go = st.form_submit_button("Save profile", type="primary")
        if go:
            ok, msg = db.update_profile(user["id"], name, email)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    with tab_s:
        with st.form("pw_form", clear_on_submit=True):
            old = st.text_input("Current password", type="password")
            new1 = st.text_input("New password", type="password")
            new2 = st.text_input("Confirm new password", type="password")
            go = st.form_submit_button("Change password", type="primary")
        if go:
            if new1 != new2:
                st.error("The new passwords do not match.")
            else:
                ok, msg = db.change_password(user["id"], old, new1)
                (st.success if ok else st.error)(msg)

    with tab_d:
        st.warning("Deleting your account removes your profile and all saved predictions. This cannot be undone.")
        with st.form("delete_form"):
            pw = st.text_input("Enter your password to confirm", type="password")
            sure = st.checkbox("I understand this is permanent")
            go = st.form_submit_button("Delete my account")
        if go:
            if not sure:
                st.error("Please tick the confirmation box.")
            else:
                ok, msg = db.delete_user(user["id"], user["username"], password=pw)
                if ok:
                    st.session_state.pop("user", None)
                    st.session_state["view"] = "home"
                    st.rerun()
                st.error(msg)
