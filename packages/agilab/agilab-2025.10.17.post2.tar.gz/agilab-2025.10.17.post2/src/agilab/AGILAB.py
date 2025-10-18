# BSD 3-Clause License
# Copyright (c) 2025, Jean-Pierre Morard, THALES SIX GTS France SAS
# All rights reserved.
# Co-author: Codex 0.42.0
"""Streamlit entry point for the AGILab interactive lab."""
import os
from pathlib import Path
from datetime import datetime

os.environ.setdefault("STREAMLIT_CONFIG_FILE", str(Path(__file__).resolve().parent / "resources" / "config.toml"))

import streamlit as st
import sys
import argparse

from agi_env.pagelib import inject_theme

# ----------------- Fast-Loading Banner UI -----------------
def quick_logo(resources_path: Path):
    """Render a lightweight banner with the AGILab logo."""
    try:
        from agi_env.pagelib import get_base64_of_image
        img_data = get_base64_of_image(resources_path / "agilab_logo.png")
        img_src = f"data:image/png;base64,{img_data}"
        st.markdown(
            f"""<div style="background-color: #333333; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 800px; margin: 20px auto;">
                    <div style="display: flex; align-items: center; justify-content: center;">
                        <h1 style="margin: 0; padding: 0 10px 0 0;">Welcome to</h1>
                        <img src="{img_src}" alt="AGI Logo" style="width:160px; margin-bottom: 20px;">
                    </div>
                    <div style="text-align: center;">
                        <strong style="color: black;">a step further toward AGI</strong>
                    </div>
                </div>""", unsafe_allow_html=True
        )
    except Exception as e:
        st.info(str(e))
        st.info("Welcome to AGILAB", icon="📦")


def display_landing_page(resources_path: Path):
    """Display the introductory copy describing AGILab's value proposition."""
    from agi_env.pagelib import get_base64_of_image
    # You can optionally show a small logo here if wanted.
    md_content = f"""
    <div class="uvp-highlight">
      <strong>Introduciton</strong>:
    <ul>
      AGILAB revolutionizing data Science experimentation with zero integration hassles. As a comprehensive framework built on pure Python and powered by Gen AI and ML, AGILAB scales effortlessly—from embedded systems to the cloud—empowering seamless collaboration on data insights and predictive modeling.
    </ul>
    </div>
    <div class="uvp-highlight">
      <strong>Founding Concept:</strong>
    <ul>
      AGILAB outlines a method for scaling into a project’s execution environment without the need for virtualization or containerization (such as Docker). The approach involves encapsulating an app's logic into two components: a worker (which is scalable and free from dependency constraints) and a manager (which is easily integrable due to minimal dependency requirements). This design enables seamless integration within a single app, contributing to the move toward Artificial General Intelligence (AGI).
      For infrastructure that required docker, there is an agilab docker script to generate a docker image in the docker directory under the project root.
    </ul>      
    </div>
      <strong>Key Features:</strong>
    <ul>
      <li><strong>Strong AI Enabler</strong>: Algos Integrations.</li>
      <li><strong>Engineering AI Enabler</strong>: Feature Engineering.</li>
      <li><strong>Availability</strong>: Works online and in standalone mode.</li>
      <li><strong>Enhanced Deployment Productivity</strong>: Automates virtual environment deployment.</li>
      <li><strong>Assisted by Generative AI</strong>: Seamless integration with OpenAI API (online), GPT-OSS (local), and Mistral-instruct (local).</li>
      <li><strong>Enhanced Scalability</strong>: Distributes both data and algorithms on a cluster.</li>
      <li><strong>User-Friendly Interface for Data Science</strong>: Integration of Jupyter-ai and ML Flow.</li>
      <li><strong>Advanced Execution Tools</strong>: Enables Map Reduce and Direct Acyclic Graph Orchestration.</li>
    </ul>
    <p>
      With AGILAB, there’s no need for additional integration—our all-in-one framework is ready to deploy, enabling you to focus on innovation rather than setup.
    </p>
    
    """
    st.markdown(md_content, unsafe_allow_html=True)


def show_banner_and_intro(resources_path: Path):
    """Render the branding banner followed by the descriptive landing copy."""
    quick_logo(resources_path)
    display_landing_page(resources_path)

def openai_status_banner(env):
    """Show a non-blocking banner if OpenAI features are unavailable."""
    import os
    key = os.environ.get("OPENAI_API_KEY") or getattr(env, "OPENAI_API_KEY", None)
    if not key:
        st.warning(
            "OpenAI features are disabled. Set OPENAI_API_KEY or launch with --openai-api-key to enable GPT tooling.",
            icon="⚠️",
        )


