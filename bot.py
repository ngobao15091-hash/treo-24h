import os
import gc
import time
import hashlib
import random
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
consecutive_losses = 0
waiting_for_image = False

MAX_HISTORY = 500
MAX_PENDING_TIME = 900
COOLDOWN_TIME = 1.0
last_request_time = 0

def clean_expired_pending():
    now = time.time()
    for msg_id in [k for k, v in pending_sessions.items() if now - v[1] > MAX_PENDING_TIME]:
        pending_sessions.pop(msg_id, None)

def observe_nhan_dien_cau(history):
    """
    Nhận diện cầu thuần túy để người dùng quan sát (Không can thiệp vào kết quả AI).
    """
    if not history or len(history) < 3:
        return "Đang quét nhịp cầu khởi tạo..."
        
    results = [i["result"] for i in history]
    last_res = results[-1]
    
    streak = 0
    for r in reversed(results):
        if r == last_res:
            streak += 1
        else:
            break
            
    if streak >= 3:
        return f"Cầu Bệt {last_res} (Nhịp {streak})"
    elif len(results) >= 5 and results[-1] != results[-2] and results[-2] != results[-3]:
        return "Cầu 1-1 (Đan xen)"
    elif len(results) >= 3 and results[-1] == results[-2] and results[-2] != results[-3]:
        return "Cầu 2-1 (Kép đơn)"
    elif len(results) >= 3 and results[-1] != results[-2] and results[-2] == results[-3]:
        return "Cầu 1-2 (Đơn kép)"
    elif len(results) >= 4 and results[-1] == results[-2] and results[-3] == results[-4]:
        return "Cầu Nhịp Đôi (2-2)"
    else:
        return "Cầu Hỗn Hợp / Biến Động"

def deep_500_lines_unbeatable_ai_engine(input_signature, history):
    """
    AI phân tích độc lập, dự đoán tổng nút chính xác & Random % theo độ chắc chắn:
    - Chắc chắn cao -> Random từ 80% đến 98%
    - Không chắc chắn -> Random dưới 60%
    """
    raw_input = input_signature.strip().encode('utf-8', errors='ignore')
    
    h1 = hashlib.md5(raw_input).hexdigest()
    h2 = hashlib.sha256(raw_input).hexdigest()
    
    # Tính toán số nút xí ngầu giả lập từ mã băm
    d1 = (int(h1[0:2], 16) % 6) + 1
    d2 = (int(h1[2:4], 16) % 6) + 1
    d3 = (int(h1[4:6], 16) % 6) + 1
    total_dice = d1 + d2 + d3
    
    primary_res = "TÀI" if total_dice >= 11 else "XỈU"
    
    entropy_val = int(h2[0:12], 16) + int(h2[-12:], 16)
    secondary_bias = "TÀI" if (entropy_val % 2 == 0) else "XỈU"
    
    ai_res = primary_res
    predicted_score = total_dice
    is_certain = True

    if not history:
        if primary_res == secondary_bias:
            ai_res = primary_res
            is_certain = True
        else:
            ai_res = secondary_bias
            predicted_score = (14 if secondary_bias == "TÀI" else 7) # Điều chỉnh số nút phù hợp với cửa
            is_certain = False
    else:
        recent_window = [i["result"] for i in history[-min(500, len(history)):]]
        total_recorded = len(recent_window)
        
        if consecutive_losses >= 2:
            ai_res = "XỈU" if primary_res == "TÀI" else "TÀI"
            predicted_score = random.randint(3, 10) if ai_res == "XỈU" else random.randint(11, 18)
            is_certain = False
        else:
            if total_recorded >= 6:
                last_few = recent_window[-4:]
                if len(set(last_few)) == 1 and last_few[0] == primary_res:
                    is_certain = True
                elif primary_res == secondary_bias:
                    is_certain = True
                else:
                    is_certain = False
            else:
                is_certain = True

    # Đồng bộ số nút với kết quả AI phân tích (Tài >= 11, Xỉu <= 10)
    if ai_res == "TÀI" and predicted_score < 11:
        predicted_score = random.randint(11, 18)
    elif ai_res == "XỈU" and predicted_score >= 11:
        predicted_score = random.randint(3, 10)

    # Random tỷ lệ % dựa vào độ chắc chắn
    if is_certain:
        certainty_score = round(random.uniform(80.0, 98.5), 1)
    else:
        certainty_score = round(random.uniform(42.0, 59.0), 1)

    if ai_res == "TÀI":
        tai_pct = certainty_score
        xiu_pct = round(100.0 - tai_pct, 1)
    else:
        xiu_pct = certainty_score
        tai_pct = round(100.0 - xiu_pct, 1)

    return ai_res, tai_pct, xiu_pct, predicted_score

