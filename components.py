"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import html
import streamlit as st
import utils
import constants as ct


############################################################
# 関数定義
############################################################

def apply_custom_style():
    """
    画面全体の装飾（CSS）を適用

    Cleanデザイン指針に沿ったトークン（constants.CUSTOM_CSS）を、画面の先頭で1回だけ読み込む。
    """
    st.markdown(ct.CUSTOM_CSS, unsafe_allow_html=True)


def display_app_title():
    """
    タイトル表示
    """
    st.markdown(f"## {ct.APP_NAME}")
    # タイトルの下に、アプリの説明を見出しの続きとして1文で表示
    st.markdown(
        f'<div class="shindan-lead"><p>{html.escape(ct.APP_CAPTION)}</p></div>',
        unsafe_allow_html=True
    )
    # タイトルとフォームの間に余白を置く
    st.write("")


def display_diagnosis_form():
    """
    メイン画面の上段に、診断の入力フォームを表示

    領域の選択だけはフォームの外（フォームの直前）に置き、その値で困りごとの選択肢を
    切り替えてからフォームを描画する。フォームの中の項目は送信ボタンを押すまで再実行が走らない。

    Returns:
        フォームの入力値をまとめた辞書
        - 「submitted」: 送信ボタンが押されたかどうか
        - 「area」「industry」「employee」「trouble_id」「trouble_text」「materials」「note」: 診断の入力値
    """
    form_input = {"submitted": False}

    with st.container(border=True):
        # ==========================================
        # 1. 相談したい領域（フォームの外に置き、選択で困りごとの選択肢を切り替える）
        # ==========================================
        st.markdown(f"##### {ct.SIDEBAR_SECTION_AREA}")
        st.caption(ct.SIDEBAR_SECTION_AREA_HELP)
        area_label = st.radio(
            label=ct.SIDEBAR_AREA_TITLE,
            options=ct.AREA_LABELS,
            horizontal=True,
            label_visibility="collapsed"
        )
        # 表示名から、困りごとの絞り込みに使う内部キーへ変換
        area_key = ct.AREA_LABEL_TO_KEY[area_label]

        # 選んだ領域の困りごと10件（ラベルは困りごとIDを除いた全文）
        trouble_options = ct.TROUBLE_OPTIONS[area_key]
        trouble_texts = []
        for trouble_id, trouble_text in trouble_options:
            trouble_texts.append(trouble_text)

        # ==========================================
        # 2〜5と送信ボタンはフォームの中（送信するまで再実行が走らない）
        # ==========================================
        with st.form(ct.DIAGNOSIS_FORM_KEY):
            # 2. 御社について（同じ行に、左: 業種のセレクトボックス、右: 従業員数のチップ5件）
            st.markdown(f"##### {ct.SIDEBAR_SECTION_COMPANY}")
            company_col1, company_col2 = st.columns([1, 2], gap="medium")
            with company_col1:
                industry = st.selectbox(
                    label=ct.SIDEBAR_INDUSTRY_TITLE,
                    options=ct.INDUSTRY_OPTIONS
                )
            with company_col2:
                # 5件を1行に収めるため、ラジオではなくチップ型（1つだけ選べる）にする
                employee = st.pills(
                    label=ct.SIDEBAR_EMPLOYEE_TITLE,
                    options=ct.EMPLOYEE_COUNT_OPTIONS,
                    default=ct.EMPLOYEE_COUNT_OPTIONS[0],
                    selection_mode="single"
                )
                # 選択を外された場合は先頭の選択肢に戻す（未選択のまま診断しない）
                if employee is None:
                    employee = ct.EMPLOYEE_COUNT_OPTIONS[0]

            st.write("")

            # 3. いちばんの困りごと（縦に10件。幅いっぱいの1列に置き、全文を1行で表示できるようにする）
            st.markdown(f"##### {ct.SIDEBAR_SECTION_TROUBLE}")
            st.caption(ct.SIDEBAR_SECTION_TROUBLE_HELP)
            trouble_col = st.columns([1])[0]
            with trouble_col:
                selected_trouble_text = st.radio(
                    label=ct.SIDEBAR_TROUBLE_TITLE,
                    options=trouble_texts,
                    label_visibility="collapsed"
                )

            st.write("")

            # 4. 社内にある材料（複数選択）
            st.markdown(f"##### {ct.SIDEBAR_SECTION_MATERIAL}")
            materials = st.multiselect(
                label=ct.SIDEBAR_MATERIAL_TITLE,
                options=ct.MATERIAL_OPTIONS,
                placeholder=ct.DIAGNOSIS_FORM_MATERIAL_PLACEHOLDER,
                label_visibility="collapsed"
            )

            st.write("")

            # 5. 補足（自由記述・任意）
            st.markdown(f"##### {ct.SIDEBAR_SECTION_NOTE}")
            st.caption(ct.SIDEBAR_SECTION_NOTE_HELP)
            note = st.text_input(
                label=ct.SIDEBAR_NOTE_TITLE,
                placeholder=ct.SIDEBAR_NOTE_PLACEHOLDER,
                label_visibility="collapsed",
                max_chars=200
            )

            st.write("")

            # 送信ボタン（強調色で、幅いっぱいに表示）
            form_input["submitted"] = st.form_submit_button(
                ct.DIAGNOSIS_FORM_SUBMIT_LABEL,
                type="primary",
                use_container_width=True
            )

    # 選ばれた困りごとの全文から、困りごとIDを引き当てる
    selected_trouble_id = ""
    for trouble_id, trouble_text in trouble_options:
        if trouble_text == selected_trouble_text:
            selected_trouble_id = trouble_id

    # 入力値を辞書へ格納
    form_input["area"] = area_label
    form_input["industry"] = industry
    form_input["employee"] = employee
    form_input["trouble_id"] = selected_trouble_id
    form_input["trouble_text"] = selected_trouble_text
    form_input["materials"] = materials
    form_input["note"] = note

    return form_input


