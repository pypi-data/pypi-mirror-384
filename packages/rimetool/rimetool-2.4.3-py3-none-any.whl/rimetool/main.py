from datetime import datetime
import os
import sys
# from .rimetool_core.utils import Epub_Processor, vcf
from .rimetool_core.utils import vcf
from .rimetool_core.utils import simple_english
from .rimetool_core.utils import simple_chinese
from .rimetool_core.utils import tosougou
import argparse

help_text = """

参数说明:

| 参数            | 说明      | 简化形式 |
| ------------- | ------- | ---- |
| --input-path  | 输入文件路径  | -i   |
| --output-path | 输出路径    | -o   |
| --tool        | 启用工具    | -t   |
| --mode        | 工具的详细功能 | -m   |
|               |         |      |

工具说明:

| 参数                    | 说明                                               | 备注                   |
| --------------------- | ------------------------------------------------ | -------------------- |
| --tool vcf            | 用于将联系人文件（.vcf）导出为rime词库                          |                      |
| --tool simple-english | 将单个词（如hello）或单个词组（如hello world）文件（.txt）导出为rime词库 | simple-english可简化为se |
| --tool simple-chinese | 将单个中文词组（如你好）文件（.txt）导出为rime词库                    | simple-chinese可简化为sc |
| --tool tosougou       | 将rime词库导出为搜狗txt词库                                |                      |

"""

# 定义模式映射 (EPUB功能已注销，不再需要模式)
mode_choices = {}


def get_args_parser(add_help=True):
    # 检查是否有 'web' 子命令
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        # 通过 web 命令启动网页端
        parser = argparse.ArgumentParser(description="启动rimetool网页界面", add_help=add_help)
        parser.add_argument('command', choices=['web'], help='启动网页界面')
        parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址 (默认: 0.0.0.0)')
        parser.add_argument('--port', default=5023, type=int, help='服务器端口 (默认: 5023)')
        parser.add_argument('--debug', action='store_true', help='启用调试模式')
        parser.add_argument('--log-dir', help='日志文件目录 (默认: 当前目录/rimetool/logs)')
        parser.add_argument('--jieba-dict', required=False, type=str, help='jieba自定义分词词典路径（仅simple-chinese/sc有效）')
        return parser
    else:
        # 具体功能的实现
        parser = argparse.ArgumentParser(description=help_text, add_help=add_help, formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--input-path', '-i', required=True, type=str)
        parser.add_argument('--output-path', '-o', default='./rimetool_output', type=str)
        parser.add_argument('--tool', '-t', required=True, choices=['vcf','simple-english','se','simple-chinese','sc','tosougou','hello'], type=str)
        parser.add_argument('--jieba-dict','-jd', required=False, type=str, help='jieba自定义分词词典路径（仅simple-chinese/sc有效）')
        # parser.add_argument('--mode', '-m', required=False, choices=list(mode_choices.keys()))
        return parser

def main(output_files=None, is_web=False):
    # 检查是否是 web 命令
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        # 启动网页界面
        parser = get_args_parser()
        args = parser.parse_args()
        
        try:
            # 直接运行 new_app.py
            import subprocess
            
            # 获取 new_app.py 的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            new_app_path = os.path.join(current_dir, 'rimetool_gui', 'new_app.py')
            
            print(f"启动rimetool网页界面...")
            print(f"访问地址: http://{args.host}:{args.port}")
            print("按 Ctrl+C 停止服务器")
            
            # 设置环境变量
            env = os.environ.copy()
            env['FLASK_HOST'] = args.host
            env['FLASK_PORT'] = str(args.port)
            if args.debug:
                env['FLASK_DEBUG'] = '1'
            
            # 设置日志目录
            if args.log_dir:
                env['RIMETOOL_LOG_DIR'] = args.log_dir
            else:
                # 默认在当前工作目录创建 rimetool/logs
                default_log_dir = os.path.join(os.getcwd(), 'rimetool', 'logs')
                env['RIMETOOL_LOG_DIR'] = default_log_dir
            
            # 运行 new_app.py
            subprocess.run([sys.executable, new_app_path], env=env, cwd=current_dir)
            
        except KeyboardInterrupt:
            print("\n网页服务器已停止")
        except Exception as e:
            print(f"启动网页服务器失败: {e}")
            sys.exit(1)
        return
    
    # 原有的处理逻辑
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    parser = get_args_parser()
    args = parser.parse_args()
    name = ""
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)
    os.makedirs(args.output_path, exist_ok=True)
    
    # 获取 jieba_dict 参数（如果有）
    jieba_dict = getattr(args, 'jieba_dict', None)
    
    if args.tool == 'vcf':
        name = vcf.main(args.input_path, args.output_path, is_web)
    elif args.tool in ['simple-english', 'se']:
        name = simple_english.main(args.input_path, args.output_path, is_web)
    elif args.tool in ['simple-chinese', 'sc']:
        name = simple_chinese.main(args.input_path, args.output_path, is_web, jieba_dict)
    elif args.tool == 'tosougou':
        name = tosougou.main(args.input_path, args.output_path, is_web)

    else:
        raise ValueError('请选择正确的工具。')
    return name

def main_with_args(args_list):
    """
    用于在GUI中调用
    """
    original_argv = sys.argv
    sys.argv = [''] + args_list  # 设置命令行参数
    try:
        parser = get_args_parser()
        args = parser.parse_args(args_list)
        output_files = None
        print("args.tool:"+args.tool)
        # if args.tool == 'epub':
        #     # EPUB功能已注销
        #     raise ValueError('EPUB功能已注销，请使用其他工具。')
        
        # 标记这是从web界面调用的
        result = main(output_files, is_web=True)
        return result
    finally:
        sys.argv = original_argv  # 恢复原始的命令行参数

if __name__ == "__main__":
    main()