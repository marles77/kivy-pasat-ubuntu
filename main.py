import os
os.environ['KIVY_AUDIO'] = 'android'#'ffpyplayer'#
import kivy
kivy.require('1.11.1')
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.factory import Factory
from kivy.storage.jsonstore import JsonStore
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
import sqlite3
from sqlite3 import Error
import datetime
import random
import uuid
import pyrebase
from time import perf_counter

from buttons import TestButton, ExitButton, InfoButton, BigButton, MainButton
from firebase_config import FirebaseConfig
from check_connect import check_connectivity

# constants
APP_NAME = "Paced Auditory Serial Addition Test"
APP_AUTHOR = "Marcin Leśniak"
APP_VERSION = "0.1.1"
APP_CREDITS = "Dorothy Gronwall Perceptual & motor skills. 1977;44(2):367-73\nhttps://freesound.org/s/185037/"
APP_DB_PATH = "Database/db_pasat.db"
APP_SETTINGS_PATH = 'Settings/settings.json'

# set window properties
if platform != 'android':
    Window.size = (1920, 1080)
Window.maximize()
window_width, window_height = Window.size
Builder.load_file('main.kv')

#TODO: zamienic printy na logi

#Database
class DB():
    def __init__(self, db_path):
        self.db_path = db_path

    def create_connection(self):
        connection = None
        try:
            connection = sqlite3.connect(self.db_path)
            print("Connection established")
        except Error as e:
            print(f"The error '{e}' occured")
        return connection

    # read db
    def read_query(self, connection, query, *value):
        cursor = connection.cursor()
        result = None
        try:
            cursor.execute(query, value)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"The error '{e}' occured")

    # modify db
    def execute_query(self, connection, query, values):
        cursor = connection.cursor()
        try:
            cursor.execute(query, values)
            connection.commit()
            print("Query executed successfully")
            if str(sm.current) != 'test':
                app.open_popup(label_popup='Zapisano')
            return cursor.lastrowid
        except Error as e:
            print(f"The error '{e}' occurred")
            return False

# Declare screens
class TitleScreen(Screen):
    tick_num = 0
    text1 = '9 4 5 4 7'
    text2 = 'P A 5 A T'
    def start(self):
        self.ids.lab_title.text = ''
        self.event = Clock.schedule_interval(self.clock_tick, 0.1)

    def open_info(self):
        app.open_popup(label_popup=f'{APP_NAME}\nAutor: {APP_AUTHOR}\nWersja: {APP_VERSION}\nId urządzenia: {app.mac_id}\nCredits:\n{APP_CREDITS}')

    def clock_tick(self, dt):
        self.tick_num += 1
        if self.tick_num > len(self.text1):
            if self.tick_num > len(self.text1)+2:
                self.ids.lab_title.text = self.text2
                self.event.cancel()
        else:
            self.ids.lab_title.text = self.text1[0:self.tick_num]

    def on_begin(self):
        if self.event:
            self.event.cancel()
        sm.current = 'menu'

class MenuScreen(Screen):
    def start(self):
        app.update_screen_history(sm.current)

