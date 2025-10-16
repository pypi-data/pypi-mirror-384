"""
Custom Parser 核心模块 - 丰富工具版本
提供大量工具让用户开发更顺利
"""

import re
import inspect
from typing import List, Optional, Any, Callable, Union, Dict, Tuple
from dataclasses import dataclass
from functools import wraps
from contextlib import contextmanager

# =============================================================================
# 基础类型
# =============================================================================

@dataclass
class ParseResult:
    """解析结果"""
    value: Any
    remaining: str
    success: bool = True
    position: int = 0
    
    def __bool__(self):
        return self.success

class ParseError(Exception):
    """解析错误"""
    def __init__(self, message, position=0, expected=None, found=None):
        super().__init__(f"位置 {position}: {message}")
        self.position = position
        self.expected = expected
        self.found = found

# =============================================================================
# 环境和上下文
# =============================================================================

class Context:
    """执行上下文"""
    def __init__(self):
        self.stack = [{}]
    
    def push_scope(self):
        """推入新作用域"""
        self.stack.append({})
    
    def pop_scope(self):
        """弹出作用域"""
        if len(self.stack) > 1:
            return self.stack.pop()
        return {}
    
    def set(self, key, value):
        """设置值"""
        self.stack[-1][key] = value
    
    def get(self, key, default=None):
        """获取值"""
        for scope in reversed(self.stack):
            if key in scope:
                return scope[key]
        return default
    
    @contextmanager
    def scope(self):
        """作用域上下文管理器"""
        self.push_scope()
        try:
            yield
        finally:
            self.pop_scope()

class FunctionRegistry:
    """函数注册表"""
    def __init__(self):
        self.functions = {}
        self.macros = {}
    
    def register(self, name, func, is_macro=False):
        """注册函数或宏"""
        if is_macro:
            self.macros[name] = func
        else:
            self.functions[name] = func
    
    def get(self, name):
        """获取函数或宏"""
        if name in self.macros:
            return self.macros[name], True
        return self.functions.get(name), False
    
    def has(self, name):
        """检查是否存在"""
        return name in self.functions or name in self.macros

class Environment:
    """用户环境"""
    def __init__(self, parent=None):
        self.parent = parent
        self.variables = {}
        self.function_registry = FunctionRegistry()
        self.context = Context()
    
    def set_variable(self, name, value):
        """设置变量"""
        self.variables[name] = value
    
    def get_variable(self, name):
        """获取变量"""
        if name in self.variables:
            return self.variables[name]
        elif self.parent:
            return self.parent.get_variable(name)
        return None
    
    def set_function(self, name, func, is_macro=False):
        """设置函数"""
        self.function_registry.register(name, func, is_macro)
    
    def get_function(self, name):
        """获取函数"""
        return self.function_registry.get(name)
    
    def has_function(self, name):
        """检查函数是否存在"""
        return self.function_registry.has(name)
    
    def child(self):
        """创建子环境"""
        return Environment(self)

# =============================================================================
# 基础解析器 - 大量基础工具
# =============================================================================

class Parser:
    """解析器基类"""
    
    def __init__(self, parse_func: Callable, name=None):
        self.parse_func = parse_func
        self.name = name
        
    def __call__(self, text: str, position=0) -> ParseResult:
        result = self.parse_func(text, position)
        if result.success and self.name:
            result.value = {self.name: result.value}
        return result
    
    def parse(self, text: str) -> Any:
        """解析文本并返回值"""
        result = self(text)
        if not result.success:
            raise ParseError("解析失败", result.position)
        if result.remaining.strip():
            raise ParseError("未完全解析", result.position)
        return result.value
    
    # 运算符重载
    def __add__(self, other):
        return seq(self, other)
    
    def __or__(self, other):
        return either(self, other)
    
    def __rshift__(self, func):
        return action(self, func)
    
    def __invert__(self):
        return optional(self)
    
    def __getitem__(self, key):
        if isinstance(key, slice):
            return count(self, key.start or 0, key.stop or float('inf'))
        return group(self, key)
    
    # 链式方法
    def many(self, min_count=0, max_count=None):
        return many(self, min_count, max_count)
    
    def optional(self, default=None):
        return optional(self, default)
    
    def one_or_more(self):
        return one_or_more(self)
    
    def sep_by(self, separator):
        return separated_by(self, separator)
    
    def end_by(self, terminator):
        return end_by(self, terminator)
    
    def skip(self):
        return skip(self)
    
    def group(self, name=None):
        return group(self, name)
    
    def map(self, func):
        return action(self, func)
    
    def filter(self, predicate):
        return filter_result(self, predicate)
    
    def default(self, default_value):
        return with_default(self, default_value)
    
    def debug(self, label=None):
        return debug_parser(self, label)
    
    def trace(self):
        return trace_parser(self)

