import typer
from typing import List, Optional
import click
from click.core import Context, Option

# 创建一个自定义的 Option 类，忽略未知参数
class IgnoreUnknownOption(Option):
    def __init__(self, *args, **kwargs):
        self.ignore_unknown = kwargs.pop('ignore_unknown', False)
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        # 如果设置了忽略未知参数，并且参数不在当前命令的参数列表中，则忽略
        if self.ignore_unknown:
            if self.name not in ctx.command.params:
                return args, opts
        return super().handle_parse_result(ctx, opts, args)

# 使用猴子补丁方法来修改 typer/click 的行为
def patch_typer_for_global_options(ignored_options: List[str]):
    """
    修改 Typer/Click 的参数处理行为，使其忽略指定的全局参数
    
    Args:
        ignored_options: 需要全局忽略的参数名列表
    """
    # 保存原始方法
    original_make_parser = click.Command.make_parser
    
    # 创建自定义方法
    def custom_make_parser(self, ctx):
        parser = original_make_parser(self, ctx)
        original_parse_args = parser.parse_args
        
        def custom_parse_args(args):
            # 过滤掉我们想要忽略的参数
            filtered_args = []
            skip_next = False
            for i, arg in enumerate(args):
                if skip_next:
                    skip_next = False
                    continue
                    
                # 检查是否是我们想要忽略的参数
                is_ignored = False
                for opt in ignored_options:
                    if arg == f"--{opt}":
                        # 如果下一个参数不是另一个选项，则也跳过它（作为值）
                        if i + 1 < len(args) and not args[i + 1].startswith("-"):
                            skip_next = True
                        is_ignored = True
                        break
                        
                if not is_ignored:
                    filtered_args.append(arg)
                    
            # 用过滤后的参数调用原始解析方法
            return original_parse_args(filtered_args)
            
        parser.parse_args = custom_parse_args
        return parser
        
    # 应用猴子补丁
    click.Command.make_parser = custom_make_parser

# 应用补丁，忽略 --no-upgrade 参数
def add_no_upgrade_option():
    """应用补丁，忽略 --no-upgrade 参数"""
    patch_typer_for_global_options(["no-upgrade"]) 