class DBScreen(Screen):
    def __init__(self, **kwargs):
        super(DBScreen, self).__init__(**kwargs)
        self.proj_dict = {}
        self.subjects = None

    def start(self, connection):
        app.update_screen_history(sm.current)
        self.select_ob(connection, None)
        self.ids.spinner_proj.values = []
        self.ids.spinner_proj.text = 'Wybierz projekt'

        select_projects = "SELECT * from t_projects ORDER BY proj_name ASC"
        projects = sql_db.read_query(connection, select_projects)
        if projects:
            projects_list = []
            for project in projects:
                projects_list.append(str(project[1]))
                self.proj_dict[str(project[1])] = project[0]
            self.ids.spinner_proj.values = projects_list
            print(self.proj_dict)
        else:
            print("Brak projektów")

    def on_spinner_select(self, value):
        #print(f"The spinner_db {self} has text {value}")
        if self.subjects:
            for subject in self.subjects:
                if subject[1] == value:
                    app.ob_id = subject[0]
                    l = list( {k: v for k, v in self.proj_dict.items() if v == subject[5]}.items() )
                    if l:
                        self.ids.spinner_proj.text = l[0][0]
                        print(l[0][1])
        self.ids.spinner_db.text = value

    def on_spinner_proj_select(self, connection, value):
        print(f"The spinner_proj {self} has text {value}")
        if value != 'Wybierz projekt':
            proj_id = self.proj_dict[value]
            #self.select_ob(connection, proj_id)
            if self.subjects:
                self.ids.spinner_db.values = []
                self.ids.spinner_db.text = 'Wybierz OB'
                subjects_list = []
                for subject in self.subjects:
                    if subject[5] == proj_id:
                        subjects_list.append(str(subject[1]))
                self.ids.spinner_db.values = subjects_list
            app.proj_id = proj_id

    def select_ob(self, connection, proj_id = None):
        self.ids.spinner_db.values = []
        self.ids.spinner_db.text = 'Wybierz OB'
        value = proj_id
        if value:
            select_subjects = "SELECT * from t_subjects WHERE proj_id = ? ORDER BY sub_code ASC"
            self.subjects = sql_db.read_query(connection, select_subjects, value)
        else:
            select_subjects = "SELECT * from t_subjects ORDER BY sub_code ASC"
            self.subjects = sql_db.read_query(connection, select_subjects)
        if self.subjects:
            subjects_list = []
            for subject in self.subjects:
                print(subject)
                subjects_list.append(str(subject[1]))
            self.ids.spinner_db.values = subjects_list
        else:
            print("Brak OB")

    # rozpoczecie testu
    def on_begin(self, sub_code, proj_name):
        sub_id = None
        proj_id = self.proj_dict.get(proj_name)
        print(f'sub_code: {sub_code}, proj_name: {proj_name}')
        for subject in self.subjects:
            if subject[1] == sub_code:
                sub_id = subject[0]
                break
        if sub_id and proj_id:
            app.ob_id = sub_id
            app.proj_id = proj_id
            print(f'sub_id: {app.ob_id}, proj_id: {app.proj_id}')
            sm.current = 'settings'

    def on_edit(self, code):
        if code != 'Wybierz OB':
            sm.current = 'update_subject'

class ProjectScreen(Screen):
    def start(self):
        app.update_screen_history(sm.current)
        self.ids.input_project_name.text = ''
        self.ids.input_project_desc.text = ''

    def save_project(self, connection, name, desc):
        name_str = name.strip()
        desc_str = desc.strip()
        if name_str and desc_str:
            select_projects = "SELECT * from t_projects WHERE proj_name = ?"
            value = name_str
            #print(value)
            projects = sql_db.read_query(connection, select_projects, value)
            if projects:
                app.open_popup(label_popup='Projekt o podanej nazwie już istnieje')
            else:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                insert_project = ("INSERT INTO t_projects (proj_name, proj_desc, proj_date) VALUES (?, ?, ?)")
                values = (name_str, desc_str, timestamp)
                sql_db.execute_query(connection, insert_project, values)
        else:
            app.open_popup(label_popup= 'Brak danych')

    # change of TextInput
    def input(self, input_id, lab_id, max_char):
        #print(f"Napisano: {len(value)}")
        value = self.ids[input_id].text
        lab_text = self.ids[lab_id].text

        if len(value) > 0 and value[len(value)-1] in '"\'':
            self.ids[input_id].text = value[0:len(value)-1]
        else:
            index = lab_text.index('(')
            self.ids[lab_id].text = f'{lab_text[:index]}({max_char - len(value)}):'
        if len(value) > max_char:
            self.ids[input_id].text = value[0:max_char]

