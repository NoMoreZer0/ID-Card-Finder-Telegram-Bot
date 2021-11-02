import telebot
import sqlite3

from telebot import types

from constans import API_KEY

bot = telebot.TeleBot(API_KEY, parse_mode=None)

bot.state = None # 1 -> Enter BarCode, 2 -> Enter ID Data

#Opens Keyboard with 3 buttons
def OpenKeyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2)
    button1 = types.KeyboardButton("/find_id_card")
    button2 = types.KeyboardButton("/help")
    button3 = types.KeyboardButton("/exit")
    markup.add(button1, button2, button3)
    return markup

__connection = None

#Verifies Connections
def GetConnection():
    global __connection
    if __connection is None:
        __connection = sqlite3.connect('users.db', check_same_thread=False)
    return __connection


#Creating Table
def CreateTable():
    table = GetConnection()
    cursor = table.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS UsersID (
        BarCode text
        EduGroupName text
        FacultyName text
        GroupName text
        StudentName text
    )''')

    table.commit()

#checks if entered BarCode exist in DataBase
def IsExist(MyBarCode):
    table = GetConnection()
    cursor = table.cursor()

    cursor.execute('SELECT * FROM UsersID')

    data = []
    for row in cursor: #iterate through all rows in table
        flag = False
        for column in row:
            if (column == MyBarCode):
                flag = True
        if flag is True:
            for column in row:
                data.append(column)
            break

    table.commit()
    return data

#adds a student's ID information into database
def AddStudent(BarCode: str, EduGroupName: str, FacultyName: str, GroupName: str, StudentName: str):
    table = GetConnection()
    cursor = table.cursor()
    cursor.execute('insert into UsersID values (?, ?, ?, ?, ?)', (BarCode, EduGroupName, FacultyName, GroupName, StudentName))
    table.commit()

#closes keyboard
def CloseKeyboard(flag, message):
    markup = types.ReplyKeyboardRemove(selective=False)
    if (flag): # if flag -> 1 then it is goodbye message
        bot.send_message(chat_id=message.chat.id, text="Good Bye!",
                     reply_markup=markup)

#check if text inputted in wrong format
def IsWrongFormat(Text):
    cnt = 0
    for i in range(0, len(Text)):
        if Text[i] == '_':
            cnt += 1
    if cnt == 4:
        return False
    return True

#handles exit command
@bot.message_handler(commands="exit")
def send_exit_message(message):
    CloseKeyboard(1, message)


#handles help command
@bot.message_handler(commands="help")
def send_help_message(message):
    bot.send_message(chat_id=message.chat.id, text="Bot will help you to find Digital Version of your ID card!\n"
                                                   "Please choose the option find_id_card and enter your bar code")

#handles find_id_card command
@bot.message_handler(commands="find_id_card")
def send_id_card(message):
    bot.send_message(chat_id=message.chat.id, text="Please enter your Bar Code!")
    bot.state = 1 #state -> 1 it means the next message is BarCode

#handles if state -> 1
@bot.message_handler(func=lambda msg:bot.state == 1)
def getBarCode(message):
    BarCode = message.text

    data = IsExist(BarCode) # data is an array

    if len(data) == 0: # if BarCode not exist array is empty
        bot.send_message(chat_id=message.chat.id, text="Couldn't find your Bar Code please enter information in the following way:")
        bot.send_message(chat_id=message.chat.id, text="BarCode_Educationl Group Name_Faculty Name_Group Name_Student Name")
        bot.send_message(chat_id=message.chat.id, text="For Example: 123456_Information and Technology_Cybersecurity_CS-123_Kimbai Kimbek")
        bot.state = 2 # now we need to add this student's information to table so state -> 2
    else: # else we will just output information in an array and close the keyboard
        bot.send_message(chat_id=message.chat.id, text='\n'.join(data))
        bot.state = None
        CloseKeyboard(1, message)

#handles when state -> 2
@bot.message_handler(func=lambda msg:bot.state == 2)
def InsertBarCode(message):
    Text = message.text

    if (IsWrongFormat(Text)):
        bot.send_message(message.chat.id, "You've sent Information in wrong format re-send it again!")
        return

    BarCode = ""
    EduGroupName = ""
    FacultyName = ""
    GroupName = ""
    StudentName = ""
    cnt = 0

    for i in range(0, len(Text)): # just process the information given from the user
        if Text[i] == '_':
            cnt += 1
            continue
        if (cnt == 0):
            BarCode += Text[i]
        elif (cnt == 1):
            EduGroupName += Text[i]
        elif (cnt == 2):
            FacultyName += Text[i]
        elif (cnt == 3):
            GroupName += Text[i]
        elif (cnt == 4):
            StudentName += Text[i]

    AddStudent(BarCode, EduGroupName, FacultyName, GroupName, StudentName) # adds a student

    data = IsExist(BarCode) # just to verify if it is added without any error

    if (len(data) != 0):
        bot.send_message(chat_id=message.chat.id, text="Your Information added successfully!")
    else:
        bot.send_message(chat_id=message.chat.id, text="Some error occured")

    bot.state = None
    CloseKeyboard(1, message)

#handles start message
@bot.message_handler(commands="start")
def send_start_message(message):
    markup = OpenKeyboard()

    bot.send_message(chat_id=message.chat.id,
                     text="Hello! This is Telegram ID card finder! Please Choose what do you want",
                     reply_markup=markup)
    CreateTable()

bot.polling()
