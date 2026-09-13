"""
このファイルは、Webアプリのメイン処理が記述されたファイルです。
"""

############################################################
# 1. ライブラリの読み込み
############################################################
# 「.env」ファイルから環境変数を読み込むための関数
from dotenv import load_dotenv
# ログ出力を行うためのモジュール
import logging
# streamlitアプリの表示を担当するモジュール
import streamlit as st
# （自作）画面表示以外の様々な関数が定義されているモジュール
import utils
# （自作）アプリ起動時に実行される初期化処理が記述された関数
from initialize import initialize
# （自作）画面表示系の関数が定義されているモジュール
import components as cn
# （自作）変数（定数）がまとめて定義・管理されているモジュール
import constants as ct


############################################################
# 2. 設定関連
############################################################
# ブラウザタブの表示文言と、画面の横幅（wide）を設定
st.set_page_config(
    page_title=ct.APP_NAME,
    layout="wide"
)

# ログ出力を行うためのロガーの設定
logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# 3. 初期化処理
############################################################
try:
    # 初期化処理（「initialize.py」の「initialize」関数を実行）
    initialize()
except Exception as e:
    # エラーログの出力
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    # エラーメッセージの画面表示
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    # 後続の処理を中断
    st.stop()

# アプリ起動時のログファイルへの出力
if not "initialized" in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)

# 利用モード（v2ではモード切替を廃止し、メイン画面は常に「AI活用診断」。ログ出力用に保持する）
st.session_state.mode = ct.ANSWER_MODE_1


############################################################
# 4. 初期表示（タイトルと、上段の入力フォーム）
############################################################
# 画面全体の装飾（CSS）を適用
cn.apply_custom_style()

# タイトル表示
cn.display_app_title()

# 入力フォームを表示（送信ボタンが押されたかどうかと入力値を受け取る）
form_input = cn.display_diagnosis_form()