class ResultsScreen(Screen):
    def start(self):
        app.update_screen_history(sm.current)
        check_connect = check_connectivity()
        print(check_connect)
        if not check_connect:
            app.open_popup(label_popup='Brak połączenia z internetem')

    def make_db_backup(self):
        success = 0
        login = {}
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = 'Backup/db.sql'
        data = '\n'.join(app.conn.iterdump())
        try:
            f = open(file_name, 'w')
            with f:
                f.write(data)
            print('zapisano')
            success = 1
        except IOError as e:
            print(f'nie udało się: {e}')
            app.open_popup(label_popup='Błąd zapisu pliku')
        if success == 1:
            try:
                auth = app.firebase.auth()
                login = auth.sign_in_with_email_and_password(app.firebase_config.user["email"], app.firebase_config.user["pass"])
                success = 2# if login["localId"].get() else 1
            except:
                success = 1
                print('nie zalogowano')
                app.open_popup(label_popup='Błąd logowania, sprawdź połączenie')
        if success == 2:
            try:
                new_file_name = app.firebase_config.storage["folder"] + 'db-' + app.mac_id + '-' + timestamp + '.sql'
                storage = app.firebase.storage()
                storage.child(new_file_name).put(file_name, login['idToken'])
                print('przesłano')
                app.open_popup(label_popup='Kopia zapasowa przesłana')
            except:
                print('nie przesłano')
                app.open_popup(label_popup='Błąd transferu, sprawdź połączenie')

class NewSubjectScreen(Screen):
    def start(self, connection):
        app.update_screen_history(sm.current)
        self.ids.input_code.text = ''
        self.ids.input_birth.text = ''
        self.ids.input_sex.text = ''
        self.ids.spinner_proj.values = []
        self.ids.spinner_proj.text = 'Wybierz projekt'

        select_projects = "SELECT * from t_projects ORDER BY proj_name ASC"
        projects = sql_db.read_query(connection, select_projects)
        if projects:
            projects_list = []
            for project in projects:
                projects_list.append(str(project[1]))
            self.ids.spinner_proj.values = projects_list
        else:
            print("Brak projektów")

    def on_spinner_proj_select(self, value):
        print(f"The spinner_proj {self} has text {value}")

    def save_subject(self, connection, code, birth, sex, proj_name, begin_test):
        code_str = code.strip()
        birth_str = birth.strip()
        sex_str = sex.strip()
        if code_str and birth_str and sex_str and proj_name != 'Wybierz projekt':
            select_subjects = "SELECT * from t_subjects WHERE sub_code = ?"
            value = code_str
            subjects = sql_db.read_query(connection, select_subjects, value)
            if subjects:
                app.open_popup(label_popup='OB o podanym kodzie już istnieje')
            else:
                select_projects = "SELECT * from t_projects WHERE proj_name = ?"
                value = proj_name
                projects = sql_db.read_query(connection, select_projects, value)
                if projects:
                    proj_id = projects[0][0]
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    insert_subject = ("INSERT INTO t_subjects (sub_code, sub_birth, sub_sex, sub_date, proj_id) VALUES (?, ?, ?, ?, ?)")
                    values = (code_str, birth_str, sex_str, timestamp, proj_id)
                    res = sql_db.execute_query(connection, insert_subject, values)
                    print(res)
                    if res and begin_test:
                        app.ob_id = res
                        app.proj_id = proj_id
                        print(f'sub_id: {app.ob_id}, proj_id: {app.proj_id}')
                        sm.current = 'settings'
                else:
                    app.open_popup(label_popup='Ups! Nie ma takiego projektu')
        else:
            app.open_popup(label_popup= 'Brak wymaganych danych')

    # change of TextInput
    def input(self, input_id, lab_id, max_char):
        #print(f"Napisano: {len(value)}")
        value = self.ids[input_id].text
        lab_text = self.ids[lab_id].text

        if len(value) > 0 and value[len(value)-1] in '"\'':
            self.ids[input_id].text = value[0:len(value)-1]
        else:
            index = lab_text.index('(')
            self.ids[lab_id].text = f'{lab_text[:index]}({max_char - len(value)}):'
        if len(value) > max_char:
            self.ids[input_id].text = value[0:max_char]

