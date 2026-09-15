"""
このファイルは、OpenAI APIを使わずに検証できる部分の単体テストです。

実行方法（アプリのフォルダ直下で実行する）:
    python -m unittest tests.test_offline

検証する範囲:
    1. パターン文書の先頭メタ行の解析（困りごとIDとパターン文書の紐づけ）
    1-2. 解決策文書の先頭メタ行の解析（困りごとIDと解決策文書の紐づけ）
    2. 診断モードの検索文の組み立て
    3. 困りごとの選択肢（4領域×11件＝44件、困りごとIDの重複なし）
    4. 診断結果のOutput Parserが、サンプルのJSON文字列を変換できること
    5. 追加質問のAgentが使う3つのToolの定義と、Toolごとの検索対象ファイルパス一覧
"""

############################################################
# ライブラリの読み込み
############################################################
import os
import sys
import types
import unittest


############################################################
# 事前準備
############################################################
# アプリ本体（constants.py など）を読み込めるよう、1つ上のフォルダをパスに追加
APP_DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR_PATH not in sys.path:
    sys.path.insert(0, APP_DIR_PATH)


def install_stub_module(module_name):
    """
    未インストールのライブラリの代わりとなる、空のモジュールを用意する

    アプリ本体は streamlit・langchain を読み込むが、このテストでは
    それらの機能を使わない。ライブラリが入っていない環境でも
    メタ行の解析と検索文の組み立てを検証できるよう、空のモジュールを差し込む。

    Args:
        module_name: モジュール名（「langchain.chains」のようにドット区切りも可）
    """
    stub_module = types.ModuleType(module_name)

    # どの属性を参照されても、空のクラスを返すようにする
    def module_getattr(attribute_name):
        return type("Stub", (), {})

    stub_module.__getattr__ = module_getattr
    # パッケージとしても読み込めるようにする
    stub_module.__path__ = []

    if module_name == "streamlit":
        # 「@st.cache_resource(show_spinner=False)」はモジュール読み込み時に評価されるため、
        # 引数を受け取って関数をそのまま返すデコレータを用意する
        def cache_resource(*args, **kwargs):
            if len(args) == 1 and not kwargs and callable(args[0]):
                # 「@st.cache_resource」のように引数なしで付けられた場合
                return args[0]

            def decorator(func):
                return func

            return decorator

        stub_module.cache_resource = cache_resource

    sys.modules[module_name] = stub_module

    # 親モジュールがある場合、親モジュールの属性としても登録する
    if "." in module_name:
        parent_name, child_name = module_name.rsplit(".", 1)
        setattr(sys.modules[parent_name], child_name, stub_module)


def prepare_modules():
    """
    アプリ本体の読み込みに必要なライブラリのうち、
    未インストールのものだけを空のモジュールで代用する

    Returns:
        langchainのOutput Parserが使えるかどうか
    """
    # 読み込み順が親から子になるよう、親モジュールを先に並べる
    module_names = [
        "streamlit",
        "dotenv",
        "langchain",
        "langchain.text_splitter",
        "langchain.prompts",
        "langchain.schema",
        "langchain.chains",
        "langchain.chains.combine_documents",
        "langchain.output_parsers",
        "langchain.agents",
        "langchain.tools",
        "langchain_openai",
        "langchain_community",
        "langchain_community.document_loaders",
        "langchain_community.document_loaders.csv_loader",
        "langchain_community.vectorstores"
    ]

    # 空のモジュールで代用したものを記録する
    stubbed_module_names = []

    for module_name in module_names:
        try:
            __import__(module_name)
        except ImportError:
            install_stub_module(module_name)
            stubbed_module_names.append(module_name)

    # 「langchain.output_parsers」が本物の場合のみ、Output Parserのテストを実施する
    return "langchain.output_parsers" not in stubbed_module_names


# ライブラリの用意（アプリ本体の読み込みより前に行う）
LANGCHAIN_AVAILABLE = prepare_modules()

import constants as ct
import initialize
import utils
import components


############################################################
# テスト
############################################################