def match(pattern: str, flags=0) -> Parser:
    """匹配正则表达式"""
    regex = re.compile(pattern, flags)
    def parse_func(text, pos=0):
        if match := regex.match(text, pos):
            return ParseResult(match.group(), text, True, match.end())
        return ParseResult(None, text, False, pos)
    return Parser(parse_func, f"match({pattern})")

def exact(literal: str) -> Parser:
    """精确匹配字面量"""
    def parse_func(text, pos=0):
        if text.startswith(literal, pos):
            return ParseResult(literal, text, True, pos + len(literal))
        return ParseResult(None, text, False, pos)
    return Parser(parse_func, f"exact('{literal}')")

def regex(pattern: str, flags=0) -> Parser:
    """正则表达式解析器"""
    return match(pattern, flags)

def char(c: str) -> Parser:
    """匹配单个字符"""
    return exact(c)

def any_char() -> Parser:
    """匹配任意字符"""
    return match(r'.')

def char_in(chars: str) -> Parser:
    """匹配字符集中的字符"""
    escaped = re.escape(chars)
    return match(f'[{escaped}]')

def char_not_in(chars: str) -> Parser:
    """匹配不在字符集中的字符"""
    escaped = re.escape(chars)
    return match(f'[^{escaped}]')

# 数字解析器
def integer() -> Parser:
    """解析整数"""
    return match(r'-?\d+') >> int

def float_number() -> Parser:
    """解析浮点数"""
    return match(r'-?\d+\.\d*') >> float

def scientific_number() -> Parser:
    """解析科学计数法数字"""
    return match(r'-?\d+(\.\d*)?[eE][+-]?\d+') >> float

def hex_number() -> Parser:
    """解析十六进制数"""
    return match(r'0[xX][0-9a-fA-F]+') >> (lambda x: int(x, 16))

def binary_number() -> Parser:
    """解析二进制数"""
    return match(r'0[bB][01]+') >> (lambda x: int(x, 2))

def number() -> Parser:
    """解析任何数字"""
    return either(scientific_number(), float_number(), hex_number(), binary_number(), integer())

# 字符串解析器
def quoted_string() -> Parser:
    """解析引号字符串（单或双）"""
    def parse_func(text, pos=0):
        if pos >= len(text):
            return ParseResult(None, text, False, pos)
        
        quote = text[pos]
        if quote not in ('"', "'"):
            return ParseResult(None, text, False, pos)
        
        i = pos + 1
        while i < len(text):
            if text[i] == '\\':
                i += 2
                continue
            if text[i] == quote:
                content = text[pos+1:i]
                # 处理转义
                content = (content.replace('\\n', '\n').replace('\\t', '\t')
                          .replace('\\r', '\r').replace('\\"', '"')
                          .replace("\\'", "'").replace('\\\\', '\\'))
                return ParseResult(content, text, True, i+1)
            i += 1
        return ParseResult(None, text, False, pos)
    return Parser(parse_func, "quoted_string")

def single_quoted_string() -> Parser:
    """解析单引号字符串"""
    return match(r"'([^'\\]*(\\.[^'\\]*)*)'") >> (lambda x: eval(f"'{x[1:-1]}'"))

