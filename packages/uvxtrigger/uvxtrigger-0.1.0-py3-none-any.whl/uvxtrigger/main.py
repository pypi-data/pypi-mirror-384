import argparse
import subprocess
import sys

def execute_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "stdout": e.stdout,
            "stderr": e.stderr,
            "returncode": e.returncode
        }

def run():
    """主函数，解析命令行参数并执行相应命令"""
    parser = argparse.ArgumentParser(description='Execute triggered via uvx')
    parser.add_argument('command', nargs='*', help='The command to execute')
    parser.add_argument('--default', action='store_true', help='Run default command')
    
    args = parser.parse_args()
    
    # 如果没有提供命令且没有指定默认命令，则显示帮助信息
    if not args.command and not args.default:
        parser.print_help()
        sys.exit(1)
    
    # 确定要执行的命令
    if args.default:
        command = "echo 'Default command executed via uvx!'; whoami; pwd"
    else:
        command = ' '.join(args.command)
    
    print(f"Executing command: {command}\n")
    
    # 执行命令并处理结果
    result = execute_command(command)
    
    if result["success"]:
        print("Command executed successfully!")
        if result["stdout"]:
            print("\nOutput:")
            print(result["stdout"])
    else:
        print(f"Command failed with return code {result['returncode']}")
        if result["stderr"]:
            print("\nError:")
            print(result["stderr"])
        sys.exit(result["returncode"])

if __name__ == "__main__":
    run()