class TestPatternMeta(unittest.TestCase):
    """
    パターン文書の先頭メタ行の解析のテスト
    """

    @classmethod
    def setUpClass(cls):
        # 「data/パターン」配下のメタ行を読み、困りごとIDごとの紐づけ一覧を作成
        pattern_folder_path = os.path.join(
            APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, ct.PATTERN_FOLDER_NAME
        )
        cls.pattern_index = initialize.build_pattern_index(pattern_folder_path)

    def get_file_names(self, trouble_id):
        """
        困りごとIDに紐づくパターン文書のファイル名の一覧を取得
        """
        file_names = []
        for pattern_info in self.pattern_index.get(trouble_id, []):
            file_names.append(os.path.basename(pattern_info["file"]))
        return file_names

    def test_人事1にP1とP5の2件が紐づく(self):
        file_names = self.get_file_names("人事1")
        self.assertEqual(len(file_names), 2)
        self.assertTrue(file_names[0].startswith("P1_"))
        self.assertTrue(file_names[1].startswith("P5_"))

    def test_集客4にP5が紐づく(self):
        file_names = self.get_file_names("集客4")
        self.assertEqual(len(file_names), 1)
        self.assertTrue(file_names[0].startswith("P5_"))

    def test_人事4と人事5と人事6に1件ずつ紐づく(self):
        self.assertEqual(len(self.get_file_names("人事4")), 1)
        self.assertTrue(self.get_file_names("人事4")[0].startswith("P3_"))
        self.assertEqual(len(self.get_file_names("人事5")), 1)
        self.assertTrue(self.get_file_names("人事5")[0].startswith("P2_"))
        self.assertEqual(len(self.get_file_names("人事6")), 1)
        self.assertTrue(self.get_file_names("人事6")[0].startswith("P4_"))

    def test_対応パターンが無い困りごとは空になる(self):
        # 付録Aで「なし」とされている困りごとIDを確認する
        for trouble_id in ["人事2", "人事3", "人事7", "人事8", "人事9", "人事10",
                           "集客1", "集客10", "顧客1", "顧客10", "業務1", "業務10"]:
            self.assertEqual(self.get_file_names(trouble_id), [])

    def test_紐づく困りごとIDは5件だけ(self):
        # メタ行から拾えた困りごとIDは、人事1・人事4・人事5・人事6・集客4の5件
        self.assertEqual(
            sorted(self.pattern_index.keys()),
            sorted(["人事1", "人事4", "人事5", "人事6", "集客4"])
        )

    def test_メタ行の各項目が取得できる(self):
        pattern_info = self.pattern_index["集客4"][0]
        self.assertEqual(pattern_info["area"], "人事")
        self.assertIn("経営者やベテラン", pattern_info["company"])
        self.assertIn("経営者の話", pattern_info["materials"])
        self.assertTrue(pattern_info["title"].startswith("P5"))

    def test_P1のevidenceに6割が含まれる(self):
        # 「**商談での一言**:」の行の本文が、「根拠となる数字」欄の本文として取得できる
        pattern_info = self.pattern_index["人事1"][0]
        self.assertTrue(os.path.basename(pattern_info["file"]).startswith("P1_"))
        self.assertIn("6割", pattern_info["evidence"])
        # 先頭キー自体は本文に含めない
        self.assertFalse(pattern_info["evidence"].startswith(ct.PATTERN_EVIDENCE_KEY))

    def test_困りごとIDの区切りの揺れを吸収する(self):
        # 半角カンマ、全角カンマ、読点、全角空白のいずれでも同じ結果になる
        self.assertEqual(initialize.split_trouble_ids(" 人事1, 集客4"), ["人事1", "集客4"])
        self.assertEqual(initialize.split_trouble_ids("人事1，集客4"), ["人事1", "集客4"])
        self.assertEqual(initialize.split_trouble_ids("人事1、集客4"), ["人事1", "集客4"])
        self.assertEqual(initialize.split_trouble_ids("　人事1 ,　集客4　"), ["人事1", "集客4"])
        self.assertEqual(initialize.split_trouble_ids("人事1,"), ["人事1"])