def page(env):
    """Render the main landing page controls and footer for the lab."""
    cols = st.columns(4)
    help_file = Path(env.help_path) / "index.html"
    from agi_env.pagelib import open_docs
    if cols[0].button("Read Documentation", use_container_width=True):
        open_docs(env, help_file, "project-editor")

    current_year = datetime.now().year
    st.markdown(
        f"""
    <div class='footer' style="display: flex; justify-content: flex-end;">
        <span>&copy; 2020-{current_year} Thales SIX GTS. Licensed under the BSD 3-Clause License.</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
    if "TABLE_MAX_ROWS" not in st.session_state:
        st.session_state["TABLE_MAX_ROWS"] = env.TABLE_MAX_ROWS
    if "GUI_SAMPLING" not in st.session_state:
        st.session_state["GUI_SAMPLING"] = env.GUI_SAMPLING


# ------------------------- Main Entrypoint -------------------------

def main():
    """Initialise the Streamlit app, bootstrap the environment and display the UI."""
    from agi_env.pagelib import get_about_content
    st.set_page_config(
        menu_items=get_about_content(),
        layout="wide",
    )
    resources_path = Path(__file__).resolve().parent / "resources"
    os.environ.setdefault("STREAMLIT_CONFIG_FILE", str(resources_path / "config.toml"))
    inject_theme(resources_path)
    st.session_state.setdefault("first_run", True)

    # Always set background style
    st.markdown(
        """<style>
        body { background: #f6f8fa !important; }
        </style>""",
        unsafe_allow_html=True
    )

    # ---- Initialize if needed (on cold start, or if 'env' key lost) ----
    if st.session_state.get("first_run", True) or "env" not in st.session_state:
        with st.spinner("Initializing environment..."):
            from agi_env.pagelib import activate_mlflow
            from agi_env import AgiEnv
            parser = argparse.ArgumentParser(description="Run the AGI Streamlit App with optional parameters.")
            parser.add_argument("--cluster-ssh-credentials", type=str, help="Cluster credentials (username:password)",
                                default=None)
            parser.add_argument("--openai-api-key", type=str, help="OpenAI API key (optional; can also use OPENAI_API_KEY)", default=None)
            parser.add_argument("--apps-dir", type=str, help="Where you store your apps (default is ./)",
                                default=None)

            args, _ = parser.parse_known_args()

            if args.apps_dir is None:
                with open(Path("~/").expanduser() / ".local/share/agilab/.agilab-path", "r") as f:
                    agilab_path = f.read()
                    before, sep, after = agilab_path.rpartition(".venv")
                    args.apps_dir = Path(before) / "apps"

            if args.apps_dir is None:
                st.error("Error: Missing mandatory parameter: --apps-dir")
                sys.exit(1)

            apps_dir = Path(args.apps_dir).expanduser() if args.apps_dir else None
            if apps_dir is None:
                st.error("Error: Missing mandatory parameter: --apps-dir")
                sys.exit(1)

            st.session_state["apps_dir"] = str(apps_dir)

            env = AgiEnv(apps_dir=apps_dir, verbose=1)
            env.init_done = True
            st.session_state['env'] = env
            st.session_state["IS_SOURCE_ENV"] = env.is_source_env
            st.session_state["IS_WORKER_ENV"] = env.is_worker_env

            if not st.session_state.get("server_started"):
                activate_mlflow(env)
                st.session_state["server_started"] = True

            openai_api_key = env.OPENAI_API_KEY if env.OPENAI_API_KEY else args.openai_api_key
            if not openai_api_key:
                st.warning("OPENAI_API_KEY not set. OpenAI-powered features will be disabled.")

            cluster_credentials = env.CLUSTER_CREDENTIALS if env.CLUSTER_CREDENTIALS else args.cluster_ssh_credentials or ""
            if openai_api_key:
                AgiEnv.set_env_var("OPENAI_API_KEY", openai_api_key)
            AgiEnv.set_env_var("CLUSTER_CREDENTIALS", cluster_credentials)
            AgiEnv.set_env_var("IS_SOURCE_ENV", str(int(bool(env.is_source_env))))
            AgiEnv.set_env_var("IS_WORKER_ENV", str(int(bool(env.is_worker_env))))
            AgiEnv.set_env_var("APPS_DIR", str(apps_dir))

            st.session_state["first_run"] = False
            st.rerun()
        return  # Don't continue

    # ---- After init, always show banner+intro and then main UI ----
    env = st.session_state['env']
    show_banner_and_intro(resources_path)
    openai_status_banner(env)
    page(env)


# ----------------- Run App -----------------
if __name__ == "__main__":
    main()
