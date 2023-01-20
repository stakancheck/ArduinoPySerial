<p align="center">
    <img src="assets/icon.png" width="20%">
</p>

<h2 align="center"> Программа для чтения значений из последовательного порта, передаваемых микроконтроллером. </h2>

## Начало работы
Для работы необходим python3.7 и выше. (Рекомендовано 3.10)

### Установка
**Linux**
```bash
git clone https://github.com/stakancheck/ArduinoPySerial
cd ArduinoPySerial
python3 -m pip install virtualenv
virtualenv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```
**Windows**
```bash
git clone https://github.com/stakancheck/ArduinoPySerial
cd ArduinoPySerial
py -m pip install venv
py -m venv venv
.\env\Scripts\activate
py -m pip install -r requirements.txt
```

### Запуск
**Linux**
```bash
python3 main.py
```
**Windows**
```bash
py main.py
```

### Конфигурация
Файл с настройками `preferences.cfg`
Каждый параметр имеет комментарий.
**После изменения параметров необходимо перезапустить программу**

### Описание работы
1. В окне *Settings* выбрать порт для платы и скорость передачи информации в порте.
> Если не отображается порт, поменяйте кабель, проверьте наличие драйверов, для Linux проверте входите ли вы в группу dialout.
2. В окне *Monitor* отображаеются текущие передаваемы показатели:
> X - первое значение
>
> Y - второе значение
>
> График - третье значение
>
> Максимальное и минимальное значения для третьего показателя можно задать в файле конфигураций. Так график будет отображаться корректней.

### Автор 
<p>
  <img src="https://user-images.githubusercontent.com/49817414/209367182-cb6dfa81-cf0d-4293-85f1-c9de3e333724.png" width=10% align="left"/>
  <h3>Артём Суханов - Техлид | Программист - <a href="https://github.com/stakancheck/" title="Аккаунт на GitHub">GitHub</a></h3>
  <p>
    Мобильная разработка на Java | Десктоп разработка на Python | Парсинг | Анализ данных 
  </p>
  
</p>

</br>
<br clear="left"/>
