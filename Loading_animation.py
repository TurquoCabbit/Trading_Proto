from time import sleep

class delay_anima:
    def __init__(self) -> None:
        self.bar = ['▏', '▎', '▍', '▌', '▋', '▊', '▉', '█']
        self.cube = ['▄ ', '▀ ', ' ▀', ' ▄']
        self.interval = 0.25

    def anima_bar(self, time):
        self.cnt = (int)(time / self.interval)
        while self.cnt > 0:
            for i in self.bar:
                print('  {} '.format(i), end = '\r')
                sleep(self.interval)
                self.cnt -= 1
                if self.cnt < 1:
                    break

    def anima_cube(self, time, clockwise = False):
        self.cnt = (int)(time / self.interval)
        while self.cnt > 0:
            for i in self.cube:
                print('  {}'.format(i), end = '\r')
                sleep(self.interval)
                self.cnt -= 1
                if self.cnt < 1:
                    break
    
    def delay(self, time):
        sleep(time)

    
if __name__ == '__main__':
    test = delay_anima()

    test.anima_bar(10)
    test.anima_cube(10)