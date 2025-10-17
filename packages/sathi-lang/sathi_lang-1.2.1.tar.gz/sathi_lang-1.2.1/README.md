# 🪷 Sathi Language — Nepali-Inspired Programming Language 🇳🇵

**Sathi Language** is a Nepali-inspired programming language that blends creativity, culture, and code — written in Python and designed to make programming feel natural, human, and expressive.

---

## 🚀 Installation

Install Sathi Language from [PyPI](https://pypi.org/project/sathi-lang/):

```bash
pip install sathi-lang
```

To check if it’s installed correctly:
```bash
sathi --help
```

---

## 🧠 Quick Example

Create a file called `hello.sathi`:

```sathi
sathi yo ho naam = "Sathi"

sathi bhana naya "Namaste, " + naam

sathi dohoryau 3 choti
  sathi bhana sangai "Hello "
  sathi bhana naya "World!"
sathi sakkyo
```

Then run it:
```bash
sathi hello.sathi
```

Output:
```
Namaste, Sathi
Hello World!
Hello World!
Hello World!
```

---

## ✨ Core Syntax

| Purpose | Syntax | Description |
|----------|---------|-------------|
| Declare variable | `sathi yo ho x = 10` | Assigns a value |
| Print | `sathi bhana "text"` | Prints text |
| Print (newline) | `sathi bhana naya "text"` | Prints with newline |
| Print (inline) | `sathi bhana sangai "text"` | Prints on same line |
| Condition | `sathi bhane x > 5` / `sathi natra` | If / else |
| Loop | `sathi dohoryau 3 choti` | Repeat 3 times |
| Function | `sathi kam gar greet(name)` | Define a function |
| Return | `sathi farki x + y` | Return a value |
| End block | `sathi sakkyo` | Close if, loop, or function |
| Math | `joda(a,b)`, `ghatau(a,b)`, `guna(a,b)`, `bhaag(a,b)` | add/subtract/multiply/divide |
| Wait | `sathi parkha 2` | Wait 2 seconds |
| Comment | `# comment` | Inline comments |

---

## 🧮 Example with Function

```sathi
sathi kam gar add(a,b)
  sathi farki joda(a,b)
sathi sakkyo

sathi yo ho result = sathi gara add(5,10)
sathi bhana "Sum: " + str(result)
```

Output:
```
Sum: 15
```

---

## 🪄 About Sathi

> “Sathi” (साथी) means *friend* in Nepali — this language is built to make coding feel friendly and approachable, like having a companion that speaks your language.

- Built with ❤️ by [**Nirajan Ghimire**](https://www.nirajang.com.np)
- Website: [https://www.nirajang.com.np/sathi](https://www.nirajang.com.np/sathi)
- GitHub: [https://github.com/nirajang20/Sathi-Language](https://github.com/nirajang20/Sathi-Language)
- LinkedIn: [https://www.linkedin.com/in/nirajang/](https://www.linkedin.com/in/nirajang/)

---

## 📦 Version History

| Version | Highlights |
|----------|-------------|
| **1.0.0** | Initial release |
| **1.1.0** | Minor syntax cleanup |
| **1.2.1 (Current)** | New syntax keywords (`naya`, `sangai`, `dohoryau`, `sakkyo`, `farki`), updated interpreter, and improved expression support |

---

## 🧩 License

**MIT License**  
© 2025 [Nirajan Ghimire](https://www.nirajang.com.np)

---

> “Code with culture — build with Sathi.” 🌸
