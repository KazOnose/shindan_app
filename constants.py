"""
このファイルは、固定の文字列や数値などのデータを変数として一括管理するファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader


############################################################
# 共通変数の定義
############################################################

# ==========================================
# 画面表示系
# ==========================================
APP_NAME = "中小企業向け AI活用診断"
APP_CAPTION = "御社にすでにある資料から、AIで何ができるかを診断します。"
ANSWER_MODE_1 = "AI活用診断"
ANSWER_MODE_2 = "パターン検索"
CHAT_INPUT_HELPER_TEXT = "診断結果への追加の質問は、こちらから送信してください。"
# 追加質問欄（診断結果の下に置くtext_input＋ボタン）の文言と、入力欄のキー
FOLLOW_UP_CARD_TITLE = "診断結果について、さらに聞く"
FOLLOW_UP_INPUT_LABEL = "診断結果への追加の質問"
FOLLOW_UP_INPUT_PLACEHOLDER = "例: この取り組みに必要な材料は？　費用はどのくらい？"
FOLLOW_UP_BUTTON_LABEL = "質問する"
FOLLOW_UP_INPUT_KEY = "follow_up_input"
FOLLOW_UP_FORM_KEY = "follow_up_form"
DOC_SOURCE_ICON = ":material/description: "
LINK_SOURCE_ICON = ":material/link: "
WARNING_ICON = ":material/warning:"
ERROR_ICON = ":material/error:"
SPINNER_TEXT = "回答を作成しています（10〜20秒ほどかかります）"
SPINNER_TEXT_DIAGNOSIS = "診断結果を作成しています（10〜20秒ほどかかります）"

# 診断中（st.spinnerの代わり）に表示する3段階の進み具合の文言
# サーバーの処理と連動しない「目安」の時間で切り替わるため、面の下に補足文を添える
DIAGNOSIS_PROGRESS_STEPS = [
    "御社に近い資料を探しています",
    "御社の状況に当てはめています",
    "診断の文章にまとめています"
]
DIAGNOSIS_PROGRESS_NOTE = "10〜20秒ほどお待ちください。"

# 初回アクセス時（ベクターストアの作成中）に表示する文言
# 「st.spinner」の文言と、その中で出すフォルダ単位の進捗バーの文言
LOADING_SPINNER_TEXT = "診断の準備をしています。少しお待ちください。"
# ベクトル化（最後の1区間）に入ったときに表示する進捗バーの値
LOADING_PROGRESS_EMBED_VALUE = 90

# ==========================================
# 画面の装飾（デザイントークン）
# ==========================================
# 設計方針: 題材は「眠っている資料を持ち込む経営者の相談窓口」。作業完了型（Operate）の画面なので
# スキャン性を優先し、大胆さは診断結果の「該当パターン」の紺の面1箇所に集中させる。
# 書体は Zen Kaku Gothic New の1ファミリー。色は紺（主役・操作）と琥珀（次の一歩の見出し）の2色に絞る。
# hallmark audit（2026-09-13）の指摘に沿い、色・余白・角丸・影はCSSカスタムプロパティ（:root）に集約し、
# グラデーションと重ね影を廃止、余白は4ptスケール、状態（hover/active/disabled/focus）を明示する。
STYLE_FONT_FAMILY = "'Zen Kaku Gothic New', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif"
STYLE_FONT_IMPORT_URL = "https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap"
STYLE_COLOR_PRIMARY = "#1f3864"       # 紺: 主役の面、主ボタン、選択中
STYLE_COLOR_PRIMARY_DEEP = "#16294A"  # 紺（濃）: 押下中（:active）
STYLE_COLOR_ACCENT = "#B45309"        # 琥珀: 「次の一歩」の見出しだけに使う
STYLE_COLOR_TEXT = "#1A1A1A"
STYLE_COLOR_TEXT_MUTED = "#5B6472"
STYLE_COLOR_TEXT_ON_PRIMARY = "#FFFFFF"
STYLE_COLOR_TEXT_ON_PRIMARY_SOFT = "#C9D6E8"  # 紺の面の上の補助文字（灰色ではなく紺から派生）
STYLE_COLOR_CANVAS = "#F5F7FA"        # 画面の地
STYLE_COLOR_SURFACE = "#FFFFFF"       # 面（フォーム・結果の各ブロック）
STYLE_COLOR_LINE = "#D9DFE7"          # 罫線
STYLE_COLOR_LINE_ON_PRIMARY = "#3D567A"  # 紺の面の上の罫線
# 画面の地を紺のグラデーションにしたため、「カードの外（紺の上）」に描かれる要素用の配色を持つ
STYLE_COLOR_PAGE_BG = "#0a0f1c"              # 画面の地（最下層のベタ色）
STYLE_COLOR_TEXT_ON_PAGE = "#ffffff"         # 紺の上の見出し・本文
STYLE_COLOR_TEXT_ON_PAGE_SOFT = "rgba(255,255,255,0.75)"  # 紺の上の補助文字（説明文・caption）
STYLE_COLOR_OVERLAY_SURFACE = "rgba(255,255,255,0.08)"    # 紺の上に置く半透明の面（通知枠・折りたたみ・吹き出し）
STYLE_COLOR_OVERLAY_LINE = "rgba(255,255,255,0.18)"       # 同じ面の枠線・区切り線
STYLE_COLOR_OVERLAY_LINE_STRONG = "rgba(255,255,255,0.35)"  # 紺の面・主ボタンを地から切り離す枠線
STYLE_CONTENT_MAX_WIDTH = "960px"
# 画面全体に適用するCSS（色・余白・角丸・影は :root のトークンで定義し、以降は var() で参照する）
CUSTOM_CSS = f"""
<style>
    @import url('{STYLE_FONT_IMPORT_URL}');

    :root {{
        --color-primary: {STYLE_COLOR_PRIMARY};
        --color-primary-deep: {STYLE_COLOR_PRIMARY_DEEP};
        --color-accent: {STYLE_COLOR_ACCENT};
        --color-text: {STYLE_COLOR_TEXT};
        --color-text-muted: {STYLE_COLOR_TEXT_MUTED};
        --color-text-on-primary: {STYLE_COLOR_TEXT_ON_PRIMARY};
        --color-text-on-primary-soft: {STYLE_COLOR_TEXT_ON_PRIMARY_SOFT};
        --color-canvas: {STYLE_COLOR_CANVAS};
        --color-surface: {STYLE_COLOR_SURFACE};
        --color-line: {STYLE_COLOR_LINE};
        --color-line-on-primary: {STYLE_COLOR_LINE_ON_PRIMARY};
        /* 画面の地（紺）の上に描かれる要素用 */
        --color-page-bg: {STYLE_COLOR_PAGE_BG};
        --color-text-on-page: {STYLE_COLOR_TEXT_ON_PAGE};
        --color-text-on-page-soft: {STYLE_COLOR_TEXT_ON_PAGE_SOFT};
        --color-overlay-surface: {STYLE_COLOR_OVERLAY_SURFACE};
        --color-overlay-line: {STYLE_COLOR_OVERLAY_LINE};
        --color-overlay-line-strong: {STYLE_COLOR_OVERLAY_LINE_STRONG};
        --font-body: {STYLE_FONT_FAMILY};
        /* 文字サイズ: 14 / 16 / 18 / 22 / 32 */
        --text-sm: 14px;
        --text-md: 16px;
        --text-lg: 18px;
        --text-xl: 22px;
        --text-2xl: 32px;
        --text-question: 19px;
        /* 余白: 4ptスケール */
        --space-xs: 4px;
        --space-sm: 8px;
        --space-md: 16px;
        --space-lg: 24px;
        --space-xl: 32px;
        --space-2xl: 48px;
        /* 角丸: 面 12 / 操作 8 / チップ 999 */
        --radius-surface: 12px;
        --radius-control: 8px;
        --radius-pill: 999px;
        /* 影は1段階だけ（白いカードと診断結果の面）。紺の地の上で浮かせるため濃くする */
        --shadow-surface: 0 8px 24px rgba(0, 0, 0, 0.35);
        /* 操作部品の高さは44pxで統一 */
        --control-height: 44px;
        --focus-ring-inner: 0 0 0 2px var(--color-surface);
        --focus-ring-outer: 0 0 0 5px var(--color-primary);
    }}

    /* Streamlit既定の装飾（最上部の虹色の帯）を消す */
    [data-testid="stDecoration"] {{
        display: none;
    }}

    /* ヘッダー帯を透明化（右上ツールバーの規則には触れない） */
    [data-testid="stHeader"] {{
        background: transparent;
        position: relative;
        z-index: 2;
    }}

    /* 書体: 1ファミリー。アイコンフォントは巻き込まない */
    html, body, .stApp, .stMarkdown, .stCaption, .stRadio, .stSelectbox, .stMultiSelect,
    .stTextInput, .stButton, .stFormSubmitButton, .stExpander, .stAlert, .stChatMessage,
    input, textarea, button, select {{
        font-family: var(--font-body);
    }}
    /* 画面の地: 紺のグラデーション。点の網目・放射グラデ・線形グラデを静止したまま重ねる */
    .stApp {{
        background-color: var(--color-page-bg);
        background-image:
            radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
            radial-gradient(at 78% 20%, rgba(31,56,100,0.55), rgba(0,0,0,0) 60%),
            linear-gradient(168deg, #141d35 0%, #0a0f1c 76%);
        background-size: 28px 28px, auto, auto;
        background-attachment: fixed;
        color: var(--color-text);
    }}
    /* 背景の動きは components.display_background_canvas() が描くcanvas（iframe）が担う。
       iframeを全画面に固定し、本文の背面へ置き、クリックは本文へ通す */
    [data-testid="stIFrame"] iframe, iframe[title="st.iframe"] {{
        position: fixed;
        inset: 0;
        width: 100vw;
        height: 100vh;
        z-index: 0;
        pointer-events: none;
        border: 0;
    }}
    /* iframeを包む要素は高さを持たせず、本文に空白を作らない */
    [data-testid="stIFrame"],
    [data-testid="stElementContainer"]:has([data-testid="stIFrame"]),
    [data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) {{
        height: 0;
        min-height: 0;
        margin: 0;
        padding: 0;
        overflow: visible;
        position: fixed;
        z-index: 0 !important;
    }}
    ::selection {{
        background: var(--color-primary);
        color: var(--color-text-on-primary);
    }}

    /* 行長を保つため本文幅を絞る（背景の動きより前面に出す） */
    [data-testid="stMain"], section.main {{
        position: relative;
        z-index: 1;
    }}
    .block-container {{
        position: relative;
        z-index: 1;
        max-width: {STYLE_CONTENT_MAX_WIDTH};
        padding-top: 3rem;
        padding-bottom: var(--space-2xl);
    }}
    /* カード外の要素（.block-container直下の各ブロック）は球より前面に出す */
    [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
    [data-testid="stExpander"],
    [data-testid="stAlert"],
    [data-testid="stChatMessage"] {{
        position: relative;
        z-index: 1;
    }}

    /* 見出しのスケール */
    .stMarkdown h2 {{
        font-size: var(--text-2xl);
        font-weight: 700;
        line-height: 1.3;
        letter-spacing: -0.01em;
        color: var(--color-text-on-page);
        padding: 0;
        margin: 0 0 var(--space-xs) 0;
    }}
    .stMarkdown h3 {{
        font-size: var(--text-xl);
        font-weight: 700;
        color: var(--color-text-on-page);
        padding: var(--space-sm) 0 0 0;
        margin: 0;
    }}
    .stMarkdown h5 {{
        font-size: var(--text-question);
        font-weight: 700;
        color: var(--color-text);
        padding: var(--space-md) 0 0 0;
        margin: 0 0 var(--space-sm) 0;
    }}
    .stMarkdown h5 .shindan-heading-note {{
        font-size: var(--text-sm);      /* 14px。補足情報なので小さく */
        font-weight: 500;
        color: var(--color-text-muted);
        margin-left: var(--space-xs);
    }}
    .stMarkdown p, .stRadio label p {{
        font-size: var(--text-md);
        line-height: 1.75;
        color: var(--color-text);
    }}
    /* カードの外（紺の上）のcaption（「最新の診断」「過去の診断（N回目）」「入力内容の1行要約」）は白系 */
    [data-testid="stCaptionContainer"] p {{
        color: var(--color-text-on-page-soft);
        font-size: var(--text-sm);
        line-height: 1.6;
    }}
    /* カードの中のcaption（設問の説明文「1つ選ぶと…」など）は今の色に戻す */
    [data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) [data-testid="stCaptionContainer"] p {{
        color: var(--color-text-muted);
    }}
    /* タイトル直下の一文は説明ではなく見出しの続き */
    .shindan-lead p {{
        font-size: var(--text-lg);
        color: var(--color-text-on-page-soft);
        margin: 0;
    }}

    /* 入力フォームの面: この画面で唯一、影で浮かせる面
       ※ 枠なしの内部ブロックも同じtestidを持つため、既定の空クラス（st-emotion-cache-0）を除外して枠付きだけに当てる */
    [data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) {{
        position: relative;
        z-index: 2;
        background: var(--color-surface);
        border: 0;
        border-radius: var(--radius-surface);
        box-shadow: var(--shadow-surface);
        padding: var(--space-sm) var(--space-md);
    }}
    [data-testid="stForm"] {{
        border: 0;
        padding: 0;
    }}
    .stRadio [role="radiogroup"] {{
        gap: var(--space-sm);
    }}
    /* 入力欄のラベル（業種・従業員数など）は種類が違っても同じ大きさに揃える */
    [data-testid="stWidgetLabel"] p {{
        font-size: var(--text-sm);
        font-weight: 500;
        color: var(--color-text);
        line-height: 1.5;
    }}
    /* 入力欄・プルダウン: 高さ44px、地は面よりわずかに沈める */
    [data-baseweb="select"] > div, [data-baseweb="input"] > div, .stTextInput input {{
        background-color: var(--color-canvas);
        border-color: var(--color-line);
        min-height: var(--control-height);
        border-radius: var(--radius-control);
    }}
    /* チップ型の選択肢（従業員数）: 高さ44px。選択中は紺、未選択は罫線 */
    button[data-testid="stBaseButton-pills"], button[data-testid="stBaseButton-pillsActive"] {{
        border-radius: var(--radius-pill);
        min-height: var(--control-height);
        padding: 0 var(--space-md);
        font-size: var(--text-sm);
        border: 1px solid var(--color-line);
        background: var(--color-surface);
        color: var(--color-text);
    }}
    button[data-testid="stBaseButton-pills"]:hover {{
        border-color: var(--color-primary);
        color: var(--color-primary);
    }}
    button[data-testid="stBaseButton-pills"]:active {{
        background: var(--color-canvas);
    }}
    button[data-testid="stBaseButton-pillsActive"],
    button[data-testid="stBaseButton-pillsActive"]:hover {{
        background: var(--color-primary);
        border-color: var(--color-primary);
        color: var(--color-text-on-primary);
    }}
    button[data-testid="stBaseButton-pillsActive"] p,
    button[data-testid="stBaseButton-pillsActive"] span {{
        color: var(--color-text-on-primary);
    }}

    /* ボタン: 高さ44px以上。主ボタンは紺のベタ塗り（グラデーション・影なし） */
    .stFormSubmitButton button, .stButton button {{
        min-height: var(--control-height);
        border-radius: var(--radius-control);
        font-size: var(--text-md);
        font-weight: 700;
    }}
    .stFormSubmitButton button {{
        min-height: 3.2rem;
        font-size: 1.1rem;
        font-weight: 700;
    }}
    .stFormSubmitButton button p {{
        font-size: 1.1rem;
        font-weight: 700;
    }}
    .stFormSubmitButton button[kind="primary"] {{
        background: var(--color-primary);
        border: 1px solid var(--color-overlay-line-strong);
        color: var(--color-text-on-primary);
    }}
    .stFormSubmitButton button[kind="primary"]:hover {{
        background: var(--color-primary-deep);
    }}
    .stFormSubmitButton button[kind="primary"]:active {{
        background: var(--color-primary-deep);
        transform: translateY(1px);
    }}
    .stFormSubmitButton button:disabled, .stButton button:disabled {{
        opacity: 0.55;
        cursor: not-allowed;
    }}
    /* フォーカスリングは二重（内側が白）にして、紺のボタンの上でも見えるようにする。表示は即時 */
    button:focus-visible, input:focus-visible, textarea:focus-visible, [role="radio"]:focus-visible {{
        outline: 0;
        box-shadow: var(--focus-ring-inner), var(--focus-ring-outer);
    }}
    /* プルダウン・複数選択の内部にある検索用の小さな入力欄にはリングを出さず、外枠全体に出す */
    [data-baseweb="select"] input:focus-visible {{
        box-shadow: none;
    }}
    [data-baseweb="select"] > div:focus-within {{
        border-color: var(--color-primary);
        box-shadow: var(--focus-ring-inner), var(--focus-ring-outer);
    }}

    /* 診断結果のブロック: 白い面を1pxの罫線で区切る。紺の地の上では影で浮かせる。該当パターンだけ紺の面 */
    .shindan-panel {{
        position: relative;
        z-index: 2;
        background: var(--color-surface);
        border: 1px solid var(--color-line);
        border-radius: var(--radius-surface);
        box-shadow: var(--shadow-surface);
        padding: var(--space-md) var(--space-lg);
        margin: 0 0 var(--space-md) 0;
    }}
    /* 紺の面は地と同化するため、白い枠線で切り離す */
    .shindan-panel.shindan-hero {{
        background: var(--color-primary);
        border: 1px solid var(--color-overlay-line-strong);
        color: var(--color-text-on-primary);
        padding: var(--space-lg) var(--space-xl);
        margin-bottom: var(--space-lg);
    }}
    .shindan-hero .shindan-block-title {{
        color: var(--color-text-on-primary-soft);
    }}
    .shindan-hero .shindan-hero-title {{
        font-size: var(--text-xl);
        font-weight: 700;
        line-height: 1.5;
        color: var(--color-text-on-primary);
        margin: 0;
    }}
    .shindan-hero .shindan-hero-title + .shindan-hero-title {{
        margin-top: var(--space-md);
        padding-top: var(--space-md);
        border-top: 1px solid var(--color-line-on-primary);
    }}
    .shindan-hero .shindan-hero-company {{
        display: block;
        font-size: var(--text-sm);
        font-weight: 500;
        color: var(--color-text-on-primary-soft);
        margin-top: var(--space-xs);
    }}
    .shindan-panel.shindan-next .shindan-block-title {{
        color: var(--color-accent);
    }}
    .shindan-block-title {{
        font-size: var(--text-md);
        font-weight: 700;
        color: var(--color-text);
        margin: 0 0 var(--space-xs) 0;
    }}
    .shindan-block-body {{
        font-size: var(--text-md);
        line-height: 1.75;
        color: var(--color-text);
        margin: 0;
    }}
    /* 4区分: 同じ大きさの箱を並べず、区分名と本文の2列の表にする（高さは中身に従う） */
    .shindan-quad-list {{
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 0;
        margin: 0;
    }}
    .shindan-quad-row {{
        display: grid;
        grid-template-columns: 220px minmax(0, 1fr);
        gap: var(--space-md);
        padding: var(--space-md) 0;
        border-top: 1px solid var(--color-line);
    }}
    .shindan-quad-row:first-child {{
        border-top: 0;
        padding-top: var(--space-xs);
    }}
    .shindan-quad-row:last-child {{
        padding-bottom: var(--space-xs);
    }}
    .shindan-quad-row .shindan-block-title {{
        margin: 0;
        overflow-wrap: anywhere;
        min-width: 0;
    }}
    @media (max-width: 640px) {{
        .shindan-quad-row {{
            grid-template-columns: minmax(0, 1fr);
            gap: var(--space-xs);
        }}
    }}

    /* 通知枠・区切り線・折りたたみ（いずれもカードの外＝紺の上に描かれるため、半透明の面＋白い文字にする） */
    [data-testid="stAlert"] {{
        border-radius: var(--radius-control);
        background: var(--color-overlay-surface);
        border: 1px solid var(--color-overlay-line);
        color: var(--color-text-on-page);
    }}
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] li,
    [data-testid="stAlert"] strong,
    [data-testid="stAlert"] span,
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {{
        color: var(--color-text-on-page);
    }}
    /* 通知枠のアイコン（material icon）も白 */
    [data-testid="stAlertContentInfo"], [data-testid="stAlertContentWarning"],
    [data-testid="stAlertContentSuccess"], [data-testid="stAlertContentError"],
    [data-testid="stAlert"] [data-testid="stIconMaterial"],
    [data-testid="stAlert"] .material-icons,
    [data-testid="stAlert"] .material-icons-outlined,
    [data-testid="stAlert"] svg {{
        color: var(--color-text-on-page);
        fill: var(--color-text-on-page);
    }}
    /* 通知枠の中のリンク（「ご相談」のmailto）も白系。下線を付けてリンクだと分かるようにする */
    [data-testid="stAlert"] a, [data-testid="stAlert"] a:visited {{
        color: var(--color-text-on-page);
        text-decoration: underline;
    }}
    hr {{
        border-color: var(--color-overlay-line);
        margin: var(--space-xl) 0 var(--space-md) 0;
    }}
    /* 「資料検索（管理者用）」の折りたたみ */
    [data-testid="stExpander"] {{
        background: var(--color-overlay-surface);
        border: 1px solid var(--color-overlay-line);
        border-radius: var(--radius-surface);
    }}
    [data-testid="stExpander"] details, [data-testid="stExpander"] summary {{
        background: transparent;
        border: 0;
    }}
    [data-testid="stExpander"] summary p {{
        color: var(--color-text-on-page);
        font-size: var(--text-sm);
    }}
    [data-testid="stExpander"] summary svg,
    [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {{
        color: var(--color-text-on-page);
        fill: var(--color-text-on-page);
    }}
    /* 見出し（summary）の文字色は .stMarkdown p 等に負けるため、具体的なセレクタで必ず勝たせる */
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] p,
    [data-testid="stExpander"] summary svg {{
        color: var(--color-text-on-page) !important;
        fill: currentColor;
    }}
    /* 折りたたみの中の文字（検索結果の資料のありか）と入力欄のラベルも白系 */
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong,
    [data-testid="stExpander"] [data-testid="stWidgetLabel"] p,
    [data-testid="stExpander"] [data-testid="stCaptionContainer"] p {{
        color: var(--color-text-on-page) !important;
    }}
    /* 入力欄は白地のまま（文字が読めるように）。ボタンは白系の枠線にする */
    [data-testid="stExpander"] .stTextInput input {{
        background-color: var(--color-surface);
        color: var(--color-text);
        border-color: var(--color-line);
    }}
    [data-testid="stExpander"] .stButton button {{
        background: transparent;
        border: 1px solid var(--color-overlay-line-strong);
        color: var(--color-text-on-page);
    }}
    [data-testid="stExpander"] .stButton button p {{
        color: var(--color-text-on-page);
    }}
    [data-testid="stExpander"] .stButton button:hover {{
        background: var(--color-overlay-surface);
        border-color: var(--color-text-on-page);
    }}

    /* 「結果を消してやり直す」ボタン。白いカードの外（背景に直接）に置かれるため、控えめな見た目にする */
    .st-key-clear_results_button {{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        height: 100%;
    }}
    .st-key-clear_results_button button {{
        min-height: 2.2rem;
        padding: 0 var(--space-md);
        background: transparent;
        border: 1px solid rgba(255,255,255,0.4);
        color: var(--color-text-on-page);
        font-size: var(--text-sm);
        font-weight: 500;
    }}
    .st-key-clear_results_button button p {{
        color: var(--color-text-on-page);
        font-size: var(--text-sm);
    }}
    .st-key-clear_results_button button:hover {{
        background: var(--color-overlay-surface);
        border-color: var(--color-text-on-page);
    }}

    /* 追加質問のやり取り（吹き出し）。カードの外に描かれるため、半透明の面＋白い文字にする */
    [data-testid="stChatMessage"] {{
        background: var(--color-overlay-surface);
        border: 1px solid var(--color-overlay-line);
        border-radius: var(--radius-surface);
        color: var(--color-text-on-page);
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p {{
        color: var(--color-text-on-page);
    }}
    [data-testid="stChatMessage"] a, [data-testid="stChatMessage"] a:visited {{
        color: var(--color-text-on-page);
        text-decoration: underline;
    }}
    [data-testid="stChatMessage"] hr {{
        border-color: var(--color-overlay-line);
    }}

    /* 初回読み込みのスピナー文言と、その中の進捗バーの文字（いずれもカードの外） */
    [data-testid="stSpinner"] p, [data-testid="stSpinner"] div {{
        color: var(--color-text-on-page-soft);
    }}
    /* 背景が動くようになったため、スピナーの回転アイコンと文言をより明るい白にして視認性を保つ */
    [data-testid="stSpinner"] i,
    [data-testid="stSpinner"] > div > div {{
        border-top-color: rgba(255,255,255,0.85) !important;
        color: rgba(255,255,255,0.85);
    }}
    [data-testid="stSpinner"] p {{
        color: rgba(255,255,255,0.85);
    }}
    [data-testid="stProgress"] p, [data-testid="stProgress"] div[data-testid="stMarkdownContainer"] p {{
        color: var(--color-text-on-page-soft);
    }}

    /* 操作への応答（短いトランジション）。フォーカスリング（box-shadow・outline）には付けない */
    button[data-testid="stBaseButton-pills"], button[data-testid="stBaseButton-pillsActive"],
    .stFormSubmitButton button, .stButton button,
    .stRadio label,
    [data-baseweb="select"] > div, [data-baseweb="input"] > div, .stTextInput input {{
        transition: background-color 120ms ease-out, border-color 120ms ease-out, color 120ms ease-out;
    }}
    @media (prefers-reduced-motion: reduce) {{
        button[data-testid="stBaseButton-pills"], button[data-testid="stBaseButton-pillsActive"],
        .stFormSubmitButton button, .stButton button,
        .stRadio label,
        [data-baseweb="select"] > div, [data-baseweb="input"] > div, .stTextInput input {{
            transition: none;
        }}
    }}

    /* 診断中だけ表示する3段階の進み具合（st.spinnerの代わり）。時間は目安であり、サーバー処理と連動しない */
    .shindan-progress-step {{
        display: flex;
        align-items: center;
        gap: var(--space-sm);
        padding: var(--space-xs) 0;
    }}
    .shindan-progress-dot {{
        width: 8px;
        height: 8px;
        border-radius: var(--radius-pill);
        background: var(--color-line);
        flex-shrink: 0;
    }}
    .shindan-progress-text {{
        font-size: var(--text-md);
        color: var(--color-text-muted);
    }}
    .shindan-progress-note {{
        font-size: var(--text-sm);
        color: var(--color-text-muted);
        margin: var(--space-sm) 0 0 0;
    }}
    /* 0〜5秒: 1行目 / 5〜11秒: 2行目 / 11秒以降: 3行目 が「紺の丸＋濃い文字」になる（合計16秒で以降は3行目のまま） */
    .shindan-progress-step[data-step="1"] .shindan-progress-dot {{
        animation: shindan-progress-dot-1 16s ease-out forwards;
    }}
    .shindan-progress-step[data-step="1"] .shindan-progress-text {{
        animation: shindan-progress-text-1 16s ease-out forwards;
    }}
    .shindan-progress-step[data-step="2"] .shindan-progress-dot {{
        animation: shindan-progress-dot-2 16s ease-out forwards;
    }}
    .shindan-progress-step[data-step="2"] .shindan-progress-text {{
        animation: shindan-progress-text-2 16s ease-out forwards;
    }}
    .shindan-progress-step[data-step="3"] .shindan-progress-dot {{
        animation: shindan-progress-dot-3 16s ease-out forwards;
    }}
    .shindan-progress-step[data-step="3"] .shindan-progress-text {{
        animation: shindan-progress-text-3 16s ease-out forwards;
    }}
    @keyframes shindan-progress-dot-1 {{
        0%, 31.25% {{ background: var(--color-primary); }}
        31.26%, 100% {{ background: var(--color-line); }}
    }}
    @keyframes shindan-progress-text-1 {{
        0%, 31.25% {{ color: var(--color-text); font-weight: 700; }}
        31.26%, 100% {{ color: var(--color-text-muted); font-weight: 500; }}
    }}
    @keyframes shindan-progress-dot-2 {{
        0%, 31.24% {{ background: var(--color-line); }}
        31.25%, 68.75% {{ background: var(--color-primary); }}
        68.76%, 100% {{ background: var(--color-line); }}
    }}
    @keyframes shindan-progress-text-2 {{
        0%, 31.24% {{ color: var(--color-text-muted); font-weight: 500; }}
        31.25%, 68.75% {{ color: var(--color-text); font-weight: 700; }}
        68.76%, 100% {{ color: var(--color-text-muted); font-weight: 500; }}
    }}
    @keyframes shindan-progress-dot-3 {{
        0%, 68.75% {{ background: var(--color-line); }}
        68.76%, 100% {{ background: var(--color-primary); }}
    }}
    @keyframes shindan-progress-text-3 {{
        0%, 68.75% {{ color: var(--color-text-muted); font-weight: 500; }}
        68.76%, 100% {{ color: var(--color-text); font-weight: 700; }}
    }}
    /* reduced-motionのときは、3行とも濃い文字で静止表示（アニメーションなし・同じ最終状態） */
    @media (prefers-reduced-motion: reduce) {{
        .shindan-progress-dot {{
            animation: none !important;
            background: var(--color-primary);
        }}
        .shindan-progress-text {{
            animation: none !important;
            color: var(--color-text);
            font-weight: 700;
        }}
    }}
</style>
"""

# 背景の点の球（canvasアニメーション）を出すかどうか。False なら canvas を描画しない（iframe も作られない）
SHOW_BACKGROUND_ANIMATION = False

# 背景の動き: 球面に散らした点をゆっくり回す canvas（components.display_background_canvas で描画）
# ・外部ライブラリは使わず、素の <canvas> と <script> だけで完結させる
# ・JSの {} をエスケープせずに済むよう、この定数は f-string にしない（値はJS側の const に直書きする）
BACKGROUND_CANVAS_HTML = """
<style>
    html, body { margin: 0; background: transparent; overflow: hidden; }
    canvas { display: block; width: 100vw; height: 100vh; }
</style>
<canvas id="shindan-bg-sphere"></canvas>
<script>
(function () {
    // --- 調整用の値 ---
    var POINT_COUNT = 380;          // 球面に散らす点の数
    var ROTATION_SECONDS = 3600;      // Y軸まわりに1周する秒数
    var CENTER_X_RATIO = 0.5;       // 球の中心（画面幅に対する割合）
    var CENTER_Y_RATIO = 0.5;       // 球の中心（画面高さに対する割合）
    var RADIUS_RATIO = 0.65;        // 半径（画面の長辺に対する割合）
    var CAMERA_FACTOR = 3;          // 視点距離 = 半径 * この値
    var LINK_DISTANCE = 100;         // 点と点を線で結ぶ投影距離の上限(px)
    var REFERENCE_LONG_SIDE = 730;  // 上の値を決めたときの画面の長辺(px)。画面がこれより広いぶんだけ点を増やし、見え方の密度を保つ
    var MAX_POINT_COUNT = 2000;     // 広い画面で増やす点の数の上限（描画負荷の抑え）
    var RADIUS_NEAR = 2;            // 手前の点の半径(px)
    var RADIUS_FAR = 0.6;           // 奥の点の半径(px)
    var ALPHA_NEAR = 0.9;           // 手前の点の不透明度
    var ALPHA_FAR = 0.15;           // 奥の点の不透明度

    var canvas = document.getElementById('shindan-bg-sphere');
    var ctx = canvas.getContext('2d');

    // 球面上に一様分布で点を置く
    var points = [];
    for (var i = 0; i < MAX_POINT_COUNT; i++) {
        var z = 2 * Math.random() - 1;
        var theta = 2 * Math.PI * Math.random();
        var r = Math.sqrt(1 - z * z);
        points.push({ x: r * Math.cos(theta), y: r * Math.sin(theta), z: z });
    }

    var width = 0, height = 0, centerX = 0, centerY = 0, radius = 0, camera = 0;
    var activeCount = POINT_COUNT;

    function resize() {
        var dpr = window.devicePixelRatio || 1;
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);
        canvas.style.width = width + 'px';
        canvas.style.height = height + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        centerX = width * CENTER_X_RATIO;
        centerY = height * CENTER_Y_RATIO;
        radius = Math.max(width, height) * RADIUS_RATIO;
        camera = radius * CAMERA_FACTOR;
        // 画面が基準より広いぶん、点の数を面積比で増やす（狭い画面では減らさない）。線の距離(px)はそのまま
        var sizeScale = Math.max(1, Math.max(width, height) / REFERENCE_LONG_SIDE);
        activeCount = Math.min(MAX_POINT_COUNT, Math.round(POINT_COUNT * sizeScale * sizeScale));
    }

    var projected = new Array(MAX_POINT_COUNT);
    for (var j = 0; j < MAX_POINT_COUNT; j++) {
        projected[j] = { x: 0, y: 0, depth: 0 };
    }

    function draw(elapsedMs) {
        var angle = (elapsedMs / 1000) * (2 * Math.PI / ROTATION_SECONDS);
        var cos = Math.cos(angle);
        var sin = Math.sin(angle);
        ctx.clearRect(0, 0, width, height);

        for (var i = 0; i < activeCount; i++) {
            var p = points[i];
            // Y軸まわりの回転
            var rx = p.x * cos + p.z * sin;
            var rz = -p.x * sin + p.z * cos;
            var ry = p.y;
            // 透視投影
            var scale = camera / (camera + rz * radius);
            var q = projected[i];
            q.x = centerX + rx * radius * scale;
            q.y = centerY + ry * radius * scale;
            // depth: 奥=0, 手前=1
            q.depth = (1 - rz) / 2;
        }

        // 近い点どうしを線で結ぶ（距離の判定は平方距離で行う）
        var limitSq = LINK_DISTANCE * LINK_DISTANCE;
        ctx.lineWidth = 0.6;
        ctx.strokeStyle = 'rgba(160,190,240,0.22)';
        ctx.beginPath();
        for (var a = 0; a < activeCount; a++) {
            for (var b = a + 1; b < activeCount; b++) {
                var dx = projected[a].x - projected[b].x;
                var dy = projected[a].y - projected[b].y;
                if (dx * dx + dy * dy < limitSq) {
                    ctx.moveTo(projected[a].x, projected[a].y);
                    ctx.lineTo(projected[b].x, projected[b].y);
                }
            }
        }
        ctx.stroke();

        // 点は奥ほど小さく薄く
        for (var k = 0; k < activeCount; k++) {
            var pt = projected[k];
            var dotRadius = RADIUS_FAR + (RADIUS_NEAR - RADIUS_FAR) * pt.depth;
            var alpha = ALPHA_FAR + (ALPHA_NEAR - ALPHA_FAR) * pt.depth;
            ctx.fillStyle = 'rgba(200,220,255,' + alpha.toFixed(3) + ')';
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, dotRadius, 0, 2 * Math.PI);
            ctx.fill();
        }
    }

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    resize();
    if (reduceMotion) {
        // 動きを減らす設定のときは1フレームだけ描いて止める
        draw(0);
        window.addEventListener('resize', function () { resize(); draw(0); });
        return;
    }

    var start = null;
    function frame(now) {
        if (start === null) { start = now; }
        draw(now - start);
        window.requestAnimationFrame(frame);
    }
    window.addEventListener('resize', resize);
    window.requestAnimationFrame(frame);
})();
</script>
"""


# 結果が出た瞬間の一回きりの登場CSS（診断直後の描画でだけ st.markdown で出す。詳細は README「1.」を参照）
# ・下から8px上がりながら不透明度0→1で360ms、cubic-bezier(0.22, 1, 0.36, 1)（ease-out）
# ・面ごとに60msずつ遅らせる（HTML生成時にstyle="animation-delay: …ms"を順番に付ける。nth-of-typeは効かないため使わない）
ENTRANCE_CSS = """
<style>
    @keyframes shindan-rise {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: none; }
    }
    .shindan-enter {
        animation: shindan-rise 360ms cubic-bezier(0.22, 1, 0.36, 1) both;
    }
    @media (prefers-reduced-motion: reduce) {
        .shindan-enter {
            animation: none !important;
        }
    }
