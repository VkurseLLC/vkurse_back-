import mysql.connector
from mysql.connector import Error
from bot_config import *
import hashlib
from encode_decode import *
import datetime

# ---------------------------------------------------------------------------------- #

def create_connection():
    connection = None

    try:
        connection = mysql.connector.connect(
            host = '80.78.240.205',
            port = 13306,
            user = 'vkurse_editor', 
            password = 'T6XBwtgQ',
            database = 'vkurse_db')

        return connection

    except Error as e:
        print(f"Произошла ошибка в create_connection'{e}'")
        bot.send_message(chat_id, f"Произошла ошибка в create_connection\n\n{e}")
        return connection

# ---------------------------------------------------------------------------------- #

def user_authorisation(connection, phome_number_value, verification_code_value):
    with connection.cursor() as cursor:
        try:

            phome_number_value = phome_number_value.replace('+','')
            phome_number_value = phome_number_value.replace('(','')
            phome_number_value = phome_number_value.replace(')','')
            phome_number_value = phome_number_value.replace('-','')
            phome_number_value = phome_number_value.replace(' ','')

            phome_number_value  = (hashlib.sha256(repr(phome_number_value).encode())).hexdigest()
            verification_code_value  = (hashlib.sha256(repr(int(verification_code_value)).encode())).hexdigest()

            cursor.execute("SELECT `id` FROM `phone_number_verification_codes` WHERE `phone_number` = %s AND verification_code = %s AND TIMEDIFF (NOW(), `dt_create`) <= '00:03:00' AND `used` = 0",
                            (str(phome_number_value), str(verification_code_value)))
            result = cursor.fetchall()
            print(f'result: {result}')
            
            if len(result) != 0: 

                cursor.execute("UPDATE `phone_number_verification_codes` SET `used` = 1 WHERE `id` = %s", (str(result[0][0]),))
                connection.commit()

                cursor.execute("SELECT `id` FROM `users` WHERE `phone_number` = %s", (str(phome_number_value),))
                result = cursor.fetchall()

                if len(result) != 0:
                    
                    cursor.execute("SELECT `id` FROM `users_account_data` WHERE `users_id` = %s", (int(result[0][0]),))
                    user_account_status = cursor.fetchall()

                    if len(user_account_status) != 0:
                        return ['successful', result[0][0], 'old_user']
                    
                    else:
                        return ['successful', result[0][0], 'new_user']
                
                else:
                    cursor.executemany("INSERT INTO users (id, phone_number, dt_reg) VALUES (NULL, %s, NOW())", [(str(phome_number_value), )])
                    connection.commit()

                    cursor.execute("SELECT `id` FROM `users` WHERE `phone_number` = %s", (str(phome_number_value),))
                    result = cursor.fetchall()

                    cursor.execute("SELECT `id` FROM `users_account_data` WHERE `users_id` = %s", (int(result[0][0]),))
                    user_account_status = cursor.fetchall()

                    if len(user_account_status) != 0:

                        return ['successful', result[0][0], 'old_user']
                    
                    else:

                        return ['successful', result[0][0], 'new_user']

            else:
                return ['verification_code_not_found']
        
        except Error as e:
            print(f"Произошла ошибка сheck_user_block'{e}'")
            bot.send_message(chat_id, f"Произошла ошибка в check_auth\n\n{e}")
            return ['error']

def check_username_availability(connection, username_value):
    with connection.cursor() as cursor:
        try:
            username_value = username_value.replace(' ','')
            
            # Делаем запрос на проверку занятости username
            cursor.execute("SELECT `users_id`, `username` FROM `users_username` WHERE `username` = %s ORDER BY `dt_upd` DESC", (str(username_value),))
            result = cursor.fetchall()
            
            # Если username не был найден в базе, то выводим True
            if len(result) == 0:
                return ['True']
            
            # Иначе делаем проверку на то, занят ли сейчас выбранный username у последнего держателя
            else:
                cursor.execute("SELECT `username` FROM `users_username` WHERE `users_id` = %s ORDER BY `dt_upd` DESC", (int(result[0][0]),))
                result = cursor.fetchall()

                if username_value != str(result[0][0]):
                    return ['True']

                else:
                    return ['False']
        
        except Error as e:
                print(f"Произошла ошибка check_username_availability: {e}")
                bot.send_message(chat_id, f"Произошла ошибка в check_username_availability\n\n{e}")
                return ['error']
        
def filling_profile(connection, users_id, username, first_name, d_birth, city):
    with connection.cursor() as cursor:

        try:
            check_username = check_username_availability(create_connection(), username)
            # users_id = get_user_id(create_connection(), )
            first_name = encrypt(repr(first_name), crypto_key)
            d_birth = encrypt(repr(d_birth), crypto_key) 
            

            cursor.execute("SELECT `id` FROM `cities` WHERE `city_name` = %s", (str(city),))
            city_id = cursor.fetchall()[0][0]

            if check_username[0] == 'True':

                cursor.executemany("INSERT INTO `users_username` (`id`, `users_id`, `username`, `dt_upd`) VALUES (NULL, %s, %s, NOW())", [(int(users_id), str(username),)])

                cursor.executemany("INSERT INTO `users_account_data` (`id`, `users_id`, `first_name`, `d_birth`, `dt_upd`) VALUES (NULL, %s, %s, %s, NOW())",
                                    [(str(users_id), str(first_name), str(d_birth),)])

                cursor.executemany("INSERT INTO `users_city` (`id`, `users_id`, `cities_id`, `dt_upd`) VALUES (NULL, %s, %s, NOW())", [(int(users_id), int(city_id),)])

                connection.commit()

                return ['successful']
            
            else:
                return ['username_is_taken']


        except Error as e:
                print(f"Произошла ошибка filling_profile: {e}")
                bot.send_message(chat_id, f"Произошла ошибка в filling_profile\n\n{e}")
                return ['error']
        
def city_selection(connection):
    with connection.cursor() as cursor:
        try:
            cursor.execute("SELECT `city_name` FROM `cities`")
            result = cursor.fetchall()
            city = []
            for cities in result:
                city.append(cities[0])

            return city
        
        except Error as e:
                print(f"Произошла ошибка city_selection: {e}")
                bot.send_message(chat_id, f"Произошла ошибка в city_selection\n\n{e}")
                return ['error']

# ---------------------------------------------------------------------------------- #

def template(connection):
    with connection.cursor() as cursor:
        try:
            pass
        
        except Error as e:
                print(f"Произошла ошибка template: {e}")
                bot.send_message(chat_id, f"Произошла ошибка в template\n\n{e}")
                return ['error']

# ---------------------------------------------------------------------------------- #


# ТЕСТОВЫЕ ЗАПРОСЫ:

# print(user_authorisation(create_connection(), '79287539056', 97173))

# print(user_authorisation(create_connection(), '+7 (928) 753-90-56', 97173))

# print(filling_profile(create_connection(), "2", "seemyownnn", "Semyon", "2003-07-03", "Ростов-на-Дону")) # Заполнение профиля

# print(user_authorisation(create_connection(), '79958932523', 80640)) # Прооверка авторизации пользователя

# city_selection(create_connection())

# print(check_username_availability(create_connection(), "seemyownn"))

# print(get_user_id(create_connection(), "79958932523"))
# print()