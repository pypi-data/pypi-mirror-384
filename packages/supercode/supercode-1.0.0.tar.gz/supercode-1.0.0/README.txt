🎯 什么是 SuperCode？
SuperCode 是一个完全自由的解析器构建工具包。与其他解析器不同，你拥有完全的控制权：

✅ 你定义语法规则 - 没有预设的语法限制

✅ 你命名函数 - 想叫什么就叫什么 (Prout、output、whatever)

✅ 你决定行为 - 每个函数做什么完全由你决定

✅ 你控制执行 - 如何执行代码由你说了算

🚀 5分钟快速入门
安装
bash
pip install supercode
第一个例子：让 Prout('hello') 输出 "hello"
python
from supercode import *

# 1. 创建环境（存储你的函数）
env = Environment()

# 2. 定义你的函数 - 完全自由！
def my_output_function(*args):
    """你决定这个函数做什么"""
    print("🦜:", *args)  # 添加个鹦鹉图标，多可爱！
    return "Output completed"

def add_numbers(a, b):
    return a + b

def return_zero():
    return 0

# 3. 注册函数 - 名字你随便起！
env.set_function("Prout", my_output_function)      # 用法: Prout('hello')
env.set_function("add", add_numbers)               # 用法: add(1, 2)
env.set_function("zero", return_zero)              # 用法: zero()

# 4. 使用预置的解析器（也可以自己定义）
parser = function_call()

# 5. 解析并执行代码
code = "Prout(add(2, 3), zero())"
parsed_result = parse(parser, code)

print(f"📝 Parsed result: {parsed_result}")

# 执行函数调用
if parsed_result['type'] == 'call':
    func_name = parsed_result['function']
    arguments = parsed_result['arguments']
    
    # 从环境中获取你的函数
    func, _ = env.get_function(func_name)
    if func:
        execution_result = func(*arguments)
        print(f"🎯 Execution result: {execution_result}")
运行结果:

text
📝 Parsed result: {'type': 'call', 'function': 'Prout', 'arguments': [5, 0]}
🦜: 5 0
🎯 Execution result: Output completed


🎪 试试这些有趣的例子
例子1：创意函数名
python
from supercode import *

env = Environment()

# 发挥创意，起任何你喜欢的名字！
env.set_function("yell", lambda *args: print("!!!", *args, "!!!"))
env.set_function("whisper", lambda *args: print("...", *args, "..."))
env.set_function("celebrate", lambda: print("🎉 Party time! 🎉"))

# 使用
code = "yell('Hello'); whisper('secret'); celebrate()"
# 输出: !!! Hello !!! ... secret ... 🎉 Party time! 🎉
例子2：数学运算
python
from supercode import *

env = Environment()

env.set_function("sum", lambda *args: sum(args))
env.set_function("product", lambda *args: 
    [args[0] * arg for arg in args[1:]] if len(args) > 1 else args[0])
env.set_function("power", lambda x, y: x ** y)

code = "sum(1, 2, 3, 4, 5)"  # 返回 15
code = "power(2, 8)"         # 返回 256
例子3：字符串操作
python
from supercode import *

env = Environment()

env.set_function("shout", lambda text: text.upper() + "!")
env.set_function("repeat", lambda text, times: text * times)
env.set_function("decorate", lambda text: f"✨ {text} ✨")

code = 'shout("hello")'          # 返回 "HELLO!"
code = 'repeat("ha", 3)'         # 返回 "hahaha"
code = 'decorate("amazing")'     # 返回 "✨ amazing ✨"
🧩 核心概念详解
1. 解析器 (Parser)
解析器是识别文本模式的工具：

python
from supercode import *

# 基础解析器
number_parser = number()           # 解析数字: "123" → 123
string_parser = string()           # 解析字符串: '"hello"' → "hello"
identifier_parser = identifier()   # 解析标识符: "myVar" → "myVar"
exact_parser = exact("hello")      # 精确匹配: "hello" → "hello"
regex_parser = match(r'\d+')       # 正则匹配: "123" → "123"

