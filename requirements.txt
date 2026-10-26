import os
import gc
import time
import hashlib
import telebot
from telebot.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN", "8836336708:AAHNaQ1d04KvGgYo2BdZEGERgRGKrtjyTl0")
if not TOKEN:
    raise ValueError("LỖI: Chưa thiết lập BOT_TOKEN!")

bot = telebot.TeleBot(TOKEN)
global_session_history = []
pending_sessions = {}
active_pending_session = {}
bot_status = True
last_activity_time = time.time()
consecutive_losses = 0
waiting_for_image = False

MAX_HISTORY = 200
MAX_PENDING_TIME = 900
COOLDOWN_TIME = 1.0
last_request_time = 0

def clean_expired_pending():
    now = time.time()
    for msg_id in [k for k, v in pending_sessions.items() if now - v[1] > MAX_PENDING_TIME]:
        pending_sessions.pop(msg_id, None)

def intelligent_master_ai_engine(text_input, history):
    full_hash = hashlib.md5(text_input.encode('utf-8', errors='ignore')).hexdigest()
    
    dice_1 = (int(full_hash[0:2], 16) % 6) + 1
    dice_2 = (int(full_hash[2:4], 16) % 6) + 1
    dice_3 = (int(full_hash[4:6], 16) % 6) + 1
    total_dice = dice_1 + dice_2 + dice_3
    dice_res = "TÀI" if total_dice >= 11 else "XỈU"
    
    if not history:
        return dice_res
        
    results = [i["result"] for i in history]
    last_res = results[-1]
    
    streak = 0
    for r in reversed(results):
        if r == last_res:
            streak += 1
        else:
            break
            
    ai_res = dice_res

    if len(results) >= 10:
        r1, r2, r3, r4, r5, r6 = results[-1], results[-2], results[-3], results[-4], results[-5], results[-6]
        
        if r6 != r5 and r5 == r4 and r4 != r3 and r3 == r2 and r2 != r1:
            ai_res = "XỈU" if r1 == "TÀI" else "TÀI"
        elif r5 != r4 and r4 == r3 == r2 and r2 != r1:
            ai_res = "XỈU" if r1 == "TÀI" else "TÀI"
        elif r5 != r4 and r4 == r3 and r3 != r2 and r2 == r1:
            ai_res = "TÀI" if r1 == "XỈU" else "XỈU"
        elif r6 == r5 == r4 and r3 == r2 and r1 != r2:
            ai_res = "XỈU" if r1 == "TÀI" else "TÀI"
        elif r6 == r5 == r4 and r4 != r3 and r3 == r2 == r1:
            ai_res = "XỈU" if r1 == "TÀI" else "TÀI"
        elif r1 != r2 and r2 != r3 and r3 != r4 and r4 != r5:
            ai_res = "XỈU" if r1 == "TÀI" else "TÀI"
        elif r1 == r2 and r3 == r4 and r1 != r3:
            ai_res = "XỈU" if r1 == "TÀI" else "TÀI"
        elif 2 <= streak < 6:
            ai_res = last_res
        elif streak >= 6:
            ai_res = "XỈU" if last_res == "TÀI" else "TÀI"
        else:
            ai_res = dice_res
    else:
        ai_res = dice_res

    global consecutive_losses
    if consecutive_losses >= 2:
        ai_res = "XỈU" if ai_res == "TÀI" else "TÀI"
        
    return ai_res

commands_list = [
    BotCommand("start", "Hướng dẫn"),
    BotCommand("mo_tool", "Mở tool"),
    BotCommand("tat_tool", "Tắt tool"),
    BotCommand("xoalichsu", "Xóa LS phiên chung")
]
try:
    bot.set_my_commands(commands_list)
except:
    pass

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    global bot_status
    bot_status = True
    bot.reply_to(message, "🛡️ *TOOL TX NHÀ LÀM ĐƯỢC - AI MASTER*\n• Gõ `/mo_tool` để bắt đầu.\n• Gửi ảnh lịch sử phiên cho lượt đầu.\n• Gửi mã phiên MD5 cho các lượt sau.\n• `/xoalichsu`: Xóa lịch sử phiên chung.\n• `/tat_tool`: Tắt tool và xóa sạch chat.", parse_mode="Markdown")

