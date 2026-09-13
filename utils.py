"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
import re
from dotenv import load_dotenv
import streamlit as st
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.output_parsers import PydanticOutputParser, RetryWithErrorOutputParser
from langchain.agents import AgentType, initialize_agent
from langchain.tools import Tool
import constants as ct


############################################################
# 設定関連
############################################################
# 「.env」ファイルで定義した環境変数の読み込み
load_dotenv()


############################################################
# 診断結果の型定義（Output Parser用）
############################################################

class DiagnosisResult(BaseModel):
    """
    診断結果の型（4ブロック＋4区分）
    """
    pattern_name: str = Field(description=ct.PARSER_DESC_PATTERN_NAME)
    for_your_company: str = Field(description=ct.PARSER_DESC_FOR_YOUR_COMPANY)
    evidence: str = Field(description=ct.PARSER_DESC_EVIDENCE)
    next_step: str = Field(description=ct.PARSER_DESC_NEXT_STEP)
    ai_can_improve: str = Field(description=ct.PARSER_DESC_AI_CAN_IMPROVE)
    ai_cannot_solve: str = Field(description=ct.PARSER_DESC_AI_CANNOT_SOLVE)
    human_judgment: str = Field(description=ct.PARSER_DESC_HUMAN_JUDGMENT)
    needs_other_system: str = Field(description=ct.PARSER_DESC_NEEDS_OTHER_SYSTEM)


############################################################
# 関数定義
############################################################

def get_source_icon(source):
    """
    メッセージと一緒に表示するアイコンの種類を取得

    Args:
        source: 参照元のありか

    Returns:
        メッセージと一緒に表示するアイコンの種類
    """
    # 参照元がWebページの場合とファイルの場合で、取得するアイコンの種類を変える
    if source.startswith("http"):
        icon = ct.LINK_SOURCE_ICON
    else:
        icon = ct.DOC_SOURCE_ICON

    return icon


def build_file_info(document):
    """
    参照元として画面表示するテキストの作成

    PDFファイルの場合のみ、ファイルパスの後ろにページ番号を付ける。

    Args:
        document: 参照元のドキュメント

    Returns:
        「ファイル名」、またはPDFの場合は「ファイル名（ページNo.N）」のテキスト
    """
    # 参照元のありか（ファイルパス、またはWebページのURL）を取得
    source = document.metadata["source"]

    # 参照元がWebページの場合はURLをそのまま使い、ファイルの場合はファイル名だけを使う
    if source.startswith("http"):
        display_source = source
    else:
        display_source = os.path.basename(source)

    # 参照元がPDFファイルで、かつページ番号が取得できた場合のみ、ページ番号を付ける
    if source.endswith(ct.PAGE_NUMBER_TARGET_EXTENSION) and "page" in document.metadata:
        # metadataの「page」は0始まりのため、+1した値を表示する
        page_number = document.metadata["page"] + 1
        return f"{display_source}{ct.PAGE_NUMBER_FORMAT.format(page_number=page_number)}"

    # PDF以外のファイル、またはページ番号が取得できない場合は、ファイル名のみ
    return display_source


def build_error_message(message):
    """
    エラーメッセージと管理者問い合わせテンプレートの連結

    Args:
        message: 画面上に表示するエラーメッセージ

    Returns:
        エラーメッセージと管理者問い合わせテンプレートの連結テキスト
    """
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])


def is_other_trouble(trouble_id):
    """
    困りごとIDが「その他」かどうかの判定

    Args:
        trouble_id: 困りごとID

    Returns:
        困りごとIDが「TROUBLE_OTHER_ID_SUFFIX」で終わる場合はTrue
    """
    return trouble_id.endswith(ct.TROUBLE_OTHER_ID_SUFFIX)


def is_other_trouble_without_note(trouble_id, note):
    """
    「その他」が選ばれていて、補足が空かどうかの判定

    Args:
        trouble_id: 困りごとID
        note: 補足（自由記述・任意）

    Returns:
        「その他」が選ばれていて、補足がNone・空文字・空白のみの場合はTrue
    """
    if not is_other_trouble(trouble_id):
        return False
    if note is None:
        return True
    return note.strip() == ""


