# 🤖 スマホで動かすリモートAIエージェント (完全無料)

GitHub Actions と Google Gemini API (無料枠) を使って、**PCを閉じていてもスマホからIssueを投稿するだけで自動でコード修正・プルリクエスト作成を行ってくれるリモートエージェント**です。

---

## 📱 スマホからの使い方

1. スマホの **GitHub アプリ**（またはブラウザ）を開く。
2. このリポジトリの **Issues** タブを開き、「New Issue」を押す。
3. タイトルと本文にやりたいことを日本語で書く。
   * **例:**
     * **タイトル:** `sample_app.py に引き算と掛け算を追加して`
     * **本文:** `add 関数しかないので、subtract と multiply も追加してください。テストも main に入れてください。`
4. 「Submit new issue」を押して投稿。
5. **数秒〜数十秒待つと、エージェントが自動で動いてプルリクエストを作成し、IssueにURLを返信してくれます。**
6. 作成されたプルリクエストを開き、「Merge pull request」を押せば完了です！

※ 追加の修正を頼みたい時は、Issue のコメントで `@agent 〜〜も修正して` と書くだけで再修正してくれます。

---

## 🚀 初回セットアップ手順（完全無料・所要時間3分）

### ステップ1: Gemini APIキーを取得（無料）
1. [Google AI Studio (API Keys)](https://aistudio.google.com/app/api-keys) にアクセス。
2. Googleアカウントでログインし、「Create API key」をクリック。
3. 表示されたキーをコピーします。

### ステップ2: GitHubリポジトリにAPIキーを登録
1. GitHub でこのリポジトリのページを開く。
2. 上部メニューの **「Settings」** をクリック。
3. 左サイドバーの **「Secrets and variables」** -> **「Actions」** をクリック。
4. **「New repository secret」** ボタンを押す。
   * **Name:** `GEMINI_API_KEY`
   * **Secret:** 先ほどコピーしたGeminiのAPIキー
5. 「Add secret」を押して保存。

### ステップ3: GitHub Actionsの権限を有効化
GitHub Actionsがプルリクエストを作成できるように、書き込み権限を許可します。
1. リポジトリの **「Settings」** -> 左サイドバーの **「Actions」** -> **「General」** を開く。
2. 下部にある **「Workflow permissions」** セクションを探す。
3. **「Read and write permissions」** を選択し、**「Allow GitHub Actions to create and approve pull requests」** にチェックを入れる。
4. 「Save」を押して保存。

---

以上で完了です！
あとはPCの電源を消して、スマホからIssueを作ってみてください。
