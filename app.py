"""Malaria Cell Detection: entry point (page router).

Views: home (public one-page site + demo), auth (sign in / sign up), account (user dashboard), admin.
"""
import streamlit as st

st.set_page_config(page_title="Malaria Cell Detection", page_icon="🔬", layout="wide", initial_sidebar_state="collapsed")

import admin_ui  # noqa: E402
import auth_ui  # noqa: E402
import db  # noqa: E402
import home  # noqa: E402
import ui  # noqa: E402


def _secret(name):
    try:
        return st.secrets.get(name)
    except Exception:  # secrets file maujood nahi
        return None


@st.cache_resource
def _boot(admin_user, admin_pass):
    db.init_db(admin_user, admin_pass)
    return True


_boot(_secret("ADMIN_USERNAME"), _secret("ADMIN_PASSWORD"))
ui.inject_css()

view = st.session_state.setdefault("view", "home")
user = auth_ui.current_user()
if view == "account" and not user:
    view = "auth"
if view == "admin" and not (user and user["role"] == "admin"):
    view = "auth" if not user else "home"
if view == "auth" and user:
    view = "admin" if user["role"] == "admin" else "account"
st.session_state["view"] = view

ui.render_nav(show_links=(view == "home"))
auth_ui.topbar(user, view)

settings = db.get_settings()
if view == "home" and settings["announcement_on"] == "1" and settings["announcement"]:
    ui.banner(settings["announcement"], "info")

if view == "home":
    home.home_view()
elif view == "auth":
    auth_ui.auth_view()
elif view == "account":
    auth_ui.account_view(user)
elif view == "admin":
    admin_ui.admin_view(user)
