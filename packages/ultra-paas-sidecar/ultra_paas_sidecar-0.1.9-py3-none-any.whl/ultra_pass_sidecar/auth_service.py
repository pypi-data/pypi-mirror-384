#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限微服务接口定义
使用Feign风格调用权限系统

功能描述:
- 定义权限校验接口
- 定义菜单资源获取接口
- 使用Feign装饰器进行服务调用
- 异构服务调用示例（调用Java权限服务）

@author: lzg
@created: 2025-07-03 09:15:32
@version: 1.0.0
"""

from . import feign, get

@feign("upcloudx-system")
class AuthPermissionService:
    """权限微服务接口"""
    
    @get("/external/auth/check")
    async def check_permission(self, url: str, code: str = None):
        """权限校验接口"""
        pass
    
    @get("/external/menu/resources")
    async def get_menu_resources(self, code: str):
        """获取菜单资源"""
        pass 

    @get("/external/user/getInfo")
    async def get_user_info(self):
        """获取用户信息"""
        pass 