def is_diagnosis_content(content):
    """
    会話ログのAIメッセージが、診断結果（4ブロックと4区分がある）かどうかの判定

    Args:
        content: 会話ログに格納したAIメッセージの辞書データ

    Returns:
        診断結果ならTrue、追加質問への回答やパターン検索の結果ならFalse
    """
    if content["mode"] != ct.ANSWER_MODE_1:
        return False
    return "result" in content or "raw_answer" in content


def has_diagnosis_result():
    """
    会話ログに診断結果が1件以上あるかどうかの判定

    Returns:
        診断結果があればTrue
    """
    for message in st.session_state.messages:
        if message["role"] == "assistant" and is_diagnosis_content(message["content"]):
            return True
    return False


def display_form_guide():
    """
    診断前だけ、フォームの下に案内文を表示（診断後は表示しない）
    """
    if has_diagnosis_result():
        return
    st.info(ct.DIAGNOSIS_FORM_GUIDE_MESSAGE)


def build_result_blocks():
    """
    会話ログを「診断結果1件＋その後の追加質問と回答」のまとまり（ブロック）に分ける

    Returns:
        ブロックのリスト（古い順）。各ブロックは会話ログのメッセージのリスト
    """
    blocks = []

    for message in st.session_state.messages:
        # 診断結果が来たら、新しいブロックを始める
        if message["role"] == "assistant" and is_diagnosis_content(message["content"]):
            blocks.append([message])
            continue

        # 診断前の追加質問など、まだブロックが無い場合は最初のブロックを作る
        if not blocks:
            blocks.append([])

        # 追加質問とその回答は、直前の診断結果のブロックに入れる
        blocks[-1].append(message)

    return blocks


def display_results():
    """
    メイン画面の下段に、診断結果と追加質問のやりとりを表示

    最新の診断結果を一番上に表示し、過去の診断はその下に残す（描画順は新しい順）。
    診断ごとの前に区切り線を入れる。
    """
    blocks = build_result_blocks()

    # 結果が1件も無い場合は何も表示しない（案内文は「display_form_guide」が出す）
    if not blocks:
        return

    # 結果セクションの見出し
    st.write("")
    st.markdown(f"### {ct.RESULT_SECTION_TITLE}")

    # 診断ボタンを押した直後の描画のときだけ、登場用の追加CSSを出す（次の再実行では出さない）
    show_entrance = st.session_state.get("just_diagnosed", False)
    if show_entrance:
        st.markdown(ct.ENTRANCE_CSS, unsafe_allow_html=True)

    # 新しい順に描画する（一番上が最新。過去の診断には何回目かのラベルを付ける）
    total = len(blocks)
    for index, block in enumerate(reversed(blocks)):
        # 診断の境目の区切り線
        st.divider()

        # 診断ごとのラベル（最新／過去のN回目）
        if index == 0:
            st.caption(ct.RESULT_BLOCK_LABEL_LATEST)
        else:
            st.caption(ct.RESULT_BLOCK_LABEL_PAST.format(number=total - index))

        for message in block:
            # 診断結果は吹き出し（chat_message）を使わず、通常の本文として表示する
            if message["role"] == "assistant" and is_diagnosis_content(message["content"]):
                # 最新ブロック（index==0）で、かつ診断直後の描画のときだけ登場アニメーションを付ける
                display_diagnosis_content(message["content"], is_latest=(index == 0 and show_entrance))
                continue

            # 追加質問とその回答は、従来どおり吹き出しで表示する
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.markdown(message["content"])
                else:
                    display_follow_up_content(message["content"])

    # 次の再実行（追加質問など）で登場アニメーションが再生されないよう、描画後にフラグを戻す
    if show_entrance:
        st.session_state.just_diagnosed = False


