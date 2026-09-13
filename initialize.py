"""
このファイルは、最初の画面読み込み時にのみ実行される初期化処理が記述されたファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from uuid import uuid4
import sys
import unicodedata
from dotenv import load_dotenv
import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import constants as ct


############################################################
# 設定関連
############################################################
# 「.env」ファイルで定義した環境変数の読み込み
load_dotenv()


############################################################
# 関数定義
############################################################

def initialize():
    """
    画面読み込み時に実行する初期化処理
    """
    # OPENAI_API_KEYの読み込み（st.secrets優先、無ければ.env）
    initialize_api_key()
    # 初期化データの用意
    initialize_session_state()
    # ログ出力用にセッションIDを生成
    initialize_session_id()
    # ログ出力の設定
    initialize_logger()
    # 困りごとIDとパターン文書の紐づけ一覧を作成
    initialize_pattern_index()
    # 業種名と業種文書の紐づけ一覧を作成
    initialize_industry_index()
    # 対応パターンが無い場合の検索対象（枠組み層）のファイルパス一覧を作成
    initialize_framework_sources()
    # 「その他」の困りごとを選んだ場合の検索対象（枠組み＋サービス）のファイルパス一覧を作成
    initialize_other_trouble_sources()
    # 追加質問のAgentが使う、Toolごとの検索対象ファイルパス一覧を作成
    initialize_agent_tool_sources()
    # RAGのRetrieverを作成
    initialize_retriever()


def initialize_api_key():
    """
    OPENAI_API_KEYの読み込み

    優先順位は「st.secrets → .env」。Streamlit Community Cloudで動かす場合はSecretsに
    登録した値を使い、ローカルではSecretsが無いため.envの値を使う。
    「langchain_openai」の「ChatOpenAI」「OpenAIEmbeddings」は環境変数「OPENAI_API_KEY」を
    読むため、ここで環境変数へセットすれば両方に効く。
    secrets ファイルが無い環境では st.secrets に触らない（触ると画面に警告が出るため）。
    """
    # Streamlitがsecrets.tomlを探す既定の2箇所のパスを組み立てる
    # 1. ユーザーのホームディレクトリ配下
    home_secrets_path = os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml")
    # 2. カレントディレクトリ（アプリの実行ディレクトリ）配下
    cwd_secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")

    # どちらかのパスにsecrets.tomlが存在するかどうかを確認
    secrets_file_exists = os.path.isfile(home_secrets_path) or os.path.isfile(cwd_secrets_path)

    if secrets_file_exists:
        # secrets.tomlが存在する場合のみ、st.secretsに触れる
        # （存在確認済みでも念のためtry文で「secrets」の有無を確認する）
        has_secret = False
        try:
            has_secret = "OPENAI_API_KEY" in st.secrets
        except Exception:
            has_secret = False

        if has_secret:
            # Secretsに登録された値を環境変数へセット
            os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
        else:
            # Secretsに「OPENAI_API_KEY」が無い場合は、従来どおり「.env」ファイルを読み込む
            load_dotenv()
    else:
        # secrets.tomlが無い場合、st.secretsには触れず「.env」ファイルだけを読み込む
        load_dotenv()


def initialize_logger():
    """
    ログ出力の設定
    """
    # 指定のログフォルダが存在すれば読み込み、存在しなければ新規作成
    os.makedirs(ct.LOG_DIR_PATH, exist_ok=True)

    # 引数に指定した名前のロガー（ログを記録するオブジェクト）を取得
    # 再度別の箇所で呼び出した場合、すでに同じ名前のロガーが存在していれば読み込む
    logger = logging.getLogger(ct.LOGGER_NAME)

    # すでにロガーにハンドラー（ログの出力先を制御するもの）が設定されている場合、同じログ出力が複数回行われないよう処理を中断する
    if logger.hasHandlers():
        return

    # 1日単位でログファイルの中身をリセットし、切り替える設定
    log_handler = TimedRotatingFileHandler(
        os.path.join(ct.LOG_DIR_PATH, ct.LOG_FILE),
        when="D",
        encoding="utf8"
    )
    # 出力するログメッセージのフォーマット定義
    # - 「levelname」: ログの重要度（INFO, WARNING, ERRORなど）
    # - 「asctime」: ログのタイムスタンプ（いつ記録されたか）
    # - 「lineno」: ログが出力されたファイルの行番号
    # - 「funcName」: ログが出力された関数名
    # - 「session_id」: セッションID（誰のアプリ操作か分かるように）
    # - 「message」: ログメッセージ
    formatter = logging.Formatter(
        f"[%(levelname)s] %(asctime)s line %(lineno)s, in %(funcName)s, session_id={st.session_state.session_id}: %(message)s"
    )

    # 定義したフォーマッターの適用
    log_handler.setFormatter(formatter)

    # ログレベルを「INFO」に設定
    logger.setLevel(logging.INFO)

    # 作成したハンドラー（ログ出力先を制御するオブジェクト）を、
    # ロガー（ログメッセージを実際に生成するオブジェクト）に追加してログ出力の最終設定
    logger.addHandler(log_handler)


def initialize_session_id():
    """
    セッションIDの作成
    """
    if "session_id" not in st.session_state:
        # ランダムな文字列（セッションID）を、ログ出力用に作成
        st.session_state.session_id = uuid4().hex


def initialize_pattern_index():
    """
    「data/パターン」配下の各ファイルの先頭メタ行を読み、
    困りごとIDごとに紐づくパターン文書の一覧（pattern_index）を作成
    """
    # すでに作成済みの場合、後続の処理を中断
    if "pattern_index" in st.session_state:
        return

    # パターン文書を格納しているフォルダのパス
    # （ドキュメントのmetadataの「source」と同じ書式になるよう、os.path.joinで連結する）
    pattern_folder_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, ct.PATTERN_FOLDER_NAME)

    # 困りごとIDをキー、パターン文書の情報リストを値とする辞書を作成
    st.session_state.pattern_index = build_pattern_index(pattern_folder_path)


def initialize_industry_index():
    """
    「data/業種」配下の各ファイルの先頭メタ行を読み、
    業種名ごとに紐づく業種文書のファイルパス一覧（industry_index）を作成
    """
    # すでに作成済みの場合、後続の処理を中断
    if "industry_index" in st.session_state:
        return

    # 業種文書を格納しているフォルダのパス
    # （ドキュメントのmetadataの「source」と同じ書式になるよう、os.path.joinで連結する）
    industry_folder_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, ct.INDUSTRY_FOLDER_NAME)

    # 業種名をキー、ファイルパスを値とする辞書を作成
    st.session_state.industry_index = build_industry_index(industry_folder_path)


def initialize_framework_sources():
    """
    対応パターンが無い困りごとの診断で検索対象とする、
    枠組み層のファイルパス一覧（framework_sources）を作成

    「data/枠組み」配下の全ファイル、「data/サービス/初期サービス案.md」、「data/解決策」配下の.mdを対象とする。
    調査文書とパターン文書は、対応パターンが無い場合の検索対象には含めない。
    """
    # すでに作成済みの場合、後続の処理を中断
    if "framework_sources" in st.session_state:
        return

    # 枠組み文書を格納しているフォルダのパス
    # （ドキュメントのmetadataの「source」と同じ書式になるよう、os.path.joinで連結する）
    framework_folder_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, ct.FRAMEWORK_FOLDER_NAME)
    # サービス文書のファイルパス
    service_file_path = os.path.join(
        ct.RAG_TOP_FOLDER_PATH, ct.SERVICE_FOLDER_NAME, ct.SERVICE_FILE_NAME
    )
    # 解決策文書を格納しているフォルダのパス
    solution_folder_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, ct.SOLUTION_FOLDER_NAME)

    st.session_state.framework_sources = build_framework_sources(
        framework_folder_path, service_file_path, solution_folder_path
    )


def build_framework_sources(framework_folder_path, service_file_path, solution_folder_path):
    """
    枠組み層のファイルパス一覧の作成

    Args:
        framework_folder_path: 枠組み文書を格納しているフォルダのパス
        service_file_path: サービス文書のファイルパス
        solution_folder_path: 解決策文書を格納しているフォルダのパス

    Returns:
        検索対象とするファイルパスのリスト（枠組み → サービス → 解決策の順）
    """
    framework_sources = []

    # 枠組みフォルダ内のファイルを、並び順が安定するよう名前順に追加する
    if os.path.isdir(framework_folder_path):
        for file_name in sorted(os.listdir(framework_folder_path)):
            full_path = os.path.join(framework_folder_path, file_name)
            # フォルダは対象外とする
            if os.path.isdir(full_path):
                continue
            # ドキュメントのmetadataの「source」と突き合わせるため、同じ調整を行ったパスを持つ
            framework_sources.append(adjust_string(full_path))

    # サービス文書を検索対象に加える
    if os.path.isfile(service_file_path):
        framework_sources.append(adjust_string(service_file_path))

    # 解決策フォルダ内の.mdを、並び順が安定するよう名前順に追加する
    if os.path.isdir(solution_folder_path):
        for file_name in sorted(os.listdir(solution_folder_path)):
            full_path = os.path.join(solution_folder_path, file_name)
            # フォルダと、Markdown以外のファイルは対象外とする
            if os.path.isdir(full_path):
                continue
            if os.path.splitext(file_name)[1] != ".md":
                continue
            # ドキュメントのmetadataの「source」と突き合わせるため、同じ調整を行ったパスを持つ
            framework_sources.append(adjust_string(full_path))

    return framework_sources


def initialize_other_trouble_sources():
    """
    「その他」の困りごとを選んだ場合の診断で検索対象とする、
    枠組み層＋サービス層のファイルパス一覧（other_trouble_sources）を作成

    「data/枠組み」配下の全ファイル ＋ 「data/サービス」配下の全ファイルを対象とする（枠組み → サービスの順）。
    """
    # すでに作成済みの場合、後続の処理を中断
    if "other_trouble_sources" in st.session_state:
        return

    # 枠組み文書を格納しているフォルダのパス
    framework_folder_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, ct.FRAMEWORK_FOLDER_NAME)
    # サービス文書を格納しているフォルダのパス
    service_folder_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, ct.SERVICE_FOLDER_NAME)

    # 既存の「build_folder_sources」を枠組み → サービスの順で呼び、結果を連結する
    other_trouble_sources = (
        build_folder_sources(framework_folder_path) + build_folder_sources(service_folder_path)
    )

    st.session_state.other_trouble_sources = other_trouble_sources


def initialize_agent_tool_sources():
    """
    追加質問のAgentが使う、Toolごとの検索対象ファイルパス一覧（agent_tool_sources）を作成

    「constants.py」の「FOLLOW_UP_TOOLS」に書いたフォルダ名を、
    Toolの名前をキーとしたファイルパスのリストへ変換して保持する。
    """
    # すでに作成済みの場合、後続の処理を中断
    if "agent_tool_sources" in st.session_state:
        return

    # Toolの名前をキー、検索対象のファイルパスのリストを値とする辞書を作成
    agent_tool_sources = {}

    for tool_info in ct.FOLLOW_UP_TOOLS:
        tool_sources = []
        # 1つのToolが複数のフォルダを見る場合があるため、フォルダごとに一覧を足していく
        for folder_name in tool_info["folders"]:
            # （ドキュメントのmetadataの「source」と同じ書式になるよう、os.path.joinで連結する）
            folder_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, folder_name)
            tool_sources.extend(build_folder_sources(folder_path))
        agent_tool_sources[tool_info["name"]] = tool_sources

    st.session_state.agent_tool_sources = agent_tool_sources


def build_folder_sources(folder_path):
    """
    フォルダ直下のファイルパス一覧の作成

    フォルダが存在しない場合は空のリストを返す（呼び出し側は検索対象の絞り込みをやめ、全体検索になる）。

    Args:
        folder_path: 検索対象とするフォルダのパス

    Returns:
        フォルダ直下のファイルパスのリスト（名前順。フォルダは含めない）
    """
    folder_sources = []

    # フォルダが存在しない場合は空のリストを返す
    if not os.path.isdir(folder_path):
        return folder_sources

    # フォルダ内のファイルを、並び順が安定するよう名前順に追加する
    for file_name in sorted(os.listdir(folder_path)):
        full_path = os.path.join(folder_path, file_name)
        # フォルダは対象外とする
        if os.path.isdir(full_path):
            continue
        # ドキュメントのmetadataの「source」と突き合わせるため、同じ調整を行ったパスを持つ
        folder_sources.append(adjust_string(full_path))

    return folder_sources


def build_pattern_index(pattern_folder_path):
    """
    パターン文書の先頭メタ行を読み、困りごとIDごとの紐づけ一覧を作成

    Args:
        pattern_folder_path: パターン文書を格納しているフォルダのパス

    Returns:
        {困りごとID: [{file, title, area, company, materials}, ...]} の辞書
    """
    pattern_index = {}

    # フォルダが存在しない場合は空の辞書を返す
    if not os.path.isdir(pattern_folder_path):
        return pattern_index

    # フォルダ内のファイル名の一覧を取得（並び順を安定させるため、名前順に並べる）
    for file_name in sorted(os.listdir(pattern_folder_path)):
        # ファイル名だけでなく、フルパスを取得
        full_path = os.path.join(pattern_folder_path, file_name)

        # フォルダの場合と、Markdown以外のファイルの場合は読み込まない
        if os.path.isdir(full_path):
            continue
        if os.path.splitext(file_name)[1] != ".md":
            continue

        # ファイルの先頭部分を読み、メタ行を解析
        with open(full_path, encoding="utf-8") as f:
            lines = f.readlines()
        pattern_info = parse_pattern_meta(lines)

        # ドキュメントのmetadataの「source」と突き合わせるため、同じ調整を行ったパスを持つ
        pattern_info["file"] = adjust_string(full_path)

        # 困りごとIDごとに、パターン文書の情報を蓄積
        for trouble_id in pattern_info["trouble_ids"]:
            pattern_index.setdefault(trouble_id, []).append(pattern_info)

    return pattern_index


def build_industry_index(industry_folder_path):
    """
    業種文書の先頭メタ行を読み、業種名ごとのファイルパスの紐づけ一覧を作成

    Args:
        industry_folder_path: 業種文書を格納しているフォルダのパス

    Returns:
        {業種名: ファイルパス} の辞書
    """
    industry_index = {}

    # フォルダが存在しない場合は空の辞書を返す
    if not os.path.isdir(industry_folder_path):
        return industry_index

    # フォルダ内のファイル名の一覧を取得（並び順を安定させるため、名前順に並べる）
    for file_name in sorted(os.listdir(industry_folder_path)):
        # ファイル名だけでなく、フルパスを取得
        full_path = os.path.join(industry_folder_path, file_name)

        # フォルダの場合と、Markdown以外のファイルの場合は読み込まない
        if os.path.isdir(full_path):
            continue
        if os.path.splitext(file_name)[1] != ".md":
            continue

        # ファイルの先頭部分を読み、メタ行を解析（「業種:」で始まる行の値のみ取得）
        with open(full_path, encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines[:ct.PATTERN_META_MAX_LINES]:
            line = line.strip()
            if line.startswith(ct.INDUSTRY_META_KEY_INDUSTRY):
                industry_name = line[len(ct.INDUSTRY_META_KEY_INDUSTRY):].strip()
                # ドキュメントのmetadataの「source」と突き合わせるため、同じ調整を行ったパスを持つ
                industry_index[industry_name] = adjust_string(full_path)
                break

    return industry_index


def parse_pattern_meta(lines):
    """
    パターン文書の先頭メタ行の解析

    Args:
        lines: パターン文書を1行ずつ格納したリスト

    Returns:
        {title, area, trouble_ids, company, materials, evidence} の辞書
    """
    # 取得できなかった項目は空文字・空リストのままとする
    pattern_info = {
        "title": "",
        "area": "",
        "trouble_ids": [],
        "company": "",
        "materials": "",
        "evidence": ""
    }

    # 先頭の数行だけを見る（本文の中に同じ文字列があっても拾わないようにする）
    for line in lines[:ct.PATTERN_META_MAX_LINES]:
        # 行の前後の空白・改行を除去
        line = line.strip()

        # 「領域: 人事」の行
        if line.startswith(ct.PATTERN_META_KEY_AREA):
            pattern_info["area"] = line[len(ct.PATTERN_META_KEY_AREA):].strip()
        # 「困りごとID: 人事1, 集客4」の行
        elif line.startswith(ct.PATTERN_META_KEY_TROUBLE_IDS):
            value = line[len(ct.PATTERN_META_KEY_TROUBLE_IDS):]
            pattern_info["trouble_ids"] = split_trouble_ids(value)
        # 「向いている会社: …」の行
        elif line.startswith(ct.PATTERN_META_KEY_COMPANY):
            pattern_info["company"] = line[len(ct.PATTERN_META_KEY_COMPANY):].strip()
        # 「材料: …」の行
        elif line.startswith(ct.PATTERN_META_KEY_MATERIALS):
            pattern_info["materials"] = line[len(ct.PATTERN_META_KEY_MATERIALS):].strip()

    # メタ行の後にある最初の見出し行（「## P1 …」）を、パターンの見出しとして取得
    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            # 先頭の「#」と空白を取り除いた文字列を見出しとする
            pattern_info["title"] = line.lstrip("#").strip()
            break

    # 本文中の「**商談での一言**: …」の段落を、「根拠となる数字」欄の本文として取得
    # （行の「:」以降の本文だけを持つ。LLMの生成文ではなくこの本文を表示する）
    for line in lines:
        line = line.strip()
        if line.startswith(ct.PATTERN_EVIDENCE_KEY):
            pattern_info["evidence"] = line[len(ct.PATTERN_EVIDENCE_KEY):].strip()
            break

    return pattern_info


def split_trouble_ids(value):
    """
    「困りごとID:」の値を、困りごとIDのリストへ変換

    半角カンマ区切りを基本とし、全角カンマ・全角空白の揺れも吸収する。

    Args:
        value: 「困りごとID:」の後ろの文字列

    Returns:
        困りごとIDのリスト
    """
    # 全角カンマ・読点は半角カンマに置き換える
    value = value.replace("，", ",").replace("、", ",")
    # 全角空白は半角空白に置き換える
    value = value.replace("　", " ")

    # 半角カンマで区切り、前後の空白を除去したうえで、空文字は除く
    trouble_ids = []
    for trouble_id in value.split(","):
        trouble_id = trouble_id.strip()
        if trouble_id:
            trouble_ids.append(trouble_id)

    return trouble_ids


def initialize_retriever():
    """
    画面読み込み時にRAGのRetriever（ベクターストアから検索するオブジェクト）を作成
    """
    # ロガーを読み込むことで、後続の処理中に発生したエラーなどがログファイルに記録される
    logger = logging.getLogger(ct.LOGGER_NAME)

    # すでにRetrieverが作成済みの場合、後続の処理を中断
    if "retriever" in st.session_state:
        return

    # 読み込みの進み具合を表示する場所を用意し、その中に進捗バーを置く
    # （準備が終わったら「progress_box.empty()」でまとめて消す）
    progress_box = st.empty()
    progress_bar = progress_box.progress(0)

    # RAGの参照先となるデータソースの読み込み（フォルダを1つ読み終えるたびに進捗バーが進む）
    docs_all = load_data_sources(progress_bar)

    # OSがWindowsの場合、Unicode正規化と、cp932（Windows用の文字コード）で表現できない文字を除去
    for doc in docs_all:
        doc.page_content = adjust_string(doc.page_content)
        for key in doc.metadata:
            doc.metadata[key] = adjust_string(doc.metadata[key])

    # 埋め込みモデルの用意（データが増えても1リクエストの上限を超えないよう、小分けにして送る）
    embeddings = OpenAIEmbeddings(chunk_size=ct.EMBEDDING_BATCH_SIZE)

    # チャンク分割用のオブジェクトを作成
    text_splitter = CharacterTextSplitter(
        chunk_size=ct.CHUNK_SIZE,
        chunk_overlap=ct.CHUNK_OVERLAP,
        separator=ct.CHUNK_SEPARATOR
    )

    # パターン文書は、先頭のメタ行（領域・困りごとID・向いている会社・材料）が
    # 各チャンクに残るよう、チャンク分割の対象から除外する
    split_target_docs = []
    no_split_docs = []
    for doc in docs_all:
        if doc.metadata.pop(ct.NO_CHUNK_SPLIT_METADATA_KEY, None):
            no_split_docs.append(doc)
        else:
            split_target_docs.append(doc)

    # チャンク分割を実施
    splitted_docs = text_splitter.split_documents(split_target_docs)
    # チャンク分割の対象外としたドキュメントを、分割済みのドキュメントに追加
    splitted_docs.extend(no_split_docs)

    # 資料の読み込みが終わり、ここからは時間のかかるベクトル化（最後の1区間）に入る
    progress_bar.progress(ct.LOADING_PROGRESS_EMBED_VALUE)

    # ベクターストアの作成
    db = Chroma.from_documents(splitted_docs, embedding=embeddings)

    # 準備が終わったことを表示し、進捗バーごと画面から消す
    progress_bar.progress(100)
    progress_box.empty()

    # 診断時にパターン文書だけへ絞り込んだRetrieverを作れるよう、ベクターストアを保持しておく
    st.session_state.db = db

    # ベクターストアを検索するRetrieverの作成
    st.session_state.retriever = db.as_retriever(
        search_type=ct.RETRIEVER_SEARCH_TYPE,
        search_kwargs={"k": ct.RETRIEVER_TOP_K, "fetch_k": ct.RETRIEVER_FETCH_K}
    )


def initialize_session_state():
    """
    初期化データの用意
    """
    if "messages" not in st.session_state:
        # 「表示用」の会話ログを順次格納するリストを用意
        st.session_state.messages = []
        # 「LLMとのやりとり用」の会話ログを順次格納するリストを用意
        st.session_state.chat_history = []

    # 診断ボタンを押した直後の描画でだけ登場アニメーションを出すためのフラグ
    if "just_diagnosed" not in st.session_state:
        st.session_state.just_diagnosed = False


def load_data_sources(progress_bar=None):
    """
    RAGの参照先となるデータソースの読み込み

    Args:
        progress_bar: 読み込みの進み具合を表示する進捗バー（省略時・Noneのときは更新しない）

    Returns:
        読み込んだ通常データソース
    """
    # データソースを格納する用のリスト
    docs_all = []

    # 「data」直下の一覧を、並び順が安定するよう名前順に取得
    top_names = sorted(os.listdir(ct.RAG_TOP_FOLDER_PATH))

    # 進捗バーの分母に使うため、直下のフォルダ数を数える
    # （「+1」は最後のベクトル化の分。フォルダを1つ読み終えるたびに1区間ずつ進める）
    folder_count = 0
    for name in top_names:
        if os.path.isdir(os.path.join(ct.RAG_TOP_FOLDER_PATH, name)):
            folder_count += 1
    folder_total = folder_count + 1

    # 読み終えたフォルダ数
    loaded_count = 0

    # ファイル読み込みの実行（渡したリストにデータが格納される）
    for name in top_names:
        full_path = os.path.join(ct.RAG_TOP_FOLDER_PATH, name)
        if os.path.isdir(full_path):
            # フォルダの場合、フォルダ単位で読み込み、読み終えたら進捗バーを進める
            recursive_file_check(full_path, docs_all)
            loaded_count += 1
            if progress_bar is not None:
                progress_bar.progress(int(loaded_count / folder_total * 100))
        else:
            # 直下にファイルが置かれている場合は、従来どおりそのまま読み込む
            file_load(full_path, docs_all)

    web_docs_all = []
    # ファイルとは別に、指定のWebページ内のデータも読み込み
    # 読み込み対象のWebページ一覧に対して処理
    for web_url in ct.WEB_URL_LOAD_TARGETS:
        # 指定のWebページを読み込み
        loader = WebBaseLoader(web_url)
        web_docs = loader.load()
        # for文の外のリストに読み込んだデータソースを追加
        web_docs_all.extend(web_docs)
    # 通常読み込みのデータソースにWebページのデータを追加
    docs_all.extend(web_docs_all)

    return docs_all


def recursive_file_check(path, docs_all):
    """
    RAGの参照先となるデータソースの読み込み

    Args:
        path: 読み込み対象のファイル/フォルダのパス
        docs_all: データソースを格納する用のリスト
    """
    # パスがフォルダかどうかを確認
    if os.path.isdir(path):
        # フォルダの場合、フォルダ内のファイル/フォルダ名の一覧を取得
        files = os.listdir(path)
        # 各ファイル/フォルダに対して処理
        for file in files:
            # ファイル/フォルダ名だけでなく、フルパスを取得
            full_path = os.path.join(path, file)
            # フルパスを渡し、再帰的にファイル読み込みの関数を実行
            recursive_file_check(full_path, docs_all)
    else:
        # パスがファイルの場合、ファイル読み込み
        file_load(path, docs_all)


def file_load(path, docs_all):
    """
    ファイル内のデータ読み込み

    Args:
        path: ファイルパス
        docs_all: データソースを格納する用のリスト
    """
    # ファイルの拡張子を取得
    file_extension = os.path.splitext(path)[1]

    # 想定していたファイル形式の場合のみ読み込む
    if file_extension in ct.SUPPORTED_EXTENSIONS:
        # ファイルの拡張子に合ったdata loaderを使ってデータ読み込み
        loader = ct.SUPPORTED_EXTENSIONS[file_extension](path)
        docs = loader.load()

        # パターン文書の場合、先頭のメタ行が各チャンクに残るよう、チャンク分割の対象外とする
        if is_pattern_file(path):
            for doc in docs:
                doc.metadata[ct.NO_CHUNK_SPLIT_METADATA_KEY] = True

        docs_all.extend(docs)


def is_pattern_file(path):
    """
    パターン文書かどうかの判定

    Args:
        path: ファイルパス

    Returns:
        パターン文書ならTrue、そうでなければFalse
    """
    # ファイルが置かれているフォルダ名が「パターン」かどうかで判定する
    folder_name = os.path.basename(os.path.dirname(path))
    return folder_name == ct.PATTERN_FOLDER_NAME


def adjust_string(s):
    """
    Windows環境でRAGが正常動作するよう調整

    Args:
        s: 調整を行う文字列

    Returns:
        調整を行った文字列
    """
    # 調整対象は文字列のみ
    if type(s) is not str:
        return s

    # OSがWindowsの場合、Unicode正規化と、cp932（Windows用の文字コード）で表現できない文字を除去
    if sys.platform.startswith("win"):
        s = unicodedata.normalize('NFC', s)
        s = s.encode("cp932", "ignore").decode("cp932")
        return s

    # OSがWindows以外の場合はそのまま返す
    return s
