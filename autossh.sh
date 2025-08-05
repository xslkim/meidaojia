#!/bin/bash

# 定义连接参数
HOST="northwest1.gpugeek.com"
PORT="55139"
USER="root"
PASSWORD="uaUMSzmAHyka2ZcBvQHZ5My9PUNRP78T"
TARGET_DIR="/root/project/hair_service_sd"
COMMAND="if ! pgrep -f 'run_copy_cost_colorb64.py'; then bash start_services.sh; fi"

# 使用expect工具自动化交互过程
/usr/bin/expect <<EOF
set timeout 30

# 启动ssh连接
spawn ssh -p $PORT $USER@$HOST

expect {
    # 处理首次连接的确认提示
    "you sure you want to continue connecting" {
        send "yes\r"
        exp_continue
    }
    # 匹配各种可能的密码提示形式
    "*password:" {
        send "$PASSWORD\r"
    }
    "Password:" {
        send "$PASSWORD\r"
    }
    "*assword:" {
        send "$PASSWORD\r"
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

# 执行检查进程并启动服务的命令
send "$COMMAND\r"

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

echo "自动化任务已完成"