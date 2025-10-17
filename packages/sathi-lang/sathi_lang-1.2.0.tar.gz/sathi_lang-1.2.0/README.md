# 🧠 Sathi Language  
> **“Code like you speak, friendly like a friend.”**  
> Created with ❤️ by [**Nirajan Ghimire (NirajanG)**](https://github.com/nirajang20)  
> 🌐 [nirajang.com.np](https://nirajang.com.np) • [LinkedIn](https://www.linkedin.com/in/nirajang/)

---

## 🌏 Overview  
**Sathi** is a Nepali-inspired, human-friendly programming language that makes coding feel conversational and intuitive.  
Its syntax resembles natural speech, making it perfect for beginners, hobbyists, and anyone who wants a more expressive way to write code.

Built and maintained by **NirajanG**, Sathi blends creativity, simplicity, and cultural connection into a clean and fun programming experience.

---

## 💻 Example Code

```sathi
sathi yo ho naam = "NirajanG"
sathi bhanna "Namaste, " + naam + "!"
sathi yo ho x = 5
sathi yo ho y = 10
sathi bhanna "Sum: " + str(x + y)

sathi suru yedi x < y bhane
    sathi bhanna "x is smaller than y."
sathi natra
    sathi bhanna "x is greater than or equal to y."
sathi banda
```

✅ **Output:**
```
Namaste, NirajanG!
Sum: 15
x is smaller than y.
```

---

## ⚙️ Installation & Usage

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/nirajang20/Sathi-Language.git
cd Sathi-Language
```

### 2️⃣ Run Your First Program
```bash
python3 sathi.py examples/hello.sathi
```

✅ Example Output:
```
Namaste, NirajanG!
Sum: 15
```

---

## 🧩 VS Code Extension

### Installation
1. Open **VS Code**
2. Go to **Extensions → Install from VSIX...**
3. Select `sathi-lang-0.1.0.vsix`
4. Open a `.sathi` file — syntax highlighting & snippets will activate automatically.

### Included Snippets

| Prefix | Expands To |
|---------|-------------|
| `bhanna` | `sathi bhanna "..."` |
| `yedi` | if-else block template |
| `doherau` | repeat loop template |

---

## 📘 Full Syntax Reference (v1.0)

### 🔹 1. Variable Declaration
```sathi
sathi yo ho naam = "Sathi"
sathi yo ho x = 10
```
Declares variables, similar to `let` in JavaScript or `var` in other languages.

---

### 🔹 2. Print Statement
```sathi
sathi bhanna "Hello, World!"
sathi bhanna "Sum: " + str(x + y)
```
Prints output to the console. The `bhanna` keyword means “say” or “print.”

---

### 🔹 3. Conditional Blocks
```sathi
sathi suru yedi x > y bhane
    sathi bhanna "x is greater."
sathi natra
    sathi bhanna "x is smaller or equal."
sathi banda
```
- `yedi` → if  
- `bhane` → then  
- `natra` → else  
- `banda` → end block

---

### 🔹 4. Loops
Repeat actions with `doherau`:

```sathi
sathi doherau 3 choti
    sathi bhanna "Repeating..."
sathi banda
```
or conditionally:
```sathi
sathi doherau jaba x < 5
    sathi bhanna "x = " + str(x)
    x = x + 1
sathi banda
```

---

### 🔹 5. Functions
```sathi
sathi samjhau add(a, b)
    sathi firta gara a + b
sathi banda

sathi bhanna add(5, 10)
```
- `samjhau` → define function  
- `firta gara` → return value

---

### 🔹 6. Input (User Prompt)
```sathi
sathi leu naam "What is your name? "
sathi bhanna "Hello, " + naam
```
- `leu` → take input

---

### 🔹 7. Importing Files
```sathi
sathi laga "math.sathi"
```
- `laga` → import another `.sathi` file

---

### 🔹 8. Comments
```sathi
# This is a comment line
```
Lines beginning with `#` are ignored by the interpreter.

---

### 🔹 9. Data Types
| Type | Example | Description |
|------|----------|--------------|
| Number | `5`, `3.14` | Integer or Float |
| String | `"Hello"` | Text |
| Boolean | `sahi`, `galat` | true / false |
| List | `[1, 2, 3]` | Collection of values |

---

### 🔹 10. Operators
| Operator | Meaning | Example |
|-----------|----------|----------|
| `+` | Addition / Concatenate | `x + y`, `"a" + "b"` |
| `-` | Subtraction | `x - y` |
| `*` | Multiplication | `x * y` |
| `/` | Division | `x / y` |
| `==` | Equal | `x == y` |
| `!=` | Not equal | `x != y` |
| `<`, `>`, `<=`, `>=` | Comparisons | `x < y`, `x >= y` |

---

## ⚡ Project Structure

```
Sathi-Language/
├── LICENSE
├── README.md
├── sathi.py
├── /examples/
│   └── hello.sathi
├── /docs/
│   └── syntax-list.md
└── /vscode-extension/
    ├── package.json
    ├── language-configuration.json
    ├── syntaxes/sathi.tmLanguage.json
    ├── snippets/sathi.json
    └── README.md
```

---

## 🧑‍💻 Contributing

You’re welcome to improve or expand Sathi!  
1. Fork this repo 🍴  
2. Create a new branch: `git checkout -b feature-name`  
3. Commit your changes: `git commit -m "Added new feature"`  
4. Push and open a pull request 🚀  

---

## 📜 License
Released under the [MIT License](LICENSE).  
Free for personal and commercial use — just give credit to **NirajanG**.

---

## 💬 Credits & Contact
**Author:** [Nirajan Ghimire](https://github.com/nirajang20)  
🌐 [Website](https://nirajang.com.np) | [LinkedIn](https://www.linkedin.com/in/nirajang/)  

> A friendly coding language born in Nepal 🇳🇵  
> Simplifying code, one `sathi` at a time.
