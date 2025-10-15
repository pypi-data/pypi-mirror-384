# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
from typing import Any, Dict, Optional, List, Union, get_type_hints, get_origin, get_args
from dataclasses import fields, is_dataclass, dataclass, MISSING
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.layout import Layout
from rich import box

console = Console()

# 现代化的图标和样式配置
ICONS = {
    "agent": "🤖",
    "app": "📱",
    "file": "📄",
    "deploy": "🚀",
    "python": "🐍",
    "package": "📦",
    "port": "🔌",
    "config": "⚙️",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "input": "🔤",
    "select": "🔘",
    "description": "✨",
    "list": "📝",
    "dict": "📋",
    "number": "🔢",
    "boolean": "🔲",
    "string": "🔤",
    "rocket": "🚀",
}

# 颜色配置
COLORS = {
    "primary": "#2196F3",      # 科技蓝
    "success": "#4CAF50",    # 活力绿
    "warning": "#FF9800",    # 橙色
    "error": "#F44336",      # 红色
    "border": "#37474F",     # 边框灰
    "muted": "#78909C",      # 柔和灰
    "label": "#64B5F6",      # 浅蓝
    "description": "#90A4AE" # 描述灰
}

# 样式配置
STYLES = {
    "title": "bold #2196F3",
    "subtitle": "bold #64B5F6",
    "success": "bold #4CAF50",
    "warning": "bold #FF9800",
    "error": "bold #F44336",
    "label": "bold #64B5F6",
    "value": "#4CAF50",
    "description": "#78909C",
    "muted": "#78909C"
}

