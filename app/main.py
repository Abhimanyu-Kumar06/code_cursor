import math
import sys
import ast
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


@dataclass
class TokenMapping:
    label: str
    value: str
    role: str  # 'digit', 'op', 'action'


class SafeEvaluator:
    def __init__(self) -> None:
        self.allowed_nodes = (
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Num,
            ast.Constant,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Pow,
            ast.USub,
            ast.UAdd,
            ast.Load,
            ast.Call,  # Only for allowed functions below
            ast.Name,
            ast.Tuple,
            ast.List,
            ast.MatMult,  # will reject in evaluator below
        )
        self.allowed_names = {
            # common constants
            'pi': math.pi,
            'e': math.e,
            # functions
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'abs': abs,
            'round': round,
        }

    def evaluate(self, expression: str) -> float:
        # Replace unicode operator symbols with Python equivalents
        sanitized = (
            expression.replace('×', '*')
            .replace('÷', '/')
            .replace('−', '-')
        )
        try:
            node = ast.parse(sanitized, mode='eval')
        except SyntaxError:
            raise ValueError('Invalid expression')
        return self._eval(node.body)

    def _eval(self, node: ast.AST) -> Any:
        if not isinstance(node, self.allowed_nodes):
            raise ValueError('Disallowed expression')

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError('Invalid constant')

        if isinstance(node, ast.Num):
            return node.n

        if isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValueError('Unsupported unary operator')

        if isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
            if isinstance(node.op, ast.Pow):
                # Avoid massive exponentiation
                if abs(left) > 1e6 or abs(right) > 10:
                    raise ValueError('Exponent too large')
                return left ** right
            raise ValueError('Unsupported operator')

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self.allowed_names:
                func = self.allowed_names[node.func.id]
                args = [self._eval(arg) for arg in node.args]
                return func(*args)
            raise ValueError('Function not allowed')

        if isinstance(node, ast.Name):
            if node.id in self.allowed_names:
                return self.allowed_names[node.id]
            raise ValueError('Unknown identifier')

        raise ValueError('Invalid expression')


class CalculatorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Aurora Calculator')
        self.setMinimumSize(420, 620)
        self.evaluator = SafeEvaluator()
        self._build_ui()
        self._apply_theme()
        self.current_expression = ''

    def _build_ui(self) -> None:
        central = QWidget(self)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(22, 22, 22, 22)
        main_layout.setSpacing(16)

        # Display
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.display.setText('0')
        self.display.setMinimumHeight(88)
        self.display.setFont(QFont('Inter', 32))
        self.display.setObjectName('Display')

        # Sub-display for expression preview
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.preview.setMinimumHeight(24)
        self.preview.setText('')
        self.preview.setObjectName('Preview')

        main_layout.addWidget(self.preview)
        main_layout.addWidget(self.display)

        # Buttons
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        buttons: list[TokenMapping] = [
            TokenMapping('AC', 'AC', 'action'),
            TokenMapping('±', 'NEG', 'action'),
            TokenMapping('%', '%', 'op'),
            TokenMapping('÷', '÷', 'op'),

            TokenMapping('7', '7', 'digit'),
            TokenMapping('8', '8', 'digit'),
            TokenMapping('9', '9', 'digit'),
            TokenMapping('×', '×', 'op'),

            TokenMapping('4', '4', 'digit'),
            TokenMapping('5', '5', 'digit'),
            TokenMapping('6', '6', 'digit'),
            TokenMapping('−', '−', 'op'),

            TokenMapping('1', '1', 'digit'),
            TokenMapping('2', '2', 'digit'),
            TokenMapping('3', '3', 'digit'),
            TokenMapping('+', '+', 'op'),

            TokenMapping('(', '(', 'op'),
            TokenMapping('0', '0', 'digit'),
            TokenMapping(')', ')', 'op'),
            TokenMapping('=', '=', 'action'),
        ]

        row = 0
        col = 0
        for mapping in buttons:
            btn = QPushButton(mapping.label)
            btn.setMinimumSize(QSize(72, 64))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setObjectName('BtnPrimary' if mapping.role == 'digit' else ('BtnAccent' if mapping.value in {'=', '+', '−', '×', '÷'} else 'BtnSecondary'))
            btn.clicked.connect(lambda checked=False, m=mapping: self._on_button(m))
            grid.addWidget(btn, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1

        main_layout.addWidget(grid_container)

        # Bottom row with utilities
        utils_layout = QHBoxLayout()
        backspace_btn = QPushButton('⌫')
        backspace_btn.setObjectName('BtnUtility')
        backspace_btn.setMinimumHeight(52)
        backspace_btn.clicked.connect(lambda: self._on_backspace())

        dot_btn = QPushButton('.')
        dot_btn.setObjectName('BtnUtility')
        dot_btn.setMinimumHeight(52)
        dot_btn.clicked.connect(lambda: self._append_token('.'))

        pow_btn = QPushButton('^')
        pow_btn.setObjectName('BtnUtility')
        pow_btn.setMinimumHeight(52)
        pow_btn.clicked.connect(lambda: self._append_token('**'))

        utils_layout.addWidget(backspace_btn)
        utils_layout.addWidget(dot_btn)
        utils_layout.addWidget(pow_btn)
        main_layout.addLayout(utils_layout)

        self.setCentralWidget(central)

        # Shortcuts
        self._install_shortcuts()

    def _apply_theme(self) -> None:
        try:
            import qdarktheme  # type: ignore
            self.setStyleSheet(qdarktheme.load_stylesheet('dark'))
        except Exception:
            pass

        # Add custom accent and glass styles
        self.setStyleSheet(self.styleSheet() + self._custom_qss())

    def _custom_qss(self) -> str:
        return (
            """
            QWidget {
                background-color: #0f1226;
            }
            #Preview {
                color: #92a0b3;
                padding: 6px 10px;
                font-size: 13px;
            }
            #Display {
                color: #e6f1ff;
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                            stop:0 rgba(23, 30, 64, 190),
                                            stop:1 rgba(21, 18, 40, 190));
                border: 1px solid rgba(255, 255, 255, 24);
                border-radius: 14px;
                padding: 12px 16px;
                selection-background-color: #3a65ff;
                selection-color: white;
            }
            QPushButton {
                font: 600 18px 'Inter';
                border-radius: 14px;
                padding: 10px 14px;
                border: 1px solid rgba(255, 255, 255, 18);
                color: #e6f1ff;
            }
            QPushButton#BtnPrimary {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #1e274f, stop:1 #141a36);
            }
            QPushButton#BtnSecondary {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #1a203f, stop:1 #10142b);
                color: #b9c7dd;
            }
            QPushButton#BtnAccent {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #6d3aff, stop:1 #3a65ff);
                border: 0px solid transparent;
                color: white;
            }
            QPushButton#BtnUtility {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #182045, stop:1 #0f1631);
                color: #d2dcf1;
            }
            QPushButton:hover {
                filter: brightness(110%);
            }
            QPushButton:pressed {
                transform: translateY(1px);
                filter: brightness(96%);
            }
            """
        )

    def _install_shortcuts(self) -> None:
        # Basic digits and operators
        for key in list('0123456789+-*/().'):
            sc = QAction(self)
            sc.setShortcut(QKeySequence(key))
            sc.triggered.connect(lambda checked=False, k=key: self._key_input(k))
            self.addAction(sc)

        # Enter for equals
        enter = QAction(self)
        enter.setShortcut(QKeySequence(Qt.Key_Return))
        enter.triggered.connect(self._on_equals)
        self.addAction(enter)

        enter2 = QAction(self)
        enter2.setShortcut(QKeySequence(Qt.Key_Enter))
        enter2.triggered.connect(self._on_equals)
        self.addAction(enter2)

        back = QAction(self)
        back.setShortcut(QKeySequence(Qt.Key_Backspace))
        back.triggered.connect(self._on_backspace)
        self.addAction(back)

        esc = QAction(self)
        esc.setShortcut(QKeySequence(Qt.Key_Escape))
        esc.triggered.connect(self._on_clear)
        self.addAction(esc)

    def _key_input(self, key: str) -> None:
        mapping = {'*': '×', '/': '÷', '-': '−'}
        if key in mapping:
            self._append_token(mapping[key])
        else:
            self._append_token(key)

    def _on_button(self, mapping: TokenMapping) -> None:
        if mapping.value == 'AC':
            self._on_clear()
            return
        if mapping.value == 'NEG':
            self._toggle_negate()
            return
        if mapping.value == '=':
            self._on_equals()
            return
        if mapping.value == '%':
            self._apply_percent()
            return
        self._append_token(mapping.value)

    def _append_token(self, token: str) -> None:
        if self.display.text() == '0' and token not in ('.', '(', ')'):
            self.display.setText('')
        current = self.display.text()
        # Prevent duplicate operators
        if token in ('+', '−', '×', '÷', '**') and current.endswith(('+', '−', '×', '÷', '**')):
            current = current[:-1]
        self.display.setText(current + token)
        self._update_preview()

    def _on_backspace(self) -> None:
        text = self.display.text()
        if len(text) > 1:
            self.display.setText(text[:-1])
        else:
            self.display.setText('0')
        self._update_preview()

    def _on_clear(self) -> None:
        self.display.setText('0')
        self.preview.setText('')

    def _toggle_negate(self) -> None:
        text = self.display.text()
        if text.startswith('−'):
            self.display.setText(text[1:])
        elif text != '0':
            self.display.setText('−' + text)
        self._update_preview()

    def _apply_percent(self) -> None:
        # Percent of the preceding number
        text = self.display.text()
        try:
            result = self.evaluator.evaluate(text.replace('%', '') + '/100')
            self.display.setText(self._format_result(result))
            self.preview.setText('')
        except Exception:
            self.preview.setText('Error')

    def _on_equals(self) -> None:
        expr = self.display.text()
        try:
            result = self.evaluator.evaluate(expr)
            self.display.setText(self._format_result(result))
            self.preview.setText('')
        except Exception:
            self.preview.setText('Error')

    def _update_preview(self) -> None:
        expr = self.display.text()
        try:
            result = self.evaluator.evaluate(expr)
            self.preview.setText(self._format_result(result))
        except Exception:
            self.preview.setText('')

    def _format_result(self, value: float) -> str:
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return ('{0:.10f}'.format(value)).rstrip('0').rstrip('.')
        return str(value)


def run() -> None:
    app = QApplication(sys.argv)
    window = CalculatorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run()