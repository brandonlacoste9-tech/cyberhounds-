#!/usr/bin/env python3
"""
🐺 CYBERHOUND ENVOY BOT
Telegram integration for Human-on-the-Loop (HOTL) approval workflow.
"""

import os
import logging
from typing import Optional, Dict
from dataclasses import dataclass

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler,
        ContextTypes, ConversationHandler
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

logger = logging.getLogger("Envoy")


@dataclass
class TelegramConfig:
    """Configuration for Telegram bot."""
    bot_token: str
    chat_id: str
    enabled: bool = False
    
    @classmethod
    def from_env(cls) -> "TelegramConfig":
        """Load config from environment variables."""
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        enabled = bool(token and chat_id and token != "YOUR_BOT_TOKEN")
        
        if not enabled:
            logger.warning("⚠️  Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        else:
            logger.info("✅ Telegram configured and enabled")
        
        return cls(
            bot_token=token,
            chat_id=chat_id,
            enabled=enabled
        )


class EnvoyBot:
    """Telegram bot for executive approval workflow."""
    
    def __init__(self, config: Optional[TelegramConfig] = None):
        self.config = config or TelegramConfig.from_env()
        self.application: Optional[Application] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the Telegram bot."""
        if not TELEGRAM_AVAILABLE:
            logger.error("❌ python-telegram-bot not installed. Run: pip install python-telegram-bot")
            return False
        
        if not self.config.enabled:
            logger.info("ℹ️  Telegram bot disabled (no token configured)")
            return False
        
        try:
            self.application = Application.builder().token(self.config.bot_token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("pending", self.cmd_pending))
            self.application.add_handler(CallbackQueryHandler(self.handle_approval))
            
            await self.application.initialize()
            self._initialized = True
            
            logger.info("✅ Envoy Bot initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram bot: {e}")
            return False
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "🐺 *Cyberhound Envoy Bot*\n\n"
            "Commands:\n"
            "/status - Check system status\n"
            "/pending - List pending strikes\n\n"
            "You'll receive alerts for new compliance gaps.",
            parse_mode="Markdown"
        )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        await update.message.reply_text(
            "🐺 *Cyberhound Status*\n\n"
            "✅ Sovereign Loop: Running\n"
            "✅ 20-Hound Swarm: Active\n"
            "📊 Pending Strikes: Check /pending",
            parse_mode="Markdown"
        )
    
    async def cmd_pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pending command."""
        # This would load from pending_strikes.json
        await update.message.reply_text(
            "📋 Use the web dashboard to view pending strikes.\n"
            "Or wait for new alerts to arrive here."
        )
    
    async def handle_approval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle approval button clicks."""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data: "action:pack_id"
        data = query.data
        action, pack_id = data.split(":", 1)
        
        if action == "approve":
            await query.edit_message_text(
                f"✅ *APPROVED*\nPack: `{pack_id}`\n\nStrike deployed!",
                parse_mode="Markdown"
            )
            logger.info(f"🚀 Strike {pack_id} APPROVED via Telegram")
            
        elif action == "veto":
            await query.edit_message_text(
                f"❌ *VETOED*\nPack: `{pack_id}`\n\nStrike discarded.",
                parse_mode="Markdown"
            )
            logger.info(f"🚫 Strike {pack_id} VETOED via Telegram")
            
        elif action == "ask":
            await query.edit_message_text(
                f"❓ *MORE INFO REQUESTED*\nPack: `{pack_id}`\n\n"
                f"Gathering additional intel...",
                parse_mode="Markdown"
            )
            logger.info(f"❓ More info requested for {pack_id}")
    
    async def send_decision_pack(self, pack: Dict) -> bool:
        """Send a Decision Pack to Telegram for approval."""
        if not self._initialized or not self.application:
            logger.warning("⚠️  Cannot send: Telegram bot not initialized")
            return False
        
        try:
            keyboard = [
                [
                    InlineKeyboardButton("✅ APPROVE", callback_data=f"approve:{pack['pack_id']}"),
                    InlineKeyboardButton("❌ VETO", callback_data=f"veto:{pack['pack_id']}"),
                ],
                [InlineKeyboardButton("❓ ASK", callback_data=f"ask:{pack['pack_id']}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"🚨 *COMPLIANCE GAP DETECTED*\n\n"
                f"*Company:* {pack['company']}\n"
                f"*Gap:* {pack['gap_description'][:100]}...\n"
                f"*Risk:* ${pack['fine_risk']:,} fine exposure\n"
                f"*Severity:* {pack['severity']}\n\n"
                f"💰 *PROPOSED STRIKE:*\n"
                f"Price: ${pack['proposed_price']:,}\n"
                f"ROI: {pack['roi_for_client']} cost avoidance\n\n"
                f"📍 {pack['jurisdiction']} | Pack: `{pack['pack_id']}`"
            )
            
            await self.application.bot.send_message(
                chat_id=self.config.chat_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            logger.info(f"📱 Sent Decision Pack {pack['pack_id']} to Telegram")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message: {e}")
            return False
    
    async def start_polling(self):
        """Start polling for commands."""
        if not self._initialized:
            logger.warning("⚠️  Cannot start polling: Bot not initialized")
            return
        
        await self.application.start()
        logger.info("✅ Telegram bot polling started")
    
    async def stop(self):
        """Stop the bot."""
        if self.application:
            await self.application.stop()
            logger.info("✅ Telegram bot stopped")


# Simple notification fallback when Telegram is not configured
class ConsoleNotifier:
    """Fallback notifier that just logs to console."""
    
    @staticmethod
    def send_decision_pack(pack: Dict):
        """Log decision pack to console."""
        print("\n" + "="*60)
        print("🚨 DECISION PACK READY FOR APPROVAL")
        print("="*60)
        print(f"\nPack ID: {pack['pack_id']}")
        print(f"Company: {pack['company']}")
        print(f"Gap: {pack['gap_description']}")
        print(f"Risk: ${pack['fine_risk']:,}")
        print(f"Price: ${pack['proposed_price']:,}")
        print(f"\nTo approve, set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        print("Or manually update pending_strikes.json")
        print("="*60 + "\n")


async def create_notifier() -> EnvoyBot:
    """Factory function to create appropriate notifier."""
    bot = EnvoyBot()
    await bot.initialize()
    return bot
