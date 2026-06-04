# ═══════════════════════════════════════════════════════════════════════════════
# CSS STYLES
# ═══════════════════════════════════════════════════════════════════════════════
CSS_STYLE = """
<style>
    .main { background-color: #0f1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252840);
        border: 1px solid #3a3f5c; border-radius: 12px;
        padding: 18px; text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; }
    .metric-label { font-size: 0.8rem; color: #8892b0; margin-top: 4px; }
    .positive  { color: #00d4aa; }
    .negative  { color: #ff6b6b; }
    .neutral   { color: #ffd166; }
    .section-header {
        font-size: 1.05rem; font-weight: 600; color: #ccd6f6;
        border-bottom: 2px solid #3a3f5c; padding-bottom: 5px; margin-bottom: 12px;
    }
    .badge {
        display:inline-block; border-radius:6px;
        padding:2px 9px; font-size:0.72rem; font-weight:600; margin:2px;
    }
    .badge-positive  { background:#00d4aa22; color:#00d4aa; border:1px solid #00d4aa55; }
    .badge-negative  { background:#ff6b6b22; color:#ff6b6b; border:1px solid #ff6b6b55; }
    .badge-neutral   { background:#ffd16622; color:#ffd166; border:1px solid #ffd16655; }
    .badge-complaint { background:#ff6b6b22; color:#ff6b6b; border:1px solid #ff6b6b55; }
    .badge-praise    { background:#00d4aa22; color:#00d4aa; border:1px solid #00d4aa55; }
    .badge-inquiry   { background:#74b9ff22; color:#74b9ff; border:1px solid #74b9ff55; }
    .badge-spam      { background:#a29bfe22; color:#a29bfe; border:1px solid #a29bfe55; }
    .badge-network   { background:#fd79a822; color:#fd79a8; border:1px solid #fd79a855; }
    .badge-billing   { background:#ffeaa722; color:#ffeaa7; border:1px solid #ffeaa755; }
    .badge-roaming   { background:#55efc422; color:#55efc4; border:1px solid #55efc455; }
    .badge-support   { background:#74b9ff22; color:#74b9ff; border:1px solid #74b9ff55; }
    .badge-general   { background:#2d3561;   color:#8892b0; border:1px solid #3a3f5c; }
    .spike-card {
        background:#ff6b6b18; border:1px solid #ff6b6b44;
        border-radius:10px; padding:12px 16px; margin-bottom:8px;
    }
    .spike-date { color:#ff6b6b; font-weight:700; font-size:0.95rem; }
    .spike-desc { color:#ccd6f6; font-size:0.85rem; margin-top:4px; }
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# LEXICONS & PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════
SHONA_POS = {
    "bho":2,"zvakanaka":3,"makorokoto":4,"ndinotenda":3,"zvaibva":2,
    "zvinoita":2,"ndinoda":2,"pakanaka":3,"thank":2,"thanks":2,
    "🙏":2,"❤️":2,"😊":2,"👍":1,"great":3,"good":2,"excellent":3,
    "love":3,"best":3,"perfect":3,"amazing":3,"awesome":3,"helpful":2,
    "affordable":2,"cheap":1,"huchi":3,"haaa":2,"💥":2,
}
SHONA_NEG = {
    "woye":-2,"haishande":-3,"haabatike":-3,"hazvibatike":-3,"tired":-2,
    "zvakaoma":-2,"hapana":-2,"haana":-2,"hazvina":-2,"zvakashata":-3,
    "kushata":-3,"problem":-2,"issue":-2,"fail":-3,"failed":-3,"failing":-3,
    "can't":-2,"cannot":-2,"error":-3,"scam":-4,"scammer":-4,"thief":-4,
    "steal":-4,"expensive":-3,"slow":-2,"mukubata":-2,"tsotsi":-4,
    "kachitsotsi":-4,"😡":-3,"😤":-2,"😭":-3,"🤔":-1,"smh":-2,"😢":-2,
    "worst":-4,"terrible":-4,"horrible":-4,"useless":-3,"disappointed":-3,
    "frustrate":-3,"frustrating":-3,"bad":-2,"poor":-2,"delay":-2,"delayed":-2,
    "ndevekufenda":-4,"kufenda":-4,"fenda":-3,"marara":-3,"mbavha":-4,
}
SHONA_WORDS = {
    "saka","zvino","ko","mune","woye","mukuti","zvakanaka","totenga","zig",
    "haishande","hapana","haana","zvakaoma","zviri","ndinoda","ndinotenda",
    "makorokoto","apa","zvayo","rakabva","kuuya","kufanira","nekuda",
    "mukubata","zvakashata","kushata","kachitsotsi","tsotsi","kubvunza",
    "tipindureiwo","hazvibatike","haabatike","hazvina","ndevekufenda",
    "kufenda","fenda","marara","mbavha","huchi",
}

# ── Complaint Detection keywords ──────────────────────────────────────────────
COMPLAINT_KW = [
    r"\bnot work\b",r"\bdon'?t work\b",r"\bhaishande\b",r"\bhaabatike\b",
    r"\bfail(ed|ing)?\b",r"\bno (network|signal|data|service)\b",
    r"\bnetwork (down|issues?|problem)\b",r"\bscam\b",r"\bsteal\b",r"\bthief\b",
    r"\btsotsi\b",r"\buseless\b",r"\bterrible\b",r"\bworst\b",r"\bdisappoint\b",
    r"\bfrustrat\b",r"\bcan'?t (connect|access|activate|use)\b",
    r"\bnot (receiving|getting|working)\b",r"\bnever (works?|received)\b",
    r"\bwoye\b",r"\bstill (waiting|no|not)\b",r"\bunresolved\b",
    r"\bwhen (will|are)\b",r"\bfix (this|your|it)\b",r"\bpoor service\b",
    r"\bkeep (failing|dropping|disconnecting)\b",r"\bcharged (wrongly|twice|incorrectly)\b",
    r"\bovercharged\b",r"\bstolen\b",r"\bno response\b",r"\bignor(ed|ing)\b",
]
PRAISE_KW = [
    r"\bthank(s| you)\b",r"\bndinotenda\b",r"\bmakorokoto\b",r"\bexcellent\b",
    r"\bamazing\b",r"\bawesome\b",r"\bperfect\b",r"\bbest\b",r"\blove\b",
    r"\bgreat (service|work|job|network)\b",r"\bwell done\b",r"\bkeep it up\b",
    r"\bimpressed\b",r"\bhappy (with|about)\b",r"\bsatisfied\b",r"\bappreciat\b",
    r"\bgood (work|job|service|network)\b",r"\bfast (network|service|response)\b",
    r"\baffordable\b",r"\bvalue (for money)\b",r"\bzvakanaka\b",r"\bbho\b",
]
INQUIRY_KW = [
    r"\bhow (do|can|much|long|to)\b",r"\bwhat (is|are|does|happened|time)\b",
    r"\bwhere (can|do|is)\b",r"\bwhen (will|is|can|does)\b",r"\bwhy (is|are|can't|won't)\b",
    r"\bcan (you|i|we|someone)\b",r"\bcould (you|someone)\b",r"\bplease (help|assist|advise)\b",
    r"\bkubvunza\b",r"\bhow much\b",r"\bany (one|body) (know|help)\b",
    r"\bwould like to\b",r"\bI need (to know|help|info)\b",r"\bis (it|there|this) possible\b",
    r"\bactivat(e|ing)\b.*\?",r"\btariff\b",r"\bpackage\b.*\?",r"\bprice\b.*\?",
    r"\bcontact\b.*\?",r"\bnumber\b.*\?",
]
SPAM_KW = [
    r"\b(click|tap) (here|this link)\b",r"\bearn \$\d+",r"\bmake money\b",
    r"\bfollow (me|us|back)\b",r"\bcheck (my|our) (profile|page|bio)\b",
    r"\bjoin (my|our|this) (group|channel|whatsapp)\b",r"\bhttps?://\S+\.(ru|xyz|tk|ml)\b",
    r"\b(free|win|winner|prize|won)\b.*\b(iphone|cash|phone|data)\b",
    r"\bbet(ting)?\b",r"\bpromotion\b.*\blink\b",r"\bwhatsapp\b.*\bjoin\b",
    r"\bshare this\b",r"\bviola\b",r"\bforward this\b",
]

# ── Topic Detection keywords ───────────────────────────────────────────────────
TOPIC_PATTERNS = {
    "network": [
        r"\bnetwork\b",r"\bsignal\b",r"\bno (data|internet|connection)\b",
        r"\b(data|internet) (not working|down|slow|issues?)\b",r"\bdropping\b",
        r"\bdisconnect\b",r"\bLTE\b",r"\b4G\b",r"\b3G\b",r"\boutage\b",
        r"\bhaabatike\b",r"\bhazvibatike\b",r"\bhaishande\b",
        r"\b(slow|fast) (internet|data|network)\b",r"\bspeed\b",r"\bping\b",
        r"\bcoverage\b",r"\btower\b",r"\bsim (not working|issue|card)\b",
    ],
    "billing": [
        r"\bbilling\b",r"\bcharg(e|ed|ing)\b",r"\bdeduct(ed|ion|ing)\b",
        r"\bbalance\b",r"\bairtime\b",r"\bmoney (stolen|missing|gone)\b",
        r"\b(lost|missing) (money|airtime|data|balance)\b",r"\brefund\b",
        r"\bovercharg(e|ed)\b",r"\bwrong(ly)? charg\b",r"\bbill\b",
        r"\bpayment\b",r"\btransaction\b",r"\bEcocash\b",r"\bUSSD\b",
        r"\b\*135\*\b",r"\brecharge\b",r"\btop.?up\b",r"\bvoucher\b",
    ],
    "roaming": [
        r"\broaming\b",r"\binternational\b",r"\babroad\b",r"\bSouth Africa\b",
        r"\bUK\b",r"\bUS(A)?\b",r"\bBotswana\b",r"\bZambia\b",r"\bMozambique\b",
        r"\btravel\b.*\bnetone\b",r"\bnetone\b.*\btravel\b",
        r"\bactivat(e|ing) (roaming|international)\b",r"\bsim swap\b",
        r"\bforeign\b",r"\boverses\b",r"\bdiaspora\b",
    ],
    "support": [
        r"\bcustomer (care|service|support)\b",r"\bhelp(desk)?\b",
        r"\bcontact (us|netone|support)\b",r"\bcall (center|centre)\b",
        r"\b0867\b",r"\b\*111\*\b",r"\bwhere (can|do) I\b",r"\bno response\b",
        r"\bignor(ed|ing)\b",r"\bnot respond\b",r"\bwaiting (for|hours|days)\b",
        r"\bsupport (team|staff|line)\b",r"\boperator\b",r"\bagent\b",
        r"\bcomplaint\b",r"\bescalat\b",r"\bresolved\b",r"\bunresolved\b",
    ],
}

DEFAULT_CHUNK_SIZE = 400

STOP_WORDS = {
    "the","and","to","a","of","is","in","i","my","it","this","that","for","are",
    "have","be","was","on","we","your","you","with","not","can","view","comment",
    "nan","","-","at","or","an","as","by","has","but","so","if","no","do","me",
    "up","its","our","am","will","would","from","please","hi","hey","good","morning",
    "netone","net","one","just","get","got","still","how","what","when","where","why",
}