class TestSolutionIndex(unittest.TestCase):
    """
    解決策文書の先頭メタ行の解析のテスト

    解決策文書は困りごとID別に1ファイルへ分かれており、領域ごとの「考え方」ファイルは
    索引に入れない（診断時に常に検索対象へ入るため）。
    """

    @classmethod
    def setUpClass(cls):
        # 「data/解決策」配下のメタ行を読み、困りごとIDごとの紐づけ一覧を作成
        cls.solution_folder_path = os.path.join(
            APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, ct.SOLUTION_FOLDER_NAME
        )
        cls.solution_index = initialize.build_solution_index(cls.solution_folder_path)

    def get_file_names(self, trouble_id):
        """
        困りごとIDに紐づく解決策文書のファイル名の一覧を取得
        """
        file_names = []
        for file_path in self.solution_index.get(trouble_id, []):
            file_names.append(os.path.basename(file_path))
        return file_names

    def test_キー数が考え方以外のファイル数と一致する(self):
        # 1ファイル＝1IDのため、索引のキー数はファイル数と等しくなる
        target_count = 0
        for file_name in os.listdir(self.solution_folder_path):
            if os.path.splitext(file_name)[1] != ".md":
                continue
            if file_name.endswith(ct.SOLUTION_THINKING_FILE_SUFFIX):
                continue
            target_count += 1
        self.assertEqual(len(self.solution_index), target_count)

    def test_その他を除くすべての困りごとにキーがある(self):
        # 画面の選択肢にある困りごとは、「その他」を除いてすべて解決策文書を持つ
        # （「その他」は困りごとが決まっていないため、枠組み層とサービスだけで診断する）
        for items in ct.TROUBLE_OPTIONS.values():
            for trouble_id, trouble_text in items:
                if utils.is_other_trouble(trouble_id):
                    self.assertNotIn(trouble_id, self.solution_index)
                else:
                    self.assertIn(trouble_id, self.solution_index)

    def test_困りごとIDごとの解決策文書は1件ずつになる(self):
        # 1ファイル＝1IDのため、どのキーもファイルは1件だけになる
        for trouble_id, file_paths in self.solution_index.items():
            self.assertEqual(len(file_paths), 1, trouble_id)

    def test_業務5は1件で解決策_業務5となる(self):
        self.assertIn("業務5", self.solution_index)
        self.assertEqual(self.get_file_names("業務5"), ["解決策_業務5.md"])

    def test_メタ行から抜けていた集客の困りごとも本文の見出しから拾える(self):
        # 元ファイルのメタ行には集客6・集客10が無かったが、本文の見出しを正としたため索引に入る
        self.assertEqual(self.get_file_names("集客6"), ["解決策_集客6.md"])
        self.assertEqual(self.get_file_names("集客10"), ["解決策_集客10.md"])

    def test_考え方ファイルは索引に入らない(self):
        for file_paths in self.solution_index.values():
            for file_path in file_paths:
                self.assertFalse(
                    os.path.basename(file_path).endswith(ct.SOLUTION_THINKING_FILE_SUFFIX)
                )

    def test_存在しないフォルダを渡すと空の辞書になる(self):
        solution_index = initialize.build_solution_index(
            os.path.join(APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, "存在しないフォルダ")
        )
        self.assertEqual(solution_index, {})


class TestIndustryIndex(unittest.TestCase):
    """
    業種文書の先頭メタ行の解析のテスト
    """

    def test_業種文書9件がすべて対応する(self):
        # 「data/業種」配下のメタ行を読み、業種名ごとの紐づけ一覧を作成
        industry_folder_path = os.path.join(
            APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, ct.INDUSTRY_FOLDER_NAME
        )
        industry_index = initialize.build_industry_index(industry_folder_path)

        # 業種文書は9件（INDUSTRY_OPTIONSのうち「その他」を除いた9件に対応）
        self.assertEqual(len(industry_index), 9)
        for industry_name, file_path in industry_index.items():
            self.assertIn(industry_name, ct.INDUSTRY_OPTIONS)
            self.assertTrue(os.path.basename(file_path).startswith("業種_"))

    def test_存在しないフォルダを渡すと空の辞書になる(self):
        industry_index = initialize.build_industry_index(
            os.path.join(APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, "存在しないフォルダ")
        )
        self.assertEqual(industry_index, {})