class UpdateSubjectScreen(Screen):
    def __init__(self, **kwargs):
        super(UpdateSubjectScreen, self).__init__(**kwargs)
        self.cache_var = None #variable that will keep the value of subject's id

    def start(self, connection):
        app.update_screen_history(sm.current)
        sub_code = app.root.get_screen('db').ids.spinner_db.text
        if sub_code and sub_code != 'Wybierz OB':
            self.ids.input_code.text = sub_code
            select_subjects = "SELECT * from t_subjects WHERE sub_code = ?"
            value = sub_code
            subjects = sql_db.read_query(connection, select_subjects, value)
            if subjects:
                self.ids.input_birth.text = str(subjects[0][2])
                self.ids.input_sex.text = str(subjects[0][3])
                self.cache_var = str(subjects[0][0])
                self.ids.spinner_proj.values = []
                select_projects = "SELECT * from t_projects ORDER BY proj_name ASC"
                projects = sql_db.read_query(connection, select_projects)
                if projects:
                    projects_list = []
                    for project in projects:
                        projects_list.append(str(project[1]))
                        # dodawanie nazwy projektu
                        if project[0] == subjects[0][5]:
                            self.ids.spinner_proj.text = str(project[1])
                    self.ids.spinner_proj.values = projects_list
                else:
                    print("Brak projektów")
                #print(self.cache_var)
            else:
                print("Coś poszło nie tak - nie znaleziono OB o podanym kodzie")

    def on_spinner_proj_select(self, value):
        print(f"The spinner_proj {self} has text {value}")
        #print(self.cache_var)

    def update_subject(self, connection, code, birth, sex, proj_name):
        code_str = code.strip()
        birth_str = birth.strip()
        sex_str = sex.strip()
        sub_id = self.cache_var
        if code_str and birth_str and sex_str and proj_name != 'Wybierz projekt':
            #check if the code is not occupied by subjects with other ids than the current one
            select_subjects = "SELECT * from t_subjects WHERE sub_code = ? AND NOT sub_id = ?"
            values = (code_str, sub_id)
            subjects = sql_db.read_query(connection, select_subjects, values)
            if subjects:
                app.open_popup(label_popup='OB o podanym kodzie już istnieje')
            else:
                select_projects = "SELECT * from t_projects WHERE proj_name = ?"
                value = proj_name
                projects = sql_db.read_query(connection, select_projects, value)
                if projects:
                    proj_id = projects[0][0]
                    #timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    insert_subject = ("UPDATE t_subjects SET sub_code=?, sub_birth=?, sub_sex=?, proj_id=? WHERE sub_id=?")
                    values = (code_str, birth_str, sex_str, proj_id, sub_id)
                    sql_db.execute_query(connection, insert_subject, values)
                    print(values)
                else:
                    app.open_popup(label_popup='Ups! Nie ma takiego projektu')
        else:
            app.open_popup(label_popup= 'Brak wymaganych danych')
    # change of TextInput
    def input(self, input_id, lab_id, max_char):
        #print(f"Napisano: {len(value)}")
        value = self.ids[input_id].text
        lab_text = self.ids[lab_id].text

        if len(value) > 0 and value[len(value)-1] in '"\'':
            self.ids[input_id].text = value[0:len(value)-1]
        else:
            index = lab_text.index('(')
            self.ids[lab_id].text = f'{lab_text[:index]}({max_char - len(value)}):'
        if len(value) > max_char:
            self.ids[input_id].text = value[0:max_char]

class SettingsScreen(Screen):
    def start(self):
        app.update_screen_history(sm.current)
        #print('json: ', app.store.get('settings')[0]['name'])
        self.settings = app.store.get('settings')
        sett_names_list = []
        self.ids.spinner_settings.values = []
        self.ids.spinner_settings.text = 'Wybierz zestaw'
        for setting in self.settings:
            sett_names_list.append(setting['name'])
        self.ids.spinner_settings.values = sett_names_list
        # sprawdzenie czy urzadzenie jest podlaczone do internetu
        check_connect = check_connectivity()
        print(check_connect)
        if check_connect:
            app.open_popup(label_popup='Przed uruchomieniem testu odłącz internet')

    def on_spinner_set_select(self, value):
        #self.ids.spinner_int.values = []
        #self.ids.spinner_int.text = 'Wybierz interwał'
        chosen_setting = {}
        for setting in self.settings:
            if setting['name'] == value:
                chosen_setting = setting
                break
        if chosen_setting:
            print(f"Chosen setting: {chosen_setting['name']}, intervals: {chosen_setting['series']}")
            #self.ids.spinner_int.values = [str(val) for val in chosen_setting['series']]
            app.setting_name = chosen_setting['name']

    def on_begin(self):
        if self.ids.spinner_settings.text != 'Wybierz zestaw':
            sm.current = 'test'