</style>
"""


# ==========================================
# サイドバー・初期メッセージの表示系
# ==========================================
SIDEBAR_TITLE = "利用目的"
SIDEBAR_AREA_TITLE = "相談したい領域"
SIDEBAR_INDUSTRY_TITLE = "業種"
SIDEBAR_EMPLOYEE_TITLE = "従業員数"
SIDEBAR_TROUBLE_TITLE = "いちばんの困りごと"
SIDEBAR_MATERIAL_TITLE = "社内にある材料"
SIDEBAR_NOTE_TITLE = "補足（※任意。「その他」を選んだ場合は困りごとをここに書いてください）"
# サイドバーの番号付き見出し（入力欄を5つの区切りに分ける）
SIDEBAR_SECTION_AREA = "1. 相談したい領域"
SIDEBAR_SECTION_COMPANY = "2. 御社について"
SIDEBAR_SECTION_TROUBLE = "3. いちばんの困りごと"
SIDEBAR_SECTION_MATERIAL = "4. 社内にある材料"
SIDEBAR_SECTION_NOTE = "5. 補足"
SIDEBAR_SECTION_NOTE_SUB = "（※任意。「その他」を選んだ場合は困りごとをここに書いてください）"
SIDEBAR_NOTE_PLACEHOLDER = "例: 今の状況や、すでに試したことがあれば書いてください"
DIAGNOSIS_BUTTON_LABEL = "診断する"

SIDEBAR_MODE_2_TITLE = "**【「パターン検索」を選択した場合】**"
SIDEBAR_MODE_2_DESCRIPTION = "入力内容と関連性が高い資料のありかを検索できます。"
SIDEBAR_MODE_2_EXAMPLE = "【入力例】\n求人票を作り直すパターンの根拠になっている調査数値"

INITIAL_AI_MESSAGE = "左のサイドバーで御社の状況を選び、「診断する」を押してください。御社にすでにある資料から、何ができるかをお見せします。"
INITIAL_AI_WARNING_MESSAGE = "診断結果は一般的な目安です。詳しい設計はご相談ください。"

# ==========================================
# 入力フォーム（v2: メイン画面の上段）の表示系
# ==========================================
DIAGNOSIS_FORM_KEY = "diagnosis_form"
# 各項目の見出しの下に出す短い補助文（ラベルの曖昧さをなくす）
SIDEBAR_SECTION_AREA_HELP = "1つ選ぶと、3の困りごとの選択肢が切り替わります。"
SIDEBAR_SECTION_TROUBLE_HELP = "いちばん近いものを1つ選んでください。"
SIDEBAR_SECTION_NOTE_HELP = "「その他」以外を選んだ場合は、書かなくても診断できます。"
# 結果セクションの見出しと、診断ごとのラベル
RESULT_SECTION_TITLE = "診断結果"
RESULT_BLOCK_LABEL_LATEST = "最新の診断"
RESULT_BLOCK_LABEL_PAST = "過去の診断（{number}回目）"
# 結果を消してやり直すボタン
RESULT_CLEAR_BUTTON_LABEL = "結果を消してやり直す"
RESULT_CLEAR_BUTTON_KEY = "clear_results_button"
DIAGNOSIS_FORM_SUBMIT_LABEL = "この内容で診断する"
DIAGNOSIS_FORM_MATERIAL_PLACEHOLDER = "あるものをすべて選んでください（無ければ空のまま）"
# 診断前に、フォームの下へ出す案内文
DIAGNOSIS_FORM_GUIDE_MESSAGE = "上の項目を選んで『この内容で診断する』を押してください。"
# 画面最下部の資料検索（管理者用）
DOC_SEARCH_EXPANDER_TITLE = "資料検索（管理者用）"
DOC_SEARCH_INPUT_LABEL = "検索したい内容"
DOC_SEARCH_INPUT_PLACEHOLDER = "例: 求人票を作り直すパターンの根拠になっている調査数値"
DOC_SEARCH_BUTTON_LABEL = "資料を検索する"

# 対応パターンが無い困りごとを選んだ場合に、診断結果の冒頭へ必ず出す1行
NO_PATTERN_NOTICE_MESSAGE = "この診断は、御社の状況に近い一般的な目安です。御社の資料をもとにした具体的な診断は、ご相談ください。"

# 4区分のうち「別の仕組みとの連携が必要な部分」が、この文言と一致する場合は行そのものを出さない
# （前後の空白と末尾の句点を取り除いてから比較する）
NEEDS_OTHER_SYSTEM_NONE_TEXT = "特にありません"

# 相談導線の文言（初版はリード獲得を実装せず、この文言のみを出す）
CONSULT_MESSAGE = "この診断は一般的な目安です。御社の資料をもとにした具体的な提案をご希望の方は、お気軽にご相談ください。"

# 相談導線のメール宛先・件名（「ご相談」をmailtoリンク化する際に使う）
CONSULT_MAIL_ADDRESS = "designstudiowave@gmail.com"
CONSULT_MAIL_SUBJECT = "AI活用診断についての相談"
# 「ご相談」をMarkdownのリンクにして表示するフォーマット（{mailto}にmailto URLを埋める）
CONSULT_MESSAGE_FORMAT = "この診断は一般的な目安です。御社の資料をもとにした具体的な提案をご希望の方は、お気軽に[ご相談]({mailto})ください。"

# 対応パターンが「ある」場合の「該当パターン」欄の組み立てフォーマット
# （LLMの生成文ではなく、パターン文書のメタ行から組み立てた文字列を表示する）
PATTERN_NAME_FORMAT = "{title}（向いている会社: {company}）"
# 「向いている会社」がメタ行から取得できなかった場合の代替文言
PATTERN_NAME_NO_COMPANY = "記載なし"
# 対応パターンが「ない」場合に、「該当パターン」欄へ固定で表示する文
NO_PATTERN_FIXED_PATTERN_NAME = "この困りごとに向けた、御社向けの具体的な取り組み例はこれから追加していきます。"
# 対応パターンが「ない」場合に、「根拠となる数字」欄へ固定で表示する文
NO_PATTERN_FIXED_EVIDENCE = "この困りごとについては、まだ裏付けとなる調査数値をご用意していません。"


# ==========================================
# 診断結果の見出し
# ==========================================
DIAGNOSIS_HEADING_PATTERN_NAME = "御社に合う取り組み"
DIAGNOSIS_HEADING_FOR_YOUR_COMPANY = "御社の場合"
DIAGNOSIS_HEADING_EVIDENCE = "根拠となる数字"
DIAGNOSIS_HEADING_NEXT_STEP = "次の一歩"
DIAGNOSIS_HEADING_AI_CAN_IMPROVE = "AIで改善できる部分"
DIAGNOSIS_HEADING_AI_CANNOT_SOLVE = "AIだけでは解決できない部分"
DIAGNOSIS_HEADING_HUMAN_JUDGMENT = "人の判断が必要な部分"
DIAGNOSIS_HEADING_NEEDS_OTHER_SYSTEM = "別の仕組みとの連携が必要な部分"

# 診断結果の先頭に出す、入力内容の1行要約
# 例: 「人事 ／ 製造 ／ 〜10名 ／ 求人を出しても応募がなかなか集まらない ／ 材料: 会社案内パンフ、経営者の話」
DIAGNOSIS_INPUT_SUMMARY_SEPARATOR = " ／ "
DIAGNOSIS_INPUT_SUMMARY_MATERIAL_PREFIX = "材料: "
DIAGNOSIS_INPUT_SUMMARY_NOTE_PREFIX = "補足: "
# 1行要約では材料名から取り除く注記（「経営者の話（口頭のみ）」→「経営者の話」）
DIAGNOSIS_INPUT_SUMMARY_MATERIAL_TRIM = "（口頭のみ）"
# 材料が1つも選ばれなかった場合の1行要約の文言（検索文側のDIAGNOSIS_QUERY_NO_MATERIALとは別に持ち、画面表示は変えない）
DIAGNOSIS_INPUT_SUMMARY_NO_MATERIAL = "特になし"


# ==========================================
# サイドバーの選択肢
# ==========================================
# 相談したい領域（表示名 → 内部キー）
AREA_LABEL_TO_KEY = {
    "人事（採用・教育・定着）": "人事",
    "集客・営業": "集客",
    "顧客対応": "顧客",
    "業務効率化": "業務"
}
AREA_LABELS = list(AREA_LABEL_TO_KEY.keys())

# 業種
INDUSTRY_OPTIONS = [
    "製造",
    "建設",
    "卸売",
    "小売・飲食",
    "運輸・物流",
    "宿泊・観光",
    "医療・介護",
    "不動産",
    "IT・情報通信",
    "その他"
]

# 従業員数
EMPLOYEE_COUNT_OPTIONS = [
    "〜10名",
    "11〜30名",
    "31〜50名",
    "51〜100名",
    "101名〜"
]

# 社内にある材料
MATERIAL_OPTIONS = [
    "昔作った求人票",
    "会社案内パンフ",
    "ホームページの事業紹介",
    "面接メモ",
    "入社後の教育資料",
    "経営者の話（口頭のみ）",
    "ベテラン社員の仕事のコツ（口頭のみ）"
]

# 困りごとIDの末尾判定用（「その他」の困りごとIDはこの文字列で終わる）
TROUBLE_OTHER_ID_SUFFIX = "その他"
# 「その他」の困りごとの表示ラベル（4領域で共通）
TROUBLE_OTHER_LABEL = "その他（困りごとを下の補足欄に書いてください）"

# いちばんの困りごと（領域の内部キー → （困りごとID, 困りごとの全文）のリスト）
# 各領域の末尾（11番目）に「その他」を追加している
TROUBLE_OPTIONS = {
    "人事": [
        ("人事1", "求人を出しても応募がなかなか集まらない"),
        ("人事2", "応募は来ても、求める経験・スキルの人を採用できない"),
        ("人事3", "どんな求人の出し方・採用方法が効果的か分からない"),
        ("人事4", "採用活動や応募者対応に割ける時間がない"),
        ("人事5", "内定を出しても辞退される"),
        ("人事6", "採用してもすぐに辞めてしまう"),
        ("人事7", "新人・若手を教える人が足りない"),
        ("人事8", "新人教育・OJTに時間をかけられない"),
        ("人事9", "社員を何からどう育てればよいか分からない"),
        ("人事10", "ベテランの知識・ノウハウをうまく引き継げない"),
        ("人事その他", TROUBLE_OTHER_LABEL)
    ],
    "集客": [
        ("集客1", "新規の問い合わせ・見込み客がなかなか増えない"),
        ("集客2", "Webサイトから問い合わせ・来店につながらない"),
        ("集客3", "Web記事・SNSで何を発信すればよいか分からない"),
        ("集客4", "自社の商品・サービスの強みや違いをうまく伝えられない"),
        ("集客5", "新しく営業する相手をどう探し、優先すればよいか分からない"),
        ("集客6", "顧客が何を求めているのか整理しきれない"),
        ("集客7", "相手に合わせた営業資料・提案書を作るのに時間がかかる"),
        ("集客8", "問い合わせ後・商談後のフォローまで手が回らない"),
        ("集客9", "必要な顧客情報・過去の商談履歴をすぐ確認できない"),
        ("集客10", "集客・営業の結果を振り返って、何を改善すべきか分からない"),
        ("集客その他", TROUBLE_OTHER_LABEL)
    ],
    "顧客": [
        ("顧客1", "問い合わせ対応に時間を取られ、他の仕事が進まない"),
        ("顧客2", "同じような問い合わせに何度も回答している"),
        ("顧客3", "回答に必要な情報を探すのに時間がかかる"),
        ("顧客4", "その場で答えられず、社内確認や折り返しが多い"),
        ("顧客5", "顧客へのメール返信文を考えるのに時間がかかる"),
        ("顧客6", "電話に出られる人がおらず、問い合わせを取りこぼすことがある"),
        ("顧客7", "担当者によって回答内容や対応品質が違う"),
        ("顧客8", "一部の担当者しか答えられない問い合わせがある"),
        ("顧客9", "問い合わせ内容や過去の対応履歴を記録・確認するのに手間がかかる"),
        ("顧客10", "顧客の要望・不満を整理・集計して、改善に活かすのが大変"),
        ("顧客その他", TROUBLE_OTHER_LABEL)
    ],
    "業務": [
        ("業務1", "書類や報告書を作るのに時間がかかる"),
        ("業務2", "データ入力・転記・照合に時間を取られている"),
        ("業務3", "同じ情報を複数のシステムやファイルに何度も入力している"),
        ("業務4", "Excel・CSVなどの集計や加工に時間がかかる"),
        ("業務5", "会議の議事録や決定事項・タスクの整理に時間がかかる"),
        ("業務6", "必要な資料や社内情報を探すのに時間がかかる"),
        ("業務7", "社内からの問い合わせや確認対応に時間を取られている"),
        ("業務8", "マニュアルや手順書の作成・更新が追いつかない"),
        ("業務9", "特定の人しか分からない仕事がある"),
        ("業務10", "社内メールや定型連絡文を書くのに時間がかかる"),
        ("業務その他", TROUBLE_OTHER_LABEL)
    ]
}


# ==========================================
# 参照元ドキュメントの表示系
# ==========================================
# PDFのページ番号の表示フォーマット（metadataの「page」は0始まりのため、+1した値を埋め込む）
PAGE_NUMBER_FORMAT = "（ページNo.{page_number}）"
# ページ番号の表示対象とする拡張子
PAGE_NUMBER_TARGET_EXTENSION = ".pdf"
# 「パターン検索」モードの補足メッセージ
MAIN_DOCUMENT_MESSAGE = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
SUB_DOCUMENT_MESSAGE = "その他、ファイルありかの候補を提示します。"
# 「AI活用診断」モードの補足メッセージ
SOURCE_LIST_MESSAGE = "参考にした資料"


# ==========================================
# ログ出力系
# ==========================================
LOG_DIR_PATH = "./logs"
LOGGER_NAME = "ApplicationLog"
LOG_FILE = "application.log"
APP_BOOT_MESSAGE = "アプリが起動されました。"
# パターン無し診断で参照した資料名のログ出力書式（countはファイル数、chunksは合計チャンク数）
NO_PATTERN_SOURCES_LOG_FORMAT = "パターン無し診断で参照した資料（{count}件・チャンク{chunks}件）: {files}"


# ==========================================
# LLM設定系
# ==========================================
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.5


# ==========================================
# RAG設定系
# ==========================================
# ベクターストアから取得する関連ドキュメントの数
RETRIEVER_TOP_K = 5
# パターン無し経路＝枠組み層の検索で取得する関連ドキュメントの数
RETRIEVER_TOP_K_NO_PATTERN = 8
# Retrieverの検索方式（MMR＝重複の少ない多様な結果を選ぶ方式）
RETRIEVER_SEARCH_TYPE = "mmr"
# MMRの候補取得数。類似度上位からこの件数を候補にし、その中から重複の少ない k 件を選ぶ
RETRIEVER_FETCH_K = 20
# 埋め込み作成時に1回のリクエストで送るチャンク数
# （OpenAIの上限は1リクエスト30万トークン。データが増えても超えないよう小分けにする）
EMBEDDING_BATCH_SIZE = 200
# チャンク分割時の1チャンクあたりの文字数
CHUNK_SIZE = 500
# チャンク分割時に隣接チャンクと重複させる文字数
CHUNK_OVERLAP = 50
# チャンク分割時の区切り文字
CHUNK_SEPARATOR = "\n"


# ==========================================
# RAG参照用のデータソース系
# ==========================================
RAG_TOP_FOLDER_PATH = "./data"
SUPPORTED_EXTENSIONS = {
    ".pdf": PyMuPDFLoader,
    ".docx": Docx2txtLoader,
    ".csv": lambda path: CSVLoader(path, encoding="utf-8"),
    ".txt": lambda path: TextLoader(path, encoding="utf-8"),
    ".md": lambda path: TextLoader(path, encoding="utf-8")
}
WEB_URL_LOAD_TARGETS = []


# ==========================================
# パターン文書の読み込み系
# ==========================================
# パターン文書を格納しているフォルダ名（「RAG_TOP_FOLDER_PATH」の直下にある想定）
# ドキュメントのmetadataの「source」と同じ書式のパスになるよう、os.path.joinで連結して使う
PATTERN_FOLDER_NAME = "パターン"
# 対応パターンが無い場合の検索対象とするフォルダ名（「RAG_TOP_FOLDER_PATH」の直下にある想定）
FRAMEWORK_FOLDER_NAME = "枠組み"
# 対応パターンが無い場合の検索対象に加えるサービス文書（フォルダ名とファイル名）
SERVICE_FOLDER_NAME = "サービス"
SERVICE_FILE_NAME = "初期サービス案.md"
# 対応パターンが無い場合の検索対象に加える解決策文書のフォルダ名（「RAG_TOP_FOLDER_PATH」の直下にある想定）
SOLUTION_FOLDER_NAME = "解決策"
# 領域ごとの「考え方」ファイルの末尾（困りごとID別の解決策ファイルと区別するために使う）
SOLUTION_THINKING_FILE_SUFFIX = "_考え方.md"
# 調査文書・記事文書のフォルダ名（「RAG_TOP_FOLDER_PATH」の直下にある想定。追加質問のAgentが検索対象にする）
RESEARCH_FOLDER_NAME = "調査"
ARTICLE_FOLDER_NAME = "記事"
# パターン文書の先頭メタ行のキー
PATTERN_META_KEY_AREA = "領域:"
PATTERN_META_KEY_TROUBLE_IDS = "困りごとID:"
PATTERN_META_KEY_COMPANY = "向いている会社:"
PATTERN_META_KEY_MATERIALS = "材料:"
# 「根拠となる数字」欄に使う段落の先頭キー（本文中の「**商談での一言**: …」の行）
PATTERN_EVIDENCE_KEY = "**商談での一言**:"
# 複数パターンの「商談での一言」を連結するときの区切り（空行）
PATTERN_EVIDENCE_SEPARATOR = "\n\n"
# メタ行を読む行数の上限（先頭の数行だけを見る）
PATTERN_META_MAX_LINES = 10
# チャンク分割の対象外とするためのmetadataキー（メタ行が各チャンクに残るようにする）
NO_CHUNK_SPLIT_METADATA_KEY = "no_chunk_split"
# 業種文書を格納しているフォルダ名（「RAG_TOP_FOLDER_PATH」の直下にある想定）
INDUSTRY_FOLDER_NAME = "業種"
# 業種文書の先頭メタ行のキー
INDUSTRY_META_KEY_INDUSTRY = "業種:"


# ==========================================
# 追加質問のAgent（Tool）系
# ==========================================
# Agentが使うLLMの温度（毎回同じ選び方になるよう0にする。モデルは「MODEL」と共通）
AGENT_TEMPERATURE = 0
# Agentが道具を使い直す回数の上限（無限に考え続けないようにする）
AGENT_MAX_ITERATIONS = 3

# 追加質問で使う3つのToolの定義
# - name: Agentが選ぶときの道具の名前
# - description: どんな質問のときに使うかの説明（Agentはこの文だけを見て選ぶ）
# - folders: 検索対象とする「RAG_TOP_FOLDER_PATH」直下のフォルダ名のリスト
# ※ Toolオブジェクトを作らなくても中身を確認できるよう、ここに辞書のリストとして持つ
FOLLOW_UP_TOOL_NAME_SOLUTION = "御社に合う取り組みを詳しく説明する"
FOLLOW_UP_TOOL_NAME_EVIDENCE = "根拠となる調査や数字を答える"
FOLLOW_UP_TOOL_NAME_SERVICE = "AI Strategic Insight のサービスと相談方法を答える"
FOLLOW_UP_TOOLS = [
    {
        "name": FOLLOW_UP_TOOL_NAME_SOLUTION,
        "description": "診断で示した取り組みの進め方、必要な材料、手順、期間について聞かれたときに使う",
        "folders": [PATTERN_FOLDER_NAME, SOLUTION_FOLDER_NAME]
    },
    {
        "name": FOLLOW_UP_TOOL_NAME_EVIDENCE,
        "description": "数字の出典、調査の内容、他社や業界の状況について聞かれたときに使う",
        "folders": [RESEARCH_FOLDER_NAME, ARTICLE_FOLDER_NAME]
    },
    {
        "name": FOLLOW_UP_TOOL_NAME_SERVICE,
        "description": "料金、サービス内容、相談の仕方、依頼の流れについて聞かれたときに使う",
        "folders": [SERVICE_FOLDER_NAME]
    }
]

# 追加質問の先頭に付ける、直前の診断内容の前置き
# （取り組み名を取得できた場合と、取得できなかった場合の2本を用意する）
FOLLOW_UP_CONTEXT_FORMAT = "直前の診断の内容は次のとおりです。相談したい領域は{area}、業種は{industry}、従業員数は{employee}、いちばんの困りごとは『{trouble_text}』。示した取り組みは『{pattern_name}』。\nこの内容を踏まえて、次の質問に答えてください。{question}"
FOLLOW_UP_CONTEXT_FORMAT_NO_PATTERN = "直前の診断の内容は次のとおりです。相談したい領域は{area}、業種は{industry}、従業員数は{employee}、いちばんの困りごとは『{trouble_text}』。\nこの内容を踏まえて、次の質問に答えてください。{question}"

# Agentでの回答に失敗し、通常のRAG回答へ切り替えたときのログ文言
AGENT_FALLBACK_MESSAGE = "Agentでの回答取得に失敗したため、通常の検索による回答に切り替えました。"


# ==========================================
# プロンプトテンプレート
# ==========================================
SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT = "会話履歴と最新の入力をもとに、会話履歴なしでも理解できる独立した入力テキストを生成してください。"

SYSTEM_PROMPT_DOC_SEARCH = """
    あなたは社内の文書検索アシスタントです。
    以下の条件に基づき、ユーザー入力に対して回答してください。

    【条件】
    1. ユーザー入力内容と以下の文脈との間に関連性がある場合、空文字「""」を返してください。
    2. ユーザー入力内容と以下の文脈との関連性が明らかに低い場合、「該当資料なし」と回答してください。

    【文脈】
    {context}