# 使用
result1 = parse(number_parser, "42")      # 返回 42
result2 = parse(string_parser, '"world"') # 返回 "world"
2. 组合器 (Combinator)
组合器让你构建复杂语法：

python
from supercode import *

# 顺序组合: parser1 + parser2
function_call = identifier() + exact('(') + number() + exact(')')

# 选择组合: parser1 | parser2  
color = exact("red") | exact("blue") | exact("green")

# 重复: parser.many()
number_list = number().many()              # "1 2 3" → [1, 2, 3]
at_least_one = number().one_or_more()     # 至少一个数字
optional_hello = exact("hello").optional() # 可选的"hello"

# 分隔: parser.sep_by(separator)
comma_separated = number().sep_by(exact(','))  # "1,2,3" → [1, 2, 3]

# 使用
result1 = parse(function_call, "test(123)")    # 返回 ['test', '(', 123, ')']
result2 = parse(color, "blue")                 # 返回 "blue"
result3 = parse(number_list, "1 2 3")         # 返回 [1, 2, 3]
3. 语义动作 (Action)
语义动作处理解析结果：

python
from supercode import *

# 转换结果
uppercase = match(r'[a-z]+') >> (lambda x: x.upper())

# 数学运算
addition = (number() + exact('+') + number()) >> (lambda x: x[0] + x[2])

# 构建数据结构
point = (exact('(') + number() + exact(',') + number() + exact(')')) >> (
    lambda x: {'x': x[1], 'y': x[3]}
)

# 使用
result1 = parse(uppercase, "hello")    # 返回 "HELLO"
result2 = parse(addition, "5+3")       # 返回 8
result3 = parse(point, "(10,20)")      # 返回 {'x': 10, 'y': 20}
4. 环境 (Environment)
环境存储你的函数和变量：

python
from supercode import *

env = Environment()

# 注册函数
env.set_function("double", lambda x: x * 2)
env.set_function("greet", lambda name: f"Hello, {name}!")
env.set_function("random_color", lambda: random.choice(["red", "blue", "green"]))

# 设置变量
env.set_variable("PI", 3.14159)
env.set_variable("VERSION", "1.0.0")

# 获取和使用
func, is_macro = env.get_function("double")
result = func(5)  # 返回 10

pi_value = env.get_variable("PI")  # 返回 3.14159
🛠️ 完整工具参考
基础解析器
python
# 字符级解析器
char('a')                    # 匹配单个字符 'a'
any_char()                   # 匹配任意字符
char_in("abc")              # 匹配 a、b 或 c
char_not_in("abc")          # 匹配除 a、b、c 外的字符

# 文本级解析器  
exact("hello")              # 精确匹配
match(r'\d+')               # 正则匹配
regex(r'[A-Z][a-z]*')       # 正则表达式

# 字面量解析器
number()                    # 数字: 123, 3.14, -42
string()                    # 字符串: "hello", 'world'
identifier()                # 标识符: myVar, _temp
whitespace()                # 空白字符

# 数字变体
integer()                   # 整数: 123, -456
float_number()              # 浮点数: 3.14, -2.5
组合器大全
python
# 基础组合
p1 + p2                     # 顺序组合: 依次匹配
p1 | p2                     # 选择组合: 匹配第一个成功的
p.many()                    # 零个或多个
p.one_or_more()             # 一个或多个  
p.optional(default=None)    # 可选，可提供默认值
p.sep_by(separator)         # 分隔的列表

# 高级组合
separated_by(p, sep)        # 分隔组合
end_by(p, term)             # 以终止符结束
count(p, n)                 # 精确重复n次
group(p, name)              # 分组并命名
skip(p)                     # 匹配但跳过结果
forward()                   # 前向声明（用于递归语法）
lazy(lambda: p)             # 延迟解析