class TestDiagnosisQuery(unittest.TestCase):
    """
    診断モードの検索文の組み立てのテスト
    """

    def test_入力値がすべて検索文に含まれる(self):
        query = utils.build_diagnosis_query(
            "人事（採用・教育・定着）",
            "製造",
            "11〜30名",
            "人事1",
            "求人を出しても応募がなかなか集まらない",
            ["昔作った求人票", "経営者の話（口頭のみ）"],
            "ハローワークにしか出していない"
        )
        self.assertIn("人事（採用・教育・定着）", query)
        self.assertIn("製造", query)
        self.assertIn("11〜30名", query)
        self.assertIn("人事1", query)
        self.assertIn("求人を出しても応募がなかなか集まらない", query)
        self.assertIn("昔作った求人票", query)
        self.assertIn("経営者の話（口頭のみ）", query)
        self.assertIn("ハローワークにしか出していない", query)

    def test_材料が未選択の場合は特になしと書かれる(self):
        query = utils.build_diagnosis_query(
            "顧客対応", "小売・飲食", "〜10名", "顧客1",
            "問い合わせ対応に時間を取られ、他の仕事が進まない", [], ""
        )
        self.assertIn(ct.DIAGNOSIS_QUERY_NO_MATERIAL, query)
        self.assertIn("未選択", query)
        # 補足が空の場合、末尾に余分な空白が残らない
        self.assertEqual(query, query.strip())

    def test_その他プラス補足ありのとき検索文に補足が入り末尾に重複しない(self):
        query = utils.build_diagnosis_query(
            "人事（採用・教育・定着）", "製造", "〜10名", "人事その他", ct.TROUBLE_OTHER_LABEL,
            [], "  求人媒体の選び方が分からない  "
        )
        # 新しい書式（DIAGNOSIS_QUERY_FORMAT_OTHER）では、補足に『』は付かない
        self.assertIn("求人媒体の選び方が分からない", query)
        self.assertNotIn(ct.TROUBLE_OTHER_LABEL, query)
        self.assertEqual(query.count("求人媒体の選び方が分からない"), 1)

    def test_その他のとき検索文に領域名が入らない(self):
        query = utils.build_diagnosis_query(
            "人事（採用・教育・定着）", "製造", "〜10名", "人事その他", ct.TROUBLE_OTHER_LABEL,
            [], "社内でAIエージェントを活用したい。"
        )
        self.assertTrue(query.startswith("社内でAIエージェントを活用したい"))
        self.assertNotIn("人事（採用・教育・定着）", query)
        self.assertNotIn(ct.TROUBLE_OTHER_LABEL, query)
        self.assertIn("製造", query)
        self.assertIn("〜10名", query)
        self.assertIn(ct.DIAGNOSIS_QUERY_NO_MATERIAL, query)
        self.assertNotIn("。。", query)


class TestIsOtherTroubleWithoutNote(unittest.TestCase):
    """
    「その他」＋補足なしの判定のテスト
    """

    def test_その他で補足が空なら真になる(self):
        self.assertTrue(utils.is_other_trouble_without_note("人事その他", ""))
        self.assertTrue(utils.is_other_trouble_without_note("集客その他", "   "))
        self.assertTrue(utils.is_other_trouble_without_note("顧客その他", None))

    def test_その他でない場合や補足がある場合は偽になる(self):
        self.assertFalse(utils.is_other_trouble_without_note("人事1", ""))
        self.assertFalse(utils.is_other_trouble_without_note("業務その他", "書類が多い"))