def double_quoted_string() -> Parser:
    """解析双引号字符串"""
    return match(r'"([^"\\]*(\\.[^"\\]*)*)"') >> (lambda x: eval(f'"{x[1:-1]}"'))

def string() -> Parser:
    """解析字符串"""
    return quoted_string()

def string_literal(literal: str) -> Parser:
    """字符串字面量"""
    return exact(literal) >> (lambda x: literal)

def number_literal(value: Union[int, float]) -> Parser:
    """数字字面量"""
    return number().filter(lambda x: x == value)

def boolean_literal(value: bool) -> Parser:
    """布尔字面量"""
    if value:
        return exact("true") >> (lambda x: True)
    else:
        return exact("false") >> (lambda x: False)

# 标识符和单词
def identifier() -> Parser:
    """解析标识符"""
    return match(r'[a-zA-Z_]\w*')

def word(chars: str = None) -> Parser:
    """解析单词"""
    if chars:
        return match(f'[{re.escape(chars)}]+')
    return match(r'\w+')

def alphanumeric() -> Parser:
    """解析字母数字"""
    return match(r'[a-zA-Z0-9]+')

def whitespace() -> Parser:
    """解析空白字符"""
    return match(r'\s*').skip()

# =============================================================================
# 组合器 - 丰富的组合工具
# =============================================================================

def seq(*parsers, **named_parsers) -> Parser:
    """顺序组合"""
    if named_parsers:
        parsers = list(parsers) + [group(p, name) for name, p in named_parsers.items()]
    
    def parse_func(text, pos=0):
        values = []
        current_pos = pos
        for parser in parsers:
            result = parser(text, current_pos)
            if not result:
                return ParseResult(None, text, False, pos)
            if result.value is not None:
                values.append(result.value)
            current_pos = result.position
        return ParseResult(values, text, True, current_pos)
    return Parser(parse_func, "seq")

def either(*parsers) -> Parser:
    """选择组合"""
    def parse_func(text, pos=0):
        for parser in parsers:
            result = parser(text, pos)
            if result:
                return result
        return ParseResult(None, text, False, pos)
    return Parser(parse_func, "either")

def many(parser, min_count=0, max_count=None) -> Parser:
    """重复零次或多次"""
    def parse_func(text, pos=0):
        values = []
        current_pos = pos
        count = 0
        
        while True:
            if max_count and count >= max_count:
                break
            result = parser(text, current_pos)
            if not result:
                break
            if result.value is not None:
                values.append(result.value)
            current_pos = result.position
            count += 1
            if current_pos == pos:  # 防止无限循环
                break
            pos = current_pos
        
        if count < min_count:
            return ParseResult(None, text, False, pos)
        return ParseResult(values, text, True, current_pos)
    return Parser(parse_func, "many")

def one_or_more(parser) -> Parser:
    """重复一次或多次"""
    return many(parser, min_count=1)

def optional(parser, default=None) -> Parser:
    """可选"""
    def parse_func(text, pos=0):
        result = parser(text, pos)
        if result:
            return result
        return ParseResult(default, text, True, pos)
    return Parser(parse_func, "optional")

def separated_by(parser, separator, min_count=0) -> Parser:
    """分隔的列表"""
    def parse_func(text, pos=0):
        values = []
        current_pos = pos
        
        # 第一个元素
        first_result = parser(text, current_pos)
        if not first_result:
            if min_count <= 0:
                return ParseResult([], text, True, pos)
            return ParseResult(None, text, False, pos)
        
        values.append(first_result.value)
        current_pos = first_result.position
        
        # 后续元素
        while True:
            # 分隔符
            sep_result = separator(text, current_pos)
            if not sep_result:
                break
            
            # 元素
            elem_result = parser(text, sep_result.position)
            if not elem_result:
                break
                
            values.append(elem_result.value)
            current_pos = elem_result.position
        
        if len(values) < min_count:
            return ParseResult(None, text, False, pos)
        return ParseResult(values, text, True, current_pos)
    return Parser(parse_func, "separated_by")

