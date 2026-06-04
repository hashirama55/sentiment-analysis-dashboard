import streamlit as st
import math
from src.logic.feedback_handler import save_feedback

def render_explorer_tab(fdf):
    # Setup session state for pagination sync
    if 'page_size' not in st.session_state:
        st.session_state.page_size = 50
    if 'page_num' not in st.session_state:
        st.session_state.page_num = 1

    def sync_top():
        st.session_state.page_num = st.session_state.pn_top
        st.session_state.page_size = st.session_state.ps_top

    def sync_bottom():
        st.session_state.page_num = st.session_state.pn_bottom
        st.session_state.page_size = st.session_state.ps_bottom

    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        sort_opts = {"Most Recent":("Date",False),"Most Liked":("Likes",False),
                     "Most Positive":("compound",False),"Most Negative":("compound",True)}
        sort_choice = st.selectbox("Sort by", list(sort_opts.keys()))
    with ec2:
        intent_filter_ex = st.multiselect("Filter intent", ["complaint","praise","inquiry","spam"],
                                           default=["complaint","praise","inquiry","spam"],
                                           key="ex_intent")
    with ec3:
        topic_filter_ex = st.multiselect("Filter topic", ["network","billing","roaming","support","general"],
                                          default=["network","billing","roaming","support","general"],
                                          key="ex_topic")

    sort_col, sort_asc = sort_opts[sort_choice]
    ex_df_full = fdf[fdf["intent"].isin(intent_filter_ex) & fdf["topic"].isin(topic_filter_ex)]
    ex_df_full = ex_df_full.sort_values(sort_col, ascending=sort_asc)

    total_results = len(ex_df_full)
    
    # --- Top Pagination Controls ---
    st.divider()
    t1, t2, t3 = st.columns([1, 1, 2])
    
    with t1:
        page_size_opts = [20, 50, 100, 200]
        st.selectbox("Items per page", page_size_opts, 
                     index=page_size_opts.index(st.session_state.page_size) if st.session_state.page_size in page_size_opts else 1,
                     key="ps_top", on_change=sync_top)
    
    total_pages = math.ceil(total_results / st.session_state.page_size) if total_results > 0 else 1
    
    # Bound check for page_num
    if st.session_state.page_num > total_pages:
        st.session_state.page_num = total_pages
    if st.session_state.page_num < 1:
        st.session_state.page_num = 1

    with t2:
        st.number_input("Page", min_value=1, max_value=total_pages, 
                        value=st.session_state.page_num, step=1, 
                        key="pn_top", on_change=sync_top)
    
    start_idx = (st.session_state.page_num - 1) * st.session_state.page_size
    end_idx = start_idx + st.session_state.page_size
    ex_df = ex_df_full.iloc[start_idx:end_idx]
    
    with t3:
        st.markdown(f"<br><div style='text-align:right;color:#8892b0;font-size:0.9rem;'>Showing {start_idx+1:,} to {min(end_idx, total_results):,} of {total_results:,} results</div>", unsafe_allow_html=True)
    # ---------------------------

    badge_sent = {
        "positive":'<span class="badge badge-positive">😊 Positive</span>',
        "negative":'<span class="badge badge-negative">😞 Negative</span>',
        "neutral": '<span class="badge badge-neutral">😐 Neutral</span>',
    }
    badge_intent = {
        "complaint":'<span class="badge badge-complaint">🚨 Complaint</span>',
        "praise":   '<span class="badge badge-praise">🌟 Praise</span>',
        "inquiry":  '<span class="badge badge-inquiry">❓ Inquiry</span>',
        "spam":     '<span class="badge badge-spam">🤖 Spam</span>',
    }
    badge_topic = {
        "network": '<span class="badge badge-network">📡 Network</span>',
        "billing": '<span class="badge badge-billing">💰 Billing</span>',
        "roaming": '<span class="badge badge-roaming">✈️ Roaming</span>',
        "support": '<span class="badge badge-support">🎧 Support</span>',
        "general": '<span class="badge badge-general">📋 General</span>',
    }

    for idx, row in ex_df.iterrows():
        bs = badge_sent.get(row["sentiment"],"")
        bi = badge_intent.get(row["intent"],"")
        bt = badge_topic.get(row["topic"],"")
        
        with st.container():
            st.markdown(f"""<div style="background:#1e2130;border:1px solid #3a3f5c;
                            border-radius:10px;padding:12px 16px;margin-bottom:8px;">
                <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-bottom:6px;">
                    {bs}{bi}{bt}
                    <span style="color:#8892b0;font-size:0.78rem;margin-left:8px;">
                        📌 <b style="color:#ccd6f6">{str(row['Post Title'])[:50]}</b> &nbsp;·&nbsp;
                        {str(row['Date'])[:16]} &nbsp;·&nbsp; 👍 {int(row['Likes'])} &nbsp;·&nbsp;
                        🌐 {row['language']} &nbsp;·&nbsp;
                        score: <b style="color:#ccd6f6">{row['compound']:+.3f}</b>
                    </span>
                </div>
                <div style="color:#e6e6e6;font-size:0.9rem;">{str(row['Comment'])[:400]}</div>
            </div>""", unsafe_allow_html=True)
            
            # --- Feedback UI (Active Learning) ---
            with st.expander("🔧 Correct labels"):
                f1, f2, f3 = st.columns(3)
                with f1:
                    new_sent = st.selectbox("Sentiment", ["positive", "neutral", "negative"], 
                                             index=["positive", "neutral", "negative"].index(row["sentiment"]),
                                             key=f"sent_{idx}")
                    if new_sent != row["sentiment"]:
                        if st.button("Fix Sentiment", key=f"btn_sent_{idx}"):
                            save_feedback(row["Comment"], row["sentiment"], new_sent, "sentiment")
                            st.toast(f"Saved sentiment correction!")
                
                with f2:
                    new_intent = st.selectbox("Intent", ["complaint", "praise", "inquiry", "spam"],
                                               index=["complaint", "praise", "inquiry", "spam"].index(row["intent"]),
                                               key=f"intent_{idx}")
                    if new_intent != row["intent"]:
                        if st.button("Fix Intent", key=f"btn_intent_{idx}"):
                            save_feedback(row["Comment"], row["intent"], new_intent, "intent")
                            st.toast(f"Saved intent correction!")
                
                with f3:
                    new_topic = st.selectbox("Topic", ["network", "billing", "roaming", "support", "general"],
                                              index=["network", "billing", "roaming", "support", "general"].index(row["topic"]),
                                              key=f"topic_{idx}")
                    if new_topic != row["topic"]:
                        if st.button("Fix Topic", key=f"btn_topic_{idx}"):
                            save_feedback(row["Comment"], row["topic"], new_topic, "topic")
                            st.toast(f"Saved topic correction!")

    # --- Bottom Pagination Controls ---
    st.divider()
    b1, b2, b3 = st.columns([1, 1, 2])
    
    with b1:
        st.selectbox("Items per page", page_size_opts, 
                     index=page_size_opts.index(st.session_state.page_size) if st.session_state.page_size in page_size_opts else 1,
                     key="ps_bottom", on_change=sync_bottom)
    
    with b2:
        st.number_input("Page", min_value=1, max_value=total_pages, 
                        value=st.session_state.page_num, step=1, 
                        key="pn_bottom", on_change=sync_bottom)
    
    with b3:
        st.markdown(f"<br><div style='text-align:right;color:#8892b0;font-size:0.9rem;'>Page {st.session_state.page_num} of {total_pages}</div>", unsafe_allow_html=True)
    # ---------------------------