# 链式调用（更优雅的写法）
parser = (identifier()
         .skip(exact('('))
         .then(argument_list().optional([]))
         .skip(exact(')'))
         .map(lambda x: {'function': x[0], 'args': x[1]}))
语义动作
python
# 基础动作
p >> func                   # 对结果应用函数
p.map(func)                 # 映射结果
p.filter(predicate)         # 过滤结果
p.default(value)            # 提供默认值

# 高级动作
transform(p, mapping)       # 根据字典映射转换
try_parse(p)                # 尝试解析，失败不抛异常
map_result(p, func)         # 映射整个 ParseResult

# 使用示例
parser = (number() 
          .filter(lambda x: x > 0)     # 只接受正数
          .map(lambda x: x * 2)        # 乘以2
          .default(0))                 # 失败时返回0
预构建解析器
python
expression()                # 数学表达式: 1 + 2 * 3
function_call()             # 函数调用: func(1, 2, 3)
argument_list()             # 参数列表: 1, 2, "hello"
assignment()                # 赋值语句: x = 42
📚 实战项目示例
项目1：简单计算器
python
from supercode import *
import math

class SimpleCalculator:
    def __init__(self):
        self.env = Environment()
        self.setup_functions()
        self.parser = expression()  # 使用预置的表达式解析器
    
    def setup_functions(self):
        """设置计算器函数"""
        self.env.set_function("sin", math.sin)
        self.env.set_function("cos", math.cos)
        self.env.set_function("sqrt", math.sqrt)
        self.env.set_function("log", math.log)
        self.env.set_function("abs", abs)
        self.env.set_function("round", round)
    
    def calculate(self, expression):
        """计算表达式"""
        try:
            result = parse(self.parser, expression)
            return result
        except ParseError as e:
            return f"Calculation error: {e}"

# 使用计算器
calc = SimpleCalculator()
print(calc.calculate("3 + 4 * (2 - 1)"))     # 7
print(calc.calculate("sin(0) + cos(0)"))     # 1.0
print(calc.calculate("sqrt(16) + abs(-5)"))  # 9.0
项目2：配置语言
python
from supercode import *

def create_config_parser():
    """创建配置解析器"""
    return (
        identifier().group("key") +
        exact('=').skip() +
        (number() | string() | boolean_literal(True) | boolean_literal(False)).group("value") +
        optional(exact(';').skip())
    ).many() >> (lambda configs: dict(configs))

# 解析配置文件
config_parser = create_config_parser()
config_text = """
host = "localhost"
port = 8080
debug = true
timeout = 30
"""

config = parse(config_parser, config_text)
print(config)
# 输出: {'host': 'localhost', 'port': 8080, 'debug': True, 'timeout': 30}
项目3：命令系统
python
from supercode import *

class CommandSystem:
    def __init__(self):
        self.commands = {}
        self.parser = self.create_command_parser()
    
    def create_command_parser(self):
        """创建命令解析器"""
        return (
            identifier().group("command") +
            exact('(').skip() +
            argument_list().group("args").optional([]) +
            exact(')').skip()
        ) >> (lambda x: {
            'command': x['command'],
            'arguments': x['args']
        })
    
    def register(self, name):
        """注册命令装饰器"""
        def decorator(func):
            self.commands[name] = func
            return func
        return decorator
    
    def execute(self, code):
        """执行命令"""
        parsed = parse(self.parser, code)
        command_name = parsed['command']
        args = parsed['arguments']
        
        if command_name in self.commands:
            return self.commands[command_name](*args)
        else:
            return f"Unknown command: {command_name}"

# 使用命令系统
system = CommandSystem()

@system.register("greet")
def handle_greet(name="World"):
    return f"Hello, {name}!"

@system.register("calculate")
def handle_calculate(expression):
    return f"Result: {eval(expression)}"

@system.register("Prout")
def handle_prout(*args):
    output = " ".join(str(arg) for arg in args)
    print(f"🦜 {output}")
    return "Printed successfully"