def display_consult_message():
    """
    相談導線の文言（ct.CONSULT_MESSAGE）を、画面全体で一番下に1回だけ表示

    診断結果が1件以上あるときだけ表示する（診断前は何も出さない）。表示する位置は
    「追加質問の欄」の直後・「資料検索（管理者用）」の直前で、診断ごとには出さない。
    """
    # 診断前は相談案内を出さない
    if not has_diagnosis_result():
        return
    st.info(ct.CONSULT_MESSAGE)


def display_follow_up_form():
    """
    診断結果の下に、追加質問の入力欄と送信ボタンを表示（回答の生成は行わない）

    診断結果が1件以上あるときだけ表示する（診断前は何も出さない）。送信後に入力欄を
    空へ戻すため、「st.form」の「clear_on_submit」を使う（描画済みの入力欄の値は
    同じ実行の中では書き換えられないため）。

    Returns:
        （送信ボタンが押されたかどうか, 入力された質問文）のタプル。
        欄を表示しない場合は（False, ""）を返す
    """
    # 診断前は追加質問の欄を出さない
    if not has_diagnosis_result():
        return False, ""

    # 結果と質問欄の間に余白を置く
    st.write("")

    # 送信のたびに入力欄を空へ戻すフォーム
    with st.form(key=ct.FOLLOW_UP_FORM_KEY, clear_on_submit=True):
        follow_up_text = st.text_input(
            label=ct.FOLLOW_UP_INPUT_LABEL,
            key=ct.FOLLOW_UP_INPUT_KEY,
            placeholder=ct.CHAT_INPUT_HELPER_TEXT
        )
        submitted = st.form_submit_button(ct.FOLLOW_UP_BUTTON_LABEL)

    return submitted, follow_up_text


def display_diagnosis_content(content, is_latest=False):
    """
    診断結果の表示

    Args:
        content: 診断結果を画面表示用に整形した辞書データ
        is_latest: 診断ボタンを押した直後に描く最新ブロックかどうか
            （Trueのときだけ、各面に登場アニメーション用のクラス「shindan-enter」を付ける）

    相談導線（st.info(ct.CONSULT_MESSAGE)）はここでは表示しない。画面全体で一番下に1回だけ
    表示する（「display_consult_message」を参照）。
    """
    # 入力内容の1行要約を表示
    st.caption(content["input_summary"])

    # 対応パターンが無い困りごとの場合、冒頭に注意文を表示
    if not content["has_pattern"]:
        st.warning(ct.NO_PATTERN_NOTICE_MESSAGE, icon=ct.WARNING_ICON)

    # 登場アニメーションの遅延（面ごとに60ms）を数えるカウンター
    entrance_state = {"panel_count": 0}

    def next_entrance_attrs():
        """
        「is_latest」のときだけ、次の面に付ける登場用のクラスと遅延スタイルを組み立てる

        Returns:
            (extra_class, style_attr) のタプル（is_latestがFalseの場合は両方空文字）
        """
        if not is_latest:
            return "", ""
        delay_ms = entrance_state["panel_count"] * 60
        entrance_state["panel_count"] += 1
        return "shindan-enter", f' style="animation-delay: {delay_ms}ms;"'

    # 診断結果を決まった形に変換できた場合、4ブロックと4区分をカードで表示
    if "result" in content:
        result = content["result"]

        # 4ブロック（該当パターン／御社の場合／根拠となる数字／次の一歩）
        # 容れ物は2種類だけ: 「該当パターン」は紺の面（この画面で唯一の大胆な面）、それ以外は罫線で区切った白い面
        # パターン無し（has_patternがFalse）の場合は、「該当パターン」の紺ブロックと
        # 「根拠となる数字」ブロックを表示しない（一般的な目安であり、根拠となる数字を確定できないため）
        if content["has_pattern"]:
            extra_class, style_attr = next_entrance_attrs()
            st.markdown(build_hero_html(result["pattern_name"], extra_class, style_attr), unsafe_allow_html=True)

        extra_class, style_attr = next_entrance_attrs()
        st.markdown(
            build_block_html(
                "", ct.DIAGNOSIS_HEADING_FOR_YOUR_COMPANY, result["for_your_company"], extra_class, style_attr
            ),
            unsafe_allow_html=True
        )
        if content["has_pattern"]:
            extra_class, style_attr = next_entrance_attrs()
            st.markdown(
                build_block_html("", ct.DIAGNOSIS_HEADING_EVIDENCE, result["evidence"], extra_class, style_attr),
                unsafe_allow_html=True
            )
        # 「次の一歩」は面は同じで、見出しの色（琥珀）だけで区別する
        extra_class, style_attr = next_entrance_attrs()
        st.markdown(
            build_block_html(
                "shindan-next", ct.DIAGNOSIS_HEADING_NEXT_STEP, result["next_step"], extra_class, style_attr
            ),
            unsafe_allow_html=True
        )

        # 4区分は同じ大きさの箱を並べず、区分名と本文の2列の表にする
        extra_class, style_attr = next_entrance_attrs()
        st.markdown(build_quad_list_html(result, extra_class, style_attr), unsafe_allow_html=True)

    # 決まった形に変換できなかった場合、生成された文章をそのまま表示
    else:
        st.warning(ct.PARSE_FALLBACK_MESSAGE, icon=ct.WARNING_ICON)
        st.markdown(content["raw_answer"])