class TestBuildInputSummary(unittest.TestCase):
    """
    診断結果の先頭に出す、入力内容の1行要約の組み立てのテスト
    """

    def test_その他のとき困りごとの位置に補足が入り末尾の補足は付かない(self):
        summary = components.build_input_summary({
            "area": "人事（採用・教育・定着）",
            "industry": "製造",
            "employee": "〜10名",
            "trouble_id": "人事その他",
            "trouble_text": ct.TROUBLE_OTHER_LABEL,
            "materials": ["会社案内パンフ"],
            "note": "  求人媒体の選び方が分からない  "
        })
        self.assertEqual(summary.count("求人媒体の選び方が分からない"), 1)
        self.assertNotIn(ct.TROUBLE_OTHER_LABEL, summary)
        self.assertNotIn(ct.DIAGNOSIS_INPUT_SUMMARY_NOTE_PREFIX, summary)

    def test_通常の困りごとのときは困りごとラベルが入り末尾に補足が付く(self):
        summary = components.build_input_summary({
            "area": "人事（採用・教育・定着）",
            "industry": "製造",
            "employee": "〜10名",
            "trouble_id": "人事1",
            "trouble_text": "求人を出しても応募がなかなか集まらない",
            "materials": ["会社案内パンフ"],
            "note": "ハローワークにしか出していない"
        })
        self.assertIn("求人を出しても応募がなかなか集まらない", summary)
        self.assertTrue(summary.endswith(
            f"{ct.DIAGNOSIS_INPUT_SUMMARY_NOTE_PREFIX}ハローワークにしか出していない"
        ))

    def test_材料が未選択の場合は要約では特になしのまま(self):
        # 検索文側のDIAGNOSIS_QUERY_NO_MATERIALを変えても、画面の1行要約は「材料: 特になし」のまま
        summary = components.build_input_summary({
            "area": "顧客対応",
            "industry": "小売・飲食",
            "employee": "〜10名",
            "trouble_id": "顧客1",
            "trouble_text": "問い合わせ対応に時間を取られ、他の仕事が進まない",
            "materials": [],
            "note": ""
        })
        self.assertIn(
            f"{ct.DIAGNOSIS_INPUT_SUMMARY_MATERIAL_PREFIX}{ct.DIAGNOSIS_INPUT_SUMMARY_NO_MATERIAL}",
            summary
        )
        self.assertIn("材料: 特になし", summary)


class TestTroubleOptions(unittest.TestCase):
    """
    困りごとの選択肢のテスト
    """

    def test_4領域それぞれ11件ある(self):
        self.assertEqual(len(ct.TROUBLE_OPTIONS), 4)
        for area_key in ["人事", "集客", "顧客", "業務"]:
            self.assertEqual(len(ct.TROUBLE_OPTIONS[area_key]), 11)

    def test_合計44件で困りごとIDが重複しない(self):
        trouble_ids = []
        for trouble_options in ct.TROUBLE_OPTIONS.values():
            for trouble_id, trouble_text in trouble_options:
                trouble_ids.append(trouble_id)
        self.assertEqual(len(trouble_ids), 44)
        self.assertEqual(len(set(trouble_ids)), 44)

    def test_領域の内部キーが困りごとの辞書と一致する(self):
        for area_key in ct.AREA_LABEL_TO_KEY.values():
            self.assertIn(area_key, ct.TROUBLE_OPTIONS)