class TestScreen(Screen):
    #ticks_num = ticks_counter = 0
    def __init__(self, **kwargs):
        super(TestScreen, self).__init__(**kwargs)
        if platform != 'android':
            self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
            self._keyboard.bind(on_key_down=self._on_keyboard_down)
        else:
            self._keyboard = None

    def set_initial_params(self):
        # zmienne dla podstawowych ustawien
        #self.sound = []
        self.init_sound = None
        self.sounds = None
        self.ob_id = self.test_id = None
        self.stim = None
        self.settings = {}
        self.times = {}
        #self.numbers = []
        self.sets = []
        self.train = False
        # zmienne dla poczatkowych parametrow
        self.stim_set = {}
        self.ser_num = self.bloc_num = self.stim_index = 0
        self.cor_sum = None
        self.answered = 0  # 0 - brak; 1 - zla; 2 - dobra;
        # zmienne kontrolujace tiki zegara
        self.tick_val = 0.01
        self.event = None
        self.curr_interval = self.actual_interval = self.rt = 0
        self.t1 = self.t2 = 0

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'q':
            App.get_running_app().stop()
        return True

    def preload(self, ob_id, setting_name):
        self.set_initial_params()
        #print(f"min state time: {self.ids.but_esc.min_state_time}")
        #print(f"rt: {self.rt}")
        app.update_screen_history(sm.current)
        self.ids.but_start.height = window_height // 5
        self.ids.lab_bottom.height = window_height // 5
        self.ids.but_start.text = 'PROSZĘ CZEKAĆ'
        self.ids.lab_bottom.text = ' '
        self.ob_id = ob_id
        settings = app.store.get('settings')
        for setting in settings:
            if setting['name'] == setting_name:
                self.settings = setting
        self.train = True if self.settings['train'] == 1 else False
        self.sets = app.store.get('sets')
        self.times = app.store.get('times')
        self.test_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        self.hide_buttons()
        #self.init_sound = SoundLoader.load('Audio/wav/init_tone.wav')
        self.sounds = SoundLoader.load('Audio/wav/sounds.wav')
        #print(self.sounds.state)
        #self.sound.append(self.init_sound)
        #self.sound[0] = SoundLoader.load('Audio/wav/init_tone.wav')
        
        if self.sounds:
            self.sounds.seek(8.30)
            self.sounds.play()
        #if self.init_sound:
        #    #self.init_sound.seek(0.86)
        #    self.init_sound.play()
    #Stare rozwiazanie
        #for num in range(1,10):
        #    file_name = 'c' + str(num) + '.wav'
        #    new_sound = SoundLoader.load('Audio/wav/'+file_name)
        #    self.sound.append(new_sound)
        #    new_sound.unload()
        #if self.sound:
        #    self.sound[9].play()

    def clock_esc(self, dt):
        self.event_esc.cancel()
        if self.ids.but_esc.state == 'down':
            if self.event:
                self.event.cancel()
            if self.init_sound:
                self.init_sound.unload()
            if self.sounds:
                self.sounds.unload()
            sm.current = 'settings'

    def escape_test(self):
        self.event_esc = Clock.schedule_interval(self.clock_esc, 2)

    def hide_buttons(self):
        for i in range(1, 5):
            index = 'but_' + str(i)
            self.ids[index].visible = False
        self.ids.but_start.visible = True

    def start(self):
        self.ids.but_start.visible = False
        for i in range(1, 5):
            index = 'but_' + str(i)
            self.ids[index].visible = True
        self.start_test(self.ser_num, self.bloc_num, self.stim_index)

    ##########################
    # tu zaczyna sie pasat.py

    # OK
    def start_test(self, ser_num, bloc_num, stim_index):
        if self.init_sound:
                self.init_sound.unload()
        self.ser_num = ser_num; self.bloc_num = bloc_num; self.stim_index = stim_index;
        if self.ser_num > len(self.settings['series'])-1:
            self.bloc_num += 1
            self.ser_num = 0
            if self.bloc_num > self.settings['blocs_in_ser']-1:
                print("Koniec testu")
                #print(f"tiki: {self.ticks_num}")
                self.ids.lab_bottom.text = 'KONIEC'
                app.open_popup(label_popup='Koniec testu')
                sm.current = 'settings'
            else:
                self.curr_interval = self.settings['series'][self.ser_num]
                self.start_clock()
        else:
            self.curr_interval = self.settings['series'][self.ser_num]
            self.start_clock()
    # OK
    def start_clock(self):
        print(f"Interval: {self.curr_interval}")

        if self.settings['stim_sets']:
            set_name = self.settings["stim_sets"][self.bloc_num]  # dodac zabezpieczenie, gdyby nie bylo elementu listy
            for s in self.sets:
                if s["name"] == set_name:
                    self.stim_set = s
                    break
            self.stim_set["set"][0] = random.randint(1, 9)
        else:
            self.stim_set = self.generate_set(self.settings['set_length'] + 1)
        # print(f"Length: {len(stim_set['set'])}\n Set: {stim_set}")
        self.actual_interval = 3 # przed prezentacja 1-go bodzca w serii
        self.cor_sum = None
        for val in range(4):
            index = 'but_' + str(val + 1)
            self.ids[index].text = ''
        self.t1 = perf_counter()
        self.event = Clock.schedule_interval(self.clock_tick, self.tick_val) #
    # OK
    def clock_tick(self, dt):
        if self.stim and self.sounds:
            pos = self.sounds.get_pos()
            if (self.sounds.state == 'play') and (pos > self.times[str(self.stim)][1]):
                #print(f"Pozycja: {pos}")
                self.sounds.stop()
                #print(self.sounds.state)

        self.t2 = perf_counter()
        czas = self.t2 - self.t1

        if czas > self.actual_interval:
            if self.train == False and self.stim_index > 0:
                self.rec_answer(app.proj_id, app.ob_id, self.curr_interval, self.stim_set['set'][self.stim_index - 1], self.answered, self.rt, self.settings['name'], self.test_id)
            if self.stim_index > len(self.stim_set['set'])-1:
                self.stim = self.cor_sum = None
            else:
                # tymczasowe
                if self.stim_index == 0:
                    #self.t1 = perf_counter()
                    print(f"Czas start! Interwal: {dt}")
                #
                self.stim = self.stim_set['set'][self.stim_index]
                #self.ticks_counter = 0
                self.actual_interval = self.curr_interval + self.times[str(self.stim)][2]
                #self.ticks_num = int( self.actual_interval / self.tick_val )
                self.cor_sum = self.stim_set["set"][self.stim_index] + self.stim_set["set"][self.stim_index - 1] if self.stim_index > 0 else None

            if self.stim:
                self.show_stim(self.stim, self.cor_sum)
            print(f"Stimulus: {self.stim}, Correct sum: {self.cor_sum}, czas: {czas:.4f}")
            self.t1 = perf_counter()
            self.stim_index += 1
            if self.stim_index > len(self.stim_set['set']):
                self.event.cancel()
                # tymczasowe
                #self.t2 = perf_counter()
                #czas = self.t2 - self.t1
                #print(f"Koniec serii, bodzcow: {self.stim_index-1}, czas: {czas:.4f}, czas na bodziec: {czas/(self.stim_index)}")
                #
                self.ser_num += 1
                self.stim_index = 0
                #self.t1 = perf_counter()
                #self.start_test(self.ser_num, self.bloc_num, 0)
                self.hide_buttons()

        # przysloniecie cyfr na przyciskach przed kolejnym bodzcem
        elif czas > self.actual_interval - 0.1:
            for val in range(4):
                index = 'but_' + str(val + 1)
                self.ids[index].font_color = (1,1,1,0)
                self.ids.lab_bottom.text = ' '

    # Show stimulus
    # OK
    def show_stim(self, stim, correct_response):#index, stim, correct_response, interval, times):
        self.rt = 0
        if self.sounds:
            self.sounds.seek(self.times[str(stim)][0])
            self.sounds.play()
        if correct_response:
            positions, corr_position = self.rand_options(stim, correct_response)
            self.answered = 0
            
            for pos in positions:
                for key, val in pos.items():
                    index = 'but_' + str(val + 1)
                    self.ids[index].text = str(key)
                    self.ids[index].font_color = (1,1,1,1)
                    self.ids[index].line_color = (1,1,1,1)
            #if self.train:
            #    self.ids.lab_bottom.text = str(correct_response - stim) + '  +  ' + str(stim) + '  =  ?'
        else:
            for val in range(4):
                index = 'but_' + str(val + 1)
                self.ids[index].text = ''
                self.ids[index].line_color = (1,1,1,1)

    # Generate a random set
    # OK
    def generate_set(self, n):
        stim_set = {"name": "random", "set": []}
        for i in range(n):
            stim_set["set"].append(random.randint(1, 9))
        return stim_set

    # Random generation of 4 options to show
    # OK
    def rand_options(self, stim, correct_response):
        available_positions = [0, 1, 2, 3]
        key = random.randint(0, 3)
        target = {correct_response: key}
        options = [target]
        available_positions.remove(key)
        # randomly reorganize positions
        random.shuffle(available_positions)

        for pos in available_positions:
            while True:
                distr_number = correct_response + random.choice([i for i in range(-4, 4) if i not in [0]])
                if (distr_number in range(1, 19)) and (
                not any(distr_number in d for d in options)):  # rozwiazanie pythoniczne :)
                    break
            options.append({distr_number: pos})

        return options, key

    # obsluga przyciskow do odpowiedzi
    def test_but_press(self, but_name):
        if self.answered == 0: # jesli brak odpowiedzi
            t3 = perf_counter()
            rt = t3 - self.t1
            text = self.ids[but_name].text
            correct = str(self.cor_sum)
            if rt > 0.15 and text:
                if text == correct:
                    self.answered = 2 # dobra odpowiedz
                    message = 'OK'
                else:
                    self.answered = 1 # zla odpowiedz
                    message = ''
                # tymczasowe
                print(f"Correct: {correct}, Button: {text}, Message: {message}, RT: {rt:.2f}")
                #
                self.rt = int(round(rt, 3) * 1000)
                if self.train:
                    if message:
                        self.ids[but_name].line_color = (0, 0.6, 0.2, 1)
                    else:
                        self.ids[but_name].line_color = (0.8, 0, 0, 1)

    # Record user answer in database
    # OK
    def rec_answer(self, proj_id, sub_id, interval, stim, correct, rt, settings_name, test_id):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #print(f'proj_id: {proj_id}, sub_id: {sub_id}, date: {timestamp}, interval: {interval}, stim: {stim}, correct: {correct}, rt: {rt}, settings_name: {settings_name}')
        insert_result = (
            "INSERT INTO t_results (proj_id, sub_id, res_date, res_interval, res_stimulus, res_correct, res_rt, res_settings_name, res_test_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
        values = (proj_id, sub_id, timestamp, interval, stim, correct, rt, settings_name, test_id)
        sql_db.execute_query(app.conn, insert_result, values)


#########################

# Create db object
sql_db = DB(APP_DB_PATH)
# Create the manager
sm = ScreenManager(transition=NoTransition())
# add screens
sm.add_widget(TitleScreen(name='title'))
sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(DBScreen(name='db'))
sm.add_widget(ProjectScreen(name='project'))
sm.add_widget(ResultsScreen(name='results'))
sm.add_widget(NewSubjectScreen(name='subject'))
sm.add_widget(UpdateSubjectScreen(name='update_subject'))
sm.add_widget(SettingsScreen(name='settings'))
sm.add_widget(TestScreen(name='test'))

# App Class
class PasatApp(App):
    # establish db connection
    conn = sql_db.create_connection()
    # establish json store
    store = JsonStore(APP_SETTINGS_PATH)
    # establish firebase staroge
    firebase_config = FirebaseConfig()
    firebase = pyrebase.initialize_app(firebase_config.config)
    # get device id based on mac address
    mac_id = hex(uuid.getnode())
    # set initial screen list to monitor history of visited screens
    screen_hist = []
    # set initial test variables
    ob_id = None
    proj_id = None
    setting_name = ''

    # build GUI
    def build(self):
        self._popup = Factory.CustomPopup()
        return sm

    # info popup open
    def open_popup(self, **kwargs):
        for id, val in kwargs.items():
            self._popup.ids[id].text = val
        self._popup.open()

    # update history of visited screens
    def update_screen_history(self, screen_name):
        self.screen_hist.append(screen_name)
        if len(self.screen_hist) > 2:
            self.screen_hist.pop(0)
        print(self.screen_hist)

if __name__ == "__main__":
    app = PasatApp()
    app.run()