def to_html_text(text):
    """
    表示用の文字列をHTMLに安全に埋め込める形へ変換（記号のエスケープと改行の変換）

    Args:
        text: 表示用の文字列

    Returns:
        エスケープ済みで、改行を<br>にした文字列
    """
    return html.escape(text).replace("\n\n", "<br><br>").replace("\n", "<br>")


def build_hero_html(pattern_name, extra_class="", style_attr=""):
    """
    「該当パターン」の紺パネルのHTMLを組み立てる

    パターン名は「見出し（向いている会社: …）」の形で複数行になることがあるため、
    1件ずつ「見出し」と「向いている会社」に分けて表示する。

    Args:
        pattern_name: 「該当パターン」欄の文字列（複数ある場合は空行区切り）
        extra_class: 面に追加するCSSクラス名（登場アニメーション用の「shindan-enter」など。通常は空文字）
        style_attr: 面に追加するstyle属性（先頭に半角空白付きの ' style="…"' の形。通常は空文字）

    Returns:
        HTML文字列
    """
    # 「（向いている会社: 」より前を見出し、後ろを向いている会社として分ける
    separator = ct.PATTERN_NAME_FORMAT.split("{title}")[1].split("{company}")[0]
    suffix = ct.PATTERN_NAME_FORMAT.split("{company}")[1]

    title_html_list = []
    for line in pattern_name.split("\n\n"):
        if separator in line:
            title, company = line.split(separator, 1)
            if company.endswith(suffix):
                company = company[:-len(suffix)]
            title_html_list.append(
                f'<p class="shindan-hero-title">{html.escape(title)}'
                f'<span class="shindan-hero-company">向いている会社: {html.escape(company)}</span></p>'
            )
        else:
            title_html_list.append(f'<p class="shindan-hero-title">{html.escape(line)}</p>')

    return (
        f'<div class="shindan-panel shindan-hero {extra_class}"{style_attr}>'
        f'<p class="shindan-block-title">{html.escape(ct.DIAGNOSIS_HEADING_PATTERN_NAME)}</p>'
        + "".join(title_html_list) +
        '</div>'
    )


def build_block_html(css_class, title, body, extra_class="", style_attr=""):
    """
    見出しと本文だけの面（「御社の場合」「根拠となる数字」「次の一歩」）のHTMLを組み立てる

    Args:
        css_class: 面の種類を表すCSSクラス名の追加分（空文字、または shindan-next）
        title: 見出し
        body: 本文
        extra_class: 面に追加するCSSクラス名（登場アニメーション用の「shindan-enter」など。通常は空文字）
        style_attr: 面に追加するstyle属性（先頭に半角空白付きの ' style="…"' の形。通常は空文字）

    Returns:
        HTML文字列
    """
    return (
        f'<div class="shindan-panel {css_class} {extra_class}"{style_attr}>'
        f'<p class="shindan-block-title">{html.escape(title)}</p>'
        f'<p class="shindan-block-body">{to_html_text(body)}</p>'
        '</div>'
    )


