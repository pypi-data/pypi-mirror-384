"""
SuperCode - 完全自由的自定义代码解析器
让你轻松构建自己的编程语言、DSL和命令系统
"""

from .core import (
    # 核心解析器
    Parser, parse, run_parser,
    
    # 基础匹配器
    match, exact, number, string, whitespace, identifier,
    integer, float_number,
    
    # 组合器
    seq, either, many, optional, one_or_more, separated_by,
    group, skip, forward,
    
    # 语义动作
    action, transform,
    
    # 环境和管理
    Environment, Context, FunctionRegistry,
    
    # 预构建解析器
    expression, function_call, argument_list, assignment,
    
    # 工具函数
    create_parser, define_language, build_language,
    
    # 错误处理
    ParseError, ParseResult,
)

from .main import (
    # 主接口
    main,
    
    # 快速启动
    quick_start, create_simple_parser,
    
    # 示例
    example_function_call, example_expression,
    
    # 模板
    template_simple_lang, template_dsl, template_command_system,
)

__version__ = "1.0.0"
__author__ = "SuperCode Team"
__description__ = "一个完全自由、工具丰富的自定义代码解析器"

__all__ = [
    # 核心功能
    'Parser', 'parse', 'run_parser',
    'match', 'exact', 'number', 'string', 'whitespace', 'identifier',
    'integer', 'float_number',
    'seq', 'either', 'many', 'optional', 'one_or_more', 'separated_by',
    'group', 'skip', 'forward',
    'action', 'transform',
    'Environment', 'Context', 'FunctionRegistry',
    'expression', 'function_call', 'argument_list', 'assignment',
    'create_parser', 'define_language', 'build_language',
    'ParseError', 'ParseResult',
    
    # 主接口
    'main', 'quick_start', 'create_simple_parser',
    'example_function_call', 'example_expression',
    'template_simple_lang', 'template_dsl', 'template_command_system',
]
