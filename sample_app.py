# サンプルアプリ: 簡単な計算機
# このアプリに対して、スマホのGitHub Issueから「引き算・掛け算を追加して」「入力チェックをつけて」などと指示できます。

def add(a: float, b: float) -> float:
    """足し算"""
    return a + b

def main():
    print("=== シンプル計算機 ===")
    num1 = 10
    num2 = 5
    print(f"{num1} + {num2} = {add(num1, num2)}")

if __name__ == "__main__":
    main()