def build_quad_list_html(result, extra_class="", style_attr=""):
    """
    4区分（AIで改善できる部分／AIだけでは解決できない部分／人の判断が必要な部分／別の仕組みとの連携が必要な部分）を、
    区分名と本文の2列の表として組み立てる（同じ大きさの箱を並べず、高さは中身に従う）

    Args:
        result: 診断結果の8項目を格納した辞書
        extra_class: 面に追加するCSSクラス名（登場アニメーション用の「shindan-enter」など。通常は空文字）
        style_attr: 面に追加するstyle属性（先頭に半角空白付きの ' style="…"' の形。通常は空文字）

    Returns:
        HTML文字列
    """
    rows = [
        (ct.DIAGNOSIS_HEADING_AI_CAN_IMPROVE, result["ai_can_improve"]),
        (ct.DIAGNOSIS_HEADING_AI_CANNOT_SOLVE, result["ai_cannot_solve"]),
        (ct.DIAGNOSIS_HEADING_HUMAN_JUDGMENT, result["human_judgment"])
    ]

    # 「別の仕組みとの連携が必要な部分」は、中身が「特にありません」のときだけ行そのものを出さない
    # （前後の空白と末尾の句点を取り除いてから比べる。他の3区分は中身にかかわらず必ず出す）
    needs_other_system = result["needs_other_system"]
    if needs_other_system.strip().rstrip("。") != ct.NEEDS_OTHER_SYSTEM_NONE_TEXT:
        rows.append((ct.DIAGNOSIS_HEADING_NEEDS_OTHER_SYSTEM, needs_other_system))
    row_html_list = []
    for title, body in rows:
        row_html_list.append(
            '<div class="shindan-quad-row">'
            f'<p class="shindan-block-title">{html.escape(title)}</p>'
            f'<p class="shindan-block-body">{to_html_text(body)}</p>'
            '</div>'
        )
    return (
        f'<div class="shindan-panel {extra_class}"{style_attr}><div class="shindan-quad-list">'
        + "".join(row_html_list) +
        '</div></div>'
    )


def build_progress_html():
    """
    診断中（st.spinnerの代わり）に表示する、3段階の進み具合のHTMLを組み立てる

    見た目は結果の白い面（shindan-panel）と同じ。3行を縦に並べ、CSSアニメーション
    （constants.pyのCUSTOM_CSS内で定義）で、時間の目安に応じて紺の丸＋濃い文字に切り替わる。

    Returns:
        HTML文字列
    """
    step_html_list = []
    for step_number, step_text in enumerate(ct.DIAGNOSIS_PROGRESS_STEPS, start=1):
        step_html_list.append(
            f'<div class="shindan-progress-step" data-step="{step_number}">'
            '<span class="shindan-progress-dot"></span>'
            f'<span class="shindan-progress-text">{html.escape(step_text)}</span>'
            '</div>'
        )

    return (
        '<div class="shindan-panel">'
        + "".join(step_html_list)
        + f'<p class="shindan-progress-note">{html.escape(ct.DIAGNOSIS_PROGRESS_NOTE)}</p>'
        + '</div>'
    )


def build_input_summary(form_input):
    """
    診断結果の先頭に出す、入力内容の1行要約を組み立てる

    例: 「人事 ／ 製造 ／ 〜10名 ／ 求人を出しても応募がなかなか集まらない ／ 材料: 会社案内パンフ、経営者の話」

    Args:
        form_input: フォームの入力値をまとめた辞書

    Returns:
        1行要約の文字列
    """
    # 領域は表示名（「人事（採用・教育・定着）」）ではなく短い内部キー（「人事」）を使う
    area_key = ct.AREA_LABEL_TO_KEY[form_input["area"]]

    # 材料は「（口頭のみ）」の注記を取り除いて並べる。未選択の場合は「特になし」
    material_names = []
    for material in form_input["materials"]:
        material_names.append(material.replace(ct.DIAGNOSIS_INPUT_SUMMARY_MATERIAL_TRIM, ""))
    if material_names:
        materials_text = "、".join(material_names)
    else:
        materials_text = ct.DIAGNOSIS_INPUT_SUMMARY_NO_MATERIAL

    note = form_input["note"]

    # 「その他」が選ばれている場合、困りごとの位置にはラベルではなく補足の内容を入れ、
    # 末尾に重複する「補足: 」は付けない
    if utils.is_other_trouble(form_input["trouble_id"]):
        trouble_text = note.strip() if note else note
    else:
        trouble_text = form_input["trouble_text"]

    summary_items = [
        area_key,
        form_input["industry"],
        form_input["employee"],
        trouble_text,
        f"{ct.DIAGNOSIS_INPUT_SUMMARY_MATERIAL_PREFIX}{materials_text}"
    ]

    # 「その他」以外で、補足が入力されている場合だけ、末尾に加える
    if not utils.is_other_trouble(form_input["trouble_id"]) and note and note.strip():
        summary_items.append(f"{ct.DIAGNOSIS_INPUT_SUMMARY_NOTE_PREFIX}{note.strip()}")

    return ct.DIAGNOSIS_INPUT_SUMMARY_SEPARATOR.join(summary_items)