def build_diagnosis_query(area, industry, employee, trouble_id, trouble_text, materials, note):
    """
    サイドバーの選択値から、Retrieverへ渡す検索文を組み立てる

    困りごとIDが「その他」の場合は、領域名・困りごとIDを含めない専用の書式
    （「DIAGNOSIS_QUERY_FORMAT_OTHER」）を使い、補足の内容を先頭に置く。

    Args:
        area: 相談したい領域（表示名）
        industry: 業種
        employee: 従業員数
        trouble_id: 困りごとID
        trouble_text: 困りごとの全文
        materials: 社内にある材料のリスト
        note: 補足（自由記述・任意）

    Returns:
        検索文（1文）
    """
    # 材料が1つも選ばれていない場合は「特になし」とする
    if materials:
        materials_text = "、".join(materials)
    else:
        materials_text = ct.DIAGNOSIS_QUERY_NO_MATERIAL

    # 補足は任意入力のため、前後の空白を除去したうえで、空の場合は何も付けない
    if note:
        note_text = note.strip()
    else:
        note_text = ""

    if is_other_trouble(trouble_id):
        # 「その他」の場合は専用の書式を使い、領域名・困りごとIDを入れない
        # 補足の末尾が「。」で終わる場合は、書式側の「。」と重なって「。。」にならないよう1つ落とす
        note_for_query = note_text
        if note_for_query.endswith("。"):
            note_for_query = note_for_query[:-1]

        query = ct.DIAGNOSIS_QUERY_FORMAT_OTHER.format(
            note=note_for_query,
            industry=industry,
            employee=employee,
            materials=materials_text
        )
    else:
        # 設計書の検索文フォーマットに、各値を埋め込む
        query = ct.DIAGNOSIS_QUERY_FORMAT.format(
            area=area,
            industry=industry,
            employee=employee,
            trouble_text=trouble_text,
            trouble_id=trouble_id,
            materials=materials_text,
            note=note_text
        )

    # 補足が無い場合、末尾に余分な空白が残らないよう除去する
    return query.strip()


def get_pattern_list(trouble_id):
    """
    困りごとIDに紐づくパターン文書の一覧を取得

    Args:
        trouble_id: 困りごとID

    Returns:
        パターン文書の情報リスト（対応パターンが無い場合は空リスト）
    """
    return st.session_state.pattern_index.get(trouble_id, [])


def get_diagnosis_parser():
    """
    診断結果用のOutput Parserを取得

    Returns:
        PydanticOutputParserのオブジェクト
    """
    return PydanticOutputParser(pydantic_object=DiagnosisResult)


def get_llm_response(chat_message, question_answer_template, format_instruction=None, filter_sources=None, top_k=None):
    """
    LLMからの回答取得

    Args:
        chat_message: ユーザー入力値（診断モードでは組み立てた検索文）
        question_answer_template: 回答生成に使うシステムプロンプト
        format_instruction: Output Parserのフォーマット命令（診断モードのみ）
        filter_sources: 検索対象を絞り込むファイルパスのリスト（対応パターンありの診断のみ）
        top_k: 検索対象を絞り込むRetrieverの取得件数（Noneの場合は「ct.RETRIEVER_TOP_K」を使う）

    Returns:
        LLMからの回答
    """
    # LLMのオブジェクトを用意
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)

    # 会話履歴なしでもLLMに理解してもらえる、独立した入力テキストを取得するためのプロンプトテンプレートを作成
    question_generator_template = ct.SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT
    question_generator_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_generator_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )

    # LLMから回答を取得する用のプロンプトテンプレートを作成
    question_answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", question_answer_template),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ]
    )
    # 診断モードの場合、Output Parserのフォーマット命令をプロンプトへ埋め込む
    if format_instruction:
        question_answer_prompt = question_answer_prompt.partial(format_instruction=format_instruction)

    # 検索対象を絞り込むファイルパスが渡された場合、そのファイルだけを検索するRetrieverを作成
    if filter_sources:
        retriever = st.session_state.db.as_retriever(
            search_type=ct.RETRIEVER_SEARCH_TYPE,
            search_kwargs={
                "k": top_k if top_k is not None else ct.RETRIEVER_TOP_K,
                "fetch_k": ct.RETRIEVER_FETCH_K,
                "filter": {"source": {"$in": filter_sources}}
            }
        )
    else:
        retriever = st.session_state.retriever

    # 会話履歴なしでもLLMに理解してもらえる、独立した入力テキストを取得するためのRetrieverを作成
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, question_generator_prompt
    )

    # LLMから回答を取得する用のChainを作成
    question_answer_chain = create_stuff_documents_chain(llm, question_answer_prompt)
    # 「RAG x 会話履歴の記憶機能」を実現するためのChainを作成
    chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # LLMへのリクエストとレスポンス取得
    llm_response = chain.invoke({"input": chat_message, "chat_history": st.session_state.chat_history})
    # LLMレスポンスを会話履歴に追加
    st.session_state.chat_history.extend([HumanMessage(content=chat_message), llm_response["answer"]])

    return llm_response