class TestOverwriteFixedFields(unittest.TestCase):
    """
    「該当パターン」欄と「根拠となる数字」欄の上書きのテスト
    """

    def build_sample_result(self):
        """
        LLMが返した想定の、上書き前の診断結果の辞書を用意する
        """
        return {
            "pattern_name": "P2 Webサイトの改善から集客を促進する",
            "for_your_company": "ホームページの事業紹介を書き直せます。",
            "evidence": "中小企業の約7割が課題としています（中小企業白書2024）。",
            "next_step": "今週は1ページ選んでください。詳しくはご相談ください。",
            "ai_can_improve": "文章の下書き作成。",
            "ai_cannot_solve": "商品そのものの改善。",
            "human_judgment": "内容が実態と合っているかの確認。",
            "needs_other_system": "特にありません"
        }

    def test_対応パターンなしの場合は固定文で上書きされる(self):
        result = utils.overwrite_fixed_fields(self.build_sample_result(), False, [])
        self.assertEqual(result["pattern_name"], ct.NO_PATTERN_FIXED_PATTERN_NAME)
        self.assertEqual(result["evidence"], ct.NO_PATTERN_FIXED_EVIDENCE)
        # 上書き対象の2欄以外は、LLMの生成文がそのまま残る
        self.assertEqual(result["for_your_company"], "ホームページの事業紹介を書き直せます。")

    def test_対応パターンありの場合はパターン索引の情報で上書きされる(self):
        pattern_list = [{
            "file": "./data/パターン/P1_眠っている情報資産から求人票・採用ページを作り直す.md",
            "title": "P1 眠っている情報資産から求人票・採用ページを作り直す",
            "area": "人事",
            "company": "従業員50名以下で、求人票を3年以上更新していない会社",
            "materials": "昔作った求人票",
            "evidence": "中途採用の課題で「応募が少ない」を挙げる中小企業は6割を超えます（中小企業白書2024）。"
        }]
        result = utils.overwrite_fixed_fields(self.build_sample_result(), True, pattern_list)
        self.assertEqual(
            result["pattern_name"],
            "眠っている情報資産から求人票・採用ページを作り直す"
            "（向いている会社: 従業員50名以下で、求人票を3年以上更新していない会社）"
        )
        # 対応パターンありの場合、「根拠となる数字」欄は「商談での一言」の本文で上書きされる（LLMの生成文は使わない）
        self.assertEqual(
            result["evidence"],
            "中途採用の課題で「応募が少ない」を挙げる中小企業は6割を超えます（中小企業白書2024）。"
        )

    def test_先頭の管理番号と末尾の注記が取り除かれ向いている会社は残る(self):
        # 「P5 …（P1の前工程）」形式のtitleを渡した場合、先頭のP番号と末尾の括弧書きが消える
        pattern_list = [{
            "file": "./data/パターン/P5_話を聞き取って魅力を言葉にする.md",
            "title": "P5 経営者とベテランの話を聞き取って、自社の魅力を言葉にする（P1の前工程）",
            "area": "人事",
            "company": "経営者やベテランの頭の中に魅力はある会社",
            "materials": "経営者の話（口頭のみ）",
            "evidence": ""
        }]
        result = utils.overwrite_fixed_fields(self.build_sample_result(), True, pattern_list)
        self.assertEqual(
            result["pattern_name"],
            "経営者とベテランの話を聞き取って、自社の魅力を言葉にする"
            "（向いている会社: 経営者やベテランの頭の中に魅力はある会社）"
        )

    def test_変換に失敗した場合はNoneのまま返る(self):
        self.assertIsNone(utils.overwrite_fixed_fields(None, False, []))


class TestFrameworkSources(unittest.TestCase):
    """
    対応パターンが無い場合の検索対象（枠組み層）の一覧のテスト
    """

    def test_枠組み10件とサービス1件と解決策4件が対象になる(self):
        framework_sources = initialize.build_framework_sources(
            os.path.join(APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, ct.FRAMEWORK_FOLDER_NAME),
            os.path.join(
                APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH,
                ct.SERVICE_FOLDER_NAME, ct.SERVICE_FILE_NAME
            ),
            os.path.join(APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, ct.SOLUTION_FOLDER_NAME)
        )
        file_names = []
        for source in framework_sources:
            file_names.append(os.path.basename(source))

        # 枠組み10件 → サービス1件 → 解決策の「考え方」4件の順で、合計15件
        self.assertEqual(len(file_names), 15)
        self.assertEqual(file_names[10], ct.SERVICE_FILE_NAME)
        for file_name in file_names[11:]:
            self.assertTrue(file_name.startswith("解決策_"))
            # 困りごとID別の解決策ファイルは枠組み層に含めない
            self.assertTrue(file_name.endswith(ct.SOLUTION_THINKING_FILE_SUFFIX))
        # 枠組みの範囲は名前順（01_〜10_で始まる）になっている
        self.assertEqual(sorted(file_names[:10]), file_names[:10])
        # 調査文書とパターン文書は検索対象に含めない
        for file_name in file_names:
            self.assertFalse(file_name.startswith("P1_"))
            self.assertNotIn("調査", file_name)


