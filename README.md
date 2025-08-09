# Aurora Calculator (PySide6)

A modern, eye-catching calculator app built with Python and Qt (PySide6). It features a glassy dark UI, responsive layout, keyboard support, and a safe expression evaluator.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app/main.py
```

## Shortcuts
- Digits and operators: `0-9`, `+ - * / ( ) .`
- Evaluate: `Enter` / `Return`
- Backspace: `Backspace`
- Clear: `Esc`

## Notes
- Uses a safe AST-based evaluator. Supports `+ − × ÷ % // ^` and functions like `sqrt( )`, `sin( )`, `log( )`.
- The percent button divides the current value by 100. 