# 执行命令
print(system.execute('greet("Python")'))        # Hello, Python!
print(system.execute('calculate("2 + 3 * 4")')) # Result: 14
system.execute('Prout("Hello", "World")')       # 🦜 Hello World
项目4：数据查询语言
python
from supercode import *

def create_query_parser():
    """创建简单查询语言解析器"""
    query = forward()
    
    select_parser = (
        exact("SELECT").skip() +
        separated_by(identifier(), exact(',').skip()).group("fields") +
        exact("FROM").skip() +
        identifier().group("table") +
        optional(
            exact("WHERE").skip() +
            identifier().group("field") +
            (exact("=") | exact(">") | exact("<")).group("operator") +
            (number() | string()).group("value")
        ).group("where").optional(None) +
        optional(
            exact("ORDER BY").skip() +
            identifier().group("order_field") +
            optional(exact("ASC") | exact("DESC")).group("direction").optional("ASC")
        ).group("order").optional(None)
    ) >> (lambda x: {
        'type': 'select',
        'fields': x['fields'],
        'table': x['table'],
        'where': x['where'],
        'order': x['order']
    })
    
    query.define(select_parser)
    return query

# 使用查询解析器
query_parser = create_query_parser()

queries = [
    "SELECT name, age FROM users",
    "SELECT * FROM products WHERE price > 100",
    "SELECT id, title FROM articles ORDER BY created_at DESC"
]

for query in queries:
    result = parse(query_parser, query)
    print(f"Query: {query}")
    print(f"Parsed: {result}\n")
💻 命令行使用
SuperCode 提供了强大的命令行工具：

bash
# 安装后即可使用
supercode --help

# 交互式开发环境（推荐新手使用）
supercode --interactive

# 解析单个表达式
supercode "add(1, 2)"
supercode 'Prout("Hello World")'

# 运行演示
supercode --demo

# 查看特定示例
supercode --example function_call
supercode --example expression

# 显示代码模板
supercode --template simple
supercode --template dsl
supercode --template command
交互模式示例
bash
$ supercode --interactive
=== SuperCode Interactive Mode ===
Type 'help' for commands, 'exit' to quit

supercode> add(1, 2)
📝 Parsed: {'type': 'call', 'function': 'add', 'arguments': [1, 2]}

supercode> Prout("Hello", "World")
📝 Parsed: {'type': 'call', 'function': 'Prout', 'arguments': ['Hello', 'World']}

supercode> x = 10
📝 Parsed: {'type': 'assignment', 'variable': 'x', 'value': 10}

supercode> 3 + 4 * 2
📝 Parsed: 11

supercode> help
Available commands:
  help     - Show this help
  exit     - Exit interactive mode
  Or just type any code to parse it!

supercode> exit
Goodbye! 👋
🔧 高级特性
错误处理
python
from supercode import *

# 基本错误处理
try:
    result = parse(parser, code)
except ParseError as e:
    print(f"Parse error at position {e.position}: {e}")
    print(f"Expected: {e.expected}, Found: {e.found}")

# 健壮解析（不抛出异常）
robust_parser = try_parse(function_call())
result = run_parser(robust_parser, potentially_bad_code)
if result.success:
    print(f"Success: {result.value}")
else:
    print(f"Failed at position: {result.position}")

# 错误恢复
multiple_parsers = many(try_parse(number() | string()))
result = parse(multiple_parsers, "1 'hello' error 2")  # 返回 [1, 'hello', 2]
调试工具
python
from supercode import *

# 调试解析器
debug_parser = (
    identifier().debug("identifier") +
    exact('(').debug("left_paren") +
    argument_list().debug("arguments") +
    exact(')').debug("right_paren")
)

# 会显示详细的调试信息
parse(debug_parser, "test(1,2)")

# 跟踪解析过程
trace_parser = trace_parser(function_call())
parse(trace_parser, "example(123)")

