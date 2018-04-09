import vk_api
import settings
import difflib

# процесс авторизации
if settings.acces_token() != '':
    bot = vk_api.VkApi(token=settings.acces_token())
    bot._auth_token()
elif settings.log_pass()[0] != '' and settings.log_pass()[1] != '':
    bot = vk_api.VkApi(login=settings.log_pass()[0], password=settings.log_pass()[1])
    bot.auth()
else:
    bot = None
    print("please login")

# списко айди тех, кто может карать банами (записывать каждое айди в кавычках (неважно двойные или одинарные) и через запятую)
#moderators = ["айди номер1", "айди номер2"]
moderators = eval(open("moderators.txt", "r").read())


def send_msg(chat_id, text, forward_messages = None):
    """отправляет сообщения"""
    if forward_messages == None:
        bot.method("messages.send", {"message": text, "chat_id": chat_id})
    else:
        bot.method("messages.send", {"message": text, "chat_id": chat_id, "forward_messages": forward_messages})


def get_msg(bot):
    """получает обновления сообщний"""
    response = bot.method("messages.get", {"count": 1})
    if response["items"][0] and response["items"][0]["read_state"] == 0:
        print(response)
        bot.method("messages.markAsRead", {"message_ids": response["items"][0]["id"]})
        return response


def users_list(chat_id):
    """составляет список тех, кто в данный момент в беседе"""
    list_users = []
    members_list = bot.method("messages.getChatUsers", {"chat_id": str(chat_id), "fields": "first_name"})
    for user in members_list:
        list_users.append({"first_name": user["first_name"],
                           "last_name": user["last_name"],
                           "uid": user["id"],
                           "chat_id": chat_id})
    return list_users


def get_user_id(first_name, last_name, chat_id):
    """пытается найти того, кого ты дал как аргументы"""
    for user in users_list(chat_id):
        if user["first_name"] == first_name and user["last_name"] == last_name:
            return user["uid"]


def kick(chat_id, body, first_name = None, last_name =  None, id = None):
    """кикает"""
    if first_name != None and last_name != None:
        try:
            # if get_user_id(first_name = first_name, last_name = last_name, chat_id = chat_id) != "Error 404":
            #     bot.method("messages.removeChatUser", {"chat_id": chat_id,
            #                                            "user_id": get_user_id(first_name, last_name, chat_id)})
            for user in users_list(chat_id):
                if similar(original=str(user["first_name"] + " " + user["last_name"]),
                           inp=str(body[1] + " " + body[2])):
                    bot.method("messages.removeChatUser", {"chat_id": chat_id,
                                                           "user_id": user["uid"]})

        except vk_api.exceptions.ApiError:
            send_msg(chat_id, text="Я не могу этого сделать (либо у меня нет прав на это, либо у тебя)", forward_messages=forward_message)
    elif id != None:
        try:
            bot.method("messages.removeChatUser", {"chat_id": chat_id,
                                               "user_id": id})
        except vk_api.exceptions.ApiError:
            pass

def add_new_moder(body, chat_id, forward_messages):
    """добавляет нового модера"""
    # if len(body) > 2:
    #     moderators.append(str(get_user_id(first_name= body[1], last_name= body[2], chat_id = chat_id)))
    #     open("moderators.txt", "w").write(str(moderators))
    #     send_msg(chat_id, text="Добавил", forward_messages=forward_message)
    if len(body) > 2:
        for user in users_list(chat_id):
            if similar(original= str(user["first_name"] + " " + user["last_name"]), inp=str(body[1] + " " + body[2])):
                # print("гг")
                uid = str(get_user_id(first_name=user["first_name"], last_name=user["last_name"], chat_id=chat_id))
                if uid not in moderators:
                    moderators.append(uid)
                    open("moderators.txt", "w").write(str(moderators))
                    text = "Добавил"
                else:
                    text = "Он уже там есть"
                send_msg(chat_id, text=text, forward_messages=forward_messages)


        # moderators.append(str(get_user_id(first_name= body[1], last_name= body[2], chat_id = chat_id)))
        # open("moderators.txt", "w").write(str(moderators))
        # send_msg(chat_id, text="Добавил", forward_messages=forward_message)

    elif len(body) == 2:
            moderators.append(body[1])
            open("moderators.txt", "w").write(str(moderators))
            send_msg(chat_id, text="Добавил", forward_messages=forward_message)


def remove_moder(chat_id, body, forward_messages):
    if len(body) > 2:
        print(moderators)
        for user in users_list(chat_id):
            if similar(original= str(user["first_name"] + " " + user["last_name"]), inp=str(body[1] + " " + body[2])):
                # print("гг")
                #send_msg(chat_id, text="Добавил", forward_messages=forward_messages)
                moderators.remove(str(get_user_id(first_name=user["first_name"], last_name=user["last_name"], chat_id=chat_id)))
                open("moderators.txt", "w").write(str(moderators))
                print(moderators)
                send_msg(chat_id, text="Удалил", forward_messages=forward_message)


def send_moder_list(chat_id, forward_message):
    text = ''
    for user in users_list(chat_id):
        #print(user)
        if str(user["uid"]) in moderators:
            text += user["first_name"] + ' ' + user["last_name"] + '\n'
    if text == "":
        text = "Не найдёны"
    send_msg(chat_id, text = text, forward_messages = forward_message)


def similar(original, inp):
    return difflib.SequenceMatcher(a = original.lower(), b = inp.lower()).ratio() > 0.7


# главная часть кода (да, я горазд писать кривые (но рабочие) алгоримты
if __name__ == '__main__':
    while True:
        response = get_msg(bot)
        if response != None:
            body = response["items"][0]["body"]
            if "chat_id" not in response["items"][0]:
                continue
            else:
                chat_id = response["items"][0]["chat_id"]
                forward_message = response["items"][0]["id"]

                if "!кик" in response["items"][0]["body"].lower():
                    if str(response["items"][0]["user_id"]) in moderators:
                        body = body.split(" ")
                        if len(body) >= 3:
                            kick(first_name= body[1], last_name= body[2], chat_id = chat_id, body = body)
                        elif len(body) == 2:
                            kick(id = body[1], chat_id = chat_id, body = body)
                    else:
                        send_msg(chat_id, text = "У тебя нет прав на это", forward_messages = forward_message)

                elif similar("!добавь", body.split(" ")[0]):
                    if str(response["items"][0]["user_id"]) in moderators:
                        body = body.split(" ")
                        chat_id = response["items"][0]["chat_id"]
                        add_new_moder(body = body, chat_id = chat_id, forward_messages = forward_message)
                        #print(moderators)
                    else:
                        send_msg(chat_id, text="У тебя нет прав на это", forward_messages= forward_message)

                elif similar("!удали", body.split()[0]):
                    remove_moder(chat_id, body.split(" "), forward_message)

                elif similar("!помощь", body.split(" ")[0]):
                    chat_id = response["items"][0]["chat_id"]
                    send_msg(chat_id, text="""кикнуть проказника(цу) - \"!кик Иван Пупкин\"\\\"!кик 123456789\""
                                \nдобавить нового модера - \"!добавить Иван Пупкин\"\\\"!добавить 123456789\"
                                \nузнать список модеров - \"!модеры\"
                                \nудалить модера - \"!удалить Иван Пупкин\"\\\"!удалить 123456789\"""", forward_messages = forward_message)

                elif similar("!модеры", body.split(" ")[0]):
                    send_moder_list(chat_id, forward_message = forward_message)