############################################################
# 5. 「この内容で診断する」ボタンが押された場合の処理
############################################################
if form_input["submitted"]:
    # 「その他」を選んだのに補足が空のまま診断しようとした場合は、ここで止める
    # （検索文を組み立てる前に判定する。この判定より後ろ（5-1〜5-3）は変えない）
    if utils.is_other_trouble_without_note(form_input["trouble_id"], form_input["note"]):
        st.error(ct.OTHER_TROUBLE_NOTE_REQUIRED_MESSAGE, icon=ct.ERROR_ICON)
        st.stop()

    # 前回の診断や追加質問の内容が今回の診断に混ざらないようにする。診断後の追加質問は、この診断からの履歴を使う
    st.session_state.chat_history = []

    # ==========================================
    # 5-1. 検索文の組み立てと、対応パターンの有無の判定
    # ==========================================
    # フォームの入力値から、Retrieverへ渡す検索文を組み立てる
    diagnosis_query = utils.build_diagnosis_query(
        form_input["area"],
        form_input["industry"],
        form_input["employee"],
        form_input["trouble_id"],
        form_input["trouble_text"],
        form_input["materials"],
        form_input["note"]
    )

    # 選ばれた困りごとIDに紐づくパターン文書の一覧を取得
    pattern_list = utils.get_pattern_list(form_input["trouble_id"])
    # 対応パターンがあるかどうかの判定
    has_pattern = len(pattern_list) > 0

    # ユーザー入力値のログ出力
    logger.info({"message": diagnosis_query, "application_mode": st.session_state.mode})

    # ==========================================
    # 5-2. LLMからの回答取得
    # ==========================================
    # 対応パターンの有無で、使用するプロンプトと検索対象を変える
    if has_pattern:
        # 対応パターンありのプロンプトを使う
        question_answer_template = ct.SYSTEM_PROMPT_DIAGNOSIS_WITH_PATTERN
        # 別の困りごとのパターンが混ざらないよう、紐づくパターン文書だけを検索対象にする
        filter_sources = []
        for pattern_info in pattern_list:
            filter_sources.append(pattern_info["file"])
    else:
        # 対応パターンなしのプロンプトを使う
        question_answer_template = ct.SYSTEM_PROMPT_DIAGNOSIS_NO_PATTERN
        # 「その他」の場合は枠組み＋サービスを、それ以外は枠組み層だけを検索対象にする
        # （プロンプト・取得件数はどちらも同じ）
        # セッションに保持しているリストの参照そのものになるため、コピーしてから使う
        # （そのままappendすると、次回以降の診断で業種文書が積み上がってしまう）
        if utils.is_other_trouble(form_input["trouble_id"]):
            filter_sources = list(st.session_state.other_trouble_sources)
        else:
            filter_sources = list(st.session_state.framework_sources)

    # 業種に対応する業種文書があれば、検索対象へ追加する
    # （業種「その他」や該当ファイルなしの場合は何もしない）
    industry_file = st.session_state.industry_index.get(form_input["industry"])
    if industry_file:
        filter_sources.append(industry_file)

    # Output Parserのフォーマット命令を作成し、プロンプトへ埋め込む
    format_instruction = utils.get_diagnosis_parser().get_format_instructions()

    # 診断中だけは「st.spinner」の代わりに、3段階の進み具合をこの空のエリアへ表示する
    # （時間はサーバーの処理と連動しない目安。LLM呼び出しが終わったら空に戻す）
    res_box = st.empty()
    res_box.markdown(cn.build_progress_html(), unsafe_allow_html=True)
    try:
        # 画面読み込み時に作成したベクターストアを使い、Chainを実行
        # （対応パターン無し＝枠組み層の検索だけ、取得件数を広めにする）
        if has_pattern:
            llm_response = utils.get_llm_response(
                diagnosis_query,
                question_answer_template,
                format_instruction=format_instruction,
                filter_sources=filter_sources
            )
        else:
            llm_response = utils.get_llm_response(
                diagnosis_query,
                question_answer_template,
                format_instruction=format_instruction,
                filter_sources=filter_sources,
                top_k=ct.RETRIEVER_TOP_K_NO_PATTERN
            )
    except Exception as e:
        # エラーログの出力
        logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
        # エラーメッセージの画面表示
        st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
        # 後続の処理を中断
        st.stop()
    # 進み具合の表示を消す
    res_box.empty()

    # 対応パターン無しの診断でだけ、参照した資料名とチャンク数をログに出す（画面には出さない。「その他」も同じログ）
    if not has_pattern:
        source_chunk_counts = utils.build_source_chunk_counts(llm_response)
        no_pattern_sources_text = "、".join(
            f"{file_info}（{count}）" for file_info, count in source_chunk_counts
        )
        logger.info(ct.NO_PATTERN_SOURCES_LOG_FORMAT.format(
            count=len(source_chunk_counts),
            chunks=sum(count for _, count in source_chunk_counts),
            files=no_pattern_sources_text
        ))

    # ==========================================
    # 5-3. 診断結果の整形と、会話ログへの追加
    # ==========================================
    # 表示は「6. 結果の表示」で会話ログからまとめて行う（最新の診断結果を一番上に出すため）
    try:
        # 入力内容の1行要約、4ブロックと4区分を画面表示用のデータに整形
        content = cn.build_diagnosis_content(
            llm_response,
            form_input,
            has_pattern,
            pattern_list,
            question_answer_template,
            format_instruction,
            diagnosis_query
        )

        # AIメッセージのログ出力
        logger.info({"message": content, "application_mode": st.session_state.mode})
    except Exception as e:
        # エラーログの出力
        logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
        # エラーメッセージの画面表示
        st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
        # 後続の処理を中断
        st.stop()

    # 表示用の会話ログにAIメッセージを追加
    # （ユーザー入力値の復唱は表示しないため、表示用ログには追加しない。入力内容の1行要約はcontentに含まれる）
    st.session_state.messages.append({"role": "assistant", "content": content})

    # 直後の描画でだけ、最新の結果ブロックに登場アニメーションを付けるためのフラグを立てる
    # （「6. 結果の表示」のdisplay_results内で読み取り、描画後にFalseへ戻す）
    st.session_state.just_diagnosed = True