"""

# 対応パターンが「ある」困りごとを選んだ場合の診断プロンプト
SYSTEM_PROMPT_DIAGNOSIS_WITH_PATTERN = """
    あなたは中小企業の経営者に向けて、AI活用の進め方を説明するアドバイザーです。
    以下の条件に基づき、ユーザーが入力した会社の状況に対して診断結果を作成してください。

    【条件】
    1. 相手は中小企業の経営者・採用担当です。専門用語（RAG、ベクター、LLM、エンベディング）を使わず、日常の言葉で書いてください。
    2. 診断結果は次の4つの内容を必ず埋めてください。
       - 該当パターン: 以下の文脈にあるパターン文書の見出しをそのまま書いてください。新しい名前を作らないでください
       - 御社の場合: 200〜300字で、次の順に書く。(1) 御社の規模・業種なら普通すでに持っているもの（文脈の資料が「材料」として挙げているもの）を1〜2つ具体名で、「〜があれば」と仮定形で示す。「社内にある材料」が選ばれていればその中のどれから始めるかを優先し、業種の資料（種別: 業種）が文脈にあれば、その資料の「すでにある材料」のうち相談領域（人事／集客・営業／顧客対応／業務効率化）に対応する欄のものを優先する。材料に口頭のものが選ばれた場合は、話を録音して文字にするところから書く。(2) 文脈の資料にある取り組みの型を1つ名指しし（例: よくある質問の整備、問い合わせ導線の見直し）、それをこの会社の材料でどう作るかを「〜を作れます」「〜から始められます」の可能形で書く。「戦略を作る」「改善する」のような抽象的な言い方で終わらせない。(3) それで日々の仕事がどう変わりそうかを1文、可能性の表現で書く。(4) 始める前に気をつける点を1文、文脈の資料にあるものだけ書く。御社の現状を説明する文（「〜の状況です」「〜に支障をきたしています」「〜が求められています」）は書かず、困りごとは入力で分かっているので言い換えない。「〜の効率化があれば」のように目的や結果を「〜があれば」に入れない。御社について分かっているのは、業種・従業員数・選んだ困りごと・選んだ材料・補足だけで、それ以外の状態を推測して断定しない。文書がある前提で「最近の〜を用意する」とは書かない
       - 根拠となる数字: 以下の文脈にある調査数値を1〜2個、出典名を添えて書く
       - 次の一歩: 150〜250字で、次の3点を含める。(1) 今週中にやる具体的な作業を1つ（何を、どこから集めるか）。(2) それを誰がやるか（経営者本人か、担当者か）。(3) 集めた結果の何を見て、次に進むか・相談するかを決めるか。文脈の資料にある取り組みの型に沿って書き、断定口調は避ける
    3. 続けて、次の4区分も必ず埋めてください。各項目は2〜3文で書いてください。
       - AIで改善できる部分
       - AIだけでは解決できない部分
       - 人の判断が必要な部分
       - 別の仕組み（RPA・API・CRM・電話システム）との連携が必要な部分
    4. 以下の文脈にあるパターンの内容だけを使い、憶測で新しい施策を作らないでください。
    9. 「〜する必要があります」「〜が重要です」「基盤が整います」で終わる文は書かないでください。
    5. 数値は以下の文脈にあるものだけを使い、出典名を添えてください。文脈に無い数値は書かないでください。文脈に数値が無い場合は「該当なし」とだけ書いてください。
    6. 「AIで解決できる」と断定しないでください。改善できる範囲と、できない範囲を必ず両方書いてください。
    7. 「次の一歩」には相談導線の文（「詳しくはご相談ください。」）を入れないでください。相談への案内は画面側で別に表示します。
    8. 「別の仕組みとの連携が必要な部分」に該当が無い場合は、「特にありません」と一言だけ書いてください。連携の提案を付け足さないでください。
    10. 断定口調を避ける。相手の話を聞かないと詳しい状況は分からないため、御社の状態・原因・効果について「〜です」「〜になります」「〜が必要です」と言い切らず、「〜の可能性があります」「〜が考えられます」「〜かもしれません」の形で書く。ただし、資料にある数値とその出典、および「何をするか」の手順（「〜から始められます」「〜を作れます」のような可能形）は明確に書いてよい。

    【文脈】
    {context}

    【出力形式】
    {format_instruction}