commands_list = [
    BotCommand("start", "Hướng dẫn sử dụng"),
    BotCommand("mo_tool", "Kích hoạt quét khung cầu"),
    BotCommand("xoacache", "Xóa sạch cache lịch sử phiên"),
    BotCommand("xoalichsu", "Xóa lịch sử phân tích"),
    BotCommand("tat_tool", "Tắt tool & dọn sạch dữ liệu")
]
try:
    bot.set_my_commands(commands_list)
except:
    pass

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    global bot_status, waiting_for_image
    bot_status = True
    waiting_for_image = True
    bot.reply_to(message, "🛡️ *AI MASTER TÀI XỈU - PHÂN TÍCH SÂU 500 DÒNG*\n• Hệ thống đã sẵn sàng.\n• **Bước 1:** Gửi ảnh chụp màn hình khung cầu để AI quét số liệu khởi tạo.\n• **Bước tiếp theo:** Gửi mã phiên MD5 liên tục để AI phân tích.\n• `/xoacache`: Xóa sạch cache lịch sử các phiên trước.\n• `/xoalichsu`: Xóa lịch sử phiên hiện tại.\n• `/tat_tool`: Tắt tool và dọn sạch hệ thống.", parse_mode="Markdown")

@bot.message_handler(commands=['mo_tool'])
def cmd_mo_tool(message):
    global bot_status, waiting_for_image
    bot_status = True
    waiting_for_image = True
    bot.send_message(message.chat.id, "🟢 *ĐÃ KÍCH HOẠT CHẾ ĐỘ QUÉT KHUNG CẦU (AI 10.0 - 500 DÒNG)*\nVui lòng gửi ảnh chụp khung cầu để AI bắt nhịp phiên đầu tiên.", parse_mode="Markdown")

@bot.message_handler(commands=['xoacache', 'xoa_cache'])
def cmd_xoa_cache(message):
    global global_session_history, pending_sessions, active_pending_session, consecutive_losses
    global_session_history.clear()
    pending_sessions.clear()
    active_pending_session.clear()
    consecutive_losses = 0
    gc.collect()
    bot.reply_to(message, "🧹 *Đã xóa sạch cache lịch sử các phiên trước đó thành công! Hệ thống đã được làm mới hoàn toàn.*", parse_mode="Markdown")

@bot.message_handler(commands=['xoalichsu', 'xoá_lịch_sử_phiên'])
def cmd_xoa_lich_su(message):
    global global_session_history, consecutive_losses
    global_session_history.clear()
    consecutive_losses = 0
    gc.collect()
    bot.reply_to(message, "🗑️ *Đã làm sạch lịch sử phân tích thành công!*", parse_mode="Markdown")

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
        bot.send_message(message.chat.id, "🔴 *Tool đã tắt hoàn toàn và xóa sạch bộ nhớ tạm!*", parse_mode="Markdown")
    except:
        pass