def build_follow_up_tool_func(tool_name):
    """
    追加質問のTool1つ分の処理（func）を作成

    Toolごとに検索対象のフォルダが違うため、Toolの名前を受け取って
    そのToolだけの検索を行う関数を作って返す。

    Args:
        tool_name: Toolの名前（「constants.py」の「FOLLOW_UP_TOOLS」のname）

    Returns:
        質問文を受け取り、回答の文字列を返す関数
    """

    def follow_up_tool_func(question):
        """
        Toolに割り当てたフォルダの中だけを検索して回答を作る

        Args:
            question: Agentが渡してきた質問文

        Returns:
            LLMからの回答の文字列
        """
        # 起動時の初期化で作った、Toolごとの検索対象ファイルパス一覧を取り出す
        # （フォルダが存在しなかった場合は空のリストになり、全体検索へ切り替わる）
        filter_sources = st.session_state.agent_tool_sources.get(tool_name, [])

        # 既存の追加質問と同じプロンプト・同じChainを使い、検索対象だけを絞る
        llm_response = get_llm_response(
            question,
            ct.SYSTEM_PROMPT_FOLLOW_UP,
            filter_sources=filter_sources
        )

        # Agentへは文字列を返す（会話履歴への追加は「get_llm_response」の中で行われる）
        return llm_response["answer"]

    return follow_up_tool_func


def build_follow_up_tools():
    """
    追加質問で使う3つのToolを作成

    Returns:
        Toolオブジェクトのリスト（「constants.py」の「FOLLOW_UP_TOOLS」の並び順）
    """
    tools = []

    for tool_info in ct.FOLLOW_UP_TOOLS:
        tools.append(
            Tool.from_function(
                func=build_follow_up_tool_func(tool_info["name"]),
                name=tool_info["name"],
                description=tool_info["description"]
            )
        )

    return tools


def get_follow_up_agent_executor():
    """
    追加質問に答えるAgentの作成

    質問の内容に応じて、3つのToolの中からAgentが使うものを選ぶ。

    Returns:
        Agentのオブジェクト（agent_executor）
    """
    # Agent用のLLMのオブジェクトを用意（道具の選び方がぶれないよう温度は0にする）
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.AGENT_TEMPERATURE)

    # 道具の説明文を読んで使う道具を決める、講座で学んだ形のAgentを作成
    agent_executor = initialize_agent(
        tools=build_follow_up_tools(),
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=ct.AGENT_MAX_ITERATIONS
    )

    return agent_executor