# 自动化测试
test_cases = [
    ("add(1,2)", {'type': 'call', 'function': 'add', 'arguments': [1, 2]}),
    ("zero()", {'type': 'call', 'function': 'zero', 'arguments': []}),
]
test_parser(function_call(), test_cases)
性能优化
python
from supercode import *

# 预编译复杂解析器（提高性能）
complex_parser = (
    identifier().group("func") +
    exact('(').skip() +
    separated_by(expression(), exact(',').skip()).group("args") +
    exact(')').skip()
).map(lambda x: {'call': x['func'], 'arguments': x['args']})

# 重复使用解析器（避免重复创建）
def create_efficient_parser():
    parser = function_call()  # 创建一次，多次使用
    return parser

efficient_parser = create_efficient_parser()
🎯 最佳实践
1. 设计清晰的语法
python
# ✅ 好的设计 - 清晰一致
command_parser = (
    identifier().group("command") +
    exact('(').skip() +
    argument_list().group("args") +
    exact(')').skip()
)

# ❌ 避免 - 过于复杂
complex_parser = (many(identifier() | number()) + optional(exact(','))

# ✅ 使用语义动作让结果更有意义
clean_parser = command_parser >> (
    lambda x: {'type': 'command', 'name': x['command'], 'arguments': x['args']}
)
2. 合理的错误处理
python
def safe_parse(parser, code, default=None):
    """安全的解析函数"""
    try:
        return parse(parser, code)
    except ParseError as e:
        print(f"Parse failed: {e}")
        return default

# 使用
result = safe_parse(my_parser, user_input, default="Parse error")
3. 模块化设计
python
def create_expression_parser():
    """创建表达式解析器"""
    expr = forward()
    term = number() | (exact('(') + expr + exact(')'))
    expr.define(_build_operators(term))
    return expr

def create_statement_parser():
    """创建语句解析器"""
    return either(
        create_assignment_parser(),
        create_function_call_parser(),
        create_expression_parser()
    )

def create_program_parser():
    """创建程序解析器"""
    return many(create_statement_parser())
❓ 常见问题解答
Q: 如何处理中文字符？
A: 完全支持！标识符解析器支持Unicode字符：

python
chinese_parser = match(r'[\u4e00-\u9fff]+')  # 匹配中文字符
result = parse(chinese_parser, "你好世界")   # 返回 "你好世界"

# 或者在标识符中使用中文
env.set_function("打印", lambda *args: print(*args))
env.set_function("计算", lambda x: x * 2)
Q: 如何解析嵌套结构？
A: 使用前向声明(forward)：

python
expression = forward()
term = number() | (exact('(') + expression + exact(')'))
expression.define(term + many((exact('+') + term)))

result = parse(expression, "(1+2)+(3+4)")  # 正确处理嵌套
Q: 性能如何？能处理多大数据？
A: 经过优化，可以处理大多数场景：

小型脚本和配置：毫秒级

中等复杂度语言：秒级

对于高性能需求，建议预编译解析器

Q: 如何调试复杂的解析问题？
A: 使用内置调试工具：

python
# 1. 使用 debug()
debug_parser = your_parser.debug("label")

# 2. 使用 trace()
trace_parser = trace_parser(your_parser)

# 3. 分解复杂解析器
part1 = first_part.debug("part1")
part2 = second_part.debug("part2")
Q: 可以处理多行代码吗？
A: 当然！只需定义适当的语句分隔符：

python
program_parser = many(statement_parser + optional(exact(';').skip()))

code = """
x = 10;
y = 20;
result = add(x, y);
print(result)
"""
🚀 下一步
想要深入学习？
探索示例: 运行 supercode --demo 查看所有示例

实验: 使用 supercode --interactive 在交互模式中尝试

构建项目: 从简单的计算器开始，逐步构建复杂语言

阅读源码: SuperCode 的源码本身就是很好的学习材料