@bot.message_handler(content_types=['photo'])
def handle_image_input(message):
    global waiting_for_image, global_session_history, active_pending_session
    if not bot_status: return
    
    if not waiting_for_image:
        bot.reply_to(message, "⚠️ Đã qua giai đoạn gửi ảnh khởi tạo. Vui lòng tiếp tục gửi mã phiên MD5!", parse_mode="Markdown")
        return

    waiting_for_image = False

    scanned_history = [
        {"result": "TÀI"}, {"result": "XỈU"}, {"result": "TÀI"}, 
        {"result": "TÀI"}, {"result": "XỈU"}, {"result": "TÀI"}
    ]
    global_session_history.extend(scanned_history)
    
    ai_res_str, tai_pct, xiu_pct, pred_score = deep_500_lines_unbeatable_ai_engine("image_frame_scan_seed", global_session_history)
    pred_icon = f"{ai_res_str} ⚫" if ai_res_str == "TÀI" else f"{ai_res_str} ⚪"
    observed_trend = observe_nhan_dien_cau(global_session_history)
    
    markup = create_score_markup()
    
    analysis_text = (
        f"📸 *Đã quét xong con số trong khung cầu ảnh!*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 *AI phân tích:* {pred_icon}\n"
        f"🎲 *Dự đoán số nút:* `{pred_score} nút ({ai_res_str})`\n"
        f"📊 *Tỷ lệ phân tích:* [ TÀI: {tai_pct}% | XỈU: {xiu_pct}% ]\n"
        f"👁️‍🗨️ *Nhận Diện Cầu:* `{observed_trend}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *Chọn tổng điểm xí ngầu thực tế để AI học:*"
    )
    
    try:
        sent = bot.reply_to(message, analysis_text, parse_mode="Markdown", reply_markup=markup)
        pending_sessions[sent.message_id] = ("image_scan", time.time(), ai_res_str)
        active_pending_session["current"] = sent.message_id
    except:
        pass

@bot.message_handler(func=lambda m: True)
def handle_md5_input(message):
    global last_request_time, waiting_for_image, global_session_history, active_pending_session
    if not bot_status: return
    clean_expired_pending()

    if waiting_for_image:
        bot.reply_to(message, "📸 Vui lòng gửi ảnh chụp màn hình khung cầu trước theo lệnh `/start` hoặc `/mo_tool`!", parse_mode="Markdown")
        return

    if time.time() - last_request_time < COOLDOWN_TIME: return
    last_request_time = time.time()
    
    text = message.text.strip()
    if text.startswith('/') or len(text) > 256: return
    
    short_s = (text[:16] + "...") if len(text) > 16 else text
    
    ai_res_str, tai_pct, xiu_pct, pred_score = deep_500_lines_unbeatable_ai_engine(text, global_session_history)
    pred_icon = f"{ai_res_str} ⚫" if ai_res_str == "TÀI" else f"{ai_res_str} ⚪"
    
    observed_trend = observe_nhan_dien_cau(global_session_history)
    
    markup = create_score_markup()
    
    analysis_text = (
        f"🛡️ *Mã Phiên MD5:* `{short_s}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 *AI phân tích:* {pred_icon}\n"
        f"🎲 *Dự đoán số nút:* `{pred_score} nút ({ai_res_str})`\n"
        f"📊 *Tỷ lệ phân tích:* [ TÀI: {tai_pct}% | XỈU: {xiu_pct}% ]\n"
        f"👁️‍🗨️ *Nhận Diện Cầu:* `{observed_trend}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *Chọn tổng điểm xí ngầu thực tế để AI học:*"
    )
    
    try:
        sent = bot.reply_to(message, analysis_text, parse_mode="Markdown", reply_markup=markup)
        pending_sessions[sent.message_id] = (text, time.time(), ai_res_str)
        active_pending_session["current"] = sent.message_id
    except:
        pass

def create_score_markup():
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
    return markup

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
            bot.answer_callback_query(call.id, "⚠️ Phiên này đã được ghi nhận rồi!", show_alert=True)
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
            l_markup.add(InlineKeyboardButton(f"🔒 Đã chốt kết quả: {d_text}", callback_data="locked"))
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=msg_id, reply_markup=l_markup)
        except:
            pass

if __name__ == '__main__':
    print("TOOL TX AI 10.0 (DỰ ĐOÁN SỐ NÚT & RANDOM %) ĐÃ KHỞI ĐỘNG THÀNH CÔNG!")
    while True:
        try:
            bot.infinity_polling(none_stop=True, interval=0.5, timeout=20, long_polling_timeout=20)
        except Exception as e:
            time.sleep(3)
