import streamlit as st
from core.execute import main



if __name__ == "__main__":
    if "current_page" not in st.session_state:
        st.session_state.current_page = "paid_record"
    main()