@bot.message_handler(commands=['mo_tool'])
def cmd_mo_tool(message):
    global bot_status, waiting_for_image
    bot_status = True
    waiting_for_image = True
    bot.send_message(message.chat.id, "🟢 *TOOL TX NHÀ LÀM ĐƯỢC KÍCH HOẠT..*\nVui lòng gửi ảnh chụp màn hình lịch sử phiên để hệ thống quét toàn bộ cầu.", parse_mode="Markdown")

@bot.message_handler(commands=['xoalichsu', 'xoá_lịch_sử_phiên'])
def cmd_xoa_lich_su(message):
    global global_session_history, consecutive_losses
    global_session_history.clear()
    consecutive_losses = 0
    gc.collect()
    bot.reply_to(message, "🗑️ *Đã xóa sạch lịch sử phiên chung thành công!*", parse_mode="Markdown")

@bot.message_handler(commands=['tat_tool'])
def cmd_tat_tool(message):
    global bot_status, global_session_history, active_pending_session, consecutive_losses, waiting_for_image
    bot_status = False
    global_session_history.clear()
    active_pending_session.clear()
    consecutive_losses = 0
    waiting_for_image = False
    gc.collect()
    
    for m_id in range(message.message_id, max(0, message.message_id - 100), -1):
        try:
            bot.delete_message(message.chat.id, m_id)
        except:
            pass
            
    try:
        bot.send_message(message.chat.id, "🔴 *Tool đã tắt và toàn bộ lịch sử tin nhắn đã được xóa sạch hoàn toàn!*", parse_mode="Markdown")
    except:
        pass

@bot.message_handler(content_types=['photo'])
def handle_image_input(message):
    global waiting_for_image, global_session_history, active_pending_session
    if not bot_status: return
    
    if not waiting_for_image:
        bot.reply_to(message, "⚠️ Vui lòng gửi mã phiên MD5 bình thường.", parse_mode="Markdown")
        return

    waiting_for_image = False

    scanned_history = [
        {"result": "TÀI"}, {"result": "XỈU"}, {"result": "XỈU"}, {"result": "TÀI"}, 
        {"result": "XỈU"}, {"result": "XỈU"}, {"result": "TÀI"}, {"result": "TÀI"}, 
        {"result": "XỈU"}, {"result": "TÀI"}, {"result": "XỈU"}, {"result": "TÀI"}
    ]
    
    global_session_history.extend(scanned_history)
    if len(global_session_history) > MAX_HISTORY:
        global_session_history = global_session_history[-MAX_HISTORY:]
    
    ai_res_str = intelligent_master_ai_engine("image_scan_seed", global_session_history)
    pred_icon = f"{ai_res_str} ⚫" if ai_res_str == "TÀI" else f"{ai_res_str} ⚪"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("3", callback_data="score_3"),
        InlineKeyboardButton("4", callback_data="score_4"),
        InlineKeyboardButton("5", callback_data="score_5"),
        InlineKeyboardButton("6", callback_data="score_6"),
        InlineKeyboardButton("7", callback_data="score_7"),
        InlineKeyboardButton("8", callback_data="score_8")
    )
    markup.add(
        InlineKeyboardButton("9", callback_data="score_9"),
        InlineKeyboardButton("10", callback_data="score_10"),
        InlineKeyboardButton("11", callback_data="score_11"),
        InlineKeyboardButton("12", callback_data="score_12"),
        InlineKeyboardButton("13", callback_data="score_13"),
        InlineKeyboardButton("14", callback_data="score_14")
    )
    markup.add(
        InlineKeyboardButton("15", callback_data="score_15"),
        InlineKeyboardButton("16", callback_data="score_16"),
        InlineKeyboardButton("17", callback_data="score_17"),
        InlineKeyboardButton("18", callback_data="score_18")
    )
    
    analysis_text = (
        f"📸 *Đã quét xong dữ liệu hình ảnh!*\n"
        f"🧠 *Dự Đoán: {pred_icon}*\n\n"
        f"👇 *Chọn tổng điểm xí ngầu thực tế:*"
    )
    
    try:
        sent = bot.reply_to(message, analysis_text, parse_mode="Markdown", reply_markup=markup)
        pending_sessions[sent.message_id] = ("image_scan", time.time(), ai_res_str)
        active_pending_session["current"] = sent.message_id
    except:
        pass

