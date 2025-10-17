from datetime import date, datetime


class thaidate:

    __slots__ = ['value', 'Buddhist', 'value_date']

    def __init__(self, value: date = None, Buddhist: bool = False) -> None:
        self.value: date = value
        self.Buddhist: bool = Buddhist
        self.value_date: list = []
        self.check_value_date()
        if int(self.value_date[2]) < int(self.value_date[0]):
            self.value_date.reverse()
        if self.Buddhist == False:
            self.value_date[2] = int(self.value_date[2])+543

    def check_value_date(self) -> None:
        if self.value in (None, ''):
            self.value = date.today()

        if isinstance(self.value, date):
            self.value_date = self.value.strftime('%Y %m %d').split()
        else:
            self.check_str_date()

    def check_str_date(self) -> None:
        try:
            if ' ' in self.value:
                self.value_date = self.value.split()
            elif '/' in self.value:
                self.value_date = self.value.split('/')
            elif '-' in self.value:
                self.value_date = self.value.split('-')
            else:
                raise Exception(
                    'คุณต้องกำหนดข้อมูลให้อยู่รูปแบบ yyyy mm dd, yyyy-mm-dd, yyyy/mm/dd เท่านั้น')

        except Exception as error:
            print('Caught this error: ' + repr(error))

    @property
    def day(self) -> int:
        return self.value_date[0]

    @property
    def full_month(self) -> str:
        full_thai_month: tuple = ('มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม',
                                  'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม')
        return full_thai_month[int(self.value_date[1]) - 1]

    @property
    def short_month(self) -> str:
        short_thai_month: tuple = ('ม.ค.', 'ก.พ.', 'มี.ค', 'เม.ษ.', 'พ.ค.',
                                   'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.')
        return short_thai_month[int(self.value_date[1]) - 1]

    @property
    def year(self) -> int:
        return self.value_date[2]

    @property
    def weekday(self) -> str:
        weekDays: tuple = ("วันอาทิตย์", "วันจันทร์", "วันอังคาร",
                           "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์")
        date_week_day: date = date(int(self.value_date[2]), int(
            self.value_date[1]), int(self.value_date[0]))
        return weekDays[date_week_day.weekday() - 1]

    @property
    def date(self) -> str:
        return f'{self.day} {self.full_month} {self.year}'

    @property
    def short_date(self) -> str:
        return f'{self.day} {self.short_month} {self.year}'

    @property
    def full_date(self) -> int:
        return f'{self.weekday}ที่ {self.day} เดือน {self.full_month} ปีพุทธศักราช {self.year}'

    @property
    def rattanakosin_era(self) -> int:
        return self.year - 2324
    
    
    
class thaidatetime(thaidate):
    __slots__ = ['value', 'Buddhist', 'value_date', 'value_time']
    
    def __init__(self, value: datetime = None, Buddhist: bool = False) -> None:
        self.value: date = value
        self.Buddhist: bool = Buddhist
        self.value_date: list = []
        self.value_time: list = []
        self.check_value_datetime()
        print(self.value_date)
        if int(self.value_date[2]) < int(self.value_date[0]):
            self.value_date.reverse()
        if self.Buddhist == False:
            self.value_date[2] = int(self.value_date[2])+543
        
    def check_value_datetime(self) -> None:
        if self.value in (None, ''):
            self.value = datetime.now()

        if isinstance(self.value, datetime):
            self.value_date = self.value.strftime('%Y %m %d %H %M %S').split()[:3]
            self.value_time = self.value.strftime('%Y %m %d %H %M %S').split()[3:6]
        elif isinstance(self.value, date):
            raise Exception(
                        'คุณใส่ argument ผิด หากคุณต้องการใช้ class thaidatetime() คุณต้องใส่ argument เป็น class datetime() หรือ string ตาม format ที่กำหนดไว้เท่านั้น')
        else:
            self.check_str_datetime()
            
    def check_str_datetime(self) -> None:
        datetime : list = []
        try:
            datetime = self.value.split()
            if len(datetime) == 2 :
            
                if '/' in datetime[0]:
                    self.value_date = datetime[0].split('/')
                elif '-' in datetime[0]:
                    self.value_date = datetime[0].split('-')
                elif ' ' in datetime[0]:
                    self.value_date = datetime[0].split()
                else:
                    raise Exception(
                        'คุณต้องกำหนดข้อมูลให้อยู่รูปแบบ yyyy mm dd HH:MM:SS, yyyy-mm-dd HH:MM:SS, yyyy/mm/dd HH:MM:SS เท่านั้น')

                if ':' in datetime[1]:
                    self.value_time = datetime[1].split(":")
                else:
                    raise Exception(
                        'คุณต้องกำหนดข้อมูลให้อยู่รูปแบบ yyyy mm dd HH:MM:SS, yyyy-mm-dd HH:MM:SS, yyyy/mm/dd HH:MM:SS เท่านั้น')
                
            else:
                self.value_date = datetime[:3]
                self.value_time = datetime[3:6]
                
        except Exception as error:
            print('Caught this error: ' + repr(error))
            
            
    @property
    def hour(self) -> int:
        return self.value_time[0] 
    
    
    @property
    def minute(self) -> int:
        return self.value_time[1] 
    
    
    @property
    def second(self) -> int:
        return self.value_time[2] 
    
    
    @property
    def fulltime(self) -> str:
        return f'เวลา {self.hour} นาฬิกา {self.minute} นาที {self.second} วินาที'


    @property
    def datetime(self) -> str:
        return f'{self.date} {self.fulltime}' 
    
    
    @property
    def fulldatetime(self) -> str:
        return f'{self.full_date} {self.fulltime}'
    
    @property
    def short_datetime(self) -> str:
        return f'{self.short_date} {self.fulltime}'
    