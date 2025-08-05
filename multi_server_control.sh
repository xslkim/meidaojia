#!/bin/bash

# 定义目标目录和检查的进程名
TARGET_DIR="/root/project/hair_service_sd"
PROCESS_NAME="run_copy_cost_colorb64.py"
START_COMMAND="bash start_services.sh"

# 读取servers.csv文件并逐行处理
while IFS=, read -r name ssh_cmd password _; do
    # 去除可能存在的空格和引号
    name=$(echo "$name" | xargs)
    ssh_cmd=$(echo "$ssh_cmd" | xargs)
    password=$(echo "$password" | xargs)
    
    echo "..................................正在处理服务器: $name ........................................"
    
    # 从ssh命令中提取端口和主机
    port=$(echo "$ssh_cmd" | grep -oP '\-p\s*\K\d+')
    host=$(echo "$ssh_cmd" | grep -oP 'root@\K[^\s]+')
    
    # 使用expect工具自动化交互过程
    /usr/bin/expect <<EOF
    set timeout 30

    # 启动ssh连接
    spawn $ssh_cmd

    expect {
        # 处理首次连接的确认提示
        "you sure you want to continue connecting" {
            send "yes\r"
            exp_continue
        }
        # 匹配各种可能的密码提示形式
        "*password:" {
            send "$password\r"
        }
        "Password:" {
            send "$password\r"
        }
        "*assword:" {
            send "$password\r"
        }
    }

    # 等待登录成功提示
    expect {
        "*\$ " {}
        "*# " {}
    }

    # 进入目标目录
    send "cd $TARGET_DIR\r"
    expect {
        "*\$ " {}
        "*# " {}
    }

    # 检查进程并决定是否启动服务
    send "if ! pgrep -f '$PROCESS_NAME'; then echo '启动服务...'; $START_COMMAND; else echo '进程已在运行，跳过启动'; fi\r"

    # 等待命令执行完成
    expect {
        "*\$ " {
            send "exit\r"
        }
        "*# " {
            send "exit\r"
        }
        timeout {
            send "exit\r"
        }
    }

    # 等待ssh会话结束
    expect eof
EOF

    echo "已完成服务器: $name"
    # 添加延时
    echo "--------------------------------------------- 等待 ----------------------------------------------"
    sleep 5
done < servers_test.csv

echo "所有服务器处理完成"