def end_by(parser, terminator) -> Parser:
    """以终止符结束的列表"""
    return separated_by(parser, terminator) + terminator

def count(parser, n: int) -> Parser:
    """精确重复n次"""
    return many(parser, min_count=n, max_count=n)

def group(parser, name: str = None) -> Parser:
    """分组"""
    if name:
        return Parser(parser.parse_func, name)
    return parser

def skip(parser) -> Parser:
    """跳过结果"""
    return action(parser, lambda x: None)

def forward() -> Parser:
    """前向声明"""
    def parse_func(text, pos=0):
        if not hasattr(parse_func, 'parser'):
            raise ParseError("前向解析器未定义", pos)
        return parse_func.parser(text, pos)
    
    parser = Parser(parse_func, "forward")
    
    def define(p):
        parse_func.parser = p
        return p
    
    parser.define = define
    return parser

def lazy(parser_func: Callable) -> Parser:
    """延迟解析器"""
    def parse_func(text, pos=0):
        return parser_func()(text, pos)
    return Parser(parse_func, "lazy")

# =============================================================================
# 语义动作和转换
# =============================================================================

def action(parser, func: Callable) -> Parser:
    """应用函数到结果"""
    def parse_func(text, pos=0):
        result = parser(text, pos)
        if result and result.value is not None:
            try:
                result.value = func(result.value)
            except Exception as e:
                return ParseResult(None, text, False, pos)
        return result
    return Parser(parse_func, f"action({parser.name})")

def transform(parser, mapping: Dict) -> Parser:
    """根据映射转换结果"""
    return action(parser, lambda x: mapping.get(x, x))

def map_result(parser, func: Callable) -> Parser:
    """映射结果（包含整个ParseResult）"""
    def parse_func(text, pos=0):
        result = parser(text, pos)
        if result:
            return func(result)
        return result
    return Parser(parse_func, f"map_result({parser.name})")

def filter_result(parser, predicate: Callable) -> Parser:
    """过滤结果"""
    def parse_func(text, pos=0):
        result = parser(text, pos)
        if result and predicate(result.value):
            return result
        return ParseResult(None, text, False, pos)
    return Parser(parse_func, f"filter({parser.name})")

def with_default(parser, default_value) -> Parser:
    """提供默认值"""
    def parse_func(text, pos=0):
        result = parser(text, pos)
        if not result:
            return ParseResult(default_value, text, True, pos)
        return result
    return Parser(parse_func, f"default({parser.name})")

def try_parse(parser) -> Parser:
    """尝试解析，不抛出异常"""
    def parse_func(text, pos=0):
        try:
            return parser(text, pos)
        except ParseError:
            return ParseResult(None, text, False, pos)
    return Parser(parse_func, f"try({parser.name})")

# =============================================================================
# 预构建解析器
# =============================================================================

def expression() -> Parser:
    """表达式解析器"""
    expr = forward()
    
    # 基础项
    term = either(
        number(),
        string(),
        identifier(),
        (exact('(') + whitespace() + expr + whitespace() + exact(')')) >> (lambda x: x[2])
    )
    
    # 乘除
    product = (term + many((either(exact('*'), exact('/')) + term))) >> (
        lambda x: _eval_binary(x[0], x[1])
    )
    
    # 加减
    expr.define(product + many((either(exact('+'), exact('-')) + product)) >> (
        lambda x: _eval_binary(x[0], x[1])
    ))
    
    return expr

def _eval_binary(left, operations):
    """求值二元运算"""
    result = left
    for op, right in operations:
        if op == '+':
            result += right
        elif op == '-':
            result -= right
        elif op == '*':
            result *= right
        elif op == '/':
            result /= right
    return result

def function_call() -> Parser:
    """函数调用"""
    return (
        identifier().group("function") +
        exact('(').skip() +
        whitespace().skip() +
        argument_list().group("arguments").optional([]) +
        whitespace().skip() +
        exact(')').skip()
    ) >> (lambda x: {'type': 'call', 'function': x['function'], 'arguments': x['arguments']})

