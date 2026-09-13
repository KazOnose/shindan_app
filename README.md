# 中小企業向け AI活用診断

中小企業の経営者・採用担当が自社の状況を選ぶと、AI活用のパターン（またはパターンが未整備な困りごとについては一般的な目安）を、根拠となる資料付きで返すアプリです。
DMM生成AIキャンプ Chapter2「社内情報特化型生成AI検索アプリ」の配布コード（Streamlit＋LangChain＋Chroma＋OpenAI）を土台に、5ファイル分割の構造をそのまま維持して改修しています。

## 起動手順（Windows / Python 3.11）

1. 仮想環境を作って有効化する

```
python -m venv env
```

Windows（コマンドプロンプト）:

```
env\Scripts\activate
```

PowerShell:

```
.\env\Scripts\Activate.ps1
```

2. パッケージを入れる

```
pip install -r requirements_windows.txt
```

3. `.env.example` を `.env` にコピーし、`OPENAI_API_KEY=` の後に自分のAPIキーを入れる（クォートは付けない）

```
OPENAI_API_KEY=（ご自身のAPIキー）
```

4. アプリを起動する

```
streamlit run main.py
```

5. 単体テスト（OpenAI APIを使わない部分の検証）を動かす（アプリのフォルダ直下で実行）

```
python -m unittest tests.test_offline
```

## 使い方

- 画面上段のフォームで、1. 相談したい領域　2. 業種・従業員数　3. いちばんの困りごと　4. 社内にある材料　5. 補足（任意）を選び、「この内容で診断する」を押すと下段に診断結果が出ます。
- 診断のあと、画面下部のチャット欄から追加の質問ができます。直前の診断の内容を踏まえて回答します。
- 「資料検索（管理者用）」は画面最下部の折りたたみ欄にあり、入力した内容と関連性が高い資料のありかを一覧で返します。

## ファイル構成

```
shindan_app/
  main.py                  画面全体の流れ（初期化・会話ログ・診断ボタン・チャット入力）
  initialize.py            起動時の初期化（ログ設定・データ読み込み・パターン紐づけ一覧・業種索引・ベクターストア作成）
  components.py            画面表示（診断フォーム・診断結果の4ブロックと4区分・資料検索欄）
  utils.py                 画面表示以外（検索文の組み立て・RAG実行・Agent・Output Parser）
  constants.py             文言・選択肢・プロンプト・RAG設定の一括管理
  .streamlit/config.toml   画面の配色
  requirements.txt         パッケージ一覧（Community Cloud公開用。requirements_windows.txtからWindows専用パッケージを除いたもの）
  requirements_windows.txt パッケージ一覧（配布コードから変更なし。Windowsのローカル環境で使う）
  .env.example             .env のひな形（OPENAI_API_KEY の1行のみ）
  .gitignore               .env とログを除外
  README.md                このファイル
  data/サービス/           初期サービス案
  data/パターン/           具体パターン P1〜P5（先頭にメタ行あり）
  data/枠組み/             AIに向く仕事の見分け方などの考え方の文書（10本）
  data/解決策/             人事／業務／集客／顧客の解決策（4本）
  data/記事/               自社メディアの記事（35本）
  data/調査/               採用課題の調査裏取り、困りごと候補の調査結果
  data/業種/               業種別の文書（9本。先頭のメタ行「種別: 業種／業種: 製造」などで索引化）
  tests/test_offline.py    APIを使わない単体テスト
  logs/                    起動時に自動作成されるログの出力先
```

## 公開手順（Streamlit Community Cloud）

1. GitHub にリポジトリを作り、このフォルダを push する（`.env` は `.gitignore` で除外済み。パッケージ一覧は `requirements.txt` を使う）
2. https://share.streamlit.io で「New app」→ リポジトリ・ブランチ・`main.py` を指定
3. Advanced settings で Python 3.11 を選ぶ
4. Secrets に `OPENAI_API_KEY = "sk-..."`（クォート有り）を登録する
5. Deploy する。初回起動時に `data/` 配下を読み込んでベクターストアを作るため、1分ほどかかる

## パターン文書の増やし方

`data/パターン/` に .md を追加し、先頭へ次の4行を置くだけで、コードを変えずに対応パターンが増えます。

```
領域: 人事
困りごとID: 人事1, 集客4
向いている会社: （1行）
材料: （列挙）
```

困りごとIDは半角カンマ区切りで複数書けます（全角カンマ・読点・全角空白の揺れも読み取ります）。パターン文書はメタ行が各チャンクに残るよう、チャンク分割の対象外にしています。

## 講座内容との対応

| 講座で学んだこと | このアプリでの使い所 |
|---|---|
| RAG（Chroma＋Retriever） | `initialize.py` で `Chroma.from_documents` によりベクターストアを作り、パターン層・枠組み層・調査データ・サービス案から検索する |
| LangChain（create_history_aware_retriever／create_stuff_documents_chain／create_retrieval_chain） | `utils.get_llm_response` で診断と追加質問の両方を同じChain構造で処理し、会話履歴を保持する |
| Streamlit（ラジオ・pills・multiselect・chat_input・session_state） | `components.display_diagnosis_form` の入力フォーム、`main.py` の会話ログと追加質問。領域の選択に応じて困りごとの選択肢10件を切り替える |
| データ前処理（課題⑥のCSV統合と同じ考え方） | パターン文書の先頭メタ行を起動時に読み、困りごとIDとパターン文書の紐づけ一覧を作る。メタ行が各チャンクに残るよう分割対象から外す |
| データ前処理（メタ行による索引） | `data/業種/` の先頭メタ行「業種:」を起動時に読んで業種→ファイルの索引を作り、診断時に選ばれた業種の文書を検索対象へ加える（`initialize.build_industry_index`） |
| 拡張子追加（課題⑤） | `SUPPORTED_EXTENSIONS` に `.md` を追加し、`data/` 配下のMarkdownを読み込む |
| プロンプト設計 | 診断プロンプトを「対応パターンあり」「対応パターンなし」の2本に分け、4ブロック固定出力・4区分の書き分け・専門用語禁止・文脈に無い数値の禁止を指示する |
| Lesson14 Agents（initialize_agent × Tool） | 追加質問で、質問内容に応じて3つの Tool（取り組みの詳細／根拠の数字／サービスと相談方法）から agent が選んで検索する。失敗時は従来の RAG 回答へフォールバック |
| Output Parser（Lesson10） | `PydanticOutputParser` で診断結果の8項目を受け取り、失敗時は `RetryWithErrorOutputParser` で1回だけ再試行する。それでも失敗した場合は生成された文章をそのまま表示してアプリを止めない |

## 診断結果の構成

1. 御社に合う取り組み（対応パターンが無い困りごとの場合は、この紺の面と「根拠となる数字」ブロックを表示せず、冒頭に「まだ御社向けの具体パターンをご用意できていません。以下は一般的な目安です。」の注意文を出す）
2. 御社の場合
3. 根拠となる数字
4. 次の一歩

続けて、AIで改善できる部分／AIだけでは解決できない部分／人の判断が必要な部分／別の仕組みとの連携が必要な部分の4区分を表示し、最後に「参考にした資料」としてRAGが参照した文書名を並べます。

初版ではメールアドレスの取得は行いません。相談導線は「詳しくはご相談ください。」の文言のみです（`constants.CONSULT_MESSAGE`）。