"""

# 対応パターンが「ない」困りごとを選んだ場合の診断プロンプト
SYSTEM_PROMPT_DIAGNOSIS_NO_PATTERN = """
    あなたは中小企業の経営者に向けて、AI活用の進め方を説明するアドバイザーです。
    以下の条件に基づき、ユーザーが入力した会社の状況に対して一般的な目安を作成してください。

    【条件】
    1. 相手は中小企業の経営者・採用担当です。専門用語（RAG、ベクター、LLM、エンベディング）を使わず、日常の言葉で書いてください。
    2. この困りごとには、まだ具体的なパターンが用意されていません。
    3. 診断結果は次の4つの内容を必ず埋めてください。
       - 該当パターン: 「該当なし」とだけ書いてください
       - 御社の場合: 200〜300字で、次の順に書く。(1) 御社の規模・業種なら普通すでに持っているもの（文脈の資料が「材料」として挙げているもの）を1〜2つ具体名で、「〜があれば」と仮定形で示す。「社内にある材料」が選ばれていればその中のどれから始めるかを優先し、業種の資料（種別: 業種）が文脈にあれば、その資料の「すでにある材料」のうち相談領域（人事／集客・営業／顧客対応／業務効率化）に対応する欄のものを優先する。材料に口頭のものが選ばれた場合は、話を録音して文字にするところから書く。(2) 文脈の資料にある取り組みの型を1つ名指しし（例: よくある質問の整備、問い合わせ導線の見直し）、それをこの会社の材料でどう作るかを「〜を作れます」「〜から始められます」の可能形で書く。「戦略を作る」「改善する」のような抽象的な言い方で終わらせない。(3) それで日々の仕事がどう変わりそうかを1文、可能性の表現で書く。(4) 始める前に気をつける点を1文、文脈の資料にあるものだけ書く。御社の現状を説明する文（「〜の状況です」「〜に支障をきたしています」「〜が求められています」）は書かず、困りごとは入力で分かっているので言い換えない。「〜の効率化があれば」のように目的や結果を「〜があれば」に入れない。御社について分かっているのは、業種・従業員数・選んだ困りごと・選んだ材料・補足だけで、それ以外の状態を推測して断定しない。文書がある前提で「最近の〜を用意する」とは書かない
       - 根拠となる数字: 「該当なし」とだけ書いてください
       - 次の一歩: 150〜250字で、次の3点を含める。(1) 今週中にやる具体的な作業を1つ（何を、どこから集めるか）。(2) それを誰がやるか（経営者本人か、担当者か）。(3) 集めた結果の何を見て、次に進むか・相談するかを決めるか。文脈の資料にある取り組みの型に沿って書き、断定口調は避ける
    4. 続けて、次の4区分も必ず埋めてください。各項目は2〜3文で書いてください。
       - AIで改善できる部分
       - AIだけでは解決できない部分
       - 人の判断が必要な部分
       - 別の仕組み（RPA・API・CRM・電話システム）との連携が必要な部分
    5. 「P1」のような番号付きのパターン名を作らないでください。パターンの名前を新しく考えないでください。
    11. 「〜する必要があります」「〜が重要です」「基盤が整います」で終わる文は書かないでください。
    6. 数値・割合・出典名を書かないでください。具体的な社名・導入事例も作らないでください。
    7. 「御社の場合」「次の一歩」と4区分は、以下の文脈にある枠組み（AIに向く仕事の見分け方、きっかけと動きの型、どこまで自動にするか、小さく始める進め方）に沿って、一般的な目安として書いてください。
    8. 「AIで解決できる」と断定しないでください。改善できる範囲と、できない範囲を必ず両方書いてください。
    9. 「次の一歩」には相談導線の文（「詳しくはご相談ください。」）を入れないでください。相談への案内は画面側で別に表示します。
    10. 「別の仕組みとの連携が必要な部分」に該当が無い場合は、「特にありません」と一言だけ書いてください。連携の提案を付け足さないでください。
    12. 断定口調を避ける。相手の話を聞かないと詳しい状況は分からないため、御社の状態・原因・効果について「〜です」「〜になります」「〜が必要です」と言い切らず、「〜の可能性があります」「〜が考えられます」「〜かもしれません」の形で書く。ただし、資料にある数値とその出典、および「何をするか」の手順（「〜から始められます」「〜を作れます」のような可能形）は明確に書いてよい。

    【文脈】
    {context}

    【出力形式】
    {format_instruction}