def build_diagnosis_content(llm_response, form_input, has_pattern, pattern_list, question_answer_template, format_instruction, chat_message):
    """
    「AI活用診断」のLLMレスポンスを、画面表示用の辞書データに整形する（画面表示は行わない）

    表示は「display_results」が会話ログから行う（最新の診断結果を一番上に出すため）。

    Args:
        llm_response: LLMからの回答
        form_input: フォームの入力値をまとめた辞書
        has_pattern: 対応パターンがあるかどうか
        pattern_list: 困りごとIDに紐づくパターン文書の情報リスト
        question_answer_template: 回答生成に使ったシステムプロンプト
        format_instruction: Output Parserのフォーマット命令
        chat_message: LLMへ渡した検索文

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    # 表示用の会話ログに格納するためのデータを用意
    content = {}
    content["mode"] = ct.ANSWER_MODE_1
    content["has_pattern"] = has_pattern
    content["area"] = form_input["area"]
    content["industry"] = form_input["industry"]
    content["employee"] = form_input["employee"]
    content["trouble_id"] = form_input["trouble_id"]
    content["trouble_text"] = form_input["trouble_text"]
    content["materials"] = form_input["materials"]
    content["note"] = form_input["note"]
    content["input_summary"] = build_input_summary(form_input)

    # LLMの回答文字列を、診断結果の型へ変換（失敗した場合はNoneが返る）
    result = utils.parse_diagnosis_result(
        llm_response["answer"], question_answer_template, format_instruction, chat_message
    )
    # 「該当パターン」欄と「根拠となる数字」欄は、LLMの生成文ではなくコードで確定させた内容にする
    # （会話ログからの再描画でも同じ表示になるよう、上書き後の値をcontentへ入れる）
    result = utils.overwrite_fixed_fields(result, has_pattern, pattern_list)

    if result:
        content["result"] = result
    else:
        # 変換できなかった場合は、生成された文章をそのまま表示するためのデータを持つ
        content["raw_answer"] = llm_response["answer"]

    # 参考にした資料の一覧（画面には表示せず、ログ出力用に保持する）
    content["file_info_list"] = utils.build_file_info_list(llm_response)

    return content


def display_follow_up_content(content):
    """
    診断後の追加質問への回答の表示

    Args:
        content: 追加質問への回答を画面表示用に整形した辞書データ
    """
    # LLMからの回答を表示（参考にした資料の一覧は表示しない）
    st.markdown(content["answer"])


def get_latest_diagnosis_content():
    """
    会話ログの中から、いちばん新しい診断結果を取得

    Returns:
        診断結果の辞書データ（診断がまだ1件も無い場合はNone）
    """
    # 新しいものから順に見て、最初に見つかった診断結果を返す
    for message in reversed(st.session_state.messages):
        if message["role"] == "assistant" and is_diagnosis_content(message["content"]):
            return message["content"]

    return None


def build_follow_up_question(chat_message):
    """
    直前の診断内容の前置きを、追加質問の先頭に付けた質問文を組み立てる

    Agentは会話履歴を見ずに道具を選ぶため、どの会社の何についての質問かを
    質問文そのものに書いておく。診断がまだ無い場合は、質問文だけをそのまま返す。

    Args:
        chat_message: 利用者が入力した追加質問の文

    Returns:
        前置きを付けた質問文（診断がまだ無い場合は入力された質問文のまま）
    """
    # いちばん新しい診断結果を取得（診断前に質問された場合はNoneが返る）
    content = get_latest_diagnosis_content()
    if not content:
        return chat_message

    # 決まった形に変換できた診断だけ、取り組み名（「該当パターン」欄）を前置きに入れる
    # （変換に失敗した診断は「raw_answer」しか持たないため、取り組み名なしの前置きにする）
    if "result" in content:
        return ct.FOLLOW_UP_CONTEXT_FORMAT.format(
            area=content["area"],
            industry=content["industry"],
            employee=content["employee"],
            trouble_text=content["trouble_text"],
            pattern_name=content["result"]["pattern_name"],
            question=chat_message
        )

    return ct.FOLLOW_UP_CONTEXT_FORMAT_NO_PATTERN.format(
        area=content["area"],
        industry=content["industry"],
        employee=content["employee"],
        trouble_text=content["trouble_text"],
        question=chat_message
    )


def build_follow_up_content(llm_response):
    """
    診断後の追加質問に対する回答を、画面表示用の辞書データに整形する（画面表示は行わない）

    Agentからの回答は文字列で返るため、文字列と、通常のRAG回答の辞書の
    どちらを渡されても同じ形の辞書を作る。

    Args:
        llm_response: Agentからの回答の文字列、または通常のRAG回答（辞書）

    Returns:
        回答を画面表示用に整形した辞書データ
    """
    # 表示用の会話ログに格納するためのデータを用意
    content = {}
    content["mode"] = ct.ANSWER_MODE_1

    # Agentからの回答（文字列）の場合、参照元の一覧は取得できないため空にする
    if isinstance(llm_response, str):
        content["answer"] = llm_response
        content["file_info_list"] = []
        return content

    content["answer"] = llm_response["answer"]

    # 参考にした資料の一覧はログ出力用に保持する（回答に必要な情報が見つからなかった場合は空にする）
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        content["file_info_list"] = utils.build_file_info_list(llm_response)
    else:
        content["file_info_list"] = []

    return content


def display_doc_search_expander(logger):
    """
    画面最下部に、資料検索（管理者用）の折りたたみ欄を表示

    検索用の入力欄と実行ボタンを置き、結果（資料のありか一覧）も同じ欄の中に表示する。
    直近の検索結果はセッションに保持し、再実行時も同じ欄に表示し続ける。

    Args:
        logger: ログ出力用のロガー
    """
    with st.expander(ct.DOC_SEARCH_EXPANDER_TITLE):
        search_text = st.text_input(
            label=ct.DOC_SEARCH_INPUT_LABEL,
            placeholder=ct.DOC_SEARCH_INPUT_PLACEHOLDER
        )
        search_button = st.button(ct.DOC_SEARCH_BUTTON_LABEL)

        # ボタンが押され、かつ検索文が入力されている場合だけ検索を実行する
        if search_button and search_text.strip():
            # ユーザー入力値のログ出力
            logger.info({"message": search_text, "application_mode": ct.ANSWER_MODE_2})

            # LLMによる回答生成（回答生成が完了するまでグルグル回す）
            with st.spinner(ct.SPINNER_TEXT):
                try:
                    # 画面読み込み時に作成したRetrieverを使い、Chainを実行
                    llm_response = utils.get_llm_response(search_text, ct.SYSTEM_PROMPT_DOC_SEARCH)
                except Exception as e:
                    # エラーログの出力
                    logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
                    # エラーメッセージの画面表示
                    st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
                    # 後続の処理を中断
                    st.stop()

            try:
                # 入力内容と関連性が高い資料のありかを表示し、表示用のデータをセッションに保持する
                st.session_state.doc_search_result = display_search_llm_response(llm_response)
                # AIメッセージのログ出力
                logger.info({"message": st.session_state.doc_search_result, "application_mode": ct.ANSWER_MODE_2})
            except Exception as e:
                # エラーログの出力
                logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
                # エラーメッセージの画面表示
                st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
                # 後続の処理を中断
                st.stop()

        # ボタンが押されていない画面更新では、直近の検索結果をそのまま表示する
        elif "doc_search_result" in st.session_state:
            display_search_content(st.session_state.doc_search_result)


def display_search_content(content):
    """
    資料検索の結果（資料のありか一覧）を、保持しているデータから表示

    Args:
        content: 資料検索の結果を画面表示用に整形した辞書データ
    """
    # ファイルのありかの情報が取得できた場合（通常時）の表示処理
    if not "no_file_path_flg" in content:
        # ==========================================
        # ユーザー入力値と最も関連性が高いメインドキュメントのありかを表示
        # ==========================================
        # 補足文の表示
        st.markdown(content["main_message"])

        # 参照元のありかに応じて、適したアイコンを取得
        icon = utils.get_source_icon(content['main_file_path'])
        # 「メインドキュメントのファイル名」（PDFの場合はページ番号付き）を表示
        st.success(content["main_file_info"], icon=icon)

        # ==========================================
        # ユーザー入力値と関連性が高いサブドキュメントのありかを表示
        # ==========================================
        if "sub_message" in content:
            # 補足メッセージの表示
            st.markdown(content["sub_message"])

            # サブドキュメントのありかを一覧表示
            for sub_choice in content["sub_choices"]:
                # 参照元のありかに応じて、適したアイコンを取得
                icon = utils.get_source_icon(sub_choice['source'])
                # 「サブドキュメントのファイル名」（PDFの場合はページ番号付き）を表示
                st.info(sub_choice["file_info"], icon=icon)
    # ファイルのありかの情報が取得できなかった場合、LLMからの回答のみ表示
    else:
        st.markdown(content["answer"])


def display_search_llm_response(llm_response):
    """
    資料検索（旧「パターン検索」モード）におけるLLMレスポンスを表示

    Args:
        llm_response: LLMからの回答

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    # LLMからのレスポンスに参照元情報が入っており、かつ「該当資料なし」が回答として返された場合
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:

        # ==========================================
        # ユーザー入力値と最も関連性が高いメインドキュメントのありかを表示
        # ==========================================
        # LLMからのレスポンス（辞書）の「context」属性の中の「0」に、最も関連性が高いドキュメント情報が入っている
        main_file_path = llm_response["context"][0].metadata["source"]
        # 画面表示用のテキストを作成（PDFの場合は「（ページNo.N）」が付く）
        main_file_info = utils.build_file_info(llm_response["context"][0])

        # 補足メッセージの表示
        main_message = ct.MAIN_DOCUMENT_MESSAGE
        st.markdown(main_message)

        # 参照元のありかに応じて、適したアイコンを取得
        icon = utils.get_source_icon(main_file_path)
        # 「メインドキュメントのファイル名」（PDFの場合はページ番号付き）を表示
        st.success(main_file_info, icon=icon)

        # ==========================================
        # ユーザー入力値と関連性が高いサブドキュメントのありかを表示
        # ==========================================
        # メインドキュメント以外で、関連性が高いサブドキュメントを格納する用のリストを用意
        sub_choices = []
        # 重複チェック用のリストを用意
        duplicate_check_list = []

        # ドキュメントが2件以上検索できた場合（サブドキュメントが存在する場合）のみ、サブドキュメントのありかを一覧表示
        for document in llm_response["context"][1:]:
            # ドキュメントのファイルパスを取得
            sub_file_path = document.metadata["source"]
            # 画面表示用のテキストを作成（PDFの場合は「（ページNo.N）」が付く）
            sub_file_info = utils.build_file_info(document)

            # メインドキュメントのファイルパスと重複している場合、処理をスキップ（表示しない）
            if sub_file_path == main_file_path:
                continue

            # 同じファイル内の異なる箇所を参照した場合、2件目以降のファイルパスに重複が発生する可能性があるため、重複を除去
            if sub_file_path in duplicate_check_list:
                continue

            # 重複チェック用のリストにファイルパスを順次追加
            duplicate_check_list.append(sub_file_path)

            # 「サブドキュメントのファイルパス」と「画面表示用のテキスト」の辞書を作成
            sub_choice = {"source": sub_file_path, "file_info": sub_file_info}

            # 後ほど一覧表示するため、サブドキュメントに関する情報を順次リストに追加
            sub_choices.append(sub_choice)

        # サブドキュメントが存在する場合のみの処理
        if sub_choices:
            # 補足メッセージの表示
            sub_message = ct.SUB_DOCUMENT_MESSAGE
            st.markdown(sub_message)

            # サブドキュメントに対してのループ処理
            for sub_choice in sub_choices:
                # 参照元のありかに応じて、適したアイコンを取得
                icon = utils.get_source_icon(sub_choice['source'])
                # 「サブドキュメントのファイル名」（PDFの場合はページ番号付き）を表示
                st.info(sub_choice["file_info"], icon=icon)

        # 表示用のデータを用意
        content = {}
        content["mode"] = ct.ANSWER_MODE_2
        content["main_message"] = main_message
        content["main_file_path"] = main_file_path
        content["main_file_info"] = main_file_info
        # サブドキュメントの情報は、取得できた場合にのみ追加
        if sub_choices:
            content["sub_message"] = sub_message
            content["sub_choices"] = sub_choices

    # LLMからのレスポンスに、ユーザー入力値と関連性の高いドキュメント情報が入って「いない」場合
    else:
        # 関連ドキュメントが取得できなかった場合のメッセージ表示
        st.markdown(ct.NO_DOC_MATCH_MESSAGE)

        # 表示用のデータを用意
        content = {}
        content["mode"] = ct.ANSWER_MODE_2
        content["answer"] = ct.NO_DOC_MATCH_MESSAGE
        content["no_file_path_flg"] = True

    return content