class TestBuildSourceChunkCounts(unittest.TestCase):
    """
    ログ出力用の、ファイル名ごとのチャンク数集計のテスト
    """

    def test_出現順でファイル名ごとのチャンク数が集計される(self):
        # API不要で確認できるよう、metadataだけを持つ簡易オブジェクトを使う
        llm_response = {
            "context": [
                types.SimpleNamespace(metadata={"source": "a.md"}),
                types.SimpleNamespace(metadata={"source": "b.md"}),
                types.SimpleNamespace(metadata={"source": "a.md"})
            ]
        }
        self.assertEqual(
            utils.build_source_chunk_counts(llm_response),
            [("a.md", 2), ("b.md", 1)]
        )


class TestOtherTroubleSources(unittest.TestCase):
    """
    「その他」の困りごとを選んだ場合の検索対象一覧の構成のテスト
    """

    def test_枠組み10件とサービス1件の11本になる(self):
        framework_sources = initialize.build_folder_sources(
            os.path.join(APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, ct.FRAMEWORK_FOLDER_NAME)
        )
        service_sources = initialize.build_folder_sources(
            os.path.join(APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, ct.SERVICE_FOLDER_NAME)
        )
        other_trouble_sources = framework_sources + service_sources
        file_names = [os.path.basename(source) for source in other_trouble_sources]

        # 枠組み10件＋サービス1件＝11本（解決策・調査・パターン・記事は含まれない）
        self.assertEqual(len(file_names), 11)
        for file_name in file_names:
            self.assertFalse(file_name.startswith("解決策_"))
            self.assertNotIn("調査", file_name)
            self.assertFalse(file_name.startswith("P1_"))


class TestFollowUpTools(unittest.TestCase):
    """
    追加質問のAgentが使う3つのToolの定義のテスト

    Toolオブジェクトを作るとLLMの用意が必要になるため、
    定義そのもの（constants.pyのFOLLOW_UP_TOOLS）を検証する。
    """

    def test_Toolは3つある(self):
        self.assertEqual(len(ct.FOLLOW_UP_TOOLS), 3)

    def test_各Toolの名前と説明が空でない(self):
        for tool_info in ct.FOLLOW_UP_TOOLS:
            self.assertTrue(tool_info["name"])
            self.assertTrue(tool_info["description"])

    def test_Toolの名前が重複しない(self):
        tool_names = []
        for tool_info in ct.FOLLOW_UP_TOOLS:
            tool_names.append(tool_info["name"])
        self.assertEqual(len(set(tool_names)), 3)

    def test_検索対象フォルダの割り当てが設計どおり(self):
        # 名前 → 検索対象フォルダ名のリスト、の形に直してから突き合わせる
        folders_by_name = {}
        for tool_info in ct.FOLLOW_UP_TOOLS:
            folders_by_name[tool_info["name"]] = tool_info["folders"]

        self.assertEqual(
            folders_by_name[ct.FOLLOW_UP_TOOL_NAME_SOLUTION],
            [ct.PATTERN_FOLDER_NAME, ct.SOLUTION_FOLDER_NAME]
        )
        self.assertEqual(
            folders_by_name[ct.FOLLOW_UP_TOOL_NAME_EVIDENCE],
            [ct.RESEARCH_FOLDER_NAME, ct.ARTICLE_FOLDER_NAME]
        )
        self.assertEqual(
            folders_by_name[ct.FOLLOW_UP_TOOL_NAME_SERVICE],
            [ct.SERVICE_FOLDER_NAME]
        )


