#!/bin/bash

# Kronos股票预测应用管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助信息
show_help() {
    echo "Kronos股票预测应用管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  status    查看服务状态"
    echo "  logs      查看服务日志"
    echo "  clean     清理容器和卷"
    echo "  build     重新构建镜像"
    echo "  test      运行测试"
    echo "  backup    备份数据卷"
    echo "  restore   恢复数据卷"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start          # 启动应用"
    echo "  $0 logs api       # 查看API服务日志"
    echo "  $0 clean --all    # 清理所有数据"
}

# 检查Docker和Docker Compose
check_requirements() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
}

# 启动服务
start_services() {
    print_info "启动Kronos股票预测应用..."

    # 创建.env文件（如果不存在）
    if [ ! -f .env ]; then
        print_info "创建环境配置文件..."
        cp .env.example .env
    fi

    # 创建volumes目录结构
    print_info "创建volumes目录结构..."
    mkdir -p volumes/{app,model,examples,finetune,logs,nginx_logs}

    # 复制初始代码到volumes目录（如果为空）
    if [ ! -f volumes/app/api.py ]; then
        print_info "复制应用代码到volumes目录..."
        cp -r app/* volumes/app/ 2>/dev/null || true
    fi

    if [ ! -f volumes/model/__init__.py ]; then
        print_info "复制模型文件到volumes目录..."
        cp -r model/* volumes/model/ 2>/dev/null || true
    fi

    if [ ! -f volumes/examples/prediction_example.py ]; then
        print_info "复制示例文件到volumes目录..."
        cp -r examples/* volumes/examples/ 2>/dev/null || true
    fi

    if [ ! -f volumes/finetune/config.py ]; then
        print_info "复制微调文件到volumes目录..."
        cp -r finetune/* volumes/finetune/ 2>/dev/null || true
    fi

    docker-compose up -d
    
    print_success "服务启动完成！"
    print_info "访问地址:"
    print_info "  主界面: http://localhost"
    print_info "  API文档: http://localhost/direct-api/docs"
    print_info "  健康检查: http://localhost/health"
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    check_health
}

# 停止服务
stop_services() {
    print_info "停止服务..."
    docker-compose down
    print_success "服务已停止"
}

# 重启服务
restart_services() {
    print_info "重启服务..."
    docker-compose restart
    print_success "服务已重启"
    
    # 检查服务状态
    sleep 5
    check_health
}

# 查看服务状态
show_status() {
    print_info "服务状态:"
    docker-compose ps
    
    echo ""
    print_info "容器资源使用:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $(docker-compose ps -q) 2>/dev/null || true
}

# 查看日志
show_logs() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_info "显示所有服务日志..."
        docker-compose logs -f --tail=100
    else
        print_info "显示 $service 服务日志..."
        docker-compose logs -f --tail=100 "$service"
    fi
}

# 清理资源
clean_resources() {
    local clean_all=$1
    
    print_warning "这将删除容器和相关资源"
    
    if [ "$clean_all" = "--all" ]; then
        print_warning "包括数据卷也将被删除！"
        read -p "确认继续？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "清理所有资源..."
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_success "清理完成"
        else
            print_info "取消清理"
        fi
    else
        read -p "确认继续？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "清理容器..."
            docker-compose down --remove-orphans
            print_success "清理完成"
        else
            print_info "取消清理"
        fi
    fi
}

# 重新构建镜像
build_images() {
    print_info "重新构建镜像..."
    docker-compose build --no-cache
    print_success "镜像构建完成"
}

# 运行测试
run_tests() {
    print_info "运行应用测试..."
    
    # 确保服务正在运行
    if ! docker-compose ps | grep -q "Up"; then
        print_info "启动服务进行测试..."
        docker-compose up -d
        sleep 15
    fi
    
    # 运行测试
    python test_app.py
}

# 检查健康状态
check_health() {
    print_info "检查服务健康状态..."
    
    # 检查Nginx
    if curl -f http://localhost/health &>/dev/null; then
        print_success "应用健康检查通过"
    else
        print_error "应用健康检查失败"
        print_info "查看服务状态:"
        docker-compose ps
    fi
}

# 备份volumes目录
backup_volumes() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"

    print_info "备份volumes目录到 $backup_dir..."
    mkdir -p "$backup_dir"

    # 备份volumes目录
    if [ -d "volumes" ]; then
        tar czf "$backup_dir/volumes.tar.gz" volumes/
        print_success "备份完成: $backup_dir/volumes.tar.gz"
    else
        print_warning "volumes目录不存在，无需备份"
    fi
}

# 恢复volumes目录
restore_volumes() {
    local backup_file=$1

    if [ -z "$backup_file" ]; then
        print_error "请指定备份文件"
        echo "用法: $0 restore <backup_file.tar.gz>"
        exit 1
    fi

    if [ ! -f "$backup_file" ]; then
        print_error "备份文件不存在: $backup_file"
        exit 1
    fi

    print_warning "这将覆盖现有volumes目录"
    read -p "确认继续？(y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "从 $backup_file 恢复数据..."

        # 停止服务
        docker-compose down

        # 备份当前volumes目录
        if [ -d "volumes" ]; then
            print_info "备份当前volumes目录..."
            mv volumes "volumes.backup.$(date +%Y%m%d_%H%M%S)"
        fi

        # 恢复volumes目录
        tar xzf "$backup_file"

        print_success "恢复完成"
        print_info "重新启动服务..."
        docker-compose up -d
    else
        print_info "取消恢复"
    fi
}

# 主函数
main() {
    # 检查依赖
    check_requirements
    
    # 解析命令
    case "${1:-help}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        clean)
            clean_resources "$2"
            ;;
        build)
            build_images
            ;;
        test)
            run_tests
            ;;
        backup)
            backup_volumes
            ;;
        restore)
            restore_volumes "$2"
            ;;
        health)
            check_health
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
