"""
SuperCode 主模块 - 精简版本
"""

from .core import *

def main():
    """命令行主入口点"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='SuperCode - 自定义代码解析器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  supercode --demo                      # 运行演示
  supercode --example function_call     # 运行函数调用示例
  supercode --template dsl              # 显示DSL模板
  supercode "add(1, 2)"                 # 解析单个表达式
  supercode --interactive               # 交互模式
        '''
    )
    
    parser.add_argument('code', nargs='?', help='要解析的代码')
    parser.add_argument('--demo', action='store_true', help='运行演示')
    parser.add_argument('--example', choices=['function_call', 'expression'], 
                       help='运行特定示例')
    parser.add_argument('--template', choices=['simple', 'dsl', 'command'], 
                       help='显示代码模板')
    parser.add_argument('--interactive', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    try:
        if args.demo:
            run_complete_demo()
        elif args.example:
            run_example(args.example)
        elif args.template:
            show_template(args.template)
        elif args.interactive or not args.code:
            start_interactive_mode()
        elif args.code:
            process_code(args.code)
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n退出 SuperCode")
    except Exception as e:
        print(f"错误: {e}")

def quick_start():
    """快速启动指南"""
    print("=== SuperCode 快速启动 ===")
    
    env = Environment()
    tools = create_parser()
    
    print("可用工具:", list(tools.keys())[:10], "...")  # 只显示前10个
    
    simple_parser = create_simple_parser()
    
    return {
        'env': env,
        'tools': tools,
        'parser': simple_parser
    }

# 移除文件相关函数，只保留核心功能
def start_interactive_mode():
    """启动交互式模式"""
    print("=== SuperCode 交互模式 ===")
    print("输入 'help' 查看命令, 'exit' 退出")
    
    quick_env = quick_start()
    env = quick_env['env']
    parser = quick_env['parser']
    
    while True:
        try:
            user_input = input("\nsupercode> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ('exit', 'quit', 'q'):
                break
            elif user_input.lower() == 'help':
                print("命令: help, exit, 或直接输入代码进行解析")
            else:
                process_user_input(user_input, parser, env)
                
        except KeyboardInterrupt:
            print("\n使用 'exit' 退出")
        except EOFError:
            break
        except Exception as e:
            print(f"错误: {e}")

def process_user_input(user_input, parser, env):
    """处理用户输入"""
    try:
        parsed = parse(parser, user_input)
        print(f"解析: {parsed}")
            
    except ParseError as e:
        print(f"解析错误: {e}")

def process_code(code: str):
    """处理代码"""
    parser = create_simple_parser()
    
    try:
        result = parse(parser, code)
        print(f"解析结果: {result}")
    except ParseError as e:
        print(f"解析错误: {e}")

# 保留核心示例功能
def run_complete_demo():
    """运行完整演示"""
    print("=== SuperCode 完整演示 ===")
    example_function_call()
    print("\n" + "="*50)
    example_expression()

def run_example(example_name: str):
    """运行特定示例"""
    examples = {
        'function_call': example_function_call,
        'expression': example_expression,
    }
    
    if example_name in examples:
        examples[example_name]()
    else:
        print(f"未知示例: {example_name}")

def show_template(template_name: str):
    """显示代码模板"""
    templates = {
        'simple': template_simple_lang,
        'dsl': template_dsl, 
        'command': template_command_system,
    }
    
    if template_name in templates:
        print(f"=== {template_name.upper()} 模板 ===")
        print(templates[template_name]())
    else:
        print(f"未知模板: {template_name}")

# 保留核心示例函数
def example_function_call():
    """函数调用解析示例"""
    print("=== 函数调用解析示例 ===")
    
    parser = create_simple_parser()
    env = Environment()
    
    @env.set_function.register
    def zero():
        return 0
    
    @env.set_function.register
    def add(a, b):
        return a + b
    
    @env.set_function.register
    def Prout(*args):
        result = ' '.join(str(arg) for arg in args)
        print(f"输出: {result}")
        return result
    
    test_cases = [
        "zero()",
        "add(1, 2)", 
        "Prout('Hello', 'World')",
        "Prout(add(1, 2))"
    ]
    
    for test in test_cases:
        print(f"\n解析: {test}")
        try:
            parsed = parse(parser, test)
            print(f"解析结果: {parsed}")
            
            if isinstance(parsed, dict) and parsed.get('type') == 'call':
                func_name = parsed['function']
                args = parsed['arguments']
                
                func, is_macro = env.get_function(func_name)
                if func:
                    result = func(*args)
                    print(f"执行结果: {result}")
                    
        except ParseError as e:
            print(f"解析错误: {e}")

def example_expression():
    """数学表达式解析示例"""
    print("=== 数学表达式解析示例 ===")
    
    parser = expression()
    
    test_cases = [
        "1 + 2",
        "3 * 4 + 5", 
        "(1 + 2) * 3",
        "10 / 2",
    ]
    
    for test in test_cases:
        try:
            result = parse(parser, test)
            print(f"{test} = {result}")
        except ParseError as e:
            print(f"{test} -> 错误: {e}")

# 保留模板函数
def template_simple_lang():
    """简单语言模板"""
    return '''
from supercode import *

# 1. 创建环境
env = Environment()

# 2. 定义你的函数
def my_function(*args):
    return "你的逻辑"

# 3. 注册函数
env.set_function("my_function", my_function)

# 4. 定义语法
my_parser = (
    identifier() + exact('(') + 
    argument_list().optional([]) + 
    exact(')')
) >> (lambda x: {
    'type': 'call', 
    'function': x[0], 
    'arguments': x[2]
})

# 5. 使用
code = "my_function('hello')"
parsed = parse(my_parser, code)
'''

def template_dsl():
    """领域特定语言模板"""
    return '''
from supercode import *

class MyDSL:
    def __init__(self):
        self.env = Environment()
        self.setup_functions()
        self.parser = self.create_parser()
    
    def setup_functions(self):
        self.env.set_function("process", self.process_data)
    
    def create_parser(self):
        return function_call()
    
    def process_data(self, data):
        return f"处理: {data}"

# 使用
dsl = MyDSL()
'''

def template_command_system():
    """命令系统模板"""
    return '''
from supercode import *

class CommandSystem:
    def __init__(self):
        self.commands = {}
        self.parser = function_call()
    
    def command(self, name):
        def decorator(func):
            self.commands[name] = func
            return func
        return decorator
    
    def execute(self, code):
        parsed = parse(self.parser, code)
        if parsed["function"] in self.commands:
            return self.commands[parsed["function"]](*parsed["arguments"])

system = CommandSystem()

@system.command("hello")
def hello(name):
    return f"Hello, {name}!"

result = system.execute("hello('World')")
'''

if __name__ == "__main__":
    main()