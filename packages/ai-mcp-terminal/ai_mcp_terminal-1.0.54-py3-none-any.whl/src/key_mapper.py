#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
键盘按键映射系统
支持所有键盘按键到终端控制序列的转换
"""

import sys

class KeyMapper:
    """键盘按键到终端控制序列的映射"""
    
    # ANSI转义序列映射
    ANSI_KEYS = {
        # 箭头键
        "UP": "\x1b[A",
        "DOWN": "\x1b[B",
        "RIGHT": "\x1b[C",
        "LEFT": "\x1b[D",
        "UP_ARROW": "\x1b[A",
        "DOWN_ARROW": "\x1b[B",
        "RIGHT_ARROW": "\x1b[C",
        "LEFT_ARROW": "\x1b[D",
        
        # 功能键 F1-F12
        "F1": "\x1bOP",
        "F2": "\x1bOQ",
        "F3": "\x1bOR",
        "F4": "\x1bOS",
        "F5": "\x1b[15~",
        "F6": "\x1b[17~",
        "F7": "\x1b[18~",
        "F8": "\x1b[19~",
        "F9": "\x1b[20~",
        "F10": "\x1b[21~",
        "F11": "\x1b[23~",
        "F12": "\x1b[24~",
        
        # 导航键
        "HOME": "\x1b[H",
        "END": "\x1b[F",
        "INSERT": "\x1b[2~",
        "DELETE": "\x1b[3~",
        "PAGEUP": "\x1b[5~",
        "PAGEDOWN": "\x1b[6~",
        "PAGE_UP": "\x1b[5~",
        "PAGE_DOWN": "\x1b[6~",
        
        # 特殊键
        "TAB": "\t",
        "ENTER": "\r",
        "RETURN": "\r",
        "BACKSPACE": "\x7f",
        "ESCAPE": "\x1b",
        "ESC": "\x1b",
        "SPACE": " ",
        
        # Ctrl组合键
        "CTRL_A": "\x01",
        "CTRL_B": "\x02",
        "CTRL_C": "\x03",
        "CTRL_D": "\x04",
        "CTRL_E": "\x05",
        "CTRL_F": "\x06",
        "CTRL_G": "\x07",
        "CTRL_H": "\x08",
        "CTRL_I": "\t",
        "CTRL_J": "\n",
        "CTRL_K": "\x0b",
        "CTRL_L": "\x0c",
        "CTRL_M": "\r",
        "CTRL_N": "\x0e",
        "CTRL_O": "\x0f",
        "CTRL_P": "\x10",
        "CTRL_Q": "\x11",
        "CTRL_R": "\x12",
        "CTRL_S": "\x13",
        "CTRL_T": "\x14",
        "CTRL_U": "\x15",
        "CTRL_V": "\x16",
        "CTRL_W": "\x17",
        "CTRL_X": "\x18",
        "CTRL_Y": "\x19",
        "CTRL_Z": "\x1a",
        
        # Alt组合键（使用ESC前缀）
        "ALT_A": "\x1ba",
        "ALT_B": "\x1bb",
        "ALT_C": "\x1bc",
        "ALT_D": "\x1bd",
        "ALT_E": "\x1be",
        "ALT_F": "\x1bf",
        "ALT_G": "\x1bg",
        "ALT_H": "\x1bh",
        "ALT_I": "\x1bi",
        "ALT_J": "\x1bj",
        "ALT_K": "\x1bk",
        "ALT_L": "\x1bl",
        "ALT_M": "\x1bm",
        "ALT_N": "\x1bn",
        "ALT_O": "\x1bo",
        "ALT_P": "\x1bp",
        "ALT_Q": "\x1bq",
        "ALT_R": "\x1br",
        "ALT_S": "\x1bs",
        "ALT_T": "\x1bt",
        "ALT_U": "\x1bu",
        "ALT_V": "\x1bv",
        "ALT_W": "\x1bw",
        "ALT_X": "\x1bx",
        "ALT_Y": "\x1by",
        "ALT_Z": "\x1bz",
    }
    
    @classmethod
    def map_key(cls, key_name: str) -> str:
        """
        将按键名称映射为终端控制序列
        
        Args:
            key_name: 按键名称（如 "UP", "CTRL_C", "F1"）
        
        Returns:
            对应的控制序列字符串
        """
        # 转换为大写
        key_upper = key_name.upper().strip()
        
        # 直接映射
        if key_upper in cls.ANSI_KEYS:
            return cls.ANSI_KEYS[key_upper]
        
        # 如果是单个字符，直接返回
        if len(key_name) == 1:
            return key_name
        
        # 尝试解析组合键（如 "Ctrl+C"）
        if "+" in key_name:
            return cls._parse_combination(key_name)
        
        # 未知按键，返回原字符串
        print(f"[KeyMapper] 警告: 未知按键 '{key_name}'，将作为普通文本发送", file=sys.stderr)
        return key_name
    
    @classmethod
    def _parse_combination(cls, combination: str) -> str:
        """
        解析组合键（如 "Ctrl+C", "Alt+F"）
        
        Args:
            combination: 组合键字符串
        
        Returns:
            对应的控制序列
        """
        parts = [p.strip().upper() for p in combination.split("+")]
        
        if len(parts) != 2:
            return combination
        
        modifier, key = parts
        
        # Ctrl组合
        if modifier == "CTRL":
            if len(key) == 1 and key.isalpha():
                # Ctrl+字母 = 字母的ASCII码 - 64
                return chr(ord(key) - 64)
            else:
                mapped_key = f"CTRL_{key}"
                return cls.ANSI_KEYS.get(mapped_key, combination)
        
        # Alt组合
        elif modifier == "ALT":
            if len(key) == 1 and key.isalpha():
                return f"\x1b{key.lower()}"
            else:
                mapped_key = f"ALT_{key}"
                return cls.ANSI_KEYS.get(mapped_key, combination)
        
        # Shift组合（大部分情况下就是大写字母或符号）
        elif modifier == "SHIFT":
            if len(key) == 1:
                return key.upper()
            # 特殊的Shift组合
            shift_map = {
                "1": "!",
                "2": "@",
                "3": "#",
                "4": "$",
                "5": "%",
                "6": "^",
                "7": "&",
                "8": "*",
                "9": "(",
                "0": ")",
                "-": "_",
                "=": "+",
                "[": "{",
                "]": "}",
                "\\": "|",
                ";": ":",
                "'": '"',
                ",": "<",
                ".": ">",
                "/": "?",
                "`": "~",
            }
            return shift_map.get(key, key.upper())
        
        return combination
    
    @classmethod
    def map_text(cls, text: str) -> str:
        """
        将文本转换为终端输入
        普通文本直接返回，特殊字符转义
        
        Args:
            text: 要发送的文本
        
        Returns:
            处理后的文本
        """
        return text
    
    @classmethod
    def get_supported_keys(cls) -> list:
        """获取所有支持的按键名称"""
        return list(cls.ANSI_KEYS.keys())
    
    @classmethod
    def is_control_key(cls, key_name: str) -> bool:
        """判断是否是控制键"""
        key_upper = key_name.upper().strip()
        return key_upper in cls.ANSI_KEYS


# 导出
__all__ = ['KeyMapper']