def parse_diagnosis_result(answer, question_answer_template, format_instruction, chat_message):
    """
    LLMの回答文字列を、診断結果の型（DiagnosisResult）へ変換

    まず「parse()」で変換を試み、失敗した場合は
    「RetryWithErrorOutputParser」で1回だけ再試行する。
    それでも失敗した場合はNoneを返し、呼び出し側で生テキストを表示する。

    Args:
        answer: LLMからの回答文字列
        question_answer_template: 回答生成に使ったシステムプロンプト
        format_instruction: Output Parserのフォーマット命令
        chat_message: LLMへ渡した入力テキスト

    Returns:
        診断結果の8項目を格納した辞書（変換に失敗した場合はNone）
    """
    # 診断結果用のOutput Parserを用意
    output_parser = get_diagnosis_parser()

    # まずはそのまま変換を試みる
    try:
        result = output_parser.parse(answer)
        return build_result_dict(result)
    except ValueError:
        # 変換に失敗した場合、例外処理用のParserで1回だけ再試行する
        pass

    # 再試行時にLLMへ渡すため、実際に使ったプロンプトの文字列をPromptValueにする
    used_prompt_text = "\n".join([
        question_answer_template.replace("{format_instruction}", format_instruction),
        chat_message
    ])
    prompt_value = PromptTemplate(
        template="{used_prompt_text}",
        input_variables=["used_prompt_text"]
    ).format_prompt(used_prompt_text=used_prompt_text)

    # 例外処理用のParserを用意し、再試行
    try:
        retry_parser = RetryWithErrorOutputParser.from_llm(
            parser=output_parser,
            llm=ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)
        )
        result = retry_parser.parse_with_prompt(answer, prompt_value)
        return build_result_dict(result)
    except ValueError:
        # 再試行しても変換できなかった場合は、呼び出し側で生テキストを表示する
        return None


def build_result_dict(result):
    """
    診断結果（DiagnosisResultのインスタンス）を、画面表示用の辞書へ変換

    Args:
        result: DiagnosisResultのインスタンス

    Returns:
        診断結果の8項目を格納した辞書
    """
    return {
        "pattern_name": result.pattern_name,
        "for_your_company": result.for_your_company,
        "evidence": result.evidence,
        "next_step": result.next_step,
        "ai_can_improve": result.ai_can_improve,
        "ai_cannot_solve": result.ai_cannot_solve,
        "human_judgment": result.human_judgment,
        "needs_other_system": result.needs_other_system
    }


def strip_pattern_title_decoration(title):
    """
    パターンの見出しから、画面表示に不要な管理番号と末尾の注記を取り除く

    パターン索引のtitleには「P1 眠っている情報資産から…」のように先頭へ管理番号（P＋数字＋空白）が付き、
    「P5 経営者とベテランの話を聞き取って…（P1の前工程）」のように末尾へ他のパターンとの関係を示す
    全角括弧書き（P＋数字で始まる）が付くことがある。画面には利用者に不要なこの2箇所だけを取り除いた
    見出しを表示する。この関数はpattern_info["title"]自体は書き換えず、表示用の文字列だけを作る。

    Args:
        title: パターン索引のtitle（例:「P5 経営者とベテランの話を聞き取って、自社の魅力を言葉にする（P1の前工程）」）

    Returns:
        先頭の管理番号と末尾の注記を取り除いた見出し
    """
    # 先頭の「P＋数字＋空白」を取り除く
    title = re.sub(r"^P\d+\s+", "", title)
    # 末尾にある「（P＋数字で始まる全角括弧書き）」だけを取り除く（前後の空白も除く）
    title = re.sub(r"\s*（P\d+[^（）]*）\s*$", "", title)
    return title


def build_pattern_name_text(pattern_list):
    """
    「御社に合う取り組み」欄に表示する文字列を、パターン文書のメタ行から組み立てる

    LLMが存在しないパターン名を作ってしまうことを防ぐため、
    この欄はLLMの生成文を使わず、パターン索引の情報から組み立てる。
    見出しは「strip_pattern_title_decoration」で管理番号・末尾の注記を除いた形にする。

    Args:
        pattern_list: 困りごとIDに紐づくパターン文書の情報リスト

    Returns:
        「見出し（向いている会社: …）」の文字列（複数ある場合は改行で連結）
    """
    pattern_name_lines = []

    for pattern_info in pattern_list:
        # 「向いている会社」がメタ行に無い場合は、代替の文言を入れる
        company = pattern_info["company"]
        if not company:
            company = ct.PATTERN_NAME_NO_COMPANY

        # 表示用の見出しだけを整形する（pattern_info["title"]そのものは書き換えない）
        display_title = strip_pattern_title_decoration(pattern_info["title"])

        pattern_name_lines.append(
            ct.PATTERN_NAME_FORMAT.format(title=display_title, company=company)
        )

    return "\n\n".join(pattern_name_lines)