"""

# 診断後の追加質問に答えるためのプロンプト（4ブロック固定にはしない）
SYSTEM_PROMPT_FOLLOW_UP = """
    あなたは中小企業の経営者に向けて、AI活用の進め方を説明するアドバイザーです。
    以下の条件に基づき、直前の診断結果についての追加の質問に回答してください。

    【条件】
    1. 相手は中小企業の経営者・採用担当です。専門用語（RAG、ベクター、LLM、エンベディング）を使わず、日常の言葉で書いてください。
    2. 以下の文脈と会話履歴に基づいて回答してください。文脈に無い数値は書かないでください。
    3. 以下の文脈との関連性が明らかに低い場合は、「回答に必要な情報が見つかりませんでした。」と回答してください。
    4. マークダウン記法で回答し、見出しを使う場合は最も大きい見出しをh5としてください。
    5. 「AIで解決できる」と断定せず、できない範囲も添えてください。
    6. あなたは AI Strategic Insight の担当者として答える。第三者（サービス提供者・コンサルタント・専門家）に問い合わせるよう勧めない。資料に無いことは「詳しくはご相談ください」で締める。
    7. 複数の項目を挙げるときは、必ず改行して箇条書き（「- 」で始まる行）にする。「以下の〜」と書いた場合は、その直後に箇条書きを置く。一文の中に項目を並べない。
    8. 断定口調を避ける。相手の話を聞かないと詳しい状況は分からないため、御社の状態・原因・効果について「〜です」「〜になります」「〜が必要です」と言い切らず、「〜の可能性があります」「〜が考えられます」「〜かもしれません」の形で書く。ただし、資料にある数値とその出典、および「何をするか」の手順（「〜から始められます」「〜を作れます」のような可能形）は明確に書いてよい。

    【文脈】
    {context}
