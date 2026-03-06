import streamlit as st
from config.settings import SETTINGS

st.set_page_config(page_title=SETTINGS.app_name, layout="wide")
st.title(SETTINGS.app_name)
st.caption("sports intelligence + content engine")
st.markdown("""
## localized modes

### live mode
- dashboard
- one-glance game card
- postgame packet

### red sox history intelligence
- history home
- season explorer
- process vs result
- era board
- history post generator
- franchise timeline
- core + pipeline explorer
""")
st.info("open pages from the left sidebar.")