def argument_list() -> Parser:
    """参数列表"""
    return separated_by(expression(), exact(',').skip() + whitespace().skip())

def assignment() -> Parser:
    """赋值语句"""
    return (
        identifier().group("variable") +
        whitespace().skip() +
        exact('=').skip() +
        whitespace().skip() +
        expression().group("value")
    ) >> (lambda x: {'type': 'assignment', 'variable': x['variable'], 'value': x['value']})

# =============================================================================
# 调试和测试工具
# =============================================================================

def debug_parser(parser, label=None) -> Parser:
    """调试解析器"""
    label = label or parser.name
    
    def parse_func(text, pos=0):
        print(f"[DEBUG {label}] 位置 {pos}, 输入: {repr(text[pos:pos+20])}...")
        result = parser(text, pos)
        if result.success:
            print(f"[DEBUG {label}] 成功: {repr(result.value)}")
        else:
            print(f"[DEBUG {label}] 失败")
        return result
    
    return Parser(parse_func, f"debug({label})")

def trace_parser(parser) -> Parser:
    """跟踪解析器"""
    indent = 0
    
    def parse_func(text, pos=0):
        nonlocal indent
        spaces = "  " * indent
        print(f"{spaces}> {parser.name} at {pos}: {repr(text[pos:pos+10])}...")
        indent += 1
        result = parser(text, pos)
        indent -= 1
        spaces = "  " * indent
        status = "成功" if result.success else "失败"
        print(f"{spaces}< {parser.name} {status}: {repr(result.value)}")
        return result
    
    return Parser(parse_func, f"trace({parser.name})")

def test_parser(parser, test_cases: List[Tuple[str, Any]]) -> bool:
    """测试解析器"""
    print(f"测试解析器: {parser.name}")
    all_passed = True
    
    for i, (input_text, expected) in enumerate(test_cases):
        try:
            result = parse(parser, input_text)
            if result == expected:
                print(f"  ✓ 测试 {i+1}: {input_text} -> {result}")
            else:
                print(f"  ✗ 测试 {i+1}: {input_text} -> {result} (期望: {expected})")
                all_passed = False
        except ParseError as e:
            print(f"  ✗ 测试 {i+1}: {input_text} -> 错误: {e}")
            all_passed = False
    
    return all_passed

# =============================================================================
# 流处理
# =============================================================================

class ParserStream:
    """解析器流"""
    def __init__(self, text: str):
        self.text = text
        self.position = 0
    
    def read(self, parser) -> Any:
        """读取并解析"""
        result = parser(self.text, self.position)
        if result.success:
            self.position = result.position
            return result.value
        raise ParseError(f"解析失败", self.position)
    
    def peek(self, parser) -> Any:
        """窥视但不移动位置"""
        result = parser(self.text, self.position)
        return result.value if result.success else None
    
    def skip(self, parser) -> bool:
        """跳过匹配的内容"""
        result = parser(self.text, self.position)
        if result.success:
            self.position = result.position
            return True
        return False
    
    def eof(self) -> bool:
        """是否到文件结尾"""
        return self.position >= len(self.text)

def tokenize(parser, text: str) -> List[Any]:
    """分词"""
    stream = ParserStream(text)
    tokens = []
    
    while not stream.eof():
        try:
            token = stream.read(parser)
            if token is not None:
                tokens.append(token)
        except ParseError:
            # 跳过无法解析的字符
            stream.position += 1
    
    return tokens

def transform_tokens(parser, transformer: Callable, text: str) -> str:
    """转换token"""
    stream = ParserStream(text)
    result = []
    last_pos = 0
    
    while not stream.eof():
        start_pos = stream.position
        try:
            token = stream.read(parser)
            if token is not None:
                # 添加前面的文本
                result.append(text[last_pos:start_pos])
                # 添加转换后的token
                result.append(transformer(token))
                last_pos = stream.position
        except ParseError:
            stream.position += 1
    
    # 添加剩余文本
    result.append(text[last_pos:])
    return ''.join(result)