"""

# 診断時にLLMへ渡す検索文のフォーマット（設計書§4-2）
DIAGNOSIS_QUERY_FORMAT = "相談したい領域は{area}。業種は{industry}、従業員数は{employee}。いちばんの困りごとは『{trouble_text}』（困りごとID: {trouble_id}）。社内にある材料は{materials}。{note}"
# 「その他」の困りごとを選んだ場合の検索文フォーマット（領域名・困りごとIDは入れず、補足を先頭に置く）
DIAGNOSIS_QUERY_FORMAT_OTHER = "{note}。業種は{industry}、従業員数は{employee}。社内にある材料は{materials}。"
# 材料が1つも選ばれなかった場合の文言
DIAGNOSIS_QUERY_NO_MATERIAL = "未選択（文脈の資料が材料として挙げるもののうち、この業種で普通持っているものを想定する）"


# ==========================================
# Output Parserの属性説明
# ==========================================
PARSER_DESC_PATTERN_NAME = "該当パターンの名前と、向いている会社の1行"
PARSER_DESC_FOR_YOUR_COMPANY = "持っているはずの材料1〜2つ（仮定形）→その材料からAIで何を作る・直すか（可能形）→日々の仕事がどう変わりそうか1文→始める前に気をつける点1文、の順で書いた200〜300字の文章"
PARSER_DESC_EVIDENCE = "根拠となる調査数値と出典名。数値が無い場合はその旨"
PARSER_DESC_NEXT_STEP = "今週中にやる具体的な作業1つ（何を、どこから集めるか）・誰がやるか（経営者本人か担当者か）・集めた結果の何を見て次に進むか相談するかを決めるか、の3点を含む150〜250字の文章（相談への案内は含めない）"
PARSER_DESC_AI_CAN_IMPROVE = "AIで改善できる部分"
PARSER_DESC_AI_CANNOT_SOLVE = "AIだけでは解決できない部分"
PARSER_DESC_HUMAN_JUDGMENT = "人の判断が必要な部分"
PARSER_DESC_NEEDS_OTHER_SYSTEM = "別の仕組み（RPA・API・CRM・電話システム）との連携が必要な部分"


# ==========================================
# LLMレスポンスの一致判定用
# ==========================================
INQUIRY_NO_MATCH_ANSWER = "回答に必要な情報が見つかりませんでした。"
NO_DOC_MATCH_ANSWER = "該当資料なし"


# ==========================================
# エラー・警告メッセージ
# ==========================================
COMMON_ERROR_MESSAGE = "このエラーが繰り返し発生する場合は、管理者にお問い合わせください。"
INITIALIZE_ERROR_MESSAGE = "初期化処理に失敗しました。"
NO_DOC_MATCH_MESSAGE = """
    入力内容と関連する社内文書が見つかりませんでした。\n
    入力内容を変更してください。
"""
CONVERSATION_LOG_ERROR_MESSAGE = "過去の会話履歴の表示に失敗しました。"
GET_LLM_RESPONSE_ERROR_MESSAGE = "回答生成に失敗しました。"
DISP_ANSWER_ERROR_MESSAGE = "回答表示に失敗しました。"
PARSE_FALLBACK_MESSAGE = "診断結果を決まった形に整えられなかったため、生成された文章をそのまま表示します。"
# 「その他」を選んだのに補足が空のまま診断しようとした場合のエラー文言
OTHER_TROUBLE_NOTE_REQUIRED_MESSAGE = "「その他」を選んだ場合は、困りごとを補足欄に書いてください。"
