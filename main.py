#!/usr/bin/env python3
"""
Discord Bot - Main Entry Point
啟動Discord機器人的主要程式
"""

import asyncio
import logging
import os
from bot import DiscordBot

def setup_logging():
    """設置日誌配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

async def main():
    """主要執行函數"""
    # 設置日誌
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 創建並啟動機器人
        bot = DiscordBot()
        logger.info("正在啟動Discord機器人...")
        await bot.start_bot()
    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在關閉機器人...")
    except Exception as e:
        logger.error(f"機器人運行時發生錯誤: {e}")
    finally:
        logger.info("機器人已關閉")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n機器人已停止運行")