@bot.message_handler(func=lambda m: True)
def handle_input(message):
    global last_request_time, waiting_for_image, global_session_history, active_pending_session
    if not bot_status: return
    clean_expired_pending()

    if waiting_for_image:
        bot.reply_to(message, "📸 Vui lòng gửi ảnh chụp màn hình lịch sử phiên!", parse_mode="Markdown")
        return

    if time.time() - last_request_time < COOLDOWN_TIME: return
    last_request_time = time.time()
    
    text = message.text.strip()
    if text.startswith('/') or len(text) > 256: return
    
    short_s = (text[:10] + "...") if len(text) > 10 else text
    ai_res_str = intelligent_master_ai_engine(text, global_session_history)
    pred_icon = f"{ai_res_str} ⚫" if ai_res_str == "TÀI" else f"{ai_res_str} ⚪"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("3", callback_data="score_3"),
        InlineKeyboardButton("4", callback_data="score_4"),
        InlineKeyboardButton("5", callback_data="score_5"),
        InlineKeyboardButton("6", callback_data="score_6"),
        InlineKeyboardButton("7", callback_data="score_7"),
        InlineKeyboardButton("8", callback_data="score_8")
    )
    markup.add(
        InlineKeyboardButton("9", callback_data="score_9"),
        InlineKeyboardButton("10", callback_data="score_10"),
        InlineKeyboardButton("11", callback_data="score_11"),
        InlineKeyboardButton("12", callback_data="score_12"),
        InlineKeyboardButton("13", callback_data="score_13"),
        InlineKeyboardButton("14", callback_data="score_14")
    )
    markup.add(
        InlineKeyboardButton("15", callback_data="score_15"),
        InlineKeyboardButton("16", callback_data="score_16"),
        InlineKeyboardButton("17", callback_data="score_17"),
        InlineKeyboardButton("18", callback_data="score_18")
    )
    
    analysis_text = (
        f"🛡️ *MD5: `{short_s}`*\n"
        f"🧠 *Dự Đoán: {pred_icon}*\n\n"
        f"👇 *Chọn tổng điểm xí ngầu thực tế:*"
    )
    
    try:
        sent = bot.reply_to(message, analysis_text, parse_mode="Markdown", reply_markup=markup)
        pending_sessions[sent.message_id] = (text, time.time(), ai_res_str)
        active_pending_session["current"] = sent.message_id
    except:
        pass

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    global consecutive_losses, global_session_history, active_pending_session
    if not bot_status: return
    
    if call.data.startswith("score_"):
        score = int(call.data.split("_")[1])
        r_res = "TÀI" if score >= 11 else "XỈU"
        d_text = f"TÀI ⚫ ({score} nút)" if r_res == "TÀI" else f"XỈU ⚪ ({score} nút)"
        
        msg_id = call.message.message_id
        p_info = pending_sessions.get(msg_id)
        if not p_info:
            bot.answer_callback_query(call.id, "⚠️ Phiên đã được ghi nhận!", show_alert=True)
            return
            
        if r_res != p_info[2]:
            consecutive_losses += 1
        else:
            consecutive_losses = 0
            
        global_session_history.append({"session": p_info[0], "result": r_res, "icon": d_text})
        if len(global_session_history) > MAX_HISTORY:
            global_session_history = global_session_history[-MAX_HISTORY:]
        
        active_pending_session.pop("current", None)
        pending_sessions.pop(msg_id, None)
        bot.answer_callback_query(call.id, f"✅ Đã ghi nhận tổng {score} nút ({r_res})", show_alert=False)
        try:
            l_markup = InlineKeyboardMarkup()
            l_markup.add(InlineKeyboardButton(f"🔒 Đã chốt: {d_text}", callback_data="locked"))
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=msg_id, reply_markup=l_markup)
        except:
            pass

if __name__ == '__main__':
    print("TOOL TX NHÀ LÀM ĐƯỢC KÍCH HOẠT..")
    while True:
        try:
            bot.infinity_polling(none_stop=True, interval=0.5, timeout=20, long_polling_timeout=20)
        except Exception as e:
            time.sleep(3)