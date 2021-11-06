from datetime import datetime
import os

class Log:
    def __init__(self, dir = '') -> None:
        self.dir = dir
        if self.dir != '':
            if not os.path.isdir(self.dir):
                os.mkdir(self.dir)

    def show(self, str = ''):
        time = datetime.now()
        print('{} : {}'.format(time.strftime('%H:%M:%S'), str))
        

    def log(self, str = ''):
        if self.dir != '':
            time = datetime.now()
        
            with open('{}/{}.log'.format(self.dir, time.strftime('%Y-%m-%d')), 'a') as file:
                file.writelines('{} : {}\n'.format(time.strftime('%Y-%m-%d %H:%M:%S'), str))


    def log_and_show(self, str = ''):
        time = datetime.now()
        print('{} : {}'.format(time.strftime('%H:%M:%S'), str))

        if self.dir != '':
            with open('{}/{}.log'.format(self.dir, time.strftime('%Y-%m-%d')), 'a') as file:
                file.writelines('{} : {}\n'.format(time.strftime('%Y-%m-%d %H:%M:%S'), str))