# =============================================================================
# 高级工具函数
# =============================================================================

def create_parser() -> Dict[str, Any]:
    """创建解析器工具包"""
    return {name: obj for name, obj in globals().items() 
            if not name.startswith('_') and callable(obj) and obj != create_parser}

def define_language() -> Any:
    """定义语言的入口点"""
    tools = create_parser()
    
    class LanguageDefiner:
        def __init__(self):
            self.env = Environment()
            self.tools = tools
            self.parsers = {}
        
        def parser(self, name):
            """定义解析器装饰器"""
            def decorator(parser_func):
                self.parsers[name] = parser_func()
                return parser_func
            return decorator
        
        def function(self, name, is_macro=False):
            """定义函数装饰器"""
            def decorator(func):
                self.env.set_function(name, func, is_macro)
                return func
            return decorator
        
        def variable(self, name, value):
            """定义变量"""
            self.env.set_variable(name, value)
        
        def build(self):
            """构建语言"""
            return self.parsers, self.env
    
    return LanguageDefiner()

def build_language(definitions: Dict[str, Parser], env: Environment = None) -> Any:
    """构建完整语言"""
    if env is None:
        env = Environment()
    
    class Language:
        def __init__(self):
            self.parsers = definitions
            self.env = env
        
        def parse(self, code: str, start: str = "program") -> Any:
            """解析代码"""
            if start not in self.parsers:
                raise ValueError(f"未知的起始解析器: {start}")
            return parse(self.parsers[start], code)
        
        def execute(self, code: str, start: str = "program") -> Any:
            """解析并执行代码"""
            parsed = self.parse(code, start)
            return self._execute(parsed)
        
        def _execute(self, parsed):
            """执行解析结果"""
            if isinstance(parsed, dict):
                if parsed.get('type') == 'call':
                    func_name = parsed['function']
                    args = [self._execute(arg) for arg in parsed['arguments']]
                    
                    func, is_macro = self.env.get_function(func_name)
                    if func:
                        return func(*args)
                    else:
                        return f"未定义函数: {func_name}"
                elif parsed.get('type') == 'assignment':
                    var_name = parsed['variable']
                    value = self._execute(parsed['value'])
                    self.env.set_variable(var_name, value)
                    return value
            elif isinstance(parsed, list):
                return [self._execute(item) for item in parsed]
            return parsed
    
    return Language()

# =============================================================================
# 工具函数
# =============================================================================

def parse(parser, text: str) -> Any:
    """使用解析器解析文本"""
    return parser.parse(text)

def run_parser(parser, text: str) -> ParseResult:
    """运行解析器并返回结果"""
    return parser(text)

# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 演示丰富的工具集
    print("=== 丰富工具集演示 ===")
    
    # 创建语言定义器
    lang_tools = define_language()
    
    # 用户定义解析器
    @lang_tools.parser("program")
    def program_parser():
        return many(lang_tools.parsers["statement"])
    
    @lang_tools.parser("statement")
    def statement_parser():
        return either(
            lang_tools.parsers["function_call"],
            lang_tools.parsers["assignment"]
        )
    
    @lang_tools.parser("function_call")
    def function_call_parser():
        return function_call()
    
    @lang_tools.parser("assignment")
    def assignment_parser():
        return assignment()
    
    # 用户定义函数
    @lang_tools.function("zero")
    def user_zero():
        return 0
    
    @lang_tools.function("add")
    def user_add(a, b):
        return a + b
    
    @lang_tools.function("Prout")
    def user_prout(*args):
        print("用户输出:", *args)
        return args[-1] if args else None
    
    # 构建语言
    parsers, env = lang_tools.build()
    language = build_language(parsers, env)
    
    # 测试
    test_code = """
    Prout(zero())
    Prout(add(2, 3))
    x = add(5, 10)
    Prout(x)
    """
    
    print("执行代码:")
    print(test_code)
    
    try:
        result = language.execute(test_code)
        print("执行结果:", result)
    except Exception as e:
        print("错误:", e)
