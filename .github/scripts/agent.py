import json
import os
import subprocess
import sys
from google import genai
from google.genai import types

def run_cmd(cmd, env=None, check=True):
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL, timeout=60)
    if check and res.returncode != 0:
        print(f"Command failed with code {res.returncode}")
        print(f"Stdout: {res.stdout}")
        print(f"Stderr: {res.stderr}")
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout.strip()

def collect_repo_files():
    """リポジトリ内のテキストファイルを収集する（.git等を除外）"""
    repo_files = {}
    ignore_dirs = {'.git', '.github', '__pycache__', 'node_modules', '.venv', 'venv'}
    ignore_exts = {'.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz'}

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ignore_exts:
                continue
            rel_path = os.path.relpath(os.path.join(root, f), '.')
            try:
                with open(rel_path, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    # 1ファイルあたり100KB超はスキップ
                    if len(content) < 100000:
                        repo_files[rel_path] = content
            except Exception:
                pass
    return repo_files

def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    issue_number = os.environ.get("ISSUE_NUMBER", "")
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_body = os.environ.get("ISSUE_BODY", "")
    comment_body = os.environ.get("COMMENT_BODY", "")
    event_name = os.environ.get("EVENT_NAME", "issues")

    if not gemini_api_key:
        print("Error: GEMINI_API_KEY is not set.")
        sys.exit(1)

    # ユーザー指示の組み立て
    if event_name == "issue_comment" and comment_body:
        user_prompt = f"【Issue #{issue_number}: {issue_title}】への追加指示:\n{comment_body}"
    else:
        user_prompt = f"【Issue #{issue_number}: {issue_title}】\n{issue_body}"

    print(f"--- Prompt Target --- \n{user_prompt}\n----------------------")

    # リポジトリ内のファイルを収集
    files = collect_repo_files()
    files_context = "\n\n".join([f"=== File: {path} ===\n{content}" for path, content in files.items()])

    # Geminiクライアント初期化
    client = genai.Client(api_key=gemini_api_key)

    system_instruction = """
あなたはGitHub上で自動でコードの修正や機能追加を行う「リモート自律型AIエンジニア」です。
ユーザーから提供されたIssueの要望と現在のリポジトリ内容を読み取り、適切な修正を行ってください。

【出力仕様】
必ず以下のJSONスキーマに従った有効なJSON形式のみを出力してください（Markdownコードブロック ```json ``` で囲んで構いません）。
{
  "explanation": "行った変更内容や理由の丁寧な解説（日本語・Markdown形式）",
  "files": [
    {
      "path": "修正または新規作成する相対ファイルパス",
      "content": "そのファイルの修正後の完全な全文コード"
    }
  ]
}

- 既存の無関係なコードを勝手に削除しないでください。
- 必要なファイルのみを更新・追加してください。
"""

    prompt = f"""
現在のリポジトリのファイル一覧と内容:
{files_context}

ユーザーからの要望 (Issue):
{user_prompt}

上記の要望を解決するためのファイル修正を作成してください。
"""

    import time
    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
    response = None
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                print(f"Requesting Gemini with model: {model_name} (attempt {attempt+1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.2,
                    )
                )
                print(f"Success with model: {model_name}")
                break
            except Exception as e:
                print(f"Model {model_name} attempt {attempt+1} failed: {e}")
                time.sleep(2)
        if response:
            break

    if not response:
        print("All models failed.")
        sys.exit(1)

    response_text = response.text.strip()
    try:
        data = json.loads(response_text)
    except Exception as e:
        print(f"JSON Parse Error: {e}\nRaw output: {response_text}")
        sys.exit(1)

    explanation = data.get("explanation", "AI Agentによる自動修正です。")
    changed_files = data.get("files", [])

    if not changed_files:
        print("変更対象のファイルがありませんでした。")
        # Issueにコメントして終了
        run_cmd(["gh", "issue", "comment", issue_number, "--body", f"🤖 **AI Agent:**\n\n要望を確認しましたが、コードの変更は必要ないと判断されたか、変更対象がありませんでした。\n\n**詳細:**\n{explanation}"])
        return

    # ファイルの書き込み
    for item in changed_files:
        path = item.get("path")
        content = item.get("content")
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(content)
        print(f"Updated file: {path}")

    # Gitブランチ作成とPush
    branch_name = f"agent/issue-{issue_number}"
    run_cmd(["git", "config", "user.name", "github-actions[bot]"])
    run_cmd(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])
    run_cmd(["git", "checkout", "-b", branch_name])
    run_cmd(["git", "add", "-A"])
    run_cmd(["git", "commit", "-m", f"feat: AI Agent fix for Issue #{issue_number}"])
    run_cmd(["git", "push", "--force", "origin", branch_name])

    # PRの作成
    pr_body = f"""## 🤖 AI Agent による自動修正

**対応Issue:** #{issue_number} - {issue_title}

### 📝 変更内容の説明
{explanation}

---
*スマホまたはPCからこのプルリクエストの「Files changed」を確認し、問題なければ **Merge pull request** を押してください。*
"""
    pr_url = run_cmd([
        "gh", "pr", "create",
        "--base", "main",
        "--head", branch_name,
        "--title", f"🤖 [AI自動修正] {issue_title}",
        "--body", pr_body
    ])
    print(f"Created PR: {pr_url}")

    # IssueにPRへのリンクをコメント
    issue_comment = f"""🤖 **AI Agentが修正プルリクエストを作成しました！**

👉 **プルリクエスト:** {pr_url}

スマホから上記PRを開き、差分を確認して「Merge pull request」を押すだけで反映されます。
追加の修正要望がある場合は、このIssueまたはPRのコメントに `@agent` を付けて指示してください。
"""
    run_cmd(["gh", "issue", "comment", issue_number, "--body", issue_comment])
    print("Done!")

if __name__ == "__main__":
    main()