class AutoPromptGenerator:
    def __init__(self):
        self.type_handlers = {
            str: self._handle_string,
            int: self._handle_int,
            float: self._handle_float,
            bool: self._handle_bool,
            list: self._handle_list,
            List: self._handle_list,
            dict: self._handle_dict,
            Dict: self._handle_dict,
        }
    
    def generate_config(self, dataclass_type: type, existing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not is_dataclass(dataclass_type):
            raise ValueError(f"{dataclass_type} must be a dataclass")
        
        config = {}
        existing_config = existing_config or {}
        
        # 获取数据类的元数据
        # 尝试从类属性获取，如果不存在则创建实例来获取字段值
        config_metadata = {}
        if hasattr(dataclass_type, '_config_metadata'):
            # 如果是类属性
            config_metadata = getattr(dataclass_type, '_config_metadata', {})
        else:
            # 如果是字段，需要创建实例来获取默认值
            try:
                # 获取字段的默认值工厂函数或默认值
                for field in fields(dataclass_type):
                    if field.name == '_config_metadata':
                        if field.default_factory is not None and field.default_factory != MISSING:
                            config_metadata = field.default_factory()
                        elif field.default != MISSING:
                            config_metadata = field.default
                        break
            except Exception:
                pass
        
        config_name = config_metadata.get('name', dataclass_type.__name__)
        
        # 获取自定义消息
        welcome_message = config_metadata.get('welcome_message')
        next_step_hint = config_metadata.get('next_step_hint')
        completion_message = config_metadata.get('completion_message')
        next_action_hint = config_metadata.get('next_action_hint')
        
        # 显示现代化的欢迎界面
        self._show_welcome_panel(config_name, welcome_message, next_step_hint)
        
        # 获取字段列表并显示进度
        visible_fields = [f for f in fields(dataclass_type) 
                         if not f.metadata.get("hidden", False) and not f.metadata.get("system", False) and f.name != "_config_metadata"]
        total_fields = len(visible_fields)
        
        for idx, field in enumerate(visible_fields, 1):
            field_name = field.name
            field_type = get_type_hints(dataclass_type).get(field_name, str)
            existing_value = existing_config.get(field_name)
            default_value = existing_value if existing_value is not None else field.default
            description = field.metadata.get("description") or field.name.replace("_", " ").title()
            
            # 显示简洁进度信息（只在第一个字段时显示）
            if idx == 1:
                console.print(f"[{idx}/{total_fields}] 配置进度\n")
            
            value = self._prompt_for_field(field_name, field_type, description, default_value, field.metadata)
            
            if value is not None:
                config[field_name] = value
        
        # 显示完成界面
        self._show_completion_panel(config, completion_message, next_action_hint)
        
        # 处理隐藏和系统字段
        for field in fields(dataclass_type):
            field_name = field.name
            if field.metadata.get("hidden", False) or field.metadata.get("system", False):
                if field_name in existing_config:
                    config[field_name] = existing_config[field_name]
        
        # 过滤掉MISSING值
        filtered_config = {}
        for key, value in config.items():
            if not isinstance(value, type(MISSING)):
                filtered_config[key] = value
        
        return filtered_config
    
    def _prompt_for_field(self, name: str, field_type: type, description: str, default: Any, metadata: Dict[str, Any] = None) -> Any:
        metadata = metadata or {}
        
        if get_origin(field_type) is not None:
            if get_origin(field_type) is Union:
                args = get_args(field_type)
                if len(args) == 2 and type(None) in args:
                    field_type = args[0]
        
        if get_origin(field_type) is list or field_type is List:
            return self._handle_list(description, default, metadata)
        
        if get_origin(field_type) is dict or field_type is Dict:
            return self._handle_dict(description, default, metadata)
        
        if default is MISSING or isinstance(default, type(MISSING)):
            default = None
        
        choices = metadata.get("choices")
        if choices:
            return self._handle_choice_selection(description, choices, default, metadata)
        
        handler = self.type_handlers.get(field_type)
        if handler:
            return handler(description, default, metadata)
        
        return self._handle_string(description, default, metadata)
    
    def _handle_choice_selection(self, description: str, choices: List[Any], default: Any, field_metadata: Dict[str, Any] = None) -> str:
        if not default or (default and default not in [choice['value'] for choice in choices]):
            default = choices[0]['value'] if choices else None
        
        # 获取字段图标（支持metadata指定）
        icon = self._get_field_icon(description, field_metadata) if field_metadata else ICONS['select']
        
        # 创建选择面板标题
        console.print(f"\n{icon} [bold #64B5F6]{description}[/bold #64B5F6]")
        
        # 处理选择项数据
        choice_descriptions = {}
        if isinstance(choices, dict):
            choice_descriptions = choices
            choices = list(choices.keys())
        elif isinstance(choices, list) and len(choices) > 0 and isinstance(choices[0], dict):
            choice_descriptions = {item["value"]: item.get("description", "") for item in choices}
            choices = [item["value"] for item in choices]
        
        # 创建现代化的选择菜单
        table = Table(show_header=False, border_style=COLORS["muted"], box=box.ROUNDED, padding=(0, 1))
        
        for i, choice in enumerate(choices, 1):
            desc = choice_descriptions.get(choice, "")
            
            # 标记默认选项
            is_default = choice == default
            default_marker = f" [{COLORS['warning']}](默认)[/{COLORS['warning']}]" if is_default else ""
            
            # 格式化选择项
            choice_text = Text()
            choice_text.append(f"{i}. ", style=f"bold {COLORS['primary']}")
            choice_text.append(f"{choice}", style="bold white")
            if desc:
                choice_text.append(f" - {desc}", style=COLORS["description"])
            choice_text.append(default_marker)
            
            table.add_row(choice_text)
        
        # 显示选择表格
        console.print(table)
        console.print()
        
        while True:
            try:
                # 创建输入提示
                prompt_text = Text()
                prompt_text.append("请选择", style=f"bold #64B5F6")
                prompt_text.append(" (输入编号或名称)", style=COLORS["description"])
                
                user_input = Prompt.ask(
                    str(prompt_text),
                    default=str(default) if default else str(choices[0]) if choices else ""
                )
                
                if user_input.isdigit():
                    choice_num = int(user_input)
                    if 1 <= choice_num <= len(choices):
                        selected = choices[choice_num - 1]
                        # 显示选择确认
                        console.print(f"\n{ICONS['success']} 已选择: [bold {COLORS['success']}]{selected}[/bold {COLORS['success']}]\n")
                        return selected
                    else:
                        console.print(f"[red]{ICONS['error']} 请输入 1-{len(choices)} 之间的数字[/red]")
                        continue
                
                if user_input in choices:
                    # 显示选择确认
                    console.print(f"\n{ICONS['success']} 已选择: [bold {COLORS['success']}]{user_input}[/bold {COLORS['success']}]\n")
                    return user_input
                else:
                    valid_choices = ", ".join([f"[cyan]{c}[/cyan]" for c in choices])
                    console.print(f"[red]{ICONS['error']} 无效选择，请选择: {valid_choices}[/red]")
                    
            except KeyboardInterrupt:
                console.print(f"\n[red]{ICONS['warning']} 选择已取消，使用默认值[/red]")
                return str(default) if default else str(choices[0]) if choices else ""
    
    def _handle_string(self, description: str, default: Any, field_metadata: Dict[str, Any] = None) -> str:
        # 获取字段图标（支持metadata指定）
        icon = self._get_field_icon(description, field_metadata) if field_metadata else ICONS['input']
        
        # 创建输入提示
        prompt_text = Text()
        prompt_text.append(f"{icon} ", style=STYLES["label"])
        prompt_text.append(f"{description}", style="bold white")
        
        result = Prompt.ask(str(prompt_text), default=str(default) if default else "")
        console.print(f"{ICONS['success']} 已输入: [bold {COLORS['success']}]{result}[/bold {COLORS['success']}]\n")
        return result
    
    def _handle_int(self, description: str, default: Any, field_metadata: Dict[str, Any] = None) -> int:
        while True:
            try:
                # 获取字段图标（支持metadata指定）
                icon = self._get_field_icon(description, field_metadata) if field_metadata else ICONS['input']
                
                # 创建输入提示
                prompt_text = Text()
                prompt_text.append(f"{icon} ", style=STYLES["label"])
                prompt_text.append(f"{description}", style="bold white")
                prompt_text.append(" (数字)", style=COLORS["description"])
                
                value = Prompt.ask(str(prompt_text), default=str(default) if default else "0")
                result = int(value) if value else 0
                console.print(f"{ICONS['success']} 已输入: [bold {COLORS['success']}]{result}[/bold {COLORS['success']}]\n")
                return result
            except ValueError:
                console.print(f"[red]{ICONS['error']} 请输入有效的整数[/red]")
    
    def _handle_float(self, description: str, default: Any, field_metadata: Dict[str, Any] = None) -> float:
        while True:
            try:
                # 获取字段图标（支持metadata指定）
                icon = self._get_field_icon(description, field_metadata) if field_metadata else ICONS['input']
                
                # 创建输入提示
                prompt_text = Text()
                prompt_text.append(f"{icon} ", style=STYLES["label"])
                prompt_text.append(f"{description}", style="bold white")
                prompt_text.append(" (数字)", style=COLORS["description"])
                
                value = Prompt.ask(str(prompt_text), default=str(default) if default else "0.0")
                result = float(value) if value else 0.0
                console.print(f"{ICONS['success']} 已输入: [bold {COLORS['success']}]{result}[/bold {COLORS['success']}]\n")
                return result
            except ValueError:
                console.print(f"[red]{ICONS['error']} 请输入有效的数字[/red]")
    
    def _handle_bool(self, description: str, default: Any, field_metadata: Dict[str, Any] = None) -> bool:
        # 获取字段图标（支持metadata指定）
        icon = self._get_field_icon(description, field_metadata) if field_metadata else ICONS['select']
        
        # 创建确认提示
        prompt_text = Text()
        prompt_text.append(f"{icon} ", style=STYLES["label"])
        prompt_text.append(f"{description}", style="bold white")
        
        result = Confirm.ask(str(prompt_text), default=bool(default))
        result_text = "是" if result else "否"
        console.print(f"{ICONS['success']} 已选择: [bold {COLORS['success']}]{result_text}[/bold {COLORS['success']}]\n")
        return result
    
    def _handle_list(self, description: str, default: Any, field_metadata: Dict[str, Any] = None) -> List[str]:
        # 获取字段图标（支持metadata指定）
        icon = self._get_field_icon(description, field_metadata) if field_metadata else ICONS['list']
        
        # 创建列表输入面板
        panel_content = Text()
        panel_content.append(f"{icon} ", style=STYLES["label"])
        panel_content.append(f"{description}", style="bold white")
        panel_content.append("\n[dim]输入每个项目后按回车，输入空行结束[/dim]", style=COLORS["description"])
        
        console.print(Panel(
            panel_content,
            border_style=COLORS["border"],
            box=box.ROUNDED,
            padding=(1, 2)
        ))
        
        items = []
        counter = 1
        
        while True:
            item = Prompt.ask(f"  [{counter}] 项目")
            if not item.strip():
                break
            items.append(item.strip())
            console.print(f"  {ICONS['success']} 已添加: [bold {COLORS['success']}]{item.strip()}[/bold {COLORS['success']}]")
            counter += 1
        
        if items:
            console.print(f"\n{ICONS['list']} 共添加 [bold {COLORS['success']}]{len(items)}[/bold {COLORS['success']}] 个项目\n")
        else:
            console.print(f"\n{ICONS['info']} 未添加任何项目\n")
            
        return items if items else (default if default is not None else [])

    def _handle_dict(self, description: str, default: Any, field_metadata: Dict[str, Any] = None) -> Dict[str, str]:
        # 获取字段图标（支持metadata指定）
        icon = self._get_field_icon(description, field_metadata) if field_metadata else ICONS['dict']
        
        # 创建美观的字典输入面板
        panel_content = Text()
        panel_content.append(f"{icon} ", style=STYLES["label"])
        panel_content.append(f"{description}", style="bold white")
        
        # 添加环境变量提示（如果描述中包含env）
        if "env" in description.lower():
            panel_content.append("\n[dim]常用环境变量:[/dim]", style=COLORS["description"])
            panel_content.append("\n[dim]  - MODEL_AGENT_API_KEY=your_api_key[/dim]", style=COLORS["description"])
            panel_content.append("\n[dim]  - DEBUG=true[/dim]", style=COLORS["description"])
            panel_content.append("\n[dim]  - LOG_LEVEL=info[/dim]", style=COLORS["description"])
        
        panel_content.append("\n[dim]输入格式: KEY=VALUE[/dim]", style=COLORS["description"])
        panel_content.append("\n[dim]命令: 'del KEY' 删除, 'list' 查看, 'clear' 清空所有, 空行结束[/dim]", style=COLORS["description"])
        
        console.print(Panel(
            panel_content,
            border_style=COLORS["border"],
            box=box.ROUNDED,
            padding=(1, 2)
        ))
        
        result_dict = {}
        if isinstance(default, dict):
            result_dict.update(default)
        
        while True:
            user_input = Prompt.ask(f"\n{icon} 变量", default="")
            
            if not user_input.strip():
                break
                
            if user_input == "list":
                if result_dict:
                    console.print(f"\n[{COLORS['warning']}]当前变量:[/{COLORS['warning']}]")
                    for key, value in result_dict.items():
                        console.print(f"  {key}={value}")
                else:
                    console.print(f"[{COLORS['muted']}]未设置变量[/{COLORS['muted']}]")
                continue
                
            if user_input == "clear":
                result_dict.clear()
                console.print(f"[{COLORS['success']}]所有变量已清空[/{COLORS['success']}]")
                continue
                
            if user_input.startswith("del "):
                key_to_delete = user_input[4:].strip()
                if key_to_delete in result_dict:
                    del result_dict[key_to_delete]
                    console.print(f"[{COLORS['success']}]已删除: {key_to_delete}[/{COLORS['success']}]")
                else:
                    console.print(f"[{COLORS['error']}]变量未找到: {key_to_delete}[/{COLORS['error']}]")
                continue
                
            if "=" not in user_input:
                console.print(f"[{COLORS['error']}]无效格式, 请使用 KEY=VALUE[/{COLORS['error']}]")
                continue
                
            key, value = user_input.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            if not key:
                console.print(f"[{COLORS['error']}]键名不能为空[/{COLORS['error']}]")
                continue
                
            if not key.replace("_", "").isalnum():
                console.print(f"[{COLORS['error']}]键名只能包含字母、数字和下划线[/{COLORS['error']}]")
                continue
                
            old_value = result_dict.get(key)
            result_dict[key] = value
            
            if old_value is not None:
                console.print(f"[{COLORS['success']}]已更新: {key}={value} (原值: {old_value})[/{COLORS['success']}]")
            else:
                console.print(f"[{COLORS['success']}]已添加: {key}={value}[/{COLORS['success']}]")
        
        if result_dict:
            console.print(f"\n{ICONS['dict']} 共配置 [bold {COLORS['success']}]{len(result_dict)}[/bold {COLORS['success']}] 个变量\n")
        else:
            console.print(f"\n{ICONS['info']} 未配置任何变量\n")
            
        return result_dict if result_dict else (default if default is not None else {})

    def _show_welcome_panel(self, config_name: str, welcome_message: Optional[str] = None, 
                           next_step_hint: Optional[str] = None):
        """显示欢迎面板"""
        # 创建标题文本
        title_text = Text(f"{ICONS['config']} {config_name} 配置", style=STYLES["title"])
        
        # 创建内容
        content = Text()
        content.append(f"{ICONS['info']} ", style=STYLES["label"])
        
        # 使用自定义欢迎信息或默认信息
        if welcome_message:
            content.append(f"{welcome_message}", style="bold white")
        else:
            content.append("欢迎使用 AgentKit 配置向导\n\n", style="bold white")
            content.append("本向导将帮助您完成应用配置，请根据提示输入相关信息。\n", style=COLORS["description"])
        
        # 添加下一步提示
        if next_step_hint:
            content.append(f"\n{next_step_hint}\n", style=f"dim {COLORS['description']}")
        
        content.append("\n您可以随时按 Ctrl+C 退出配置。\n", style="dim")
        
        # 创建面板
        panel = Panel(
            content,
            title=title_text,
            border_style=COLORS["muted"],
            box=box.DOUBLE,
            padding=(1, 2),
            expand=False
        )
        
        console.print(panel)
        console.print()

    def _show_progress(self, current: int, total: int, field_name: str, description: str):
        """显示进度指示器"""
        # 获取字段图标（支持metadata指定）
        icon = self._get_field_icon(field_name)
        
        # 创建进度条
        progress_width = 30
        filled_width = int((current / total) * progress_width)
        progress_bar = f"[{'█' * filled_width}{'░' * (progress_width - filled_width)}]"
        
        # 创建进度信息
        progress_text = Text()
        progress_text.append(f"{icon} ", style=STYLES["label"])
        progress_text.append(f"{description}", style="bold white")
        progress_text.append(f"  [{current}/{total}]\n", style=STYLES["description"])
        progress_text.append(f"    {progress_bar} {current/total*100:.0f}%", style=COLORS["label"])
        
        console.print(progress_text)
        console.print()
    
    def _show_progress_clean(self, current: int, total: int, field_name: str, description: str):
        """显示清理的进度指示器（不重复显示进度条）"""
        # 获取字段图标（支持metadata指定）
        icon = self._get_field_icon(field_name)
        
        # 只在第一个字段或字段变更时显示进度条
        if current == 1 or current != getattr(self, '_last_progress', 0):
            # 创建进度条
            progress_width = 30
            filled_width = int((current / total) * progress_width)
            progress_bar = f"[{'█' * filled_width}{'░' * (progress_width - filled_width)}]"
            
            # 创建进度信息
            progress_text = Text()
            progress_text.append(f"{icon} ", style=STYLES["label"])
            progress_text.append(f"{description}", style="bold white")
            progress_text.append(f"  [{current}/{total}]\n", style=STYLES["description"])
            progress_text.append(f"    {progress_bar} {current/total*100:.0f}%", style=COLORS["label"])
            
            console.print(progress_text)
            console.print()
            
            # 记录当前进度
            self._last_progress = current

    def _get_field_icon(self, field_name: str, field_metadata: Dict[str, Any] = None) -> str:
        """根据字段metadata或字段名获取对应的图标"""
        # 优先使用metadata中指定的图标
        if field_metadata and "icon" in field_metadata:
            return field_metadata["icon"]
        
        # 回退到硬编码映射（保持向后兼容）
        icon_map = {
            "agent_name": ICONS["agent"],
            "entry_point": ICONS["file"],
            "current_workflow": ICONS["deploy"],
            "description": ICONS["description"],
            "python_version": ICONS["python"],
            "dependencies_file": ICONS["package"],
            "entry_port": ICONS["port"],
        }
        return icon_map.get(field_name, ICONS["config"])

    def _show_completion_panel(self, config: Dict[str, Any], completion_message: Optional[str] = None,
                             next_action_hint: Optional[str] = None):
        """显示配置完成界面"""
        # 创建标题文本
        title_text = Text(f"{ICONS['success']} 配置完成", style=STYLES["success"])
        
        # 创建配置总结表格
        table = Table(show_header=True, header_style=f"bold {COLORS['primary']}", 
                     border_style=COLORS["muted"], box=box.ROUNDED)
        table.add_column("配置项", style=STYLES["label"], width=20)
        table.add_column("值", style=STYLES["value"], width=30)
        
        # 添加配置项到表格
        for key, value in config.items():
            if not key.startswith('_'):  # 跳过内部字段
                formatted_key = self._format_field_name(key)
                if isinstance(value, type(MISSING)):
                    formatted_value = "未设置"
                elif value is None:
                    formatted_value = "未设置"
                else:
                    formatted_value = str(value)
                table.add_row(formatted_key, formatted_value)
        
        # 创建完成面板
        completion_panel = Panel(
            Align.center(table),
            title=title_text,
            border_style=COLORS["success"],
            box=box.ROUNDED,
            padding=(1, 2)
        )
        
        console.print("\n")
        console.print(completion_panel)
        
        # 显示自定义完成消息或默认消息
        if completion_message:
            console.print(f"\n{ICONS['success']} {completion_message}\n")
        else:
            console.print(f"\n{ICONS['rocket']} 配置已保存，现在可以使用 agentkit build 构建应用了！\n")
        
        # 显示下一步操作提示
        if next_action_hint:
            console.print(f"{ICONS['info']} {next_action_hint}\n", style=COLORS["description"])

    def _format_field_name(self, field_name: str) -> str:
        """格式化字段名称"""
        name_map = {
            "agent_name": "应用名称",
            "entry_point": "入口文件",
            "current_workflow": "部署模式",
            "description": "应用描述",
            "python_version": "Python版本",
            "dependencies_file": "依赖文件",
            "entry_port": "端口",
        }
        return name_map.get(field_name, field_name.replace("_", " ").title())

auto_prompt = AutoPromptGenerator()

def generate_config_from_dataclass(dataclass_type: type, existing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return auto_prompt.generate_config(dataclass_type, existing_config)