############################################################
# 6. 結果の表示（下段。最新の診断結果を一番上に表示する）
############################################################
# 診断前だけ、フォームの下に案内文を表示（診断処理の後に判定するため、送信直後の画面でも案内文は出ない）
cn.display_form_guide()

try:
    # 診断結果と追加質問のやりとりを、会話ログから表示
    cn.display_results()
except Exception as e:
    # エラーログの出力
    logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
    # エラーメッセージの画面表示
    st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    # 後続の処理を中断
    st.stop()


############################################################
# 7. 追加質問の受け付けと、送信時の処理
############################################################
# 質問欄は結果の下に置く（診断前は表示されず、押されたかどうかと入力文だけが返る）
follow_up_submitted, follow_up_text = cn.display_follow_up_form()

# ボタンが押され、かつ質問文が入力されている場合だけ回答を作る（空白のみの入力は何もしない）
if follow_up_submitted and follow_up_text.strip():
    chat_message = follow_up_text.strip()

    # ==========================================
    # 7-1. ユーザーメッセージのログ出力
    # ==========================================
    logger.info({"message": chat_message, "application_mode": st.session_state.mode})

    # ==========================================
    # 7-2. LLMからの回答取得（Agentが3つのToolから選んで検索する）
    # ==========================================
    # 直前の診断の文脈で追加質問に答えるプロンプトを使う
    question_answer_template = ct.SYSTEM_PROMPT_FOLLOW_UP

    # Agentは会話履歴を見ずに道具を選ぶため、直前の診断内容を前置きとして質問文に付ける
    agent_question = cn.build_follow_up_question(chat_message)

    # 「st.spinner」でグルグル回っている間、表示の不具合が発生しないよう空のエリアを表示
    res_box = st.empty()
    # LLMによる回答生成（回答生成が完了するまでグルグル回す）
    with st.spinner(ct.SPINNER_TEXT):
        try:
            # 質問の内容に応じてToolを選ぶAgentを作り、実行する
            # （道具の選び方の経過は「verbose=True」によりターミナルにだけ出る）
            agent_executor = utils.get_follow_up_agent_executor()
            llm_response = agent_executor.run(agent_question)
        except Exception as e:
            # Agentでの回答に失敗した場合は、警告ログを出したうえで従来の検索による回答に切り替える
            logger.warning(f"{ct.AGENT_FALLBACK_MESSAGE}\n{e}")
            try:
                # 画面読み込み時に作成したRetrieverを使い、Chainを実行
                llm_response = utils.get_llm_response(chat_message, question_answer_template)
            except Exception as e:
                # エラーログの出力
                logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
                # エラーメッセージの画面表示
                st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
                # 後続の処理を中断
                st.stop()

    # ==========================================
    # 7-3. 回答の整形と、会話ログへの追加
    # ==========================================
    # 表示は「6. 結果の表示」で会話ログからまとめて行う
    try:
        # 追加質問への回答を画面表示用のデータに整形
        content = cn.build_follow_up_content(llm_response)

        # AIメッセージのログ出力
        logger.info({"message": content, "application_mode": st.session_state.mode})
    except Exception as e:
        # エラーログの出力
        logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
        # エラーメッセージの画面表示
        st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
        # 後続の処理を中断
        st.stop()

    # 表示用の会話ログにユーザーメッセージを追加
    st.session_state.messages.append({"role": "user", "content": chat_message})
    # 表示用の会話ログにAIメッセージを追加
    st.session_state.messages.append({"role": "assistant", "content": content})

    # 質問欄より上にある「6. 結果の表示」は描き終えているため、画面を作り直して
    # 今のやりとりを会話ログから並び順どおりに表示する
    st.rerun()

# 相談導線の文言を、質問欄の下に1回だけ表示（診断前は表示しない）
cn.display_consult_message()


############################################################
# 8. 資料検索（管理者用）の折りたたみ欄（画面の最下部）
############################################################
cn.display_doc_search_expander(logger)