class TestFolderSources(unittest.TestCase):
    """
    Toolごとの検索対象ファイルパス一覧の作成のテスト
    """

    def build_sources(self, folder_name):
        """
        「data」直下のフォルダ名から、検索対象のファイルパス一覧を作る
        """
        return initialize.build_folder_sources(
            os.path.join(APP_DIR_PATH, ct.RAG_TOP_FOLDER_PATH, folder_name)
        )

    def test_サービスは1件で調査は2件(self):
        self.assertEqual(len(self.build_sources(ct.SERVICE_FOLDER_NAME)), 1)
        self.assertEqual(
            os.path.basename(self.build_sources(ct.SERVICE_FOLDER_NAME)[0]),
            ct.SERVICE_FILE_NAME
        )
        self.assertEqual(len(self.build_sources(ct.RESEARCH_FOLDER_NAME)), 2)

    def test_存在しないフォルダは空のリストになる(self):
        self.assertEqual(self.build_sources("存在しないフォルダ"), [])


class TestDiagnosisParser(unittest.TestCase):
    """
    診断結果のOutput Parserのテスト
    """

    @unittest.skipUnless(LANGCHAIN_AVAILABLE, "langchainが未インストールのため実行しない")
    def test_サンプルのJSON文字列を変換できる(self):
        sample_json = """{
    "pattern_name": "P1 眠っている情報資産から求人票・採用ページを作り直す（従業員50名以下で、求人票を3年以上更新していない会社）",
    "for_your_company": "昔の求人票と会社案内があるため、書き直しの材料はそろっています。",
    "evidence": "中小企業の採用課題 調査裏取りより、応募が集まらないという回答が最も多い項目です。",
    "next_step": "今週は昔の求人票を1枚探すところから始めてください。詳しくはご相談ください。",
    "ai_can_improve": "文章の書き直しと言い換えの下書き作成。",
    "ai_cannot_solve": "給与や休日といった条件そのものの改善。",
    "human_judgment": "書かれた内容が実態と合っているかの確認。",
    "needs_other_system": "求人媒体への掲載と応募者管理の仕組みとの連携。"
}"""
        result = utils.get_diagnosis_parser().parse(sample_json)
        self.assertTrue(result.pattern_name.startswith("P1"))
        self.assertIn("詳しくはご相談ください。", result.next_step)
        self.assertEqual(
            result.needs_other_system, "求人媒体への掲載と応募者管理の仕組みとの連携。"
        )


class TestBuildQuadListHtml(unittest.TestCase):
    """
    4区分の表の組み立て（「特にありません」の行を出さない判定）のテスト
    """

    def build_result(self, needs_other_system):
        """
        4区分の値だけを持つ診断結果の辞書を作る

        Args:
            needs_other_system: 「別の仕組みとの連携が必要な部分」の値

        Returns:
            診断結果の辞書
        """
        return {
            "ai_can_improve": "求人票の書き直しの下書き作成。",
            "ai_cannot_solve": "給与や休日の条件そのものの改善。",
            "human_judgment": "書かれた内容が実態と合っているかの確認。",
            "needs_other_system": needs_other_system
        }

    def assert_other_three_headings(self, quad_html):
        """
        「別の仕組みとの連携が必要な部分」以外の3見出しが含まれることを確認する

        Args:
            quad_html: 組み立てられたHTML文字列
        """
        self.assertIn(ct.DIAGNOSIS_HEADING_AI_CAN_IMPROVE, quad_html)
        self.assertIn(ct.DIAGNOSIS_HEADING_AI_CANNOT_SOLVE, quad_html)
        self.assertIn(ct.DIAGNOSIS_HEADING_HUMAN_JUDGMENT, quad_html)

    def test_特にありませんのときは別の仕組みの行を出さない(self):
        for value in ["特にありません", "特にありません。", "  特にありません。 "]:
            with self.subTest(value=value):
                quad_html = components.build_quad_list_html(self.build_result(value))
                self.assertNotIn(ct.DIAGNOSIS_HEADING_NEEDS_OTHER_SYSTEM, quad_html)
                self.assert_other_three_headings(quad_html)

    def test_中身があるときは別の仕組みの行を出す(self):
        quad_html = components.build_quad_list_html(
            self.build_result("CRMとの連携が必要です")
        )
        self.assertIn(ct.DIAGNOSIS_HEADING_NEEDS_OTHER_SYSTEM, quad_html)
        self.assertIn("CRMとの連携が必要です", quad_html)
        self.assert_other_three_headings(quad_html)


if __name__ == "__main__":
    unittest.main()