def build_evidence_text(pattern_list):
    """
    「根拠となる数字」欄に表示する文字列を、パターン文書の「商談での一言」から組み立てる

    LLMが文脈に無い数値を作ってしまうことを防ぐため、
    この欄はLLMの生成文を使わず、パターン索引に保持した本文をそのまま使う。

    Args:
        pattern_list: 困りごとIDに紐づくパターン文書の情報リスト

    Returns:
        「商談での一言」の本文（複数ある場合は空行で連結。取得できなかったものは除く）
    """
    evidence_lines = []

    for pattern_info in pattern_list:
        evidence = pattern_info.get("evidence", "")
        if evidence:
            evidence_lines.append(evidence)

    return ct.PATTERN_EVIDENCE_SEPARATOR.join(evidence_lines)


def overwrite_fixed_fields(result, has_pattern, pattern_list):
    """
    「該当パターン」欄と「根拠となる数字」欄を、コードで確定させた内容に上書きする

    - 対応パターンあり: 「該当パターン」欄をパターン索引の情報で、「根拠となる数字」欄を「商談での一言」の本文で上書きする
    - 対応パターンなし: 「該当パターン」欄と「根拠となる数字」欄を固定文で上書きする

    Args:
        result: 診断結果の8項目を格納した辞書（変換に失敗した場合はNone）
        has_pattern: 対応パターンがあるかどうか
        pattern_list: 困りごとIDに紐づくパターン文書の情報リスト

    Returns:
        上書き後の辞書（引数のresultがNoneの場合はNoneをそのまま返す）
    """
    # 決まった形に変換できなかった場合は、上書きする対象が無いためそのまま返す
    if not result:
        return result

    if has_pattern:
        # LLMが作ったパターン名は使わず、パターン文書のメタ行から組み立てた文字列を入れる
        result["pattern_name"] = build_pattern_name_text(pattern_list)
        # LLMが作った数値は使わず、パターン文書の「商談での一言」の本文を入れる
        result["evidence"] = build_evidence_text(pattern_list)
    else:
        # LLMが作ったパターン名と数値は捨て、固定文を入れる
        result["pattern_name"] = ct.NO_PATTERN_FIXED_PATTERN_NAME
        result["evidence"] = ct.NO_PATTERN_FIXED_EVIDENCE

    return result


def build_file_info_list(llm_response):
    """
    LLMが参照したドキュメントの一覧から、画面表示用のテキストの一覧を作成

    Args:
        llm_response: LLMからの回答

    Returns:
        参照元の画面表示用テキストのリスト（重複は除去）
    """
    # 参照元のファイルパスの一覧（重複チェック用）と、画面表示用テキストの一覧を格納するためのリストを用意
    file_path_list = []
    file_info_list = []

    # LLMが回答生成の参照元として使ったドキュメントの一覧に対してループ処理
    for document in llm_response["context"]:
        # ファイルパスを取得
        file_path = document.metadata["source"]
        # 画面表示用のテキストを作成（PDFの場合は「（ページNo.N）」が付く）
        file_info = build_file_info(document)

        # ファイルパスの重複は除去（同じファイルは関連性が最も高い1件のみ表示する）
        if file_path in file_path_list:
            continue
        file_path_list.append(file_path)

        # ファイル情報をリストに順次追加
        file_info_list.append(file_info)

    return file_info_list


def build_source_chunk_counts(llm_response):
    """
    LLMが参照したドキュメントの一覧から、ファイル名（表示用テキスト）ごとのチャンク数を集計

    Args:
        llm_response: LLMからの回答

    Returns:
        [(ファイル情報, 件数), ...] のリスト（出現順を保つ）
    """
    # 出現順を保つための一覧と、件数を数えるための辞書を用意
    file_info_order = []
    chunk_counts = {}

    # LLMが回答生成の参照元として使ったドキュメントの一覧に対してループ処理
    for document in llm_response["context"]:
        # 画面表示用のテキストを作成（PDFの場合は「（ページNo.N）」が付く）
        file_info = build_file_info(document)

        # 初めて出てきたファイル情報の場合、出現順の一覧に追加
        if file_info not in chunk_counts:
            file_info_order.append(file_info)
            chunk_counts[file_info] = 0
        chunk_counts[file_info] += 1

    return [(file_info, chunk_counts[file_info]) for file_info in file